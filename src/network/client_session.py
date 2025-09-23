import asyncio
import json
from typing import List, Dict, Any
from websockets.protocol import State
from websockets.server import WebSocketServerProtocol
import logging
from ..utils.mcp_protocol import create_mcp_event


logger = logging.getLogger(__name__)

class ClientSession:
    """封装单个客户端连接的所有状态信息"""

    def __init__(self, websocket: WebSocketServerProtocol):
        self.websocket = websocket
        self.remote_address = websocket.remote_address
        self.mac_addr: str | None = None
        self.tools: List[Dict[str, Any]] = []
        self.audio_buffer: bytearray = bytearray()
        self.session_id: str = f"session_{id(self)}"
        self._is_registered = False

    def register(self, mac_addr: str, tools: List[Dict[str, Any]]):
        self.mac_addr = mac_addr
        self.tools = tools
        self._is_registered = True

    def is_registered(self) -> bool:
        return self._is_registered

    def get_tools(self) -> List[Dict[str, Any]]:
        """获取客户端工具列表"""
        return self.tools

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
                logger.info(f"发送二进制数据到 [{self.mac_addr}], 大小: {len(data)} 字节")
                await self.websocket.send(data)
                logger.info(f"二进制数据发送成功")
            except Exception as e:
                logger.error(f"发送二进制数据到 {self.mac_addr or self.remote_address} 失败: {e}")
        else:
            logger.warning(f"尝试向已关闭的连接 ({self.mac_addr or self.remote_address}) 发送二进制数据，已忽略。")

    async def send_mcp_event(self, method: str, params: Dict[str, Any] = None):
        await self.send_json(create_mcp_event(method, params))

    async def send_audio(self, audio_data: bytes):
        """发送音频数据到客户端"""
        if not audio_data:
            return
            
        logger.info(f"开始发送音频流程，数据大小: {len(audio_data)} 字节")
        
        # 1. 发送控制指令
        logger.info("发送 start_audio 指令...")
        await self.send_mcp_event(method="mcp/server/start_audio")
        logger.info("start_audio 指令发送完成")
        
        # 2. 发送音频数据（分块发送）
        logger.info("发送音频数据...")
        chunk_size = 64 * 1024  # 64KB chunks
        total_sent = 0
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            await self.send_binary(chunk)
            total_sent += len(chunk)
            logger.info(f"已发送 {total_sent}/{len(audio_data)} 字节")
        
        logger.info("音频数据发送完成")
            
        # 3. 发送结束信号
        logger.info("发送结束信号...")
        await self.send_binary(b'')
        logger.info("结束信号发送完成")
        logger.info("音频流程发送完成") 