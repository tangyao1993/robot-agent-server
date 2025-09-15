import torch
import numpy as np
import asyncio
from silero_vad import load_silero_vad

class VADProcessor:
    """
    使用 Silero-VAD 进行语音活动检测的处理器。
    这是一个更现代、更抗噪音的VAD模型。
    """
    def __init__(self, model, threshold=0.5, sample_rate=16000, min_silence_duration_ms=1000):
        """
        初始化 Silero VAD 处理器 (轻量级，无IO)。

        Args:
            model: 预先加载的 Silero VAD 模型。
            threshold (float): 语音概率阈值 (0-1)，高于此值被认为是语音。
            sample_rate (int): 音频采样率 (必须是 8000 或 16000)。
            min_silence_duration_ms (int): 判定为结束所需的静音总时长 (毫秒)。
        """
        self.model = model
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.min_silence_duration_ms = min_silence_duration_ms

        self.window_size_samples = 512 if sample_rate == 16000 else 256
        
        self._buffer = torch.empty(0)
        self.silent_samples_count = 0
        self.speech_started = False
        
    def _bytes_to_float_tensor(self, audio_bytes):
        """将16-bit PCM字节流转换为float32的PyTorch Tensor"""
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return torch.from_numpy(audio_np)

    def process(self, audio_chunk_bytes):
        """
        处理传入的音频块，进行VAD分析。

        Args:
            audio_chunk_bytes (bytes): 16-bit PCM 单声道音频数据。

        Returns:
            bool: True 表示检测到长时间静音，应停止录音；False 则继续。
        """
        if not audio_chunk_bytes:
            return False

        audio_tensor = self._bytes_to_float_tensor(audio_chunk_bytes)
        self._buffer = torch.cat([self._buffer, audio_tensor])

        while self._buffer.shape[0] >= self.window_size_samples:
            chunk_to_process = self._buffer[:self.window_size_samples]
            self._buffer = self._buffer[self.window_size_samples:]
            
            speech_prob = self.model(chunk_to_process, self.sample_rate).item()
            
            if speech_prob > self.threshold:
                if not self.speech_started:
                    print(f"VAD: 检测到语音开始 (概率: {speech_prob:.2f})")
                self.speech_started = True
                self.silent_samples_count = 0
            elif self.speech_started:
                self.silent_samples_count += self.window_size_samples
            
            min_silence_samples = self.sample_rate * self.min_silence_duration_ms / 1000
            if self.silent_samples_count >= min_silence_samples:
                print(f"VAD: 检测到 {self.min_silence_duration_ms}ms 静音，触发停止。")
                return True
        
        return False 