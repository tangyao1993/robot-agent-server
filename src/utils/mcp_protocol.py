"""
简化的MCP协议工具
"""

import json
from typing import Dict, Any

def create_mcp_event(method: str, params: Dict[str, Any] = None) -> str:
    """创建MCP事件"""
    event = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {}
    }
    return json.dumps(event)