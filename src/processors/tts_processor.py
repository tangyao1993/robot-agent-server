"""
简化的TTS处理器 - 移除pygame依赖
"""

import logging
import httpx
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)

class TTSProcessor:
    def __init__(self, api_url: str = "192.168.1.5:5001", api_key: Optional[str] = None):
        """
        初始化TTS处理器
        
        Args:
            api_url: 本地TTS API地址
            api_key: API密钥（如果需要）
        """
        self.api_url = api_url
        self.api_key = api_key
        self.logger = logging.getLogger("TTSProcessor")
        
        # 音频参数
        self.sample_rate = 16000
        self.channels = 1
        self.sample_width = 2

    async def text_to_speech_generator(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        核心功能：将单段文本转换为TTS音频流生成器。
        这个函数只负责生成音频，不负责发送。
        """
        if not text:
            self.logger.warning("TTS generator收到了空文本，直接返回。")
            return

        # 构建请求
        headers = {
            'Content-Type': 'application/json'
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            
        data = {
            "text": text
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST", 
                    f"http://{self.api_url}", 
                    json=data, 
                    headers=headers
                ) as response:
                
                    if response.status_code != 200:
                        error_content = await response.aread()
                        self.logger.error(f"TTS API 请求失败: {response.status_code}, {error_content.decode()}")
                        # 产生一小段静音以避免下游音频流中断
                        yield b'\x00' * 3200 
                        return
                    
                    # 流式接收音频数据
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            yield chunk
                            
        except Exception as e:
            self.logger.error(f"TTS请求异常: {e}")
            # 产生静音以避免中断
            yield b'\x00' * 3200

    async def text_to_speech(self, text: str) -> bytes:
        """
        将文本转换为音频数据（完整音频）
        """
        if not text:
            return b'\x00' * 3200

        headers = {
            'Content-Type': 'application/json'
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            
        data = {
            "text": text
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"http://{self.api_url}", 
                    json=data, 
                    headers=headers
                )
                
                if response.status_code == 200:
                    return await response.aread()
                else:
                    self.logger.error(f"TTS API 请求失败: {response.status_code}")
                    return b'\x00' * 3200
                    
        except Exception as e:
            self.logger.error(f"TTS请求异常: {e}")
            return b'\x00' * 3200

    def is_ready(self) -> bool:
        """检查TTS服务是否可用"""
        return True