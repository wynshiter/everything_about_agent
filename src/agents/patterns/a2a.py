"""
Agent-to-Agent (A2A) Protocol Pattern Implementation
Chapter 15: A2A Protocol

A2A 协议 - 实现 Agent 之间的标准化通信和协作。
支持发现、任务协商、信息交换和协同工作。
"""

from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import uuid
import asyncio
from loguru import logger
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class MessageType(Enum):
    """A2A 消息类型"""
    DISCOVERY = auto()      # 发现请求/响应
    TASK = auto()           # 任务分配
    QUERY = auto()          # 信息查询
    RESPONSE = auto()       # 响应
    NEGOTIATION = auto()    # 协商
    NOTIFICATION = auto()   # 通知
    ERROR = auto()          # 错误


class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()
    ASSIGNED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    DELEGATED = auto()


@dataclass
class AgentCapability:
    """Agent 能力描述"""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class A2AMessage:
    """A2A 消息"""
    message_id: str
    message_type: MessageType
    sender_id: str
    receiver_id: Optional[str]  # None 表示广播
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None  # 用于关联请求和响应
    ttl: int = 300  # 消息存活时间（秒）


@dataclass
class AgentProfile:
    """Agent 档案"""
    agent_id: str
    name: str
    capabilities: List[AgentCapability]
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.now)


class A2ABus:
    """
    A2A 消息总线
    负责 Agent 之间的消息路由
    """
    
    def __init__(self):
        self.agents: Dict[str, 'A2AAgent'] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.running = False
        logger.info("A2A Bus initialized")
    
    def register_agent(self, agent: 'A2AAgent'):
        """注册 Agent"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Agent {agent.agent_id} registered on A2A Bus")
    
    def unregister_agent(self, agent_id: str):
        """注销 Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent {agent_id} unregistered from A2A Bus")
    
    async def send_message(self, message: A2AMessage) -> bool:
        """发送消息"""
        await self.message_queue.put(message)
        logger.debug(f"Message {message.message_id} queued")
        return True
    
    async def route_messages(self):
        """消息路由循环"""
        self.running = True
        while self.running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._deliver_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Message routing error: {e}")
    
    async def _deliver_message(self, message: A2AMessage):
        """投递消息到目标 Agent"""
        # 检查消息是否过期
        age = (datetime.now() - message.timestamp).total_seconds()
        if age > message.ttl:
            logger.warning(f"Message {message.message_id} expired")
            return
        
        # 广播或单播
        if message.receiver_id is None:
            # 广播（除发送者外）
            for agent_id, agent in self.agents.items():
                if agent_id != message.sender_id:
                    await agent.receive_message(message)
        else:
            # 单播
            target = self.agents.get(message.receiver_id)
            if target:
                await target.receive_message(message)
            else:
                logger.warning(f"Target agent {message.receiver_id} not found")
    
    def discover_agents(self, capability_filter: str = None) -> List[AgentProfile]:
        """发现具备特定能力的 Agent"""
        results = []
        for agent in self.agents.values():
            profile = agent.get_profile()
            if capability_filter:
                if any(capability_filter.lower() in cap.name.lower() 
                       for cap in profile.capabilities):
                    results.append(profile)
            else:
                results.append(profile)
        return results
    
    def stop(self):
        """停止消息总线"""
        self.running = False
        logger.info("A2A Bus stopped")


