# 🧠 Robot Agent Server - 云端大脑

基于 **asyncio** 的高性能 Python 服务器，是整个 AI 机器人系统的智能核心。

## 🎯 重构后的特点

- **架构简化**：采用模块化文件夹结构，代码更清晰
- **Ollama集成**：使用本地Ollama模型替代Gemini，降低成本
- **工作流简化**：LangGraph工作流从6个节点简化为2个节点
- **代码精简**：移除了复杂的视频处理和音乐播放功能

## 📁 文件结构

```
robot-agent-server/
├── src/
│   ├── main.py                    # 主程序入口
│   ├── network/
│   │   ├── websocket_server.py    # WebSocket服务器
│   │   └── message_handler.py     # 消息处理
│   ├── processors/
│   │   ├── fun_asr_local.py       # 本地语音识别
│   │   └── tts_processor.py       # 语音合成
│   ├── workflow/
│   │   ├── graph.py               # LangGraph工作流
│   │   ├── nodes.py               # 工作流节点
│   │   └── state.py               # 工作流状态
│   ├── llm/
│   │   └── ollama_client.py       # Ollama客户端
│   ├── database/
│   │   └── database_manager.py    # 数据库管理
│   └── utils/
│       └── audio_utils.py         # 音频工具
├── assets/
│   └── audio_files/              # 音频文件存储
├── config/
│   └── settings.py               # 配置文件
├── mysql.sql                     # 数据库结构
├── requirements.txt              # 依赖包
└── test.py                       # 测试文件
```

## 🔧 核心组件

### 1. 网络层
- **WebSocket服务器**: 管理客户端连接和消息路由
- **消息处理器**: 处理MCP协议消息和音频流
- **会话管理**: 维护设备会话状态

### 2. 处理层
- **语音识别(ASR)**: 使用FunASR进行本地语音识别
- **语音合成(TTS)**: 支持多种TTS服务的语音合成
- **音频处理**: 音频格式转换和流式处理

### 3. AI层
- **Ollama客户端**: 连接本地Ollama服务
- **LangGraph工作流**: 简化的状态机工作流
- **对话管理**: 维护对话上下文和历史

### 4. 数据层
- **MySQL数据库**: 存储设备信息和对话历史
- **音频文件**: 管理生成的音频文件
- **配置管理**: 系统配置和环境变量

## 🚀 工作流程

### 简化的LangGraph工作流
```
[客户端连接] → Entry Node → Chat Node → [响应客户端]
     ↑                                    ↓
     └──────────── [完成] ←────────────────┘
```

### 详细处理流程
1. **客户端连接**
   - WebSocket握手和认证
   - 设备注册和能力上报
   - 创建会话上下文

2. **音频处理**
   - 接收客户端音频流
   - 缓存完整的音频数据
   - 调用ASR服务转换为文本

3. **AI处理**
   - 将文本发送给Ollama模型
   - 生成回复文本
   - 调用TTS服务生成语音

4. **响应返回**
   - 流式返回音频数据
   - 更新对话历史
   - 清理临时资源

## ⚙️ 配置说明

### 环境变量
```bash
# Ollama配置
OLLAMA_BASE_URL=http://192.168.1.4:11434
OLLAMA_MODEL=qwen2.5:7b

# TTS服务配置（可选）
MINDCRaft_API_URL=你的TTS服务URL
MINDCRaft_API_KEY=你的TTS服务密钥

# 服务器配置
HOST=0.0.0.0
PORT=8889
```

### 数据库配置
```sql
-- 创建数据库和表结构
mysql -u root -p < mysql.sql
```

## 📦 部署步骤

### 1. 安装依赖
```bash
cd robot-agent-server
pip install -r requirements.txt
```

### 2. 配置数据库
```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE robot_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入表结构
mysql -u root -p robot_agent < mysql.sql
```

### 3. 启动Ollama服务
```bash
# 启动Ollama服务
ollama serve

# 拉取模型
ollama pull qwen2.5:7b
```

### 4. 运行服务器
```bash
cd src
python main.py
```

服务器将在 `0.0.0.0:8889` 启动，WebSocket端点为 `/ws`

## 🔧 开发和调试

### 运行测试
```bash
cd src
python test.py
```

### 日志配置
在 `config/settings.py` 中配置日志级别：
```python
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

### 性能监控
- WebSocket连接数
- 音频处理延迟
- ASR和TTS调用时间
- 数据库查询性能

## 🎨 MCP协议支持

支持的消息类型：
- `mcp/registerTools`: 设备注册
- `mcp/audio/start_stream`: 开始音频流
- `mcp/audio/end_stream`: 结束音频流
- `mcp/server/start_audio`: 服务器开始音频
- `mcp/server/end_audio`: 服务器结束音频
- `mcp/call_tool`: 调用工具

## 📋 技术规格

- **框架**: Python 3.8+ with asyncio
- **Web服务器**: 自定义WebSocket服务器
- **AI模型**: Ollama (qwen2.5:7b)
- **ASR**: FunASR
- **TTS**: 支持多种TTS服务
- **数据库**: MySQL 8.0+
- **音频格式**: 16kHz PCM

## 🤝 兼容性

- **客户端**: robot-agent v2.0+
- **Ollama**: v0.1.0+
- **Python**: 3.8+
- **操作系统**: Linux, macOS, Windows

## 📝 API文档

### WebSocket端点
- **路径**: `/ws`
- **协议**: WebSocket
- **端口**: 8889

### 消息格式
```json
{
  "jsonrpc": "2.0",
  "method": "方法名",
  "params": {
    "参数": "值"
  },
  "id": "消息ID"
}
```

## 🔒 安全考虑

1. **WebSocket认证**: 基于MAC地址的设备认证
2. **输入验证**: 严格的消息格式验证
3. **资源限制**: 音频文件大小和时长限制
4. **错误处理**: 优雅的错误处理和恢复

---

> 这个项目是重构后的简化版本，采用本地Ollama模型，降低了API调用成本，同时保持了核心的语音对话功能。