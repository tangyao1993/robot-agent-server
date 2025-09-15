import asyncio
import websockets
import logging
import os

logger = logging.getLogger("WebSocketServer")

class WebSocketServer:
    """WebSocket服务器类，处理客户端连接和通信"""
    
    def __init__(self, host, port, ws_path, on_connect=None, on_message=None, on_disconnect=None, on_timeout=None, timeout=6000):
        """
        初始化WebSocket服务器
        
        Args:
            host: 主机名或IP地址
            port: 端口号
            ws_path: WebSocket路径
            on_connect: 新客户端连接时的回调函数
                        函数签名: def handler(websocket)
            on_message: 收到消息时的回调函数
                        函数签名: async def handler(websocket, message)
            on_disconnect: 客户端断开连接时的回调函数
                        函数签名: async def handler(websocket)
            on_timeout: 客户端闲置超时回调函数
                        函数签名: async def handler(websocket)
            timeout: 闲置超时秒数
        """
        self.host = host
        self.port = port
        self.ws_path = ws_path
        self.on_connect = on_connect
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self.on_timeout = on_timeout
        self.timeout = timeout
        self.connected_clients = set()
        
    async def handler(self, websocket):
        """
        处理WebSocket连接和消息
        
        Args:
            websocket: WebSocket连接
        """
        # 处理新连接
        remote_address = websocket.remote_address
        logger.info(f"客户端 {remote_address} 已连接. 当前连接数: {len(self.connected_clients) + 1}")
        self.connected_clients.add(websocket)
        if self.on_connect:
            await self.on_connect(websocket)

        try:
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), self.timeout)
                    if self.on_message:
                        await self.on_message(websocket, message)
                    else:
                        logger.warning("未设置消息处理函数 (on_message)，消息将被忽略")
                except asyncio.TimeoutError:
                    logger.info(f"客户端 {websocket.remote_address} 闲置超时")
                    if self.on_timeout:
                        await self.on_timeout(websocket)
                    # on_timeout 处理器负责关闭连接，这里直接退出循环
                    break
        except websockets.exceptions.ConnectionClosed as e:
            # 区分是正常关闭还是异常关闭
            if e.code == 1000 or e.code == 1001:
                logger.warning(f"客户端 {remote_address} 主动断开连接: {e}")
            else:
                logger.error(f"与客户端 {remote_address} 的连接异常关闭: {e}")
        except Exception as e:
            logger.error(f"处理客户端 {remote_address} 时发生错误: {e}", exc_info=True)
        finally:
            # 处理断开连接
            self.connected_clients.remove(websocket)
            if self.on_disconnect:
                await self.on_disconnect(websocket)
            logger.info(f"客户端 {remote_address} 已断开连接, 当前客户端数量: {len(self.connected_clients)}")
    
    def get_client_count(self):
        """获取当前连接的客户端数量"""
        return len(self.connected_clients)
            
    async def start(self):
        """启动WebSocket服务器"""
        logger.info(f"启动WebSocket服务器于 ws://{self.host}:{self.port}{self.ws_path}")
        # 通过设置 ping_interval=None 禁用自动心跳检测，防止客户端因不支持ping/pong而超时断开
        async with websockets.serve(self.handler, self.host, self.port, ping_interval=None):
            await asyncio.Future()  # run forever 