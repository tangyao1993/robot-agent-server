from __future__ import annotations

import contextlib
import time
import wave
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_wav_chunks(
    file_path: str,
    chunk_duration_ms: int = 200,
    target_sample_rate: int = 16000,
) -> Tuple[List[bytes], Dict[str, float]]:
    """
    将 WAV 文件读取为 PCM 分块数据。

    Args:
        file_path: WAV 文件路径，建议为 16kHz/16bit/mono。
        chunk_duration_ms: 每块持续时间（毫秒）。
        target_sample_rate: 目标采样率（默认 16kHz）。

    Returns:
        (chunks, metadata)：
            chunks 为 PCM 字节列表；
            metadata 包含 channels / sample_width / frame_rate / total_frames。
    """
    wav_path = Path(file_path)
    if not wav_path.exists():
        raise FileNotFoundError(f"未找到音频文件: {file_path}")

    chunks: List[bytes] = []
    metadata: dict = {}

    with contextlib.closing(wave.open(str(wav_path), "rb")) as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        frame_rate = wf.getframerate()
        total_frames = wf.getnframes()

        metadata = {  # 原始元数据
            "source_channels": channels,
            "source_sample_width": sample_width,
            "source_frame_rate": frame_rate,
            "source_total_frames": total_frames,
            "source_duration_sec": total_frames / frame_rate if frame_rate else 0,
        }

        raw_bytes = wf.readframes(total_frames)

    pcm = _normalize_audio(
        raw_bytes,
        channels=channels,
        sample_width=sample_width,
        sample_rate=frame_rate,
        target_sample_rate=target_sample_rate,
    )

    metadata.update(
        {
            "channels": 1,
            "sample_width": 2,
            "frame_rate": target_sample_rate,
            "duration_sec": len(pcm) / 2 / target_sample_rate,
        }
    )

    if chunk_duration_ms <= 0:
        chunk_duration_ms = 200

    frames_per_chunk = int(target_sample_rate * (chunk_duration_ms / 1000.0))
    frames_per_chunk = max(frames_per_chunk, 1)

    frame_size = 2  # int16 单声道
    chunk_size = frames_per_chunk * frame_size

    while True:
        frames = pcm[:chunk_size]
        if not frames:
            break
        chunks.append(frames)
        pcm = pcm[chunk_size:]

    return chunks, metadata


def save_audio_bytes(data: bytes, suffix: str = "wav") -> Path:
    """
    将服务器返回的音频二进制保存到 output 目录。

    Args:
        data: 音频字节流。
        suffix: 期望文件后缀，默认为 wav。

    Returns:
        保存后的文件路径。
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    file_name = f"server_audio_{timestamp}.{suffix}"
    file_path = OUTPUT_DIR / file_name
    file_path.write_bytes(data)
    return file_path


def generate_temp_wav_from_text(text: str) -> Optional[Path]:
    """
    使用 pyttsx3 将文本转换为本地 WAV 文件。
    需要系统安装 pyttsx3 及对应语音后端。

    Returns:
        生成文件的路径；若无法生成则返回 None。
    """
    if not text.strip():
        return None

    try:
        import pyttsx3  # pylint: disable=import-error
    except Exception:
        return None

    engine = pyttsx3.init()
    temp_path = OUTPUT_DIR / f"tts_input_{int(time.time())}.wav"
    engine.save_to_file(text, str(temp_path))
    engine.runAndWait()
    return temp_path if temp_path.exists() else None


def _normalize_audio(
    pcm_bytes: bytes,
    *,
    channels: int,
    sample_width: int,
    sample_rate: int,
    target_sample_rate: int,
) -> bytes:
    """将任意声道/采样率的 PCM 数据转换为 16kHz、16bit、单声道。"""
    if not pcm_bytes:
        return b""

    dtype = {1: np.uint8, 2: np.int16, 4: np.int32}.get(sample_width)
    if dtype is None:
        raise ValueError(f"不支持的采样宽度: {sample_width}")

    audio = np.frombuffer(pcm_bytes, dtype=dtype).astype(np.float32)

    if sample_width == 1:
        audio = (audio - 128.0) / 128.0  # uint8 -> float32 [-1,1)
    elif sample_width == 2:
        audio = audio / 32768.0
    elif sample_width == 4:
        audio = audio / 2147483648.0

    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)

    if sample_rate != target_sample_rate:
        audio = _resample(audio, sample_rate, target_sample_rate)

    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767.0).astype(np.int16)
    return audio_int16.tobytes()


def _resample(data: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
    """线性插值重采样。"""
    if orig_rate == target_rate or data.size == 0:
        return data

    duration = data.size / orig_rate
    target_size = max(int(round(duration * target_rate)), 1)

    orig_times = np.linspace(0.0, duration, num=data.size, endpoint=False)
    target_times = np.linspace(0.0, duration, num=target_size, endpoint=False)

    return np.interp(target_times, orig_times, data).astype(np.float32)
