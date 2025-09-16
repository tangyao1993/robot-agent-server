from .agent_state import AgentState
from langchain_core.messages import HumanMessage
from typing import Dict, Any, Optional
from langchain_core.runnables.config import RunnableConfig
import logging
logger = logging.getLogger(__name__)
def entry_node(state: AgentState, config: Optional[RunnableConfig] = None):
    logger.info("==========entry_node==========")
    return {"messages": [HumanMessage(content=state["user_input"])]}