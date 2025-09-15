### 🤖 `robot-agent` (机器人客户端)

这个项目是运行在 **ESP32-S3** 嵌入式设备上的 **MicroPython** 应用程序。它直接控制机器人的硬件，并作为用户与服务器之间的桥梁。

**核心功能:**

1.  **硬件驱动**:
    *   **屏幕**: 使用 `LVGL` 图形库驱动一块彩色屏幕，可以显示机器人的各种状态和动画（例如，通过 `image_state_display.py` 实现的眨眼、哭泣、惊讶等表情）。
    *   **麦克风**: 通过 `microphone.py` 捕获用户的声音。
    *   **扬声器**: 通过 `speaker.py` 播放声音。
    *   **物理按键**: 作为用户发起对话的触发器。

2.  **核心工作流程**:
    *   **待机**: 程序启动后，设备进入待机状态，屏幕上可能会显示待机动画（如眨眼）。
    *   **录音与上传**: 当用户按下物理按键时，设备会立即开始通过麦克风录音，并通过 `WebSocket` 连接，将音频数据实时地、流式地传输到 `robot-agent-server`。
    *   **接收与响应**: 录音结束后，它会等待服务器的回应。服务器会将生成的语音流式传输回来，`robot-agent` 接收到这些音频数据后，立即通过扬声器播放出来。
    *   **远程工具执行**: 它自身定义了一些可以在本地执行的“工具”（定义在 `tools.py` 中）。服务器可以发送一个 JSON 指令，要求设备执行某个工具（比如调整屏幕亮度、播放特定动画等），设备执行后会将结果返回给服务器。

**小结**: `robot-agent` 本身不具备智能，它是一个纯粹的“感知和执行”端，负责收集用户的声音并忠实地执行来自服务器的指令。

---

### 🧠 `robot-agent-server` (云端大脑)

这个项目是一个基于 `asyncio` 的高性能 Python 服务器，是整个系统的智能核心。它负责处理所有复杂的计算任务。

**核心功能:**

1.  **连接管理**:
    *   通过 `websocket_server.py` 监听并管理来自 `robot-agent` 客户端的 `WebSocket` 连接。
    *   当设备连接时，通过 `message_handler.py` 中的注册流程，记录设备的 MAC 地址和它所支持的“工具”列表，并将设备信息存入数据库(`database_manager.py`)。

2.  **核心工作流程**:
    *   **语音转文字 (ASR)**: 接收到客户端发来的音频流后，使用 `fun_asr_local.py` 中的语音识别引擎，将完整的音频数据转换成文字。
    *   **AI 大脑处理**: 将识别出的文字，连同客户端的历史对话记录，一起发送给一个大型语言模型 (LLM) 进行处理（从代码结构 `agent_graph` 和 `gemini_key` ，使用了 Google Gemini 模型）。
    *   **决策与工具调用**: AI 大脑根据用户的输入进行决策。如果用户的意图是调用一个设备端的功能（例如“把屏幕调亮”），AI会生成一个调用工具的指令，服务器再将该指令通过 WebSocket 发送给 `robot-agent` 执行。
    *   **文字转语音 (TTS)**: AI 大脑生成回复文本后，`tts_processor.py` 会调用 TTS 引擎，将这段文字实时转换成语音流。
    *   **流式响应**: 最关键的一步，服务器不会等所有语音都生成完毕再发送，而是边生成边通过 `WebSocket` 将语音数据块流式地传回给 `robot-agent`，极大地降低了用户听见回复的延迟。

**小结**: `robot-agent-server` 是机器人的“大脑”，它完成了从“听懂”（ASR）到“思考”（LLM），再到“说话”（TTS）的整个认知过程。

---

### 交互流程图

为了更直观地展示它们的协作方式，我为你创建了一个交互流程图：

```Mermaid
sequenceDiagram
    participant User as 用户
    participant Agent as robot-agent (设备端)
    participant Server as robot-agent-server (云端)
    participant ASR as 语音识别服务
    participant LLM as AI大语言模型
    participant TTS as 语音合成服务

    User->>Agent: 按下物理按键
    Agent->>Server: 建立WebSocket连接并注册
    Server-->>Agent: 注册成功

    activate Agent
    User->>Agent: 开始说话
    Agent->>Server: [流式传输] 实时麦克风音频
    User->>Agent: 结束说话
    Agent->>Server: [流式传输] 发送音频结束信号
    deactivate Agent

    activate Server
    Server->>ASR: 发送完整音频数据
    ASR-->>Server: 返回识别后的文本

    Server->>LLM: 发送文本和历史对话
    LLM-->>Server: [流式返回] AI生成的回复文本

    Server->>TTS: [流式处理] 将文本分句并合成语音
    TTS-->>Server: [流式返回] 合成的语音流

    Server->>Agent: [流式传输] 将语音流实时发回设备
    deactivate Server

    activate Agent
    Agent->>User: 实时播放收到的语音
    deactivate Agent
```