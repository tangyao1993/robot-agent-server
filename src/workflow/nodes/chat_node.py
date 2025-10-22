import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from workflow.state import WorkflowState
from ..prompts import SYSTEM_PROMPT
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

# 复用LangGraph兼容的本地模型客户端，避免每次调用重复初始化
chat_model = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="123",
    model="Qwen/Qwen3-0.6B",
)

async def chat_node(state: WorkflowState) -> WorkflowState:
    """聊天节点 - 处理用户输入并生成回复"""
    try:
        messages = []
        if SYSTEM_PROMPT:
            messages.append(SystemMessage(content=SYSTEM_PROMPT))
        messages.append(HumanMessage(content=state.user_text))

        response = await chat_model.ainvoke(messages)

        state.bot_text = response.content
        state.current_node = "chat"

        logger.info(f"生成回复: {state.bot_text[:100]}...")

    except Exception as e:
        logger.error(f"聊天节点处理失败: {e}")
        state.bot_text = "抱歉，我现在无法正常回复。"
        state.current_node = "chat"

    return state
