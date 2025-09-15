from langgraph.graph import StateGraph, END
from .agent_state import AgentState
from .entry_node import entry_node
from .intent_node import intent_node
from .tool_node import tool_node
from .chat_node import chat_node
import logging
from .music_node import music_node
from .notify_listen_node import notify_listen_node

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def next_step_router(state: AgentState):
    step = state.get("current_step", 0)
    if "post_process" in state and step < len(state["post_process"]):
        return state["post_process"][step]
    return END

def build_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("entry", entry_node)
    workflow.add_node("intent", intent_node)
    workflow.add_node("tool", tool_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("music", music_node)
    workflow.add_node("notify_listen", notify_listen_node)

    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "intent")
    workflow.add_conditional_edges(
        "intent",
        next_step_router,
        {
            "chat": "chat",
            "tool": "tool",
            "music": "music",
            "notify_listen": "notify_listen"
        }
    )
    workflow.add_conditional_edges(
        "chat",
        next_step_router,
        {
            "chat": "chat",
            "tool": "tool",
            "music": "music",
            "notify_listen": "notify_listen"
        }
    )
    workflow.add_conditional_edges(
        "tool",
        next_step_router,
        {
            "chat": "chat",
            "tool": "tool",
            "music": "music",
            "notify_listen": "notify_listen"
        }
    )
    workflow.add_conditional_edges(
        "music",
        next_step_router,
        {
            "chat": "chat",
            "tool": "tool",
            "music": "music",
            "notify_listen": "notify_listen"
        }
    )
    workflow.add_conditional_edges(
        "notify_listen",
        next_step_router,
        {
            "chat": "chat",
            "tool": "tool",
            "music": "music",
            "notify_listen": "notify_listen"
        }
    )
    return workflow.compile()

if __name__ == "__main__":


    local_tools = [
        {
            "name": "get_music",
            "description": "当用户想要听歌时使用此工具。请优先、直接地调用此工具，即使用户只提供了歌曲名称，或者歌名看起来很模糊、不完整，甚至是单个汉字。你的主要任务是根据用户输入填充参数并调用工具，而不是与用户对话寻求澄清。",
            "main_type": "local",  # 表示这是一个本地(服务器端)工具
            "sub_type": "async",   
            "parameters": {
            "type": "object",
            "properties": {
                "song_name": {
                "type": "string",
                "description": "用户想要播放的歌曲名称。必须严格按照用户的原始输入提取，即使歌名很常见（如 '猜'）或只是一个单字（如 '小'）。不要进行任何补充或联想。e.g. '稻香', '七里香', '猜', '小'"
                },
                "artist_name": {
                "type": "string",
                "description": "歌曲的演唱者或艺术家。必须严格、完整地使用用户提供的原始名称，不要进行任何形式的拆分、简化或联想。例如，如果用户说'二硕'，就应该提取'二硕'，而不是'硕'或'李钟硕'。"
                }
            },
            "required": [
                "song_name"
            ]
            },
            "post_process": ["chat", "music", "notify_listen"]
        }
    ]
    app = build_workflow()
    from client_session import ClientSession
    import websockets.server
    websocket = websockets.server.WebSocketServerProtocol(None)
    websocket.remote_address = ("127.0.0.1", 8080)
    client_session = ClientSession(websocket=websocket)
    client_session.update_tools(local_tools)
    app.invoke({"user_input": "播放周杰伦稻香","tools_definition": local_tools},
               config={
                    "configurable": {
                        'mac_addr': "test",
                        'client_session': client_session
                    }
                })