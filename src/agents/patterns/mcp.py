"""
Model Context Protocol (MCP) Pattern Implementation
Chapter 10: MCP (Model Context Protocol)

MCP 是一个开放协议，用于标准化 AI 模型与外部数据源、工具之间的集成。
它提供了一种统一的方式来连接 AI 助手与数据所在的位置。
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger


class MCPResourceType(Enum):
    """MCP 资源类型"""
    FILE = "file"
    DATABASE = "database"
    API = "api"
    MEMORY = "memory"
    TOOL = "tool"


@dataclass
class MCPResource:
    """MCP 资源定义"""
    name: str
    resource_type: MCPResourceType
    uri: str
    description: str
    handler: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPContext:
    """MCP 上下文容器"""
    resources: List[MCPResource] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def add_resource(self, resource: MCPResource):
        """添加资源到上下文"""
        self.resources.append(resource)
        logger.info(f"MCP: 添加资源 {resource.name} ({resource.resource_type.value})")
    
    def get_resource(self, name: str) -> Optional[MCPResource]:
        """获取指定资源"""
        for r in self.resources:
            if r.name == name:
                return r
        return None
    
    def read_resource(self, name: str) -> Any:
        """读取资源数据"""
        resource = self.get_resource(name)
        if not resource:
            raise ValueError(f"资源不存在: {name}")
        
        if resource.handler:
            return resource.handler()
        return self.data.get(name)


class MCPServer:
    """
    MCP 服务器实现
    管理资源注册、上下文提供和工具暴露
    """
    
    def __init__(self, name: str):
        self.name = name
        self.resources: Dict[str, MCPResource] = {}
        self.tools: Dict[str, Callable] = {}
        self.contexts: Dict[str, MCPContext] = {}
        logger.info(f"MCP Server '{name}' initialized")
    
    def register_resource(self, resource: MCPResource):
        """注册资源"""
        self.resources[resource.name] = resource
        logger.info(f"MCP Server: 注册资源 {resource.name}")
    
    def register_tool(self, name: str, handler: Callable, description: str = ""):
        """注册工具"""
        self.tools[name] = handler
        logger.info(f"MCP Server: 注册工具 {name}")
    
    def create_context(self, context_id: str) -> MCPContext:
        """创建新的上下文"""
        context = MCPContext()
        self.contexts[context_id] = context
        return context
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """列出所有可用资源"""
        return [
            {
                "name": r.name,
                "type": r.resource_type.value,
                "uri": r.uri,
                "description": r.description
            }
            for r in self.resources.values()
        ]
    
    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有可用工具"""
        return [
            {"name": name, "description": getattr(handler, "__doc__", "")}
            for name, handler in self.tools.items()
        ]


class MCPAgent:
    """
    MCP Agent 实现
    使用 MCP 协议与外部资源和工具交互
    """
    
    def __init__(self, model_id: str = None, mcp_server: Optional[MCPServer] = None):
        self.llm = model_loader.load_llm(model_id)
        self.mcp_server = mcp_server or MCPServer("default")
        self.context = MCPContext()
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🔗 MCPAgent initialized with model: {effective_id}")
    
    def connect_resource(self, resource: MCPResource):
        """连接外部资源"""
        self.context.add_resource(resource)
        self.mcp_server.register_resource(resource)
    
    def query_with_context(self, query: str, context_resources: List[str] = None) -> str:
        """
        使用 MCP 上下文查询 LLM
        
        Args:
            query: 用户查询
            context_resources: 要包含的上下文资源名称列表
        """
        # 收集上下文数据
        context_data = []
        if context_resources:
            for resource_name in context_resources:
                try:
                    data = self.context.read_resource(resource_name)
                    context_data.append(f"[{resource_name}]\n{data}\n")
                except Exception as e:
                    logger.warning(f"读取资源 {resource_name} 失败: {e}")
        
        # 构建增强提示
        context_str = "\n".join(context_data) if context_data else "无额外上下文"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能助手，可以使用以下上下文信息来回答问题。
上下文信息通过 MCP (Model Context Protocol) 协议提供。"""),
            ("user", """可用上下文:
{context}

用户问题: {query}

请基于上下文信息回答问题。如果上下文不足以回答，请明确说明。""")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        logger.info(f"MCP: 使用 {len(context_data)} 个资源回答查询")
        return chain.invoke({"context": context_str, "query": query})
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行 MCP 工具"""
        if tool_name not in self.mcp_server.tools:
            raise ValueError(f"工具 {tool_name} 未注册")
        
        logger.info(f"MCP: 执行工具 {tool_name}")
        return self.mcp_server.tools[tool_name](**kwargs)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取 Agent 能力清单"""
        return {
            "resources": self.mcp_server.list_resources(),
            "tools": self.mcp_server.list_tools(),
            "context_resources": [r.name for r in self.context.resources]
        }


# --- 预定义资源处理器示例 ---

def create_file_resource(file_path: str) -> MCPResource:
    """创建文件资源"""
    def read_file():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
    
    return MCPResource(
        name=f"file_{file_path.replace('/', '_')}",
        resource_type=MCPResourceType.FILE,
        uri=f"file://{file_path}",
        description=f"File: {file_path}",
        handler=read_file
    )


def create_memory_resource(memory_dict: Dict[str, Any], name: str = "memory") -> MCPResource:
    """创建内存资源"""
    return MCPResource(
        name=name,
        resource_type=MCPResourceType.MEMORY,
        uri=f"memory://{name}",
        description="In-memory data storage",
        handler=lambda: str(memory_dict)
    )


if __name__ == "__main__":
    print("=" * 60)
    print("MCP (Model Context Protocol) Pattern Demo")
    print("=" * 60)
    
    # 创建 MCP Agent
    agent = MCPAgent()
    
    # 创建示例资源
    memory_data = {"user_name": "张三", "preference": "喜欢简洁回答"}
    memory_resource = create_memory_resource(memory_data, "user_profile")
    
    # 连接资源
    agent.connect_resource(memory_resource)
    
    # 添加另一个资源
    agent.connect_resource(MCPResource(
        name="company_knowledge",
        resource_type=MCPResourceType.DATABASE,
        uri="db://company_docs",
        description="公司内部知识库"
    ))
    
    print("\n--- MCP Agent Capabilities ---")
    caps = agent.get_capabilities()
    print(f"Resources: {[r['name'] for r in caps['resources']]}")
    print(f"Tools: {[t['name'] for t in caps['tools']]}")
    
    print("\n--- Note ---")
    print("MCP requires LLM backend running for actual query execution")
    print("Resources connected:", [r.name for r in agent.context.resources])
