"""
Goal Setting and Monitoring Pattern Implementation
Chapter 11: Goal Setting and Monitoring

目标设定与监控模式 - 让 Agent 能够设定、追踪和调整目标。
适用于长期任务、项目管理和自主 Agent 系统。
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger
import json


class GoalStatus(Enum):
    """目标状态"""
    PENDING = auto()      # 待开始
    ACTIVE = auto()       # 进行中
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败
    CANCELLED = auto()    # 已取消
    BLOCKED = auto()      # 被阻塞


class GoalPriority(Enum):
    """目标优先级"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Milestone:
    """里程碑定义"""
    name: str
    description: str
    criteria: str  # 完成标准
    completed: bool = False
    completed_at: Optional[datetime] = None


@dataclass
class Goal:
    """目标定义"""
    id: str
    name: str
    description: str
    status: GoalStatus = GoalStatus.PENDING
    priority: GoalPriority = GoalPriority.MEDIUM
    
    # 时间相关
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 进度和指标
    progress: float = 0.0  # 0-100
    success_criteria: str = ""  # 成功标准
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 层级结构
    parent_id: Optional[str] = None
    sub_goals: List[str] = field(default_factory=list)
    
    # 里程碑
    milestones: List[Milestone] = field(default_factory=list)
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_progress(self, progress: float):
        """更新进度"""
        self.progress = max(0.0, min(100.0, progress))
        if self.progress >= 100.0 and self.status != GoalStatus.COMPLETED:
            self.mark_completed()
    
    def mark_completed(self):
        """标记为完成"""
        self.status = GoalStatus.COMPLETED
        self.progress = 100.0
        self.completed_at = datetime.now()
        logger.info(f"Goal '{self.name}' completed!")
    
    def mark_started(self):
        """标记为开始"""
        if self.status == GoalStatus.PENDING:
            self.status = GoalStatus.ACTIVE
            self.started_at = datetime.now()
            logger.info(f"Goal '{self.name}' started")
    
    def is_overdue(self) -> bool:
        """检查是否逾期"""
        if self.deadline and self.status in [GoalStatus.PENDING, GoalStatus.ACTIVE]:
            return datetime.now() > self.deadline
        return False
    
    def check_milestone(self, milestone_name: str) -> bool:
        """检查里程碑"""
        for m in self.milestones:
            if m.name == milestone_name and not m.completed:
                m.completed = True
                m.completed_at = datetime.now()
                logger.info(f"Milestone '{milestone_name}' completed for goal '{self.name}'")
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.name,
            "priority": self.priority.name,
            "progress": self.progress,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_overdue": self.is_overdue(),
            "milestones": [
                {"name": m.name, "completed": m.completed}
                for m in self.milestones
            ],
            "sub_goals": self.sub_goals
        }