class A2AAgent:
    """
    A2A Agent 实现
    支持与其他 Agent 的标准化通信
    """
    
    def __init__(self, agent_id: str, name: str, model_id: str = None,
                 bus: Optional[A2ABus] = None):
        self.agent_id = agent_id
        self.name = name
        self.llm = model_loader.load_llm(model_id)
        self.bus = bus
        self.capabilities: List[AgentCapability] = []
        self.task_handlers: Dict[str, Callable] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.collaboration_history: List[A2AMessage] = []
        
        if bus:
            bus.register_agent(self)
        
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🤝 A2AAgent '{name}' ({agent_id}) initialized")
    
    def register_capability(self, capability: AgentCapability):
        """注册能力"""
        self.capabilities.append(capability)
        logger.info(f"Agent {self.agent_id} registered capability: {capability.name}")
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
    
    def get_profile(self) -> AgentProfile:
        """获取 Agent 档案"""
        return AgentProfile(
            agent_id=self.agent_id,
            name=self.name,
            capabilities=self.capabilities,
            metadata={"task_types": list(self.task_handlers.keys())}
        )
    
    async def send_message(self, message_type: MessageType, 
                          receiver_id: Optional[str],
                          payload: Dict[str, Any],
                          correlation_id: str = None) -> str:
        """发送消息"""
        if not self.bus:
            raise RuntimeError("Agent not connected to A2A Bus")
        
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            payload=payload,
            correlation_id=correlation_id
        )
        
        await self.bus.send_message(message)
        return message.message_id
    
    async def receive_message(self, message: A2AMessage):
        """接收消息"""
        self.collaboration_history.append(message)
        logger.debug(f"Agent {self.agent_id} received {message.message_type.name} from {message.sender_id}")
        
        # 根据消息类型处理
        handlers = self.message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
        
        # 默认处理
        await self._handle_message_default(message)
    
    async def _handle_message_default(self, message: A2AMessage):
        """默认消息处理"""
        if message.message_type == MessageType.DISCOVERY:
            # 响应发现请求
            await self.send_message(
                MessageType.RESPONSE,
                message.sender_id,
                {"profile": self.get_profile().__dict__},
                correlation_id=message.message_id
            )
        
        elif message.message_type == MessageType.TASK:
            # 处理任务
            await self._handle_task_message(message)
        
        elif message.message_type == MessageType.QUERY:
            # 处理查询
            await self._handle_query_message(message)
    
    async def _handle_task_message(self, message: A2AMessage):
        """处理任务消息"""
        task_data = message.payload.get("task", {})
        task_type = task_data.get("type")
        task_id = task_data.get("id")
        
        handler = self.task_handlers.get(task_type)
        if handler:
            try:
                result = await handler(task_data)
                await self.send_message(
                    MessageType.RESPONSE,
                    message.sender_id,
                    {"task_id": task_id, "status": "completed", "result": result},
                    correlation_id=message.message_id
                )
            except Exception as e:
                await self.send_message(
                    MessageType.ERROR,
                    message.sender_id,
                    {"task_id": task_id, "error": str(e)},
                    correlation_id=message.message_id
                )
        else:
            await self.send_message(
                MessageType.ERROR,
                message.sender_id,
                {"task_id": task_id, "error": f"Unknown task type: {task_type}"},
                correlation_id=message.message_id
            )
    
    async def _handle_query_message(self, message: A2AMessage):
        """处理查询消息"""
        query = message.payload.get("query", "")
        
        # 使用 LLM 生成响应
        prompt = ChatPromptTemplate.from_template("""
你作为 Agent {agent_name}，回答其他 Agent 的查询。

你的能力: {capabilities}

查询: {query}

请提供简洁、准确的回答。
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        response = chain.invoke({
            "agent_name": self.name,
            "capabilities": ", ".join([c.name for c in self.capabilities]),
            "query": query
        })
        
        await self.send_message(
            MessageType.RESPONSE,
            message.sender_id,
            {"answer": response},
            correlation_id=message.message_id
        )
    
    async def delegate_task(self, task: Dict[str, Any], 
                           target_agent_id: str = None,
                           capability_requirement: str = None) -> Optional[str]:
        """
        委托任务给其他 Agent
        
        Args:
            task: 任务描述
            target_agent_id: 目标 Agent ID（可选）
            capability_requirement: 能力要求（用于自动选择 Agent）
        
        Returns:
            消息 ID
        """
        if not target_agent_id and capability_requirement:
            # 自动发现合适的 Agent
            candidates = self.bus.discover_agents(capability_requirement)
            if candidates:
                target_agent_id = candidates[0].agent_id
        
        if not target_agent_id:
            logger.error("No suitable agent found for delegation")
            return None
        
        return await self.send_message(
            MessageType.TASK,
            target_agent_id,
            {"task": task}
        )
    
    async def broadcast_discovery(self):
        """广播发现请求"""
        return await self.send_message(
            MessageType.DISCOVERY,
            None,  # 广播
            {"agent_id": self.agent_id, "capabilities": [c.name for c in self.capabilities]}
        )


class A2ACollaboration:
    """
    A2A 协作编排
    管理多 Agent 之间的复杂协作
    """
    
    def __init__(self, bus: A2ABus):
        self.bus = bus
        self.orchestration_tasks: Dict[str, Dict[str, Any]] = {}
    
    async def execute_workflow(self, workflow_id: str, 
                               steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行多 Agent 工作流
        
        Args:
            workflow_id: 工作流 ID
            steps: 步骤列表，每个步骤指定需要的 capability 和任务
        
        Returns:
            执行结果
        """
        results = []
        
        for i, step in enumerate(steps):
            capability = step.get("capability")
            task = step.get("task")
            
            # 发现合适的 Agent
            agents = self.bus.discover_agents(capability)
            if not agents:
                results.append({"step": i, "error": f"No agent with capability: {capability}"})
                continue
            
            # 选择第一个 Agent 并委托任务
            # 实际实现中可能需要更复杂的负载均衡
            target = agents[0]
            
            # 这里简化处理，实际应使用异步等待响应
            results.append({
                "step": i,
                "agent": target.agent_id,
                "task": task,
                "status": "delegated"
            })
        
        return {"workflow_id": workflow_id, "results": results}


if __name__ == "__main__":
    print("=" * 60)
    print("A2A (Agent-to-Agent) Protocol Pattern Demo")
    print("=" * 60)
    
    # 创建 A2A 总线
    bus = A2ABus()
    
    # 创建 Agent
    agent1 = A2AAgent("agent_001", "Researcher", bus=bus)
    agent2 = A2AAgent("agent_002", "Writer", bus=bus)
    
    # 注册能力
    agent1.register_capability(AgentCapability(
        name="research",
        description="Perform research on given topics"
    ))
    agent2.register_capability(AgentCapability(
        name="writing",
        description="Write articles and content"
    ))
    
    # 显示注册信息
    print("\n--- Agent Registry ---")
    for agent_id, agent in bus.agents.items():
        profile = agent.get_profile()
        print(f"  {profile.agent_id}: {profile.name}")
        print(f"    Capabilities: {[c.name for c in profile.capabilities]}")
    
    # 发现测试
    print("\n--- Discovery Test ---")
    researchers = bus.discover_agents("research")
    print(f"Found {len(researchers)} research agents")
    
    writers = bus.discover_agents("writing")
    print(f"Found {len(writers)} writing agents")
    
    print("\n--- Note ---")
    print("Full A2A messaging requires async event loop")
