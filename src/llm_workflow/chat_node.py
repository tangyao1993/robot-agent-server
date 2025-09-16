from .agent_state import AgentState
from langchain_ollama import ChatOllama
from llm_workflow.system_instruction import ROLE_INSTRUCTION
from langchain_core.messages import SystemMessage
from typing import Dict, Any, Optional
from langchain_core.runnables.config import RunnableConfig
import logging
from config import get_ollama_config

logger = logging.getLogger(__name__)

# 获取 Ollama 配置
ollama_config = get_ollama_config()
llm = ChatOllama(
    model=ollama_config["model_name"],
    base_url=ollama_config["base_url"],
    temperature=0.7
)
def chat_node(state: AgentState, config: Optional[RunnableConfig] = None):
    logger.info("==========chat_node==========")
    messages = [SystemMessage(content=ROLE_INSTRUCTION)] + state["messages"]

    logger.info(f"==========chat_node messages: {messages}==========")
    result = llm.invoke(messages)
    logger.info(f"==========chat_node result: {result}==========")
    state["messages"] = [result]
    state["current_step"] = state.get("current_step", 0) + 1
    return state




