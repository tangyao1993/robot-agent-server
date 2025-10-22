from __future__ import annotations

import asyncio
import json
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

import websockets
from websockets.client import WebSocketClientProtocol

from .audio_utils import (
    load_wav_chunks,
    save_audio_bytes,
)
from .tts_provider import BaseTTSProvider, create_tts_provider


@dataclass(slots=True)
class SessionEvent:
    """统一的事件数据模型。"""

    type: str
    message: Optional[str] = None
    data: Any = None


class SimulatorSession:
    """封装与服务器的 WebSocket 交互，提供同步接口供 CLI/GUI 调用。"""

    def __init__(
        self,
        host: str,
        port: int,
        ws_path: str = "/ws",
        mac_addr: str = "00:11:22:33:44:55",
        tools: Optional[list[dict[str, Any]]] = None,
        event_callback: Optional[Callable[[SessionEvent], None]] = None,
        *,
        tts_mode: str = "index",
        index_tts_root: Optional[str] = None,
        index_tts_voice: Optional[str] = None,
        tts_provider: Optional[BaseTTSProvider] = None,
    ):
        self.host = host
        self.port = port
        self.ws_path = ws_path
        self.mac_addr = mac_addr
        self.tools = tools or []
        self._event_callback = event_callback or (lambda event: None)

        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._run_loop,
            name="SimulatorSessionLoop",
            daemon=True,
        )
        self._loop_thread.start()

        self._ws: Optional[WebSocketClientProtocol] = None
        self._recv_task: Optional[asyncio.Task] = None
        self._connected = False

        self._receiving_audio = False
        self._audio_buffer = bytearray()
        self.tts_provider: Optional[BaseTTSProvider]
        try:
            self.tts_provider = tts_provider or create_tts_provider(
                tts_mode,
                repo_root=index_tts_root,
                voice_path=index_tts_voice,
            )
        except Exception as exc:  # noqa: BLE001
            self.tts_provider = None
            self._emit("error", f"TTS 初始化失败: {exc}")

    # ------------------------------------------------------------------#
    # 公共 API
    # ------------------------------------------------------------------#

    def update_connection(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        ws_path: Optional[str] = None,
        mac_addr: Optional[str] = None,
    ):
        if host:
            self.host = host
        if port:
            self.port = port
        if ws_path:
            self.ws_path = ws_path
        if mac_addr:
            self.mac_addr = mac_addr

    def connect(self) -> asyncio.Future:
        """建立连接并自动注册。"""
        return asyncio.run_coroutine_threadsafe(self._connect(), self._loop)

    def disconnect(self) -> asyncio.Future:
        """断开连接并停止监听。"""
        return asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)

    def send_wav_file(
        self,
        file_path: str,
        chunk_duration_ms: int = 200,
        inter_chunk_delay: float = 0.0,
    ) -> asyncio.Future:
        """读取 WAV 并按 PCM 流发送。"""
        return asyncio.run_coroutine_threadsafe(
            self._send_wav_file(file_path, chunk_duration_ms, inter_chunk_delay),
            self._loop,
        )

    def send_text_as_audio(
        self,
        text: str,
        chunk_duration_ms: int = 200,
    ) -> asyncio.Future:
        """使用本地 TTS 将文本转为音频再发送。"""
        return asyncio.run_coroutine_threadsafe(
            self._send_text_as_audio(text, chunk_duration_ms),
            self._loop,
        )

    def send_raw_audio(self, data_iter: Iterable[bytes]) -> asyncio.Future:
        """直接发送原始 PCM 块。"""
        return asyncio.run_coroutine_threadsafe(
            self._send_audio_chunks(data_iter),
            self._loop,
        )

    def is_connected(self) -> bool:
        return self._connected

    def close(self):
        """关闭会话及事件循环。"""
        if self._loop.is_closed():
            return

        def _stop_loop():
            self._loop.stop()

        try:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop).result(timeout=5)
        except Exception:
            pass
        self._loop.call_soon_threadsafe(_stop_loop)
        self._loop_thread.join(timeout=2)

    def set_tts_provider(self, provider: Optional[BaseTTSProvider]):
        self.tts_provider = provider
        if provider:
            self._emit("status", f"TTS 已切换至 {provider.name}")
        else:
            self._emit("status", "TTS 已禁用")

    # ------------------------------------------------------------------#
    # 内部实现
    # ------------------------------------------------------------------#

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        self._loop.close()

    def _emit(self, event_type: str, message: Optional[str] = None, data: Any = None):
        event = SessionEvent(type=event_type, message=message, data=data)
        try:
            self._event_callback(event)
        except Exception:  # callback 不能影响主流程
            pass

    async def _connect(self):
        if self._connected:
            self._emit("status", "已连接，无需重复操作")
            return

        url = f"ws://{self.host}:{self.port}{self.ws_path}"
        try:
            self._emit("status", f"正在连接 {url} ...")
            self._ws = await websockets.connect(url, ping_interval=None)
            self._connected = True
            self._emit("status", f"已连接到 {url}")
            await self._send_registration()
            self._recv_task = asyncio.create_task(self._receive_loop())
        except Exception as exc:
            self._emit("error", f"连接失败: {exc}")
            self._connected = False
            self._ws = None

    async def _disconnect(self):
        if not self._connected:
            return
        try:
            if self._recv_task:
                self._recv_task.cancel()
            if self._ws:
                await self._ws.close()
        finally:
            self._connected = False
            self._ws = None
            self._recv_task = None
            self._receiving_audio = False
            self._audio_buffer.clear()
            self._emit("status", "连接已断开")

    async def _send_registration(self):
        if not self._ws:
            return
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "mcp/registerTools",
            "params": {
                "mac_addr": self.mac_addr,
                "tools": self.tools,
            },
        }
        await self._ws.send(json.dumps(payload, ensure_ascii=False))
        self._emit("log", f"发送注册请求: {payload}")

    async def _send_text_as_audio(self, text: str, chunk_duration_ms: int):
        if not text.strip():
            self._emit("error", "请输入非空文本")
            return

        if not self.tts_provider:
            self._emit("error", "TTS 未配置，请手动发送音频文件。")
            return

        try:
            wav_path = await asyncio.to_thread(self.tts_provider.synthesize, text)
        except Exception as exc:
            self._emit("error", f"TTS 生成失败: {exc}")
            return

        path = Path(wav_path)
        self._emit("status", f"文本已转换音频: {path.name}")
        await self._send_wav_file(str(path), chunk_duration_ms, inter_chunk_delay=0.0)

    async def _send_wav_file(self, file_path: str, chunk_duration_ms: int, inter_chunk_delay: float):
        if not self._connected or not self._ws:
            self._emit("error", "未连接服务器")
            return
        try:
            chunks, meta = load_wav_chunks(file_path, chunk_duration_ms)
        except Exception as exc:
            self._emit("error", f"读取音频失败: {exc}")
            return

        source_rate = meta.get("source_frame_rate")
        if source_rate and source_rate != meta.get("frame_rate"):
            self._emit(
                "log",
                f"音频采样率已从 {source_rate}Hz 转换为 {meta.get('frame_rate')}Hz。",
            )

        self._emit(
            "status",
            f"开始发送音频: {file_path} ({meta.get('duration_sec', 0):.2f}s, {len(chunks)} 块)",
        )
        await self._send_audio_chunks(chunks, inter_chunk_delay)

    async def _send_audio_chunks(
        self,
        chunks: Iterable[bytes],
        inter_chunk_delay: float = 0.0,
    ):
        if not self._connected or not self._ws:
            self._emit("error", "未连接服务器")
            return

        chunk_count = 0
        async for chunk in self._iterate_chunks(chunks, inter_chunk_delay):
            await self._ws.send(chunk)
            chunk_count += 1

        await self._send_end_stream()
        self._emit("status", f"音频发送完成，共发送 {chunk_count} 个块")

    async def _send_end_stream(self):
        if not self._ws:
            return

        end_event = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "mcp/audio/end_stream",
            "params": {},
        }
        await self._ws.send(json.dumps(end_event, ensure_ascii=False))
        self._emit("log", "发送 mcp/audio/end_stream 指令")

    async def _iterate_chunks(self, chunks: Iterable[bytes], delay: float):
        for chunk in chunks:
            if chunk:
                yield chunk
                if delay > 0:
                    await asyncio.sleep(delay)

    async def _receive_loop(self):
        assert self._ws
        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    await self._handle_binary(message)
                else:
                    await self._handle_text(message)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self._emit("error", f"接收消息失败: {exc}")
        finally:
            await self._disconnect()

    async def _handle_text(self, message: str):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            self._emit("log", f"收到文本消息: {message}")
            return

        method = data.get("method")
        if method == "mcp/server/start_audio":
            self._receiving_audio = True
            self._audio_buffer.clear()
            self._emit("status", "服务器开始推送音频")
            return

        if data.get("result"):
            self._emit("log", f"收到 RPC 响应: {data}")
        else:
            self._emit("json", data=data)

    async def _handle_binary(self, payload: bytes):
        if not payload:
            if self._receiving_audio and self._audio_buffer:
                saved_path = save_audio_bytes(bytes(self._audio_buffer))
                self._emit("audio_saved", f"音频已保存: {saved_path}", data=str(saved_path))
            self._audio_buffer.clear()
            self._receiving_audio = False
            return

        if self._receiving_audio:
            self._audio_buffer.extend(payload)
        else:
            self._emit("log", f"收到未标记的二进制数据，长度: {len(payload)} 字节")
