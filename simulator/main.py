from __future__ import annotations

import argparse
import queue
import shlex
import sys
import threading
from pathlib import Path

if __package__:
    from .backend import SimulatorSession, SessionEvent
    from .backend.tts_provider import create_tts_provider
else:  # 直接运行脚本时补充路径
    sys.path.append(str(Path(__file__).resolve().parent))
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from backend import SimulatorSession, SessionEvent  # type: ignore  # noqa: E402
    from backend.tts_provider import create_tts_provider  # type: ignore  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Robot Agent Server 客户端模拟器")
    parser.add_argument("--host", default="127.0.0.1", help="服务器地址")
    parser.add_argument("--port", type=int, default=8889, help="服务器端口")
    parser.add_argument("--ws-path", default="/ws", help="WebSocket 路径")
    parser.add_argument("--mac", default="00:11:22:33:44:55", help="模拟设备 MAC 地址")
    parser.add_argument("--gui", action="store_true", help="启动 tkinter GUI")
    parser.add_argument("--auto-connect", action="store_true", help="启动后自动连接服务器")
    parser.add_argument("--tts", choices=["index", "pyttsx3", "none"], default="index", help="TTS 模式")
    parser.add_argument(
        "--index-tts-root",
        default=str(Path.home() / "workspace" / "index-tts"),
        help="IndexTTS 仓库路径",
    )
    parser.add_argument(
        "--index-tts-voice",
        default=str(Path.home() / "workspace" / "index-tts" / "wanwanxiaohe.mp3"),
        help="IndexTTS 音色参考文件",
    )
    return parser.parse_args()


