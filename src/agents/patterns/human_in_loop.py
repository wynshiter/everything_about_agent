"""
Human-in-the-Loop Pattern Implementation
Chapter 13: Human-in-the-Loop

人在回路模式 - 在关键决策点引入人工审核和干预，
确保 AI 系统的行为符合人类意图和价值观。
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import asyncio
from loguru import logger
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ApprovalStatus(Enum):
    """审批状态"""
    PENDING = auto()    # 待审批
    APPROVED = auto()   # 已批准
    REJECTED = auto()   # 已拒绝
    MODIFIED = auto()   # 已修改后批准
    TIMEOUT = auto()    # 超时
    ESCALATED = auto()  # 已升级


class InterventionType(Enum):
    """干预类型"""
    APPROVAL = auto()       # 审批
    REVIEW = auto()         # 审核
    CLARIFICATION = auto()  # 澄清
    OVERRIDE = auto()       # 覆盖
    FEEDBACK = auto()       # 反馈


@dataclass
class HumanDecision:
    """人工决策记录"""
    decision_id: str
    status: ApprovalStatus
    made_by: str  # 决策者标识
    timestamp: datetime = field(default_factory=datetime.now)
    comments: str = ""
    modifications: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterventionRequest:
    """干预请求"""
    request_id: str
    intervention_type: InterventionType
    title: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    options: List[Dict[str, Any]] = field(default_factory=list)
    
    # 状态
    status: ApprovalStatus = ApprovalStatus.PENDING
    decision: Optional[HumanDecision] = None
    
    # 时间控制
    created_at: datetime = field(default_factory=datetime.now)
    timeout_seconds: Optional[int] = None
    
    def is_expired(self) -> bool:
        """检查是否超时"""
        if self.timeout_seconds is None:
            return False
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.timeout_seconds


class HumanInterface:
    """
    人工接口抽象
    可以是 CLI、Web UI、消息通知等
    """
    
    async def request_approval(self, request: InterventionRequest) -> HumanDecision:
        """请求审批"""
        raise NotImplementedError
    
    async def notify(self, message: str, level: str = "info"):
        """发送通知"""
        logger.info(f"[{level.upper()}] {message}")


class CLIHumanInterface(HumanInterface):
    """命令行人工接口"""
    
    async def request_approval(self, request: InterventionRequest) -> HumanDecision:
        """通过 CLI 请求审批"""
        print("\n" + "="*60)
        print(f"🛑 HUMAN INTERVENTION REQUIRED")
        print("="*60)
        print(f"Type: {request.intervention_type.name}")
        print(f"Title: {request.title}")
        print(f"\nDescription:\n{request.description}")
        
        if request.options:
            print("\nOptions:")
            for i, opt in enumerate(request.options, 1):
                print(f"  {i}. {opt.get('label', opt.get('value', str(opt)))}")
        
        print("\nCommands:")
        print("  (a)pprove - 批准")
        print("  (r)eject  - 拒绝")
        print("  (m)odify  - 修改")
        print("  (e)scalate - 升级")
        
        # 模拟输入（实际使用时需要真实输入）
        # 这里返回一个模拟决策
        return HumanDecision(
            decision_id=f"dec_{request.request_id}",
            status=ApprovalStatus.APPROVED,
            made_by="human_user",
            comments="Approved via CLI"
        )


class HumanInLoopManager:
    """
    人在回路管理器
    管理所有需要人工干预的请求
    """
    
    def __init__(self, human_interface: Optional[HumanInterface] = None):
        self.interface = human_interface or CLIHumanInterface()
        self.pending_requests: Dict[str, InterventionRequest] = {}
        self.completed_requests: Dict[str, InterventionRequest] = {}
        self.decision_callbacks: Dict[str, List[Callable]] = {}
        self.auto_approve_patterns: List[str] = []  # 自动批准的模式
        self.block_patterns: List[str] = []  # 自动阻止的模式
    
    async def request_intervention(self, 
                                   intervention_type: InterventionType,
                                   title: str,
                                   description: str,
                                   context: Dict[str, Any] = None,
                                   options: List[Dict[str, Any]] = None,
                                   timeout_seconds: int = 300,
                                   callback: Callable = None) -> Optional[HumanDecision]:
        """
        请求人工干预
        
        Args:
            intervention_type: 干预类型
            title: 标题
            description: 描述
            context: 上下文信息
            options: 可选操作
            timeout_seconds: 超时时间
            callback: 决策后的回调函数
        
        Returns:
            HumanDecision 或 None（如果超时）
        """
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        request = InterventionRequest(
            request_id=request_id,
            intervention_type=intervention_type,
            title=title,
            description=description,
            context=context or {},
            options=options or [],
            timeout_seconds=timeout_seconds
        )
        
        # 检查自动批准/阻止规则
        auto_decision = self._check_auto_rules(request)
        if auto_decision:
            request.status = auto_decision.status
            request.decision = auto_decision
            self.completed_requests[request_id] = request
            logger.info(f"Auto-decision for {request_id}: {auto_decision.status.name}")
            return auto_decision
        
        # 添加到待处理队列
        self.pending_requests[request_id] = request
        if callback:
            self.decision_callbacks[request_id] = [callback]
        
        logger.info(f"Intervention requested: {title}")
        
        # 请求人工决策
        try:
            decision = await asyncio.wait_for(
                self.interface.request_approval(request),
                timeout=timeout_seconds
            )
            
            request.decision = decision
            request.status = decision.status
            
            # 移动已完成
            del self.pending_requests[request_id]
            self.completed_requests[request_id] = request
            
            # 执行回调
            if request_id in self.decision_callbacks:
                for cb in self.decision_callbacks[request_id]:
                    try:
                        cb(decision)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
            
            return decision
            
        except asyncio.TimeoutError:
            request.status = ApprovalStatus.TIMEOUT
            del self.pending_requests[request_id]
            self.completed_requests[request_id] = request
            logger.warning(f"Intervention timeout: {request_id}")
            return None
    
    def _check_auto_rules(self, request: InterventionRequest) -> Optional[HumanDecision]:
        """检查自动规则"""
        # 检查自动批准
        for pattern in self.auto_approve_patterns:
            if pattern in request.title or pattern in request.description:
                return HumanDecision(
                    decision_id=f"auto_{request.request_id}",
                    status=ApprovalStatus.APPROVED,
                    made_by="auto_approver",
                    comments=f"Auto-approved: matches pattern '{pattern}'"
                )
        
        # 检查自动阻止
        for pattern in self.block_patterns:
            if pattern in request.title or pattern in request.description:
                return HumanDecision(
                    decision_id=f"auto_{request.request_id}",
                    status=ApprovalStatus.REJECTED,
                    made_by="auto_blocker",
                    comments=f"Auto-blocked: matches pattern '{pattern}'"
                )
        
        return None
    
    def add_auto_approve_pattern(self, pattern: str):
        """添加自动批准模式"""
        self.auto_approve_patterns.append(pattern)
        logger.info(f"Auto-approve pattern added: {pattern}")
    
    def add_block_pattern(self, pattern: str):
        """添加阻止模式"""
        self.block_patterns.append(pattern)
        logger.warning(f"Block pattern added: {pattern}")
    
    def get_pending_count(self) -> int:
        """获取待处理请求数"""
        return len(self.pending_requests)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "pending": len(self.pending_requests),
            "completed": len(self.completed_requests),
            "by_status": {
                status.name: len([r for r in self.completed_requests.values() 
                                if r.status == status])
                for status in ApprovalStatus
            }
        }


class HumanInLoopAgent:
    """
    人在回路 Agent
    在关键决策点引入人工审核
    """
    
    def __init__(self, model_id: str = None, 
                 human_interface: Optional[HumanInterface] = None):
        self.llm = model_loader.load_llm(model_id)
        self.hilm = HumanInLoopManager(human_interface)
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"👤 HumanInLoopAgent initialized with model: {effective_id}")
    
    async def execute_with_approval(self, 
                                    action_name: str,
                                    action_description: str,
                                    action_func: Callable,
                                    *args, **kwargs) -> Any:
        """
        执行需要批准的操作
        
        Args:
            action_name: 操作名称
            action_description: 操作描述
            action_func: 实际执行函数
            *args, **kwargs: 传递给函数的参数
        
        Returns:
            操作结果或 None（如果被拒绝）
        """
        # 请求批准
        decision = await self.hilm.request_intervention(
            intervention_type=InterventionType.APPROVAL,
            title=f"Execute: {action_name}",
            description=action_description,
            context={"action": action_name, "args": str(args), "kwargs": str(kwargs)}
        )
        
        if not decision or decision.status not in [ApprovalStatus.APPROVED, ApprovalStatus.MODIFIED]:
            logger.warning(f"Action '{action_name}' was not approved")
            return None
        
        # 执行操作
        try:
            if asyncio.iscoroutinefunction(action_func):
                return await action_func(*args, **kwargs)
            else:
                return action_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            raise
    
    async def clarify_with_human(self, question: str, 
                                 context: Dict[str, Any] = None) -> str:
        """向人类澄清问题"""
        decision = await self.hilm.request_intervention(
            intervention_type=InterventionType.CLARIFICATION,
            title="Clarification Needed",
            description=question,
            context=context
        )
        
        if decision and decision.comments:
            return decision.comments
        return "No clarification provided"
    
    def configure_auto_rules(self, auto_approve: List[str] = None, 
                            auto_block: List[str] = None):
        """配置自动规则"""
        if auto_approve:
            for pattern in auto_approve:
                self.hilm.add_auto_approve_pattern(pattern)
        
        if auto_block:
            for pattern in auto_block:
                self.hilm.add_block_pattern(pattern)
    
    def get_intervention_stats(self) -> Dict[str, Any]:
        """获取干预统计"""
        return self.hilm.get_stats()


if __name__ == "__main__":
    print("=" * 60)
    print("Human-in-the-Loop Pattern Demo")
    print("=" * 60)
    
    async def demo():
        # 创建 Agent
        agent = HumanInLoopAgent()
        
        # 配置自动规则
        agent.configure_auto_rules(
            auto_approve=["safe_operation"],
            auto_block=["dangerous"]
        )
        
        # 演示自动批准
        print("\n--- Testing Auto-Approval ---")
        decision = await agent.hilm.request_intervention(
            intervention_type=InterventionType.APPROVAL,
            title="safe_operation test",
            description="This is a safe operation test"
        )
        if decision:
            print(f"Auto-decision: {decision.status.name}")
            print(f"Reason: {decision.comments}")
        
        # 演示统计
        print("\n--- Intervention Stats ---")
        stats = agent.get_intervention_stats()
        print(f"Pending: {stats['pending']}")
        print(f"Completed: {stats['completed']}")
        print(f"By status: {stats['by_status']}")
    
    # 运行演示
    asyncio.run(demo())
