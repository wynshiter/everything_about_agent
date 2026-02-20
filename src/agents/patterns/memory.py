"""
Memory Management Pattern Implementation
Chapter 8: Memory Management
"""

from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.utils.model_loader import model_loader
from loguru import logger


class MemoryAgent:
    """记忆管理 Agent"""
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        self.short_term_memory: List = []
        self.long_term_memory: Dict = {}
        logger.info("MemoryAgent initialized")
    
    def add_to_short_term(self, message: str, role: str = "user"):
        """添加到短期记忆"""
        if role == "user":
            self.short_term_memory.append(HumanMessage(content=message))
        else:
            self.short_term_memory.append(AIMessage(content=message))
    
    def get_context(self, max_messages: int = 10) -> List:
        """获取上下文"""
        return self.short_term_memory[-max_messages:]
    
    def save_to_long_term(self, key: str, value: Any):
        """保存到长期记忆"""
        self.long_term_memory[key] = value
    
    def recall(self, key: str) -> Any:
        """召回长期记忆"""
        return self.long_term_memory.get(key)


if __name__ == "__main__":
    print("Chapter 8: Memory Management")
