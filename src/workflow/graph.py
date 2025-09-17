import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from workflow.nodes.chat_node import chat_node
from workflow.nodes.entry_node import entry_node
from workflow.state import WorkflowState

# 创建简化的工作流图
workflow = StateGraph(WorkflowState)

# 添加节点
workflow.add_node("entry", entry_node)
workflow.add_node("chat", chat_node)

# 设置入口点和简单流程
workflow.set_entry_point("entry")
workflow.add_edge("entry", "chat")
workflow.add_edge("chat", END)

# 编译工作流
app = workflow.compile()

async def run_workflow(user_text: str, session_id: str = None, device_info: dict = None) -> WorkflowState:
    """运行工作流"""
    # 初始化状态
    state = WorkflowState(
        user_text=user_text,
        session_id=session_id,
        device_info=device_info
    )
    
    # 运行工作流
    result_dict = await app.ainvoke(state)
    
    # 如果结果是字典，转换为WorkflowState对象
    if isinstance(result_dict, dict):
        return WorkflowState(**result_dict)
    
    return result_dict