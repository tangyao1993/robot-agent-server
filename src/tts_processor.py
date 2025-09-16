"""
TTS工具类 - 直接使用音频流播放
"""

import asyncio
import logging
import httpx
import pygame
import io
import numpy as np
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)

class TTSProcessor:
    def __init__(self, api_url: str = "192.168.1.4:5001", api_key: Optional[str] = None):
        """
        初始化TTS处理器
        
        Args:
            api_url: 本地TTS API地址
            api_key: API密钥（如果需要）
        """
        self.api_url = api_url
        self.api_key = api_key
        self.logger = logging.getLogger("TTSProcessor")
        
        # 初始化pygame音频 - 使用单声道
        pygame.mixer.init(frequency=16000, size=-16, channels=1, buffer=512)
        
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
                    
                    async for chunk in response.aiter_bytes():
                        yield chunk

        except httpx.ReadTimeout:
            self.logger.error("TTS API 请求超时")
            # 同样产生静音
            yield b'\x00' * 3200
        except Exception as e:
            self.logger.error(f"TTS generator 发生未知错误: {e}", exc_info=True)
            yield b'\x00' * 3200

    async def text_stream_to_speech_stream(self, text_generator: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """
        新函数：将一个异步文本块生成器转换为一个连续的音频流生成器。
        """
        async for text_chunk in text_generator:
            cleaned_chunk = text_chunk.strip()
            if not cleaned_chunk:
                continue
            
            # 对于每个文本块，调用核心的音频生成器并迭代其结果
            async for audio_chunk in self.text_to_speech_generator(cleaned_chunk):
                yield audio_chunk

    async def play_text(self, text: str) -> None:
        """
        直接播放文本的语音，不保存为文件
        
        Args:
            text: 要转换成语音的文本
        """
        if not text:
            self.logger.warning("收到空文本，跳过播放")
            return
            
        try:
            self.logger.info(f"开始播放文本: {text}")
            
            # 创建音频流缓冲区
            audio_buffer = io.BytesIO()
            
            # 流式获取音频数据
            async for audio_chunk in self.text_to_speech_generator(text):
                if audio_chunk:
                    audio_buffer.write(audio_chunk)
                    
                    # 当缓冲区有足够数据时播放
                    if audio_buffer.tell() >= 8192:  # 8KB缓冲区
                        await self._play_audio_chunk(audio_buffer)
            
            # 播放剩余的音频数据
            if audio_buffer.tell() > 0:
                await self._play_audio_chunk(audio_buffer)
                
            self.logger.info("语音播放完成")
            
        except Exception as e:
            self.logger.error(f"TTS播放发生错误: {e}", exc_info=True)
            
    async def _play_audio_chunk(self, audio_buffer: io.BytesIO) -> None:
        """
        播放音频块
        
        Args:
            audio_buffer: 音频数据缓冲区
        """
        try:
            # 获取当前缓冲区数据
            audio_data = audio_buffer.getvalue()
            
            if len(audio_data) == 0:
                return
                
            # 重置缓冲区
            audio_buffer.seek(0)
            audio_buffer.truncate()
            
            # 在异步线程中播放音频
            await asyncio.get_event_loop().run_in_executor(
                None, 
                self._play_audio_sync, 
                audio_data
            )
            
        except Exception as e:
            self.logger.error(f"播放音频块时发生错误: {e}", exc_info=True)
            
    def _play_audio_sync(self, audio_data: bytes) -> None:
        """
        同步播放音频数据（在单独线程中执行）
        
        Args:
            audio_data: 音频数据
        """
        try:
            # 转换字节数据为numpy数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # 使用pygame播放音频
            sound = pygame.sndarray.make_sound(audio_array)
            sound.play()
            
            # 等待播放完成
            while pygame.mixer.get_busy():
                pygame.time.wait(10)
                
        except Exception as e:
            self.logger.error(f"同步播放音频时发生错误: {e}", exc_info=True)
            
    async def play_text_sync(self, text: str) -> None:
        """
        同步播放文本（阻塞式）
        
        Args:
            text: 要转换成语音的文本
        """
        await self.play_text(text)
        
    def close(self) -> None:
        """关闭音频设备"""
        try:
            pygame.mixer.quit()
            self.logger.info("音频设备已关闭")
        except Exception as e:
            self.logger.error(f"关闭音频设备时发生错误: {e}", exc_info=True)


# 使用示例
async def main():
    # 创建TTS处理器
    tts_processor = TTSProcessor()
    
    try:
        # 播放文本
        await tts_processor.play_text("你好啊，你叫什么")
        
        # 等待播放完成
        await asyncio.sleep(1)
        
        # 播放更多文本
        await tts_processor.play_text("这是一个测试语音播放的例子")
        
    finally:
        # 关闭处理器
        tts_processor.close()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())