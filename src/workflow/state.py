from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class WorkflowState:
    """工作流状态 - 简化版本"""
    user_text: str = ""                    # 用户输入文本
    bot_text: str = ""                     # AI回复文本
    audio_data: Optional[bytes] = None     # 音频数据
    session_id: Optional[str] = None       # 会话ID
    device_info: Optional[Dict[str, Any]] = None  # 设备信息
    current_node: str = "entry"            # 当前节点
    metadata: Optional[Dict[str, Any]] = None  # 元数据