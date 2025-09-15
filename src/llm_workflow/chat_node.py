from .agent_state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from llm_workflow.system_instruction import ROLE_INSTRUCTION
from langchain_core.messages import SystemMessage
from typing import Dict, Any
import logging
logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite-preview-06-17",
                             google_api_key="AIzaSyAhvycuMLKRzdsuMG7l_l8V5rZEIyWW-S4")
def chat_node(state: AgentState, config: Dict[str, Any]):
    logger.info("==========chat_node==========")
    messages = [SystemMessage(content=ROLE_INSTRUCTION)] + state["messages"]

    logger.info(f"==========chat_node messages: {messages}==========")
    result = llm.invoke(messages)
    logger.info(f"==========chat_node result: {result}==========")
    state["messages"] = [result]
    state["current_step"] = state.get("current_step", 0) + 1
    return state




