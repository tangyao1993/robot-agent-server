import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """Ollama本地LLM客户端"""
    def __init__(self, base_url: str = "http://192.168.1.4:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url
        self.model = model
        logger.info(f"初始化Ollama客户端: {base_url}, 模型: {model}")
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用Ollama生成回复"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API调用失败: {response.status} - {error_text}")
                        return "抱歉，我现在无法正常回复。"
        except Exception as e:
            logger.error(f"Ollama API调用异常: {e}")
            return "抱歉，我现在无法正常回复。"
    
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