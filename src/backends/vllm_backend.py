import aiohttp
import asyncio
from typing import Dict, Any, AsyncIterator, List
from .base import ModelBackend, ModelResponse
from loguru import logger
import requests
import json

class VLLMBackend(ModelBackend):
    """vLLM后端实现 - 生产级目标"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._base_url = config.get("connection", {}).get("host", "http://localhost:8000")
        logger.info(f"🔧 初始化vLLM后端 at {self._base_url}")
    
    def load_model(self, model_id: str, config: Dict[str, Any]) -> bool:
        """vLLM模型加载需通过命令行"""
        logger.warning("vLLM模型需手动启动或通过API动态加载（如果支持）：vllm serve {model_id}")
        # In a real scenario, we might call an endpoint to load a lora or check if model matches.
        return True
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        # Implementing sync generation via requests
        url = f"{self._base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        
        # Adapt parameters
        params = kwargs.get("parameters", {})
        data = {
            "model": kwargs.get("model", "default"), # vLLM often ignores model name if only one is served, or needs exact match
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            **params
        }

        try:
            resp = requests.post(url, json=data, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            return ModelResponse(
                content=result["choices"][0]["message"]["content"],
                usage=result.get("usage", {})
            )
        except Exception as e:
            logger.error(f"vLLM generation error: {e}")
            raise

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[ModelResponse]:
        """vLLM流式API实现"""
        url = f"{self._base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        params = kwargs.get("parameters", {})
        data = {
            "model": kwargs.get("model", "default"),
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **params
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as resp:
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: ") and line != "data: [DONE]":
                        json_str = line[6:]  # Remove "data: "
                        try:
                            chunk = json.loads(json_str)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield ModelResponse(content=content)
                        except json.JSONDecodeError:
                            pass
    
    def is_available(self) -> bool:
        try:
            requests.get(f"{self._base_url}/health", timeout=5)
            return True
        except:
            return False
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        return {"backend": "vllm", "model": model_id}
    
    def list_loaded_models(self) -> List[str]:
        # vLLM API获取模型列表
        try:
            resp = requests.get(f"{self._base_url}/v1/models")
            if resp.status_code == 200:
                return [m["id"] for m in resp.json()["data"]]
        except:
            pass
        return ["vllm-model-placeholder"]
