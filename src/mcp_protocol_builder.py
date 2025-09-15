import uuid
from typing import List, Dict, Any

def create_registration_response(request_id: str) -> dict:
    """
    创建一个标准的JSON-RPC响应，用于成功确认客户端的工具注册。

    Args:
        request_id: 从客户端注册请求中收到的原始ID。

    Returns:
        一个符合MCP协议的JSON-RPC响应字典。
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "status": "registered",
            "message": "Tools were successfully registered."
        }
    }

def create_tool_execution_request(tool_name: str, tool_input: dict) -> dict:
    """
    创建一个标准的JSON-RPC请求，用于命令客户端执行一个工具。
    会自动生成一个唯一的'id'。

    Args:
        tool_name: 要执行的工具名称。
        tool_input: 调用工具所需的参数。

    Returns:
        一个符合MCP协议的 mcp/tool/execute 请求字典。
    """
    tool_call_id = f"tool-call-{uuid.uuid4()}"
    return {
        "jsonrpc": "2.0",
        "method": "mcp/tool/execute",
        "params": {
            "tool_name": tool_name,
            "tool_input": tool_input
        },
        "id": tool_call_id
    }
def create_mcp_event(method: str, params: Dict[str, Any] = None):
    """
    遵循MCP协议，发送一个控制事件（文本帧）。
    
    Args:
        method (str): MCP方法名, e.g., 'stream_start'.
        params (Dict): 与方法相关的参数。
    """
    if params is None:
        params = {}
        
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params
    }