import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MockOllamaClient:
    """模拟的Ollama客户端，用于测试"""
    def __init__(self, base_url: str = "http://192.168.1.5:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url
        self.model = model
        logger.info(f"初始化模拟Ollama客户端: {base_url}, 模型: {model}")
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """模拟调用Ollama生成回复"""
        logger.info(f"模拟LLM调用: {prompt[:50]}...")
        
        # 简单的回复逻辑
        if "你好" in prompt:
            return "你好！很高兴见到你！"
        elif "天气" in prompt:
            return "今天天气不错呢！"
        elif "名字" in prompt:
            return "我是一个AI助手，很高兴为您服务！"
        else:
            return "我理解了您的问题，让我想想怎么回答..."
    
    async def chat(self, messages: list) -> str:
        """对话模式"""
        # 将消息历史转换为prompt
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt += f"用户: {content}\n"
            else:
                prompt += f"助手: {content}\n"
        
        prompt += "助手:"
        
        return await self.generate(prompt)