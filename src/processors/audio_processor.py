import wave
import logging
import os
from datetime import datetime

logger = logging.getLogger("AudioProcessor")

class AudioProcessor:
    """音频处理类，负责处理和保存音频数据"""
    
    def __init__(self, audio_dir):
        """
        初始化音频处理器
        
        Args:
            audio_dir: 音频文件保存目录
        """
        self.audio_dir = audio_dir
        os.makedirs(self.audio_dir, exist_ok=True)
        
    def save_as_wav(self, audio_data, remote_address, channels=1, sample_width=2, sample_rate=16000):
        """
        将原始PCM数据保存为WAV文件
        
        Args:
            audio_data: 原始音频数据
            remote_address: 客户端地址信息，用于生成文件名
            channels: 音频通道数
            sample_width: 采样宽度（字节）
            sample_rate: 采样率
            
        Returns:
            file_path: 保存的文件路径
        """
        try:
            # 生成唯一的会话ID和文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"session_{timestamp}_{remote_address[0].replace('.', '_')}"
            file_path = os.path.join(self.audio_dir, f"{session_id}.wav")
            
            # 保存为WAV文件
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)  # 2 bytes for 16 bits
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)
            return file_path
            
        except Exception as e:
            logger.error(f"保存WAV文件失败: {e}", exc_info=True)
            return None 