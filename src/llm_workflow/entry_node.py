from .agent_state import AgentState
from langchain_core.messages import HumanMessage
from typing import Dict, Any
import logging
logger = logging.getLogger(__name__)
def entry_node(state: AgentState, config: Dict[str, Any]):
    logger.info("==========entry_node==========")
    return {"messages": [HumanMessage(content=state["user_input"])]}