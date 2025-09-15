from .agent_state import AgentState
from typing import List, Dict, Any
from langchain_core.messages import ToolMessage
from online_music_player_v2 import get_music
import asyncio
from client_session import ClientSession
from mcp_protocol_builder import create_tool_execution_request
import logging
logger = logging.getLogger(__name__)
# Tool registry
local_tools = {
    "get_music": get_music,
}
async def play_music(pcm_data, client_session: ClientSession):
    await client_session.stream_audio(pcm_data)

async def play_music_wrapper(tool_call_args, client_session: ClientSession):
    pcm_data = await get_music(**tool_call_args)
    if pcm_data:
        await play_music(pcm_data, client_session)

def get_tool_definition(tools_definition: List[Dict[str, Any]], tool_name: str) -> Dict[str, Any]:
    for tool in tools_definition:
        if tool["name"] == tool_name:
            return tool
    return None

def tool_node(state: AgentState, config: Dict[str, Any]):

    logger.info("==========tool_node==========")

    #main_type：local 和 remote，local 是本地函数分长时间和短时间函数，remote 是设备端全部当做异步处理
    #sub_type：sync 和 async，sync 是同步表示必须要返回结果，async 是异步表示直接返回处理中的状态

    client_session = config["configurable"]["client_session"]


    if client_session is None:
        tool_results = test_tool_node(state)
        return {"messages": tool_results}

    #工具调用结果
    tool_results = []
    
    tools_definition = client_session.get_tools()

    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call['name']
        tool_definition = get_tool_definition(tools_definition, tool_name)
        if tool_definition["main_type"] == "local":
            if tool_definition["sub_type"] == "async":
                tool_results.append(ToolMessage(content="正在处理中", tool_call_id=tool_call["id"]))
                asyncio.create_task(local_tools[tool_name](**tool_call['args']))
            elif tool_definition["sub_type"] == "sync":
                if tool_name in local_tools:
                    tool_function = local_tools[tool_name]
                    tool_args = tool_call['args']
                    result = tool_function(**tool_args)
                    tool_results.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
                else:
                    # Handle case where tool is not found
                    tool_results.append(ToolMessage(content=f"工具 '{tool_name}' 未找到", tool_call_id=tool_call["id"]))
        elif tool_definition["main_type"] == "remote":
            tool_results.append(ToolMessage(content="正在处理中", tool_call_id=tool_call["id"]))
            asyncio.create_task(client_session.send_json(create_tool_execution_request(tool_name, tool_call['args'])))

            asyncio.create_task(client_session.send_mcp_event(
            method="mcp/tool/execute",
            params={
                "tool_name": tool_name,
                "tool_input": tool_call['args']
            }))

    logger.info(f"==========tool_node result: {tool_results}==========")
    state["messages"] = tool_results
    state["current_step"] = state.get("current_step", 0) + 1
    return state


def test_tool_node(state: AgentState):
    tool_results = []
    tools_definition = state["tools_definition"];
    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call['name']
        tool_definition = get_tool_definition(tools_definition, tool_name)
        if tool_definition["main_type"] == "local":
            if tool_definition["sub_type"] == "async":
                tool_results.append(ToolMessage(content="正在处理中", tool_call_id=tool_call["id"]))
                if tool_name == "get_music":
                    logger.info(f"==========test_tool_node get_music: {tool_call['args']}==========")
                else:
                    logger.info(f"==========test_tool_node other tool: {tool_name}==========")
            elif tool_definition["sub_type"] == "sync":
                if tool_name in local_tools:
                    logger.info(f"==========test_tool_node other tool: {tool_name}==========")
                else:
                    # Handle case where tool is not found
                    tool_results.append(ToolMessage(content=f"工具 '{tool_name}' 未找到", tool_call_id=tool_call["id"]))
        elif tool_definition["main_type"] == "remote":
            tool_results.append(ToolMessage(content="正在处理中", tool_call_id=tool_call["id"]))

    logger.info(f"==========tool_node result: {tool_results}==========")
    return tool_results
