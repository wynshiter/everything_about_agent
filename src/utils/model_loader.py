from src.utils.backend_manager import backend_manager
import yaml
import os
from typing import Optional, Any, Dict

class ModelLoader:
    """模型加载器 - 通过后端抽象层加载模型"""
    
    def __init__(self):
        # We access the backend manager dynamically to get the current state
        pass
    
    def get_full_config(self) -> Dict[str, Any]:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(base_path, "configs/models.yaml")
        
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_model_config(self, model_id: str) -> Any:
        full_config = self.get_full_config()
            
        if model_id not in full_config.get("models", {}):
            raise ValueError(f"Model {model_id} not found in configuration.")
            
        return full_config["models"][model_id]

    @property
    def active_model_id(self) -> str:
        """获取当前激活的模型ID"""
        full_config = self.get_full_config()
        return full_config.get("active_model", "qwen2.5:3b")

    def load_llm(self, model_id: Optional[str] = None):
        """加载LLM（通过当前后端）。如果未指定model_id，则使用配置中的active_model"""
        if model_id is None:
            model_id = self.active_model_id
            
        # Ensure we have the active backend
        backend = backend_manager.active_backend
        backend_name = backend_manager.active_backend_name
        
        model_info = self.get_model_config(model_id)
        
        # 验证模型是否支持当前后端
        if backend_name not in model_info.get("supported_backends", []):
            raise ValueError(
                f"模型 {model_id} 不支持后端 {backend_name}"
            )
        
        # 通过后端的repo加载
        repo = model_info["backend_repos"][backend_name]
        parameters = model_info.get("parameters", {})
        
        # 调用后端加载方法 (backend implementation might just pull or verify)
        success = backend.load_model(repo, parameters)
        if not success:
            raise RuntimeError(f"模型加载失败: {repo}")
        
        # 返回适配的LLM实例
        if backend_name == "ollama":
            from langchain_ollama import ChatOllama
            # Using ChatOllama for chat models
            return ChatOllama(
                model=repo,
                base_url=backend.base_url,
                **parameters
            )
        elif backend_name == "vllm":
            from langchain_openai import ChatOpenAI
            # vLLM兼容OpenAI API
            return ChatOpenAI(
                base_url=f"{backend.base_url}/v1",
                api_key="EMPTY", # vLLM usually doesn't require key
                model=repo,
                **parameters
            )
        else:
             raise ValueError(f"Unsupported backend for LangChain adaptation: {backend_name}")

model_loader = ModelLoader()