class GoalManager:
    """目标管理器"""
    
    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.listeners: List[Callable] = []
    
    def add_goal(self, goal: Goal) -> str:
        """添加目标"""
        self.goals[goal.id] = goal
        self._notify_listeners("created", goal)
        logger.info(f"Goal added: {goal.name}")
        return goal.id
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """获取目标"""
        return self.goals.get(goal_id)
    
    def update_goal(self, goal_id: str, **updates) -> bool:
        """更新目标"""
        goal = self.goals.get(goal_id)
        if not goal:
            return False
        
        for key, value in updates.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
        
        self._notify_listeners("updated", goal)
        return True
    
    def delete_goal(self, goal_id: str) -> bool:
        """删除目标"""
        if goal_id in self.goals:
            goal = self.goals.pop(goal_id)
            self._notify_listeners("deleted", goal)
            return True
        return False
    
    def list_goals(self, status: Optional[GoalStatus] = None, 
                   priority: Optional[GoalPriority] = None) -> List[Goal]:
        """列出目标"""
        goals = list(self.goals.values())
        
        if status:
            goals = [g for g in goals if g.status == status]
        if priority:
            goals = [g for g in goals if g.priority == priority]
        
        # 按优先级和时间排序
        goals.sort(key=lambda g: (g.priority.value, g.created_at))
        return goals
    
    def get_active_goals(self) -> List[Goal]:
        """获取活跃目标"""
        return self.list_goals(status=GoalStatus.ACTIVE)
    
    def get_overdue_goals(self) -> List[Goal]:
        """获取逾期目标"""
        return [g for g in self.goals.values() if g.is_overdue()]
    
    def add_sub_goal(self, parent_id: str, sub_goal: Goal) -> bool:
        """添加子目标"""
        parent = self.goals.get(parent_id)
        if not parent:
            return False
        
        sub_goal.parent_id = parent_id
        self.goals[sub_goal.id] = sub_goal
        parent.sub_goals.append(sub_goal.id)
        
        logger.info(f"Sub-goal '{sub_goal.name}' added to '{parent.name}'")
        return True
    
    def calculate_progress(self, goal_id: str) -> float:
        """计算目标进度（包括子目标）"""
        goal = self.goals.get(goal_id)
        if not goal:
            return 0.0
        
        if not goal.sub_goals:
            return goal.progress
        
        # 如果有子目标，基于子目标计算
        sub_progresses = []
        for sub_id in goal.sub_goals:
            sub = self.goals.get(sub_id)
            if sub:
                sub_progresses.append(self.calculate_progress(sub_id))
        
        if sub_progresses:
            avg_progress = sum(sub_progresses) / len(sub_progresses)
            goal.progress = avg_progress
            return avg_progress
        
        return goal.progress
    
    def register_listener(self, callback: Callable):
        """注册状态监听器"""
        self.listeners.append(callback)
    
    def _notify_listeners(self, event: str, goal: Goal):
        """通知监听器"""
        for listener in self.listeners:
            try:
                listener(event, goal)
            except Exception as e:
                logger.error(f"Listener error: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取目标汇总"""
        total = len(self.goals)
        by_status = {}
        for status in GoalStatus:
            count = len([g for g in self.goals.values() if g.status == status])
            by_status[status.name] = count
        
        return {
            "total_goals": total,
            "by_status": by_status,
            "active": len(self.get_active_goals()),
            "overdue": len(self.get_overdue_goals()),
            "completion_rate": (by_status.get("COMPLETED", 0) / total * 100) if total > 0 else 0
        }


class GoalSettingAgent:
    """
    目标设定与监控 Agent
    帮助用户设定 SMART 目标并监控执行
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        self.goal_manager = GoalManager()
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🎯 GoalSettingAgent initialized with model: {effective_id}")
    
    def create_smart_goal(self, description: str) -> Goal:
        """
        使用 LLM 帮助创建 SMART 目标
        
        SMART = Specific, Measurable, Achievable, Relevant, Time-bound
        """
        prompt = ChatPromptTemplate.from_template("""
分析以下目标描述，将其转化为 SMART 目标格式：

目标描述: {description}

请输出 JSON 格式：
{{
    "specific": "具体描述",
    "measurable": "可衡量的标准",
    "achievable": "可行性分析",
    "relevant": "相关性说明",
    "time_bound": "时间限制",
    "milestones": ["里程碑1", "里程碑2", "里程碑3"],
    "priority": "HIGH/MEDIUM/LOW"
}}

只输出 JSON，不要其他文字。
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({"description": description})
            smart_data = json.loads(result)
            
            # 创建目标
            goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            priority = GoalPriority[smart_data.get("priority", "MEDIUM")]
            
            goal = Goal(
                id=goal_id,
                name=description[:50],
                description=description,
                priority=priority,
                success_criteria=smart_data.get("measurable", ""),
                metadata={"smart_analysis": smart_data}
            )
            
            # 添加里程碑
            for ms_name in smart_data.get("milestones", []):
                goal.milestones.append(Milestone(
                    name=ms_name,
                    description=f"完成: {ms_name}",
                    criteria=ms_name
                ))
            
            self.goal_manager.add_goal(goal)
            logger.info(f"SMART goal created: {goal.name}")
            return goal
            
        except Exception as e:
            logger.error(f"Failed to create SMART goal: {e}")
            # 回退到简单目标创建
            goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            goal = Goal(
                id=goal_id,
                name=description[:50],
                description=description
            )
            self.goal_manager.add_goal(goal)
            return goal
    
    def monitor_goal(self, goal_id: str) -> Dict[str, Any]:
        """监控目标状态"""
        goal = self.goal_manager.get_goal(goal_id)
        if not goal:
            return {"error": "Goal not found"}
        
        # 更新进度
        self.goal_manager.calculate_progress(goal_id)
        
        # 检查逾期
        if goal.is_overdue() and goal.status == GoalStatus.ACTIVE:
            logger.warning(f"Goal '{goal.name}' is overdue!")
        
        return goal.to_dict()
    
    def suggest_next_actions(self, goal_id: str) -> List[str]:
        """建议下一步行动"""
        goal = self.goal_manager.get_goal(goal_id)
        if not goal:
            return []
        
        prompt = ChatPromptTemplate.from_template("""
基于以下目标状态，建议下一步行动：

目标: {goal_name}
描述: {description}
当前进度: {progress}%
状态: {status}
未完成里程碑: {milestones}

请提供 3-5 个具体的下一步行动建议。
每行一个建议，简洁明了。
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        incomplete_milestones = [m.name for m in goal.milestones if not m.completed]
        
        result = chain.invoke({
            "goal_name": goal.name,
            "description": goal.description,
            "progress": goal.progress,
            "status": goal.status.name,
            "milestones": ", ".join(incomplete_milestones) if incomplete_milestones else "无"
        })
        
        return [line.strip() for line in result.split("\n") if line.strip()]
    
    def get_dashboard(self) -> Dict[str, Any]:
        """获取目标仪表板"""
        summary = self.goal_manager.get_summary()
        
        # 即将到期的目标
        active_goals = self.goal_manager.get_active_goals()
        urgent = [g for g in active_goals if g.deadline and 
                  (g.deadline - datetime.now()).days <= 3]
        
        return {
            "summary": summary,
            "urgent_goals": [g.to_dict() for g in urgent],
            "recent_goals": [g.to_dict() for g in list(self.goal_manager.goals.values())[-5:]]
        }


if __name__ == "__main__":
    print("=" * 60)
    print("Goal Setting and Monitoring Pattern Demo")
    print("=" * 60)
    
    # 创建 Agent
    agent = GoalSettingAgent()
    
    # 手动创建一些示例目标（不使用 LLM）
    goal1 = Goal(
        id="goal_001",
        name="学习 Python",
        description="在 3 个月内掌握 Python 编程基础",
        priority=GoalPriority.HIGH,
        milestones=[
            Milestone("基础语法", "学习变量、数据类型", "能写简单脚本"),
            Milestone("面向对象", "学习类和对象", "能设计简单类"),
            Milestone("项目实战", "完成一个项目", "独立开发项目")
        ]
    )
    goal1.mark_started()
    goal1.update_progress(30)
    agent.goal_manager.add_goal(goal1)
    
    goal2 = Goal(
        id="goal_002",
        name="阅读论文",
        description="每周阅读 3 篇 AI 相关论文",
        priority=GoalPriority.MEDIUM
    )
    agent.goal_manager.add_goal(goal2)
    
    # 显示仪表板
    print("\n--- Goal Dashboard ---")
    dashboard = agent.get_dashboard()
    print(f"总目标数: {dashboard['summary']['total_goals']}")
    print(f"活跃目标: {dashboard['summary']['active']}")
    print(f"逾期目标: {dashboard['summary']['overdue']}")
    print(f"完成率: {dashboard['summary']['completion_rate']:.1f}%")
    
    print("\n--- Active Goals ---")
    for goal in agent.goal_manager.get_active_goals():
        print(f"  - {goal.name}: {goal.progress}% ({goal.status.name})")
