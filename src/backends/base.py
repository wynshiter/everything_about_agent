from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator, List, Optional
from pydantic import BaseModel

class ModelResponse(BaseModel):
    """统一响应格式"""
    content: str
    tool_calls: list = []
    usage: Dict[str, int] = {}
    latency: float = 0.0

class ModelBackend(ABC):
    """模型后端抽象基类 - 支持Ollama/vLLM/HTTP"""
    
    @abstractmethod
    def load_model(self, model_id: str, config: Dict[str, Any]) -> bool:
        """加载模型"""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """同步生成"""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[ModelResponse]:
        """流式生成"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查后端服务是否可用"""
        pass
    
    @abstractmethod
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """获取模型信息"""
        pass
    
    @abstractmethod
    def list_loaded_models(self) -> List[str]:
        """列出已加载模型"""
        pass

    @property
    def base_url(self) -> str:
        """获取Base URL"""
        return getattr(self, "_base_url", "")
