"""
简化的TTS处理器 - 使用本地IndexTTS模型
"""

import asyncio
import logging
import wave
from pathlib import Path
from typing import AsyncGenerator, Optional
import os

from simulator.backend.tts_provider import create_tts_provider, BaseTTSProvider


class TTSProcessor:
    def __init__(
        self,
        mode: str = "index",
        repo_root: Optional[str] = None,
        voice_path: Optional[str] = None,
        chunk_size: int = 64 * 1024,
    ):
        """
        初始化TTS处理器

        Args:
            mode: 本地TTS模式，默认使用IndexTTS
            repo_root: IndexTTS仓库目录
            voice_path: 参考音色音频文件路径
            chunk_size: 流式输出时的块大小
        """
        self.logger = logging.getLogger("TTSProcessor")
        self.chunk_size = chunk_size
        self._provider: Optional[BaseTTSProvider] = None

        resolved_mode = os.getenv("TTS_MODE", mode)
        resolved_repo_root = repo_root or os.getenv("INDEX_TTS_ROOT")
        resolved_voice_path = voice_path or os.getenv("INDEX_TTS_VOICE")

        try:
            self._provider = create_tts_provider(
                resolved_mode,
                repo_root=resolved_repo_root,
                voice_path=resolved_voice_path,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"初始化TTS提供者失败: {exc}")
            self._provider = None

        # 默认音频参数，后续会在生成音频后根据实际文件更新
        self.sample_rate = 16000
        self.channels = 1
        self.sample_width = 2

    async def _synthesize(self, text: str) -> Optional[Path]:
        if not text or not text.strip():
            self.logger.warning("收到空文本，跳过TTS合成。")
            return None
        if not self._provider:
            self.logger.error("TTS提供者未正确初始化。")
            return None

        try:
            return await asyncio.to_thread(self._provider.synthesize, text)
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"TTS合成失败: {exc}")
            return None

    async def _load_audio_bytes(self, file_path: Path) -> bytes:
        def _read() -> bytes:
            return file_path.read_bytes()

        return await asyncio.to_thread(_read)

    async def _update_audio_meta(self, file_path: Path) -> None:
        def _read_meta() -> tuple[int, int, int]:
            with wave.open(str(file_path), "rb") as wav_file:
                return (
                    wav_file.getframerate(),
                    wav_file.getnchannels(),
                    wav_file.getsampwidth(),
                )

        try:
            frame_rate, channels, sample_width = await asyncio.to_thread(_read_meta)
        except Exception:
            return

        self.sample_rate = frame_rate
        self.channels = channels
        self.sample_width = sample_width

    async def text_to_speech_generator(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        核心功能：将单段文本转换为TTS音频流生成器。
        这个函数只负责生成音频，不负责发送。
        """
        wav_path = await self._synthesize(text)
        if not wav_path:
            yield b"\x00" * 3200
            return

        await self._update_audio_meta(wav_path)

        audio_bytes = await self._load_audio_bytes(wav_path)
        for start in range(0, len(audio_bytes), self.chunk_size):
            yield audio_bytes[start : start + self.chunk_size]

    async def text_to_speech(self, text: str) -> bytes:
        """
        将文本转换为音频数据（完整音频）
        """
        wav_path = await self._synthesize(text)
        if not wav_path:
            return b"\x00" * 3200

        await self._update_audio_meta(wav_path)
        audio_bytes = await self._load_audio_bytes(wav_path)
        self.logger.info(f"TTS返回音频数据大小: {len(audio_bytes)} 字节")
        return audio_bytes

    def is_ready(self) -> bool:
        """检查TTS服务是否可用"""
        return self._provider is not None
