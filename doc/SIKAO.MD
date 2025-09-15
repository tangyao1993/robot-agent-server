### 最开始的计划是做一个能自主思考的AI智能体
``` mermaid
graph TD;
    __start__([<p>__start__</p>]):::first
    entry(entry)
    agent(agent)
    tools_call(tools_call)
    finalize_response(finalize_response)
    __end__([<p>__end__</p>]):::last
    __start__ --> entry;
    agent -.-> finalize_response;
    agent -.-> tools_call;
    entry --> agent;
    tools_call --> agent;
    finalize_response --> __end__;
    classDef default fill:#f2f0ff,line-height:1.2
    classDef first fill-opacity:0
    classDef last fill:#bfb6fc
```

### 由于延迟太高，经过测试ASR很快，langgraph很慢，TTS更慢，想让整个流程进行流式输出
- 第一步计划langgraph流式，但是由于LLM绑定了tools，导致LLM不能使用流式输出
- 改用chat和意图识别拆分，但是绑定了这种langgraph框架又有很多不好操作的地方
- langgraph改流式问题Unrecognized FinishReason enum value: 12， 'int' object has no attribute 'name'
- 决定去掉langgraph使用

