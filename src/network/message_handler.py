import json
import logging
import asyncio
from .client_session import ClientSession
from ..database.operations import DatabaseManager
from ..processors.audio_processor import AudioProcessor
from ..processors.asr_processor import SpeechRecognizer
from ..processors.tts_processor import TTSProcessor
from ..workflow.graph import run_workflow

logger = logging.getLogger("MessageHandler")
class MessageHandler:
    def __init__(self, db_manager: DatabaseManager, audio_processor: AudioProcessor, speech_recognizer: SpeechRecognizer):
        self.db_manager = db_manager
        self.audio_processor = audio_processor
        self.speech_recognizer = speech_recognizer
        self.sessions: dict = {}
        self.tts_processor = TTSProcessor()
        
        logger.info("MessageHandler初始化完成")

    async def on_connect(self, websocket):
        logger.info(f"新客户端连接: {websocket.remote_address}")
        self.sessions[websocket] = ClientSession(websocket)

    async def on_disconnect(self, websocket):
        session = self.sessions.pop(websocket, None)
        if session:
            logger.info(f"客户端 {session.mac_addr or session.remote_address} 已断开")

    async def handle_message(self, websocket, message):
        session = self.sessions.get(websocket)
        if not session: return

        if isinstance(message, bytes):
            # 音频数据处理
            await self._handle_audio_data(session, message)
        else:
            try:
                data = json.loads(message)
                method = data.get("method")

                if method == "mcp/registerTools":
                    await self._handle_registration(session, data)
                elif method == "mcp/audio/end_stream":
                    # 客户端结束录音
                    await self._handle_end_stream(session)
                else:
                    logger.debug(f"收到其他消息: {method}")
                
            except (json.JSONDecodeError, KeyError):
                logger.warning(f"收到非JSON或无效MCP消息: {message}")

    async def _handle_end_stream(self, session: ClientSession):
        """处理音频流结束"""
        logger.info(f"[{session.mac_addr}] 收到结束音频流信号，处理已录制音频。")
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
            
            response_data = {"id": rpc_request.get("id"), "result": {"status": "success"}}
            await session.send_json(response_data)
            logger.info(f"设备 {mac_addr} 注册成功")
        except Exception as e:
            logger.error(f"注册时出错: {e}", exc_info=True)

    async def _handle_audio_data(self, session: ClientSession, message: bytes):
        """处理音频数据"""
        session.append_audio(message)

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
        """简化的LLM控制器"""
        try:
            # 使用新的工作流
            result = await run_workflow(
                user_text=text,
                session_id=session.session_id,
                device_info={"mac_addr": session.mac_addr}
            )
            
            if result.bot_text:
                logger.info(f"LLM回复: {result.bot_text[:100]}...")
                
                # 使用TTS生成音频
                audio_data = await self.tts_processor.text_to_speech(result.bot_text)
                if audio_data:
                    logger.info(f"准备发送音频数据到客户端 [{session.mac_addr}], 大小: {len(audio_data)} 字节")
                    await session.send_audio(audio_data)
                    logger.info(f"音频数据发送完成")
                else:
                    logger.warning(f"TTS返回空音频数据，文本: {result.bot_text}")
                    
        except Exception as e:
            logger.error(f"LLM处理失败: {e}", exc_info=True)
            error_text = "抱歉，处理您的请求时出现了问题。"
            audio_data = await self.tts_processor.text_to_speech(error_text)
            if audio_data:
                await session.send_audio(audio_data)
    async def on_timeout(self, websocket):
        logger.warning(f"客户端 {websocket.remote_address} 连接超时，准备关闭。")
        await websocket.close(code=1000, reason="Timeout")
