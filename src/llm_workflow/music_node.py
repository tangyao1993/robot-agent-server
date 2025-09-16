from .agent_state import AgentState
from typing import Dict, Any, Optional
from langchain_core.runnables.config import RunnableConfig
import logging
logger = logging.getLogger(__name__)

def music_node(state: AgentState, config: Optional[RunnableConfig] = None):
    logger.info("==========music_node==========")
    # 这里实现音乐播放逻辑，例如调用音频流推送等
    # TODO: 实现具体音乐播放
    state["current_step"] = state.get("current_step", 0) + 1
    return state 