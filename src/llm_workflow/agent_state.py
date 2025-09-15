from typing import TypedDict, Annotated, List
import operator
from langchain_core.messages import AnyMessage
from typing import Dict, Any

class AgentState(TypedDict):
    user_input: str
    messages: Annotated[List[AnyMessage], operator.add]
    tools_definition: List[Dict[str, Any]]
    post_process: List[str]  # 新增，流程步骤
    current_step: int        # 新增，当前流程步骤索引