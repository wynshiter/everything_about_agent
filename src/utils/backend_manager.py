from typing import Dict, Optional, List
from src.backends.base import ModelBackend
import yaml
from loguru import logger
import os

# Circular import avoidance: Import specific backends inside methods or use dynamic loading if needed.
# For now, I'll import them at the top but handle the circular dependency if ModelBackend needed BackendManager (it doesn't).
from src.backends.ollama_backend import OllamaBackend
from src.backends.vllm_backend import VLLMBackend

class BackendManager:
    """后端管理器 - 动态切换Ollama/vLLM"""
    
    def __init__(self):
        self._backends: Dict[str, ModelBackend] = {}
        self._active_backend_name: Optional[str] = None
        self._load_backends()
    
    def _load_backends(self):
        """加载所有后端配置"""
        # Adjust paths to be relative to the project root or absolute
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        backend_configs = [
            ("ollama", os.path.join(base_path, "configs/backends/ollama.yaml")),
            ("vllm", os.path.join(base_path, "configs/backends/vllm.yaml")),
        ]
        
        for backend_name, config_path in backend_configs:
            try:
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f)
                    
                    if backend_name == "ollama":
                        self._backends[backend_name] = OllamaBackend(config)
                    elif backend_name == "vllm":
                        self._backends[backend_name] = VLLMBackend(config)
                    
                    logger.info(f"✅ 加载后端: {backend_name}")
                else:
                    logger.warning(f"⚠️ 后端配置不存在: {config_path}")
            except Exception as e:
                logger.error(f"❌ 后端加载失败 {backend_name}: {e}")
        
        # Load active backend from models.yaml or default to ollama
        try:
            models_config_path = os.path.join(base_path, "configs/models.yaml")
            if os.path.exists(models_config_path):
                 with open(models_config_path, "r", encoding="utf-8") as f:
                    models_config = yaml.safe_load(f)
                    preferred = models_config.get("active_backend", "ollama")
                    if preferred in self._backends:
                        self._active_backend_name = preferred
        except Exception:
            pass

        # Fallback
        if not self._active_backend_name and "ollama" in self._backends:
            self._active_backend_name = "ollama"
    
    @property
    def active_backend(self) -> ModelBackend:
        """获取当前激活后端实例"""
        if self._active_backend_name is None:
            raise ValueError("无可用后端")
        return self._backends[self._active_backend_name]
    
    @property
    def active_backend_name(self) -> str:
        """获取当前激活后端名称"""
        return self._active_backend_name

    def switch_backend(self, backend_name: str) -> bool:
        """切换后端"""
        if backend_name not in self._backends:
            available = list(self._backends.keys())
            logger.error(f"后端 {backend_name} 不存在。可用: {available}")
            return False
        
        # 检查后端健康状态 (Optional: can be skipped if we want to force switch)
        if not self._backends[backend_name].is_available():
            logger.warning(f"后端 {backend_name} 服务似乎不可用，但仍尝试切换")
        
        self._active_backend_name = backend_name
        logger.info(f"🔄 切换到后端: {backend_name}")
        return True
    
    def list_backends(self) -> Dict[str, Dict]:
        """列出所有后端及其状态"""
        result = {}
        for name, backend in self._backends.items():
            result[name] = {
                "available": backend.is_available(),
                "active": name == self._active_backend_name,
                "type": type(backend).__name__
            }
        return result

# 全局单例
backend_manager = BackendManager()
