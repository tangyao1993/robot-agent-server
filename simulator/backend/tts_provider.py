from __future__ import annotations

import importlib
import sys
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .audio_utils import generate_temp_wav_from_text, OUTPUT_DIR


class BaseTTSProvider(ABC):
    """TTS 提供者基类。"""

    name: str = "base"

    @abstractmethod
    def synthesize(self, text: str) -> Path:
        """将文本转换为 WAV 文件并返回路径。"""


class Pyttsx3TTSProvider(BaseTTSProvider):
    """使用 pyttsx3 生成语音。"""

    name = "pyttsx3"

    def synthesize(self, text: str) -> Path:
        wav = generate_temp_wav_from_text(text)
        if not wav:
            raise RuntimeError("pyttsx3 不可用，请安装依赖或改用其它 TTS。")
        return wav


class IndexTTSTTSProvider(BaseTTSProvider):
    """集成本地 IndexTTS 模型。"""

    name = "index"

    def __init__(
        self,
        repo_root: Path,
        voice_path: Path,
        *,
        model_dir: Optional[Path] = None,
        fp16: bool = False,
        deepspeed: bool = False,
        cuda_kernel: bool = False,
    ):
        self.repo_root = repo_root.expanduser().resolve()
        self.voice_path = voice_path.expanduser().resolve()
        self.model_dir = (model_dir or (self.repo_root / "checkpoints")).resolve()
        self.fp16 = fp16
        self.deepspeed = deepspeed
        self.cuda_kernel = cuda_kernel

        self._lock = threading.Lock()
        self._tts = None

        if not self.repo_root.exists():
            raise FileNotFoundError(f"未找到 IndexTTS 仓库目录: {self.repo_root}")
        if not self.model_dir.exists():
            raise FileNotFoundError(f"未找到模型目录: {self.model_dir}")
        if not self.voice_path.exists():
            raise FileNotFoundError(f"未找到音色参考文件: {self.voice_path}")

    def synthesize(self, text: str) -> Path:
        if not text.strip():
            raise ValueError("请输入非空文本。")

        tts = self._ensure_model()
        output_dir = OUTPUT_DIR / "index_tts"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time() * 1000)
        output_path = output_dir / f"indextts_{timestamp}.wav"

        kwargs = {
            "spk_audio_prompt": str(self.voice_path),
            "text": text,
            "output_path": str(output_path),
            "verbose": False,
        }

        # IndexTTS2 返回生成文件路径
        result = tts.infer(**kwargs)

        final_path = Path(result if isinstance(result, str) else output_path)
        if not final_path.exists():
            raise RuntimeError(f"IndexTTS 未生成音频文件: {final_path}")
        return final_path

    def _ensure_model(self):
        with self._lock:
            if self._tts is not None:
                return self._tts

            sys.path.insert(0, str(self.repo_root))
            sys.path.insert(0, str(self.repo_root / "indextts"))

            try:
                infer_module = importlib.import_module("indextts.infer_v2")
            except ImportError as exc:  # noqa: F841
                raise RuntimeError(
                    f"无法导入 IndexTTS ({exc}), 请确认已安装依赖并在 --index-tts-root 指定正确目录。"
                ) from exc
            IndexTTS2 = getattr(infer_module, "IndexTTS2")  # noqa: N806

            self._tts = IndexTTS2(
                model_dir=str(self.model_dir),
                cfg_path=str(self.model_dir / "config.yaml"),
                use_fp16=self.fp16,
                use_deepspeed=self.deepspeed,
                use_cuda_kernel=self.cuda_kernel,
            )

            return self._tts


def create_tts_provider(
    mode: str,
    *,
    repo_root: Optional[str] = None,
    voice_path: Optional[str] = None,
) -> Optional[BaseTTSProvider]:
    mode = (mode or "index").lower()
    if mode == "none":
        return None
    if mode == "pyttsx3":
        return Pyttsx3TTSProvider()
    if mode == "index":
        default_root = Path.home() / "workspace" / "index-tts"
        repo = Path(repo_root).expanduser() if repo_root else default_root
        voice = Path(voice_path).expanduser() if voice_path else (repo / "wanwanxiaohe.mp3")
        return IndexTTSTTSProvider(repo_root=repo, voice_path=voice)
    raise ValueError(f"不支持的 TTS 模式: {mode}")
