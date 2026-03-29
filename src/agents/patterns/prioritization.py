"""
Prioritization Pattern Implementation
Chapter 19: Prioritization & Scheduling

优先级与调度模式 - 管理多个任务的优先级和执行顺序，
优化资源利用并确保重要任务优先完成。
"""

from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta
import heapq
from loguru import logger
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class PriorityLevel(Enum):
    """优先级等级"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    BLOCKED = auto()
    CANCELLED = auto()


@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    priority: PriorityLevel
    status: TaskStatus = TaskStatus.PENDING
    
    # 时间属性
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[timedelta] = None
    
    # 执行属性
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    
    # 依赖关系
    dependencies: Set[str] = field(default_factory=set)
    
    # 资源需求
    required_resources: List[str] = field(default_factory=list)
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other: 'Task') -> bool:
        """用于优先队列比较"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        # 同优先级按截止时间
        if self.deadline and other.deadline:
            return self.deadline < other.deadline
        return self.created_at < other.created_at
    
    def is_ready(self) -> bool:
        """检查任务是否准备好执行"""
        return self.status == TaskStatus.PENDING and not self.dependencies
    
    def is_overdue(self) -> bool:
        """检查是否逾期"""
        if self.deadline and self.status in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]:
            return datetime.now() > self.deadline
        return False
    
    def urgency_score(self) -> float:
        """计算紧急度分数 (0-1)"""
        base_score = 1.0 / self.priority.value
        
        # 如果有截止时间，增加紧急度
        if self.deadline:
            time_remaining = (self.deadline - datetime.now()).total_seconds()
            if time_remaining < 0:
                base_score += 1.0  # 已逾期
            elif time_remaining < 3600:  # 1小时内
                base_score += 0.5
            elif time_remaining < 86400:  # 24小时内
                base_score += 0.3
        
        return min(base_score, 1.0)


class TaskQueue:
    """
    任务队列
    支持优先级排序的队列实现
    """
    
    def __init__(self):
        self._queue: List[Task] = []
        self._task_map: Dict[str, Task] = {}
        self._counter = 0  # 用于打破平局的计数器
    
    def enqueue(self, task: Task) -> bool:
        """添加任务到队列"""
        if task.id in self._task_map:
            logger.warning(f"Task {task.id} already in queue")
            return False
        
        self._counter += 1
        # 使用 (优先级, 计数器, 任务) 的元组
        heapq.heappush(self._queue, (task.priority.value, self._counter, task))
        self._task_map[task.id] = task
        task.status = TaskStatus.QUEUED
        
        logger.info(f"Task {task.id} ({task.name}) queued with priority {task.priority.name}")
        return True
    
    def dequeue(self) -> Optional[Task]:
        """取出最高优先级任务"""
        while self._queue:
            _, _, task = heapq.heappop(self._queue)
            if task.id in self._task_map:
                del self._task_map[task.id]
                return task
        return None
    
    def peek(self) -> Optional[Task]:
        """查看最高优先级任务（不取出）"""
        while self._queue:
            _, _, task = self._queue[0]
            if task.id in self._task_map:
                return task
            heapq.heappop(self._queue)
        return None
    
    def remove(self, task_id: str) -> bool:
        """从队列中移除任务"""
        if task_id in self._task_map:
            del self._task_map[task_id]
            logger.info(f"Task {task_id} removed from queue")
            return True
        return False
    
    def update_priority(self, task_id: str, new_priority: PriorityLevel) -> bool:
        """更新任务优先级"""
        task = self._task_map.get(task_id)
        if not task:
            return False
        
        # 重新入队
        self.remove(task_id)
        task.priority = new_priority
        self.enqueue(task)
        
        logger.info(f"Task {task_id} priority updated to {new_priority.name}")
        return True
    
    def get_all(self) -> List[Task]:
        """获取队列中所有任务（按优先级排序）"""
        return sorted(self._task_map.values())
    
    def __len__(self) -> int:
        return len(self._task_map)


