from .agent_state import AgentState
import logging
import asyncio
from typing import Dict, Any, Optional
from langchain_core.runnables.config import RunnableConfig
logger = logging.getLogger(__name__)

async def notify_listen_node(state: AgentState, config: Optional[RunnableConfig] = None):
    logger.info("==========notify_listen_node==========")
    if config is None:
        logger.error("notify_listen_node 需要 config 参数")
        state["current_step"] = state.get("current_step", 0) + 1
        return state
    
    client_session = config["configurable"]["client_session"]
    await client_session.send_mcp_event(
        method="mcp/server/end_audio",
        params={})
    state["current_step"] = state.get("current_step", 0) + 1
    return state 