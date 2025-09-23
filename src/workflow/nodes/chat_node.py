import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from workflow.state import WorkflowState
from llm.ollama_client import OllamaClient
from llm.prompts import SYSTEM_PROMPT
import logging

logger = logging.getLogger(__name__)

async def chat_node(state: WorkflowState) -> WorkflowState:
    """聊天节点 - 处理用户输入并生成回复"""
    llm_client = OllamaClient()
    
    try:
        # 调用LLM生成回复
        response = await llm_client.generate(
            prompt=state.user_text,
            system_prompt=SYSTEM_PROMPT
        )
        
        # 更新状态
        state.bot_text = response
        state.current_node = "chat"
        
        logger.info(f"生成回复: {response[:100]}...")
        
    except Exception as e:
        logger.error(f"聊天节点处理失败: {e}")
        state.bot_text = "抱歉，我现在无法正常回复。"
        state.current_node = "chat"
    
    return state