def run_cli(args: argparse.Namespace):
    event_queue: "queue.Queue[SessionEvent]" = queue.Queue()

    def handle_event(event: SessionEvent):
        event_queue.put(event)

    tts_mode = args.tts
    index_root = str(Path(args.index_tts_root).expanduser())
    index_voice = str(Path(args.index_tts_voice).expanduser())

    session = SimulatorSession(
        host=args.host,
        port=args.port,
        ws_path=args.ws_path,
        mac_addr=args.mac,
        event_callback=handle_event,
        tts_mode=tts_mode,
        index_tts_root=index_root,
        index_tts_voice=index_voice,
    )

    printer = threading.Thread(
        target=_event_printer,
        args=(event_queue,),
        name="SimEventPrinter",
        daemon=True,
    )
    printer.start()

    if args.auto_connect:
        _wait_future(session.connect())

    print("输入 help 查看可用命令，Ctrl+C 或 exit 退出。")

    try:
        while True:
            raw = input("sim> ").strip()
            if not raw:
                continue
            cmd, *rest = shlex.split(raw)
            if cmd in {"exit", "quit"}:
                break
            if cmd == "connect":
                _wait_future(session.connect())
            elif cmd == "disconnect":
                _wait_future(session.disconnect())
            elif cmd == "set":
                if len(rest) != 2:
                    print("用法: set <field> <value> （field: host/port/mac/path）")
                    continue
                field, value = rest
                if field == "host":
                    session.update_connection(host=value)
                elif field == "port":
                    session.update_connection(port=int(value))
                elif field == "mac":
                    session.update_connection(mac_addr=value)
                elif field in {"path", "ws_path"}:
                    session.update_connection(ws_path=value)
                else:
                    print("未知字段")
            elif cmd == "send-file":
                if not rest:
                    print("用法: send-file <wav路径> [chunk_ms]")
                    continue
                path = Path(rest[0]).expanduser()
                chunk_ms = int(rest[1]) if len(rest) > 1 else 200
                _wait_future(session.send_wav_file(str(path), chunk_duration_ms=chunk_ms))
            elif cmd == "send-text":
                if not rest:
                    print("用法: send-text <文本> [chunk_ms]")
                    continue
                text = rest[0]
                chunk_ms = int(rest[1]) if len(rest) > 1 else 200
                _wait_future(session.send_text_as_audio(text, chunk_duration_ms=chunk_ms))
            elif cmd == "tts":
                if not rest:
                    print("用法: tts <mode|root|voice> <值>")
                    continue
                subcmd = rest[0]
                if subcmd == "mode" and len(rest) >= 2:
                    new_mode = rest[1].lower()
                    if new_mode not in {"index", "pyttsx3", "none"}:
                        print("TTS 模式仅支持 index/pyttsx3/none")
                        continue
                    old_mode = tts_mode
                    tts_mode = new_mode
                    try:
                        provider = create_tts_provider(tts_mode, repo_root=index_root, voice_path=index_voice)
                    except Exception as exc:  # noqa: BLE001
                        print(f"[错误] 切换 TTS 失败: {exc}")
                        tts_mode = old_mode
                        continue
                    session.set_tts_provider(provider if tts_mode != "none" else None)
                elif subcmd == "root" and len(rest) >= 2:
                    old_root = index_root
                    index_root = str(Path(rest[1]).expanduser())
                    print(f"已更新 IndexTTS 路径: {index_root}")
                    if tts_mode != "none":
                        try:
                            provider = create_tts_provider(tts_mode, repo_root=index_root, voice_path=index_voice)
                        except Exception as exc:  # noqa: BLE001
                            print(f"[错误] 更新 TTS 失败: {exc}")
                            index_root = old_root
                        else:
                            session.set_tts_provider(provider)
                elif subcmd == "voice" and len(rest) >= 2:
                    old_voice = index_voice
                    index_voice = str(Path(rest[1]).expanduser())
                    print(f"已更新音色参考文件: {index_voice}")
                    if tts_mode != "none":
                        try:
                            provider = create_tts_provider(tts_mode, repo_root=index_root, voice_path=index_voice)
                        except Exception as exc:  # noqa: BLE001
                            print(f"[错误] 更新 TTS 失败: {exc}")
                            index_voice = old_voice
                        else:
                            session.set_tts_provider(provider)
                else:
                    print("用法: tts <mode|root|voice> <值>")
            elif cmd == "help":
                print(
                    "命令列表:\n"
                    "  connect                 连接服务器并注册\n"
                    "  disconnect              断开当前连接\n"
                    "  set <field> <value>     修改连接参数 (host/port/mac/path)\n"
                    "  send-file <wav> [ms]    读取 WAV 并以 PCM 流发送\n"
                    "  send-text <text> [ms]   使用本地 TTS 将文本转换为音频发送\n"
                    "  tts mode <type>         切换 TTS 模式 (index/pyttsx3/none)\n"
                    "  tts root <path>         设置 IndexTTS 仓库目录\n"
                    "  tts voice <path>        设置音色参考文件\n"
                    "  exit/quit               退出程序\n"
                )
            else:
                print(f"未知命令: {cmd}")
    except KeyboardInterrupt:
        print("\n收到中断信号，准备退出...")
    finally:
        session.close()


def _event_printer(event_queue: "queue.Queue[SessionEvent]"):
    while True:
        event = event_queue.get()
        if event.type == "status":
            print(f"[状态] {event.message}")
        elif event.type == "log":
            print(f"[日志] {event.message}")
        elif event.type == "error":
            print(f"[错误] {event.message}", file=sys.stderr)
        elif event.type == "audio_saved":
            print(f"[音频] {event.message}")
        elif event.type == "json":
            print(f"[JSON] {event.data}")


def _wait_future(future):
    try:
        return future.result()
    except Exception as exc:
        print(f"[错误] 操作失败: {exc}", file=sys.stderr)
        return None


def main():
    args = parse_args()
    if args.gui:
        if __package__:
            from .gui.app import launch_gui
        else:  # 直接运行脚本
            sys.path.append(str(Path(__file__).resolve().parent))
            sys.path.append(str(Path(__file__).resolve().parent / "gui"))
            from gui.app import launch_gui  # type: ignore  # noqa: E402

        launch_gui(args)
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
