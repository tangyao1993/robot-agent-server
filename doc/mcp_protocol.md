### 协议概述

本文档定义了 **MCP**，一个用于在服务器（AI Agent）和客户端（具备工具执行能力的设备）之间进行通信的轻量级协议。

所有通信都基于 **JSON-RPC 2.0** 格式。

### Tool 定义中的额外字段

在 `mcp/registerTools` 中，每个工具的定义可以包含额外的元数据字段，用于分类和路由。

*   `main_type` (string): 工具的主要分类，表示其执行环境或主要目的。
    *   当前可用枚举: `["remote","local"]`
    *   `"remote"` 表示该工具由连接的客户端（机器人、智能设备等）在本地执行。
    *   `"local"` 表示该工具由服务端提供
*   `sub_type` (string): 工具的次要分类，用于进一步描述其功能。
    *   当前可用枚举: `["control","query"]`
    *   `"control"` 表示该工具用于控制设备的某个方面（如音量、屏幕、表情等）,目前是不等待返回结果，直接伪造成功提升响应速度。
    *   `"query"` 表示该工具响应结果需要等待结果之后传给chat_node进行最终回复

---
### 1. 客户端 -> 服务器：注册工具

当客户端连接成功后，它 **必须** 发送此消息来向服务器声明它所具备的工具。

这是一个 **JSON-RPC 请求**。客户端 **必须** 提供一个 `id` 以便接收服务器的确认回执。

*   `method`: `mcp/registerTools`

**请求示例:**
```json
{
  "jsonrpc": "2.0",
  "method": "mcp/registerTools",
  "params": {
    "mac_addr": "AA-BB-CC-DD-EE-FF",
    "tools": [
      {
        "name": "amplify_volume",
        "description": "设置设备音量",
        "main_type": "remote",
        "sub_type": "control",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "integer",
                    "description": "音量大小，从0到100。0为静音，100为最大音量。"
                }
            },
            "required": ["level"]
        }
      },
      {
        "name": "set_virtual_human_expression",
        "description": "设置AI虚拟人的表情",
        "main_type": "remote",
        "sub_type": "control",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "要设置的表情",
                    "enum": ["close_eyes_smile", "close_eyes", "amazed", "smile", "cry", "idle"]
                }
            },
            "required": ["expression"]
        }
      }
    ]
  },
  "id": "client-reg-001"
}
```
**注意**:
*   `params.tools` 数组中的每个对象都定义了一个客户端具备的工具。服务器端的AI模型将直接使用这些信息来决定何时以及如何调用您的工具。
*   客户端 **必须** 发送一个唯一的 `id`，服务器将使用此 `id` 在响应中进行确认。

---

### 2. 服务器 -> 客户端：执行工具

当AI Agent决定需要使用客户端的一个工具时，服务器会向客户端发送此消息。

这是一个 **JSON-RPC 请求**。

*   `method`: `mcp/tool/execute`

**请求示例:**
```json
{
  "jsonrpc": "2.0",
  "method": "mcp/tool/execute",
  "params": {
    "tool_name": "amplify_volume",
    "tool_input": {
      "level": 80
    }
  },
  "id": "tool-call-12345-abcdef"
}
```
**注意**:
*   `params.tool_input` 的结构会严格匹配您在`mcp/registerTools`中为该工具定义的`parameters`。
*   `id` 是一个由服务器生成的唯一字符串，用于标识这次特定的工具调用。**客户端在响应时必须原样返回这个 `id`**。

---

### 3. 客户端 -> 服务器：返回工具执行结果

在客户端执行完服务器请求的工具后，**必须** 发送此消息作为响应。

这是一个 **JSON-RPC 响应**。它必须包含与请求完全相同的 `id`。

#### 成功的情况

**响应示例:**
```json
{
  "jsonrpc": "2.0",
  "id": "tool-call-12345-abcdef",
  "result": {
    "status": "success",
    "message": "音量已成功设置为 80"
  }
}
```
**注意**:
*   `result` 字段的内容可以是任何有效的JSON值（对象、数组、字符串、数字等）。服务器会将其内容直接传递给AI模型作为工具的输出。

#### 失败的情况

如果工具在客户端执行时出错，您应该返回一个 `error` 对象。

**响应示例:**
```json
{
  "jsonrpc": "2.0",
  "id": "tool-call-12345-abcdef",
  "error": {
    "code": -32000,
    "message": "执行失败：音量级别超出范围（0-100）。"
  }
}
```
**注意**:
*   `code` 可以使用JSON-RPC定义的-32000到-32099之间的值来表示服务器定义的错误。
*   `message` 应该是一个简明扼要的错误描述。

---

### 4. 服务器 -> 客户端：确认工具注册

在服务器成功接收并处理完客户端的 `mcp/registerTools` 请求后，会发送此消息作为响应。

这是一个 **JSON-RPC 响应**。它会包含与注册请求完全相同的 `id`。

**响应示例:**
```json
{
  "jsonrpc": "2.0",
  "id": "client-reg-001",
  "result": {
    "status": "registered",
    "message": "Tools were successfully registered."
  }
}
```

---

### 5. 服务器 -> 客户端：发送AI消息

当AI Agent生成了要发送给最终用户的回复时，服务器会通过此消息推送给客户端。这通常用于流式传输AI的思考过程或最终答案。

这是一个 **JSON-RPC 通知** (没有 `id`)。

*   `method`: `mcp/ai/message`

**请求示例:**
```json
{
  "jsonrpc": "2.0",
  "method": "mcp/ai/message",
  "params": {
    "type": "chunk",
    "content": "北京今天天气晴朗，气温25摄氏度，有微风。"
  }
}
```
**注意**:
*   `params.type`: 消息的类型。常见的值有:
    *   `"chunk"`: 表示这是一个流式消息片段。客户端应该将这些片段拼接起来显示。
    *   `"final"`: 表示这是AI的最终完整回复。
    *   `"thought"`: 表示这是AI的思考过程，客户端可以选择是否显示。
*   `params.content`: 消息的具体文本内容。