class PriorityScheduler:
    """
    优先级调度器
    管理任务执行顺序和资源分配
    """
    
    def __init__(self, max_concurrent: int = 3):
        self.queue = TaskQueue()
        self.max_concurrent = max_concurrent
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        self.task_history: List[Dict[str, Any]] = []
        self._running = False
        logger.info(f"PriorityScheduler initialized (max_concurrent={max_concurrent})")
    
    def submit(self, task: Task) -> str:
        """提交任务"""
        self.queue.enqueue(task)
        self._check_and_schedule()
        return task.id
    
    def submit_batch(self, tasks: List[Task]) -> List[str]:
        """批量提交任务"""
        return [self.submit(t) for t in tasks]
    
    def _check_and_schedule(self):
        """检查并调度任务"""
        # 检查完成的任务，更新依赖
        self._update_dependencies()
        
        # 启动就绪的任务
        while (len(self.running_tasks) < self.max_concurrent and 
               len(self.queue) > 0):
            task = self.queue.peek()
            if not task:
                break
            
            # 检查资源可用性
            if self._check_resources(task):
                task = self.queue.dequeue()
                self._start_task(task)
            else:
                break
    
    def _check_resources(self, task: Task) -> bool:
        """检查资源是否可用"""
        # 简化实现：检查是否有冲突资源
        for running_task in self.running_tasks.values():
            if set(task.required_resources) & set(running_task.required_resources):
                return False
        return True
    
    def _start_task(self, task: Task):
        """开始执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self.running_tasks[task.id] = task
        
        logger.info(f"Task {task.id} ({task.name}) started")
        
        # 这里应该启动异步执行
        # 简化实现中只记录状态
        if task.func:
            try:
                result = task.func(*task.args, **task.kwargs)
                self._complete_task(task.id, result)
            except Exception as e:
                self._fail_task(task.id, str(e))
        else:
            # 无函数的任务直接完成
            self._complete_task(task.id, None)
    
    def _complete_task(self, task_id: str, result: Any):
        """完成任务"""
        task = self.running_tasks.pop(task_id, None)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            self.completed_tasks[task_id] = task
            
            self.task_history.append({
                "task_id": task_id,
                "action": "completed",
                "result": result,
                "timestamp": datetime.now()
            })
            
            logger.info(f"Task {task_id} completed")
            self._check_and_schedule()
    
    def _fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        task = self.running_tasks.pop(task_id, None)
        if task:
            task.status = TaskStatus.FAILED
            task.metadata["error"] = error
            self.failed_tasks[task_id] = task
            
            logger.error(f"Task {task_id} failed: {error}")
            self._check_and_schedule()
    
    def _update_dependencies(self):
        """更新任务依赖关系"""
        completed_ids = set(self.completed_tasks.keys())
        
        for task in list(self.queue.get_all()):
            # 移除已完成的依赖
            task.dependencies -= completed_ids
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 检查是否在队列中
        if self.queue.remove(task_id):
            return True
        
        # 检查是否正在运行（简化实现，实际可能需要中断机制）
        if task_id in self.running_tasks:
            logger.warning(f"Cannot cancel running task {task_id}")
            return False
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "queued": len(self.queue),
            "running": len(self.running_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "queue_details": [
                {"id": t.id, "name": t.name, "priority": t.priority.name}
                for t in self.queue.get_all()[:5]  # 前5个
            ]
        }
    
    def get_overdue_tasks(self) -> List[Task]:
        """获取逾期任务"""
        overdue = []
        for task in list(self.queue.get_all()) + list(self.running_tasks.values()):
            if task.is_overdue():
                overdue.append(task)
        return overdue


class PrioritizationAgent:
    """
    优先级 Agent
    智能分析和设置任务优先级
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        self.scheduler = PriorityScheduler()
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"📋 PrioritizationAgent initialized with model: {effective_id}")
    
    def analyze_priority(self, task_description: str, 
                        context: Dict[str, Any] = None) -> PriorityLevel:
        """
        使用 LLM 分析任务优先级
        
        Args:
            task_description: 任务描述
            context: 上下文信息
        
        Returns:
            优先级等级
        """
        prompt = ChatPromptTemplate.from_template("""
分析以下任务的优先级:

任务: {task}
上下文: {context}

请判断优先级等级（仅输出一个词）:
- CRITICAL: 紧急且重要，需要立即处理
- HIGH: 重要但不紧急，应尽快处理
- MEDIUM: 一般优先级
- LOW: 低优先级
- BACKGROUND: 背景任务，有空时处理

优先级:
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = chain.invoke({
                "task": task_description,
                "context": str(context) if context else "无"
            }).strip().upper()
            
            priority_map = {
                "CRITICAL": PriorityLevel.CRITICAL,
                "HIGH": PriorityLevel.HIGH,
                "MEDIUM": PriorityLevel.MEDIUM,
                "LOW": PriorityLevel.LOW,
                "BACKGROUND": PriorityLevel.BACKGROUND
            }
            
            return priority_map.get(response, PriorityLevel.MEDIUM)
        except Exception as e:
            logger.error(f"Priority analysis failed: {e}")
            return PriorityLevel.MEDIUM
    
    def create_task(self, name: str, description: str, 
                   deadline: Optional[datetime] = None,
                   auto_priority: bool = True,
                   **kwargs) -> Task:
        """
        创建任务
        
        Args:
            name: 任务名称
            description: 任务描述
            deadline: 截止时间
            auto_priority: 是否自动分析优先级
        
        Returns:
            Task 对象
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        if auto_priority:
            priority = self.analyze_priority(description)
        else:
            priority = kwargs.get("priority", PriorityLevel.MEDIUM)
        
        return Task(
            id=task_id,
            name=name,
            description=description,
            priority=priority,
            deadline=deadline,
            **kwargs
        )
    
    def submit_task(self, task: Task) -> str:
        """提交任务到调度器"""
        return self.scheduler.submit(task)
    
    def get_dashboard(self) -> Dict[str, Any]:
        """获取任务仪表板"""
        status = self.scheduler.get_status()
        overdue = self.scheduler.get_overdue_tasks()
        
        return {
            "scheduler_status": status,
            "overdue_count": len(overdue),
            "overdue_tasks": [{"id": t.id, "name": t.name} for t in overdue]
        }


if __name__ == "__main__":
    print("=" * 60)
    print("Prioritization Pattern Demo")
    print("=" * 60)
    
    # 创建优先级 Agent
    agent = PrioritizationAgent()
    
    # 创建示例任务
    tasks = [
        Task("t1", "Fix critical bug", PriorityLevel.CRITICAL),
        Task("t2", "Update documentation", PriorityLevel.LOW),
        Task("t3", "Review pull request", PriorityLevel.HIGH),
        Task("t4", "Code refactoring", PriorityLevel.MEDIUM),
        Task("t5", "Daily backup", PriorityLevel.BACKGROUND),
    ]
    
    print("\n--- Submitting Tasks ---")
    for task in tasks:
        agent.submit_task(task)
        print(f"Submitted: {task.name} ({task.priority.name})")
    
    # 查看队列状态
    print("\n--- Queue Status ---")
    status = agent.scheduler.get_status()
    print(f"Queued: {status['queued']}")
    print(f"Running: {status['running']}")
    print(f"Completed: {status['completed']}")
    
    # 查看队列详情
    print("\n--- Queue Details (Top 5) ---")
    for t in status['queue_details']:
        print(f"  [{t['priority']}] {t['name']}")
    
    # 仪表板
    print("\n--- Dashboard ---")
    dashboard = agent.get_dashboard()
    print(f"Overdue tasks: {dashboard['overdue_count']}")
