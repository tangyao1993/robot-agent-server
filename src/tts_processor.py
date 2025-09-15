import httpx
import logging
from typing import AsyncGenerator

from src.config import get_tts_config, get_tts_model_config

logger = logging.getLogger("src.tts_processor")

class TTSProcessor:
    def __init__(self):
        self.config = get_tts_config()
        self.model_config = get_tts_model_config()
        self.logger = logging.getLogger("TTSProcessor")

    async def text_to_speech_generator(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        核心功能：将单段文本转换为TTS音频流生成器。
        这个函数只负责生成音频，不负责发送。
        """
        if not text:
            self.logger.warning("TTS aenerator收到了空文本，直接返回。")
            return

        headers = {"Authorization": f"Bearer {self.config['api_key']}"}
        request_body = {
            "model": self.model_config["model"],
            "text": text,
            "voice_id": self.model_config["voice_id"],
            "output_format": self.model_config["output_format"],
            "audio_sample_rate": self.model_config["audio_sample_rate"],
            "speed": self.model_config["speed"],
            "stream": True
        }

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", self.config["api_url"], json=request_body, headers=headers, timeout=20.0) as response:
                
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
