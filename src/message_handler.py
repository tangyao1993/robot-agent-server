import json
import logging
import asyncio
from client_session import ClientSession
from database_manager import DatabaseManager
from audio_processor import AudioProcessor
from fun_asr_local import SpeechRecognizer
from tts_processor import TTSProcessor
from mcp_protocol_builder import create_registration_response
from vad_processor import VADProcessor
from silero_vad import load_silero_vad
from llm_workflow.llm_main import build_workflow

logger = logging.getLogger("MessageHandler")
class MessageHandler:
    def __init__(self, db_manager: DatabaseManager, audio_processor: AudioProcessor, speech_recognizer: SpeechRecognizer):
        self.db_manager = db_manager
        self.audio_processor = audio_processor
        self.speech_recognizer = speech_recognizer
        self.sessions: dict = {}
        self.tts_processor = TTSProcessor()
        self.vad_processors: dict = {}
        self.llm_app = build_workflow()
        
        logger.info("正在加载 SileroVAD 模型...")
        try:
            self.vad_model = load_silero_vad(onnx=True)
            logger.info("SileroVAD 模型加载成功。")
        except Exception as e:
            logger.error(f"无法加载 SileroVAD 模型: {e}", exc_info=True)
            self.vad_model = None

    async def on_connect(self, websocket):
        logger.info(f"新客户端连接: {websocket.remote_address}")
        self.sessions[websocket] = ClientSession(websocket)

    async def on_disconnect(self, websocket):
        session = self.sessions.pop(websocket, None)
        if session:
            logger.info(f"客户端 {session.mac_addr or session.remote_address} 已断开")
        if websocket in self.vad_processors:
            del self.vad_processors[websocket]
            logger.info(f"已清理客户端 {session.remote_address} 的VAD实例")

    async def handle_message(self, websocket, message):
        session = self.sessions.get(websocket)
        if not session: return

        if isinstance(message, bytes):
            # Audio stream from old or new client
            if websocket in self.vad_processors:
                await self._handle_audio_stream(session, message)
                
        else:
            try:
                logger.info(f"=========收到客户端消息: {message}")
                data = json.loads(message)
                method = data.get("method")

                if method == "mcp/registerTools":
                    await self._handle_registration(session, data)
                elif method == "mcp/audio/start_stream":
                    await self._handle_start_stream(session)
                elif method == "mcp/audio/end_stream":
                    # This is from the old client when user stops talking
                    await self._handle_end_stream(session, data.get("params", {}).get("reason"))
                elif "id" in data and ("result" in data or "error" in data):
                    # 这个逻辑现在被集中处理，但为兼容可能保留
                    # handle_tool_result(data, session.tool_futures)
                    logger.warning(f"收到一个未处理的工具结果: {data}")
                
            except (json.JSONDecodeError, KeyError):
                logger.warning(f"收到非JSON或无效MCP消息: {message}")

    async def _handle_start_stream(self, session: ClientSession):
        if not self.vad_model:
            logger.error("VAD模型未加载，无法处理音频流。")
            return
            
        processor = VADProcessor(self.vad_model, threshold=0.3)
        self.vad_processors[session.websocket] = processor
        session.clear_audio_buffer()

    async def _handle_end_stream(self, session: ClientSession, reason: str = None):
        if reason == "timeout":
            logger.info(f"[{session.mac_addr}] 客户端聆听超时，会话结束。")
            if session.websocket in self.vad_processors:
                del self.vad_processors[session.websocket]
            return

        logger.info(f"[{session.mac_addr}] 收到结束音频流信号，处理已录制音频。")
        if session.websocket in self.vad_processors:
            del self.vad_processors[session.websocket]
        
        await self._process_completed_audio(session)

    async def _stop_client_recording(self, session: ClientSession):
        logger.info(f"VAD触发停止: 正在通知客户端 {session.mac_addr} 停止录音。")
        if session.websocket in self.vad_processors:
            del self.vad_processors[session.websocket]

        stop_message = {
            "jsonrpc": "2.0",
            "method": "mcp/audio/stop_stream",
            "params": {}
        }
        await session.send_json(stop_message)
        await self._process_completed_audio(session)

    async def _handle_registration(self, session: ClientSession, rpc_request: dict):
        try:
            params = rpc_request.get("params", {})
            mac_addr = params.get("mac_addr")
            if not mac_addr:
                await session.websocket.close()
                return

            session.register(mac_addr, params.get("tools", []))
            if not await self.db_manager.get_device(mac_addr):
                await self.db_manager.register_device(mac_addr)
            
            await self.db_manager.update_device_login(mac_addr)
            
            response = create_registration_response(rpc_request.get("id"))
            await session.send_json(response)
            logger.info(f"设备 {mac_addr} 注册成功")
        except Exception as e:
            logger.error(f"注册时出错: {e}", exc_info=True)

    async def _handle_audio_stream(self, session: ClientSession, message: bytes):
        vad_processor = self.vad_processors.get(session.websocket)
        if not vad_processor:
            return

        session.append_audio(message)
        should_stop = vad_processor.process(message)
        if should_stop:
            await self._stop_client_recording(session)

    async def _process_completed_audio(self, session: ClientSession):       
        full_audio_data = session.get_full_audio_and_clear()
        if not full_audio_data: return

        file_path = self.audio_processor.save_as_wav(full_audio_data, session.remote_address)
        if not file_path: return
        
        text = self.speech_recognizer.recognize(file_path)
        logger.info(f"[{session.mac_addr}] ASR识别结果: {text}")
        
        # 统一入口，调用新的总控制器
        await self._agent_controller(text, session)

    async def _agent_controller(self, text: str, session: ClientSession):
        async def llm_text_generator():
            llm_stream = self.llm_app.astream(
                {"user_input": text, "tools_definition": session.get_tools()},
                config={
                    "configurable": {
                        'mac_addr': session.mac_addr,
                        'client_session': session
                    }
                }
            )
            async for event in llm_stream:
                if "messages" in event:
                    # 'messages' 是一个 AIMessageChunk 对象的异步生成器
                    async for chunk in event["messages"]:
                        if isinstance(chunk.content, str) and chunk.content:
                            logger.info(f"LLM Chunk: {chunk.content}")
                            yield chunk.content
        audio_generator = self.tts_processor.text_stream_to_speech_stream(llm_text_generator())
        await session.stream_audio(audio_generator)
    async def on_timeout(self, websocket):
        logger.warning(f"客户端 {websocket.remote_address} 连接超时，准备关闭。")
        await websocket.close(code=1000, reason="Timeout")
