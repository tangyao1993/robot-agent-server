import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from workflow.state import WorkflowState

async def entry_node(state: WorkflowState) -> WorkflowState:
    """入口节点 - 初始化状态"""
    state.current_node = "entry"
    
    # 可以在这里添加一些初始化逻辑
    # 例如：日志记录、数据预处理等
    
    return state