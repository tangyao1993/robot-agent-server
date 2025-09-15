# 构建方法
python -m venv .venv
.\.venv\Scripts\activate

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/


# 自主思考AGENT

### 使用langgraph进行流程绘制

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


### 针对memory的处理
- 每次对话退出时（默认60无输入退出）会进行对话摘要，然后清除checkpointer数据，防止checkpointer无限扩大

- 



https://github.com/tjni/langgraph-checkpoint-mysql