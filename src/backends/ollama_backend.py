import ollama
import asyncio
from typing import Dict, Any, AsyncIterator, List
from .base import ModelBackend, ModelResponse
from loguru import logger
import time

class OllamaBackend(ModelBackend):
    """Ollama后端实现 - 临时开发环境"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._base_url = config.get("connection", {}).get("host", "http://localhost:11434")
        logger.info(f"🔧 初始化Ollama后端 at {self._base_url}")
        # Configure ollama client if needed, though the library usually defaults to localhost:11434 or OLLAMA_HOST env var
    
    def load_model(self, model_id: str, config: Dict[str, Any]) -> bool:
        try:
            logger.info(f"⬇️ Ollama开始拉取/加载模型: {model_id}")
            ollama.pull(model_id)
            logger.info(f"✅ Ollama加载模型成功: {model_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ollama加载失败: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        start = time.time()
        
        try:
            response = ollama.chat(
                model=kwargs.get("model", "qwen2.5:3b"),
                messages=[{"role": "user", "content": prompt}],
                options=kwargs.get("parameters", {})
            )
            
            return ModelResponse(
                content=response["message"]["content"],
                latency=time.time() - start,
                usage={
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "completion_tokens": response.get("eval_count", 0)
                }
            )
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[ModelResponse]:
        # Ollama流式实现
        try:
            stream = ollama.chat(
                model=kwargs.get("model", "qwen2.5:3b"),
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                options=kwargs.get("parameters", {})
            )
            for chunk in stream:
                content = chunk["message"]["content"]
                if content:
                    yield ModelResponse(content=content)
        except Exception as e:
             logger.error(f"Ollama streaming error: {e}")
             raise

    def is_available(self) -> bool:
        try:
            ollama.list()
            return True
        except:
            return False
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        return {"backend": "ollama", "model": model_id}
    
    def list_loaded_models(self) -> List[str]:
        try:
            return [m["name"] for m in ollama.list()["models"]]
        except:
            return []
