#!/usr/bin/env python3
import sys
import os
import asyncio
import logging
import json

# --- Start of Path Fix ---
# 将项目根目录（robot-agent-server）添加到sys.path
# 这样，无论从哪里运行脚本，都可以正确解析 'from src.xxx' 这样的导入
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End of Path Fix ---

# 导入自定义模块
from src.processors.audio_processor import AudioProcessor
from src.network.websocket_server import WebSocketServer
from src.processors.asr_processor import SpeechRecognizer
from src.database.operations import db_manager
from src.network.message_handler import MessageHandler

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Main")



# 服务器配置
HOST = "0.0.0.0"
PORT = 8889
WS_PATH = "/ws"

# 获取脚本所在的目录
# 获取项目根目录（src的父目录）
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(script_dir,"assets","audio_files")

async def main():
    """服务器主入口函数"""
    try:
        await db_manager.connect()

        # 2. 初始化服务处理器
        audio_processor = AudioProcessor(AUDIO_DIR)
        speech_recognizer = SpeechRecognizer()
        
        # 3. 初始化消息处理器
        message_handler = MessageHandler(db_manager, audio_processor, speech_recognizer)

        # 4. 创建并启动WebSocket服务器
        ws_server = WebSocketServer(
            host=HOST, 
            port=PORT, 
            ws_path=WS_PATH, 
            on_connect=message_handler.on_connect,
            on_message=message_handler.handle_message, 
            on_disconnect=message_handler.on_disconnect
        )
        await ws_server.start()
        
    except Exception as e:
        logger.critical(f"服务器启动失败: {e}", exc_info=True)
    finally:
        if db_manager:
            await db_manager.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器被手动中断")
    except Exception as e:
        logger.critical(f"服务器运行时发生错误: {e}", exc_info=True) 