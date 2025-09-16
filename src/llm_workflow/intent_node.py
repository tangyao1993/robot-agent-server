from .agent_state import AgentState
from langchain_ollama import ChatOllama
import logging
from langchain_core.messages import SystemMessage
from llm_workflow.system_instruction import INTENT_INSTRUCTION
from typing import Dict, Any, Optional
from config import get_ollama_config
from langchain_core.runnables.config import RunnableConfig

logger = logging.getLogger(__name__)

# 获取 Ollama 配置
ollama_config = get_ollama_config()
llm = ChatOllama(
    model=ollama_config["model_name"],
    base_url=ollama_config["base_url"],
    temperature=0
)

def get_tool_definition(tools_definition, tool_name):
    for tool in tools_definition:
        if tool["name"] == tool_name:
            return tool
    return None

def intent_node(state: AgentState, config: Optional[RunnableConfig] = None):
    logger.info("==========intent_node==========")
    if config is None:
        logger.error("intent_node 需要 config 参数")
        return {"messages": state["messages"], "post_process": ["chat", "notify_listen"], "current_step": 0}
    
    client_session = config["configurable"]["client_session"]
    tools_definition = client_session.get_tools()
    #把工具定义转换成可调用的工具
    tools = []
    for tool in tools_definition:
        tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"]
        })
    llm_with_tools = llm.bind_tools(tools)
    result = llm_with_tools.invoke([SystemMessage(content=INTENT_INSTRUCTION)] + state["messages"])
    logger.info(f"==========intent_node result: {result}==========")

    # 多工具合并 post_process
    tool_calls = getattr(result, 'tool_calls', []) if hasattr(result, 'tool_calls') else []
    all_steps = []
    for tool_call in tool_calls:
        tool_def = get_tool_definition(tools_definition, tool_call["name"])
        steps = tool_def.get("post_process", ["chat", "notify_listen"])
        for step in steps:
            if step not in all_steps:
                all_steps.append(step)
    if not all_steps:
        all_steps = ["chat", "notify_listen"]
    return {
        "messages": [result],
        "post_process": all_steps,
        "current_step": 0,
        "tools_definition": tools_definition
    }




