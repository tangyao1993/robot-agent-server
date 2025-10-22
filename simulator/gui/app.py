from __future__ import annotations

import queue
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

if __package__:
    from ..backend import SimulatorSession, SessionEvent
    from ..backend.tts_provider import create_tts_provider
else:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from backend import SimulatorSession, SessionEvent  # type: ignore  # noqa: E402
    from backend.tts_provider import create_tts_provider  # type: ignore  # noqa: E402


@dataclass(slots=True)
class GUIArgs:
    host: str = "127.0.0.1"
    port: int = 8889
    ws_path: str = "/ws"
    mac: str = "00:11:22:33:44:55"
    auto_connect: bool = False
    tts_mode: str = "index"
    index_root: str = str(Path.home() / "workspace" / "index-tts")
    index_voice: str = str(Path.home() / "workspace" / "index-tts" / "wanwanxiaohe.mp3")


class SimulatorApp(tk.Tk):
    def __init__(self, args: GUIArgs):
        super().__init__()
        self.title("Robot Agent 客户端模拟器")
        self.geometry("840x620")
        self.args = args

        self.event_queue: "queue.Queue[SessionEvent]" = queue.Queue()
        self.session = SimulatorSession(
            host=args.host,
            port=args.port,
            ws_path=args.ws_path,
            mac_addr=args.mac,
            event_callback=self.event_queue.put,
            tts_mode=args.tts_mode,
            index_tts_root=args.index_root,
            index_tts_voice=args.index_voice,
        )

        self._audio_files: list[str] = []

        self._build_widgets()
        self.after(100, self._process_events)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if args.auto_connect:
            self._trigger_future(self.session.connect())

    # ------------------------------------------------------------------#
    # UI 构建
    # ------------------------------------------------------------------#

    def _build_widgets(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # 连接设置
        connection_frame = ttk.LabelFrame(container, text="连接配置")
        connection_frame.pack(fill=tk.X, padx=4, pady=4)

        self.host_var = tk.StringVar(value=self.session.host)
        self.port_var = tk.IntVar(value=self.session.port)
        self.path_var = tk.StringVar(value=self.session.ws_path)
        self.mac_var = tk.StringVar(value=self.session.mac_addr)

        ttk.Label(connection_frame, text="Host").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        ttk.Entry(connection_frame, textvariable=self.host_var, width=18).grid(row=0, column=1, padx=4, pady=2)
        ttk.Label(connection_frame, text="Port").grid(row=0, column=2, sticky="w", padx=4, pady=2)
        ttk.Entry(connection_frame, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=4, pady=2)
        ttk.Label(connection_frame, text="Path").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        ttk.Entry(connection_frame, textvariable=self.path_var, width=18).grid(row=1, column=1, padx=4, pady=2)
        ttk.Label(connection_frame, text="MAC").grid(row=1, column=2, sticky="w", padx=4, pady=2)
        ttk.Entry(connection_frame, textvariable=self.mac_var, width=18).grid(row=1, column=3, padx=4, pady=2)

        ttk.Button(connection_frame, text="连接", command=self.connect).grid(row=0, column=4, padx=6, pady=2)
        ttk.Button(connection_frame, text="断开", command=self.disconnect).grid(row=1, column=4, padx=6, pady=2)

        # 发送配置
        send_frame = ttk.LabelFrame(container, text="请求发送")
        send_frame.pack(fill=tk.X, padx=4, pady=8)

        self.chunk_var = tk.IntVar(value=200)
        ttk.Label(send_frame, text="分块(ms)").grid(row=0, column=0, padx=4, pady=2)
        ttk.Spinbox(send_frame, from_=50, to=2000, increment=50, textvariable=self.chunk_var, width=8).grid(
            row=0, column=1, padx=4, pady=2
        )

        self.text_input = tk.Entry(send_frame, width=50)
        self.text_input.grid(row=0, column=2, padx=6, pady=2, sticky="ew")
        ttk.Button(send_frame, text="发送文本(TTS)", command=self.send_text).grid(row=0, column=3, padx=4, pady=2)
        ttk.Button(send_frame, text="发送音频文件", command=self.send_file).grid(row=0, column=4, padx=4, pady=2)

        send_frame.columnconfigure(2, weight=1)

        # TTS 设置
        tts_frame = ttk.LabelFrame(container, text="TTS 配置")
        tts_frame.pack(fill=tk.X, padx=4, pady=4)

        ttk.Label(tts_frame, text="模式").grid(row=0, column=0, padx=4, pady=2, sticky="w")
        self.tts_mode_var = tk.StringVar(value=self.args.tts_mode)
        ttk.OptionMenu(
            tts_frame,
            self.tts_mode_var,
            self.tts_mode_var.get(),
            "index",
            "pyttsx3",
            "none",
        ).grid(row=0, column=1, padx=4, pady=2, sticky="w")

        ttk.Label(tts_frame, text="IndexTTS 路径").grid(row=1, column=0, padx=4, pady=2, sticky="w")
        self.index_root_var = tk.StringVar(value=self.args.index_root)
        ttk.Entry(tts_frame, textvariable=self.index_root_var, width=40).grid(row=1, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(tts_frame, text="选择目录", command=self.choose_index_root).grid(row=1, column=2, padx=4, pady=2)

        ttk.Label(tts_frame, text="音色参考").grid(row=2, column=0, padx=4, pady=2, sticky="w")
        self.index_voice_var = tk.StringVar(value=self.args.index_voice)
        ttk.Entry(tts_frame, textvariable=self.index_voice_var, width=40).grid(row=2, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(tts_frame, text="选择文件", command=self.choose_voice_file).grid(row=2, column=2, padx=4, pady=2)

        ttk.Button(tts_frame, text="应用设置", command=self.apply_tts_settings).grid(row=0, column=3, padx=8, pady=2, rowspan=3, sticky="ns")
        tts_frame.columnconfigure(1, weight=1)

        # 日志输出
        log_frame = ttk.LabelFrame(container, text="事件与日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.log_text = tk.Text(log_frame, height=18, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 音频记录
        audio_frame = ttk.LabelFrame(container, text="收到的音频")
        audio_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.audio_list = tk.Listbox(audio_frame, height=6)
        self.audio_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        ttk.Button(audio_frame, text="打开所在目录", command=self.open_output_dir).pack(anchor="e", padx=4, pady=2)

    # ------------------------------------------------------------------#
    # 会话控制
    # ------------------------------------------------------------------#

    def connect(self):
        self.session.update_connection(
            host=self.host_var.get(),
            port=self.port_var.get(),
            ws_path=self.path_var.get(),
            mac_addr=self.mac_var.get(),
        )
        self._trigger_future(self.session.connect())

    def disconnect(self):
        self._trigger_future(self.session.disconnect())

    def send_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 WAV 文件",
            filetypes=[("WAV 文件", "*.wav"), ("所有文件", "*.*")],
        )
        if not file_path:
            return
        chunk = max(self.chunk_var.get(), 50)
        self._trigger_future(self.session.send_wav_file(file_path, chunk_duration_ms=chunk))

    def send_text(self):
        text = self.text_input.get().strip()
        if not text:
            messagebox.showinfo("提示", "请输入要发送的文本")
            return
        chunk = max(self.chunk_var.get(), 50)
        self._trigger_future(self.session.send_text_as_audio(text, chunk_duration_ms=chunk))

    def choose_index_root(self):
        directory = filedialog.askdirectory(title="选择 IndexTTS 仓库目录")
        if directory:
            self.index_root_var.set(directory)

    def choose_voice_file(self):
        file_path = filedialog.askopenfilename(
            title="选择音色参考文件",
            filetypes=[("音频文件", "*.wav *.mp3 *.flac"), ("所有文件", "*.*")],
        )
        if file_path:
            self.index_voice_var.set(file_path)

    def apply_tts_settings(self):
        mode = self.tts_mode_var.get()
        root = self.index_root_var.get()
        voice = self.index_voice_var.get()
        try:
            provider = None if mode == "none" else create_tts_provider(mode, repo_root=root, voice_path=voice)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("错误", f"TTS 初始化失败: {exc}")
            return
        self.args.tts_mode = mode
        self.args.index_root = root
        self.args.index_voice = voice
        self.session.set_tts_provider(provider)

    def open_output_dir(self):
        output_dir = Path(__file__).resolve().parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("darwin"):
                import subprocess

                subprocess.call(["open", str(output_dir)])
            elif sys.platform.startswith("win"):
                import os

                os.startfile(str(output_dir))  # type: ignore[attr-defined]
            else:
                import subprocess

                subprocess.call(["xdg-open", str(output_dir)])
        except Exception as exc:  # pragma: no cover
            messagebox.showerror("错误", f"无法打开目录: {exc}")

    # ------------------------------------------------------------------#
    # 事件和日志
    # ------------------------------------------------------------------#

    def _trigger_future(self, future):
        if future is None:
            return

        def _callback(fut):
            try:
                fut.result()
            except Exception as exc:
                self.event_queue.put(SessionEvent(type="error", message=str(exc)))

        future.add_done_callback(lambda fut: self.after(0, _callback, fut))

    def _process_events(self):
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_events)

    def _handle_event(self, event: SessionEvent):
        if event.type in {"status", "log", "error"}:
            self._append_log(event)
        if event.type == "audio_saved" and event.data:
            self._audio_files.append(event.data)
            self.audio_list.insert(tk.END, event.data)
        if event.type == "json":
            self._append_log(event)

    def _append_log(self, event: SessionEvent):
        text = event.message or ""
        if event.type == "json" and event.data:
            text = f"JSON: {event.data}"
        prefix = {
            "status": "[状态] ",
            "log": "[日志] ",
            "error": "[错误] ",
            "json": "",
        }.get(event.type, "")

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{prefix}{text}\n")
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.see(tk.END)

    # ------------------------------------------------------------------#
    # 生命周期
    # ------------------------------------------------------------------#

    def on_close(self):
        self.session.close()
        self.destroy()


def launch_gui(args: Optional[object] = None):
    gui_args = GUIArgs()
    if args:
        gui_args.host = getattr(args, "host", gui_args.host)
        gui_args.port = getattr(args, "port", gui_args.port)
        gui_args.ws_path = getattr(args, "ws_path", gui_args.ws_path)
        gui_args.mac = getattr(args, "mac", gui_args.mac)
        gui_args.auto_connect = getattr(args, "auto_connect", gui_args.auto_connect)
        gui_args.tts_mode = getattr(args, "tts", gui_args.tts_mode)
        gui_args.index_root = getattr(args, "index_tts_root", gui_args.index_root)
        gui_args.index_voice = getattr(args, "index_tts_voice", gui_args.index_voice)

    app = SimulatorApp(gui_args)
    app.mainloop()
