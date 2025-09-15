import asyncio
import json
from typing import List, Dict, Any
from websockets.protocol import State
from websockets.server import WebSocketServerProtocol
import logging
from mcp_protocol_builder import create_mcp_event


logger = logging.getLogger(__name__)

class ClientSession:
    """封装单个客户端连接的所有状态信息"""

    def __init__(self, websocket: WebSocketServerProtocol):
        self.websocket = websocket
        self.remote_address = websocket.remote_address
        self.mac_addr: str | None = None
        # self.history: List[Dict[str, Any]] = []
        self.tools: List[Dict[str, Any]] = []
        self.audio_buffer: bytearray = bytearray()
        self.tool_futures: Dict[str, asyncio.Future] = {}
        self.response_templates: Dict[str, List[str]] = {} # 缓存响应模板
        self._is_registered = False

    def register(self, mac_addr: str, tools: List[Dict[str, Any]]):
        self.mac_addr = mac_addr
        self.tools = tools
        self._is_registered = True

    def is_registered(self) -> bool:
        return self._is_registered

    def update_tools(self, tools: List[Dict[str, Any]]):
        self.tools = tools

    def get_tools(self) -> List[Dict[str, Any]]:
        # 定义服务器端提供的本地工具
        local_tools = [
            {
                "name": "get_music",
                "description": "当用户想要听歌时使用此工具。请优先、直接地调用此工具，即使用户只提供了歌曲名称，或者歌名看起来很模糊、不完整，甚至是单个汉字。你的主要任务是根据用户输入填充参数并调用工具，而不是与用户对话寻求澄清。",
                "main_type": "local",  # 表示这是一个本地(服务器端)工具
                "sub_type": "async",   
                "parameters": {
                "type": "object",
                "properties": {
                    "song_name": {
                    "type": "string",
                    "description": "用户想要播放的歌曲名称。必须严格按照用户的原始输入提取，即使歌名很常见（如 '猜'）或只是一个单字（如 '小'）。不要进行任何补充或联想。e.g. '稻香', '七里香', '猜', '小'"
                    },
                    "artist_name": {
                    "type": "string",
                    "description": "歌曲的演唱者或艺术家。必须严格、完整地使用用户提供的原始名称，不要进行任何形式的拆分、简化或联想。例如，如果用户说'二硕'，就应该提取'二硕'，而不是'硕'或'李钟硕'。"
                    }
                },
                "required": [
                    "song_name"
                ]
                }
            }
        ]
        # 合并客户端工具和本地工具
        return self.tools + local_tools
        
    # def get_history(self) -> List[Dict[str, Any]]:
    #     return self.history

    # def add_message(self, message: Dict[str, Any]):
    #     """添加一条消息到会话历史中。"""
    #     self.history.append(message)
    
    # def clear_history(self):
    #     self.history.clear()

    def append_audio(self, chunk: bytes):
        self.audio_buffer.extend(chunk)

    def clear_audio_buffer(self):
        """清空音频缓冲区。"""
        self.audio_buffer.clear()

    def get_full_audio_and_clear(self) -> bytes:
        full_data = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        return full_data

    async def send_json(self, data: Dict[str, Any]):
        """异步发送JSON文本数据到客户端"""
        if self.websocket.state == State.OPEN:
            try:
                logger.info(f"=========发送服务端JSON: {data}")
                await self.websocket.send(json.dumps(data, ensure_ascii=False))
            except Exception as e:
                logger.error(f"发送JSON到 {self.mac_addr or self.remote_address} 失败: {e}")
        else:
            logger.warning(f"尝试向已关闭的连接 ({self.mac_addr or self.remote_address}) 发送JSON，已忽略。")
            
    async def send_binary(self, data: bytes):
        """异步发送二进制数据到客户端"""
        if self.websocket.state == State.OPEN:
            try:
                await self.websocket.send(data)
            except Exception as e:
                logger.error(f"发送二进制数据到 {self.mac_addr or self.remote_address} 失败: {e}")
        else:
            logger.warning(f"尝试向已关闭的连接 ({self.mac_addr or self.remote_address}) 发送二进制数据，已忽略。")

    async def send_mcp_event(self, method: str, params: Dict[str, Any] = None):
        await self.send_json(create_mcp_event(method,params))

    async def stream_audio(self, audio_generator):
        """
        根据新的混合协议，向客户端发送完整的音频流。
        1. 发送 'stream_start' MCP控制消息。
        2. 流式发送二进制音频数据。
        3. 发送一个0长度的二进制消息作为结束信号。
        """
        # 1. 发送控制指令
        await self.send_mcp_event(method="mcp/server/start_audio")
        
        # 2. 流式传输音频数据
        async for chunk in audio_generator:
            await self.send_binary(chunk)
            
        # 3. 发送结束信号 (0长度的二进制包)
        await self.send_binary(b'') 