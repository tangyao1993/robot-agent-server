from .agent_state import AgentState
import logging
import asyncio
from typing import Dict, Any
logger = logging.getLogger(__name__)

def notify_listen_node(state: AgentState, config: Dict[str, Any]):
    logger.info("==========notify_listen_node==========")
    client_session = config["configurable"]["client_session"]
    asyncio.create_task(client_session.send_mcp_event(
            method="mcp/server/end_audio",
            params={}))
    state["current_step"] = state.get("current_step", 0) + 1
    return state 