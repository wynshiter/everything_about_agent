"""
Exception Handling and Recovery Pattern Implementation
Chapter 12: Exception Handling and Recovery

异常处理与恢复模式 - 让 Agent 能够优雅地处理错误、重试失败操作并从故障中恢复。
"""

from typing import Dict, Any, List, Optional, Callable, Type, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
import time
import traceback
from loguru import logger
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = auto()      # 轻微错误，可以继续
    MEDIUM = auto()   # 中等错误，需要处理
    HIGH = auto()     # 严重错误，可能无法恢复
    CRITICAL = auto() # 致命错误，必须终止


class RecoveryStrategy(Enum):
    """恢复策略"""
    RETRY = auto()           # 重试
    FALLBACK = auto()        # 使用备用方案
    SKIP = auto()            # 跳过
    ABORT = auto()           # 终止
    DELEGATE = auto()        # 委托给其他组件
    MANUAL = auto()          # 需要人工干预


@dataclass
class ErrorContext:
    """错误上下文"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    traceback_str: str = ""
    context_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "severity": self.severity.name,
            "timestamp": self.timestamp,
            "context": self.context_data
        }


@dataclass
class RecoveryResult:
    """恢复结果"""
    success: bool
    strategy_used: RecoveryStrategy
    result: Any = None
    message: str = ""
    retry_count: int = 0


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.error_log: List[ErrorContext] = []
        self.recovery_strategies: Dict[Type, RecoveryStrategy] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.retry_policies: Dict[str, Dict[str, Any]] = {}
    
    def register_strategy(self, error_type: Type, strategy: RecoveryStrategy):
        """为特定错误类型注册恢复策略"""
        self.recovery_strategies[error_type] = strategy
        logger.info(f"Registered {strategy.name} for {error_type.__name__}")
    
    def register_fallback(self, operation_name: str, handler: Callable):
        """注册备用处理器"""
        self.fallback_handlers[operation_name] = handler
    
    def configure_retry(self, operation_name: str, max_retries: int = 3, 
                        backoff_factor: float = 1.0, retry_exceptions: List[Type] = None):
        """配置重试策略"""
        self.retry_policies[operation_name] = {
            "max_retries": max_retries,
            "backoff_factor": backoff_factor,
            "retry_exceptions": retry_exceptions or [Exception],
            "current_retry": 0
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorContext:
        """处理错误并记录"""
        error_context = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            severity=self._classify_severity(error),
            traceback_str=traceback.format_exc(),
            context_data=context or {}
        )
        
        self.error_log.append(error_context)
        logger.error(f"Error handled: {error_context.error_type} - {error_context.error_message}")
        
        return error_context
    
    def _classify_severity(self, error: Exception) -> ErrorSeverity:
        """分类错误严重程度"""
        critical_errors = (SystemExit, KeyboardInterrupt, MemoryError)
        high_errors = (ConnectionError, TimeoutError, PermissionError)
        
        if isinstance(error, critical_errors):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, high_errors):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def attempt_recovery(self, error: Exception, operation: Callable, 
                        operation_name: str, *args, **kwargs) -> RecoveryResult:
        """尝试恢复"""
        error_context = self.handle_error(error, {"operation": operation_name})
        
        # 确定恢复策略
        strategy = self._determine_strategy(error, operation_name)
        
        logger.info(f"Attempting recovery with strategy: {strategy.name}")
        
        if strategy == RecoveryStrategy.RETRY:
            return self._execute_retry(operation, operation_name, *args, **kwargs)
        
        elif strategy == RecoveryStrategy.FALLBACK:
            return self._execute_fallback(operation_name, *args, **kwargs)
        
        elif strategy == RecoveryStrategy.SKIP:
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.SKIP,
                message="Operation skipped"
            )
        
        elif strategy == RecoveryStrategy.DELEGATE:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.DELEGATE,
                message="Error delegated for handling"
            )
        
        else:  # ABORT or MANUAL
            return RecoveryResult(
                success=False,
                strategy_used=strategy,
                message=f"Operation aborted: {error_context.error_message}"
            )
    
    def _determine_strategy(self, error: Exception, operation_name: str) -> RecoveryStrategy:
        """确定恢复策略"""
        error_type = type(error)
        
        # 检查是否有注册的策略
        if error_type in self.recovery_strategies:
            return self.recovery_strategies[error_type]
        
        # 检查重试策略
        if operation_name in self.retry_policies:
            return RecoveryStrategy.RETRY
        
        # 检查是否有备用处理器
        if operation_name in self.fallback_handlers:
            return RecoveryStrategy.FALLBACK
        
        # 默认策略
        severity = self._classify_severity(error)
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.ABORT
        elif severity == ErrorSeverity.HIGH:
            return RecoveryStrategy.MANUAL
        else:
            return RecoveryStrategy.SKIP
    
    def _execute_retry(self, operation: Callable, operation_name: str, 
                       *args, **kwargs) -> RecoveryResult:
        """执行重试"""
        policy = self.retry_policies.get(operation_name, {
            "max_retries": 3,
            "backoff_factor": 1.0,
            "current_retry": 0
        })
        
        max_retries = policy["max_retries"]
        backoff = policy["backoff_factor"]
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Retry attempt {attempt}/{max_retries} for {operation_name}")
                time.sleep(backoff * (attempt - 1))  # 指数退避
                
                result = operation(*args, **kwargs)
                return RecoveryResult(
                    success=True,
                    strategy_used=RecoveryStrategy.RETRY,
                    result=result,
                    message=f"Success after {attempt} retries",
                    retry_count=attempt
                )
            except Exception as e:
                logger.warning(f"Retry {attempt} failed: {e}")
                if attempt == max_retries:
                    break
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.RETRY,
            message=f"Failed after {max_retries} retries",
            retry_count=max_retries
        )
    
    def _execute_fallback(self, operation_name: str, *args, **kwargs) -> RecoveryResult:
        """执行备用方案"""
        handler = self.fallback_handlers.get(operation_name)
        if not handler:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK,
                message="No fallback handler available"
            )
        
        try:
            result = handler(*args, **kwargs)
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK,
                result=result,
                message="Fallback execution successful"
            )
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK,
                message=f"Fallback also failed: {str(e)}"
            )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        if not self.error_log:
            return {"total_errors": 0}
        
        severity_counts = {}
        error_type_counts = {}
        
        for error in self.error_log:
            severity_counts[error.severity.name] = severity_counts.get(error.severity.name, 0) + 1
            error_type_counts[error.error_type] = error_type_counts.get(error.error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_log),
            "by_severity": severity_counts,
            "by_type": error_type_counts,
            "recent_errors": [e.to_dict() for e in self.error_log[-5:]]
        }


def resilient(max_retries: int = 3, fallback_value: Any = None, 
              retry_exceptions: tuple = (Exception,)):
    """
    装饰器：使函数具备弹性
    
    Args:
        max_retries: 最大重试次数
        fallback_value: 失败时的回退值
        retry_exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    logger.warning(f"{func.__name__} attempt {attempt} failed: {e}")
                    if attempt == max_retries:
                        if fallback_value is not None:
                            logger.info(f"Using fallback value for {func.__name__}")
                            return fallback_value
                        raise
                    time.sleep(0.5 * attempt)  # 简单退避
            return fallback_value
        return wrapper
    return decorator


class ExceptionHandlerAgent:
    """
    异常处理与恢复 Agent
    集成 LLM 进行错误分析和恢复建议
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        self.error_handler = ErrorHandler()
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🛡️ ExceptionHandlerAgent initialized with model: {effective_id}")
    
    def analyze_error(self, error_context: ErrorContext) -> str:
        """使用 LLM 分析错误并提供建议"""
        prompt = ChatPromptTemplate.from_template("""
分析以下错误并提供处理建议：

错误类型: {error_type}
错误信息: {error_message}
严重程度: {severity}
上下文: {context}

请提供:
1. 错误原因分析
2. 建议的恢复策略
3. 预防措施

简明扼要地回答。
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "error_type": error_context.error_type,
            "error_message": error_context.error_message,
            "severity": error_context.severity.name,
            "context": str(error_context.context_data)
        })
    
    def execute_with_recovery(self, operation: Callable, operation_name: str,
                             *args, **kwargs) -> RecoveryResult:
        """执行操作并处理可能的异常"""
        try:
            result = operation(*args, **kwargs)
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.RETRY,  # 实际上没有重试
                result=result,
                message="Operation completed successfully"
            )
        except Exception as e:
            logger.error(f"Operation {operation_name} failed: {e}")
            return self.error_handler.attempt_recovery(
                e, operation, operation_name, *args, **kwargs
            )
    
    def register_recovery_strategy(self, error_type: Type, strategy: RecoveryStrategy):
        """注册恢复策略"""
        self.error_handler.register_strategy(error_type, strategy)
    
    def get_recovery_report(self) -> Dict[str, Any]:
        """获取恢复报告"""
        return self.error_handler.get_error_summary()


if __name__ == "__main__":
    print("=" * 60)
    print("Exception Handling and Recovery Pattern Demo")
    print("=" * 60)
    
    # 创建 Agent
    agent = ExceptionHandlerAgent()
    
    # 配置重试策略
    agent.error_handler.configure_retry(
        "api_call",
        max_retries=3,
        backoff_factor=1.0
    )
    
    # 注册备用处理器
    def fallback_handler(*args, **kwargs):
        return {"status": "fallback", "data": "default"}
    
    agent.error_handler.register_fallback("api_call", fallback_handler)
    
    # 测试弹性装饰器
    @resilient(max_retries=2, fallback_value="default_value")
    def unstable_operation(should_fail: bool = True):
        """模拟不稳定操作"""
        if should_fail:
            raise ConnectionError("Simulated connection error")
        return "success"
    
    print("\n--- Testing Resilient Decorator ---")
    result = unstable_operation(should_fail=False)
    print(f"Success case: {result}")
    
    result = unstable_operation(should_fail=True)
    print(f"Failure with fallback: {result}")
    
    # 模拟错误处理
    print("\n--- Simulating Error Handling ---")
    try:
        raise ValueError("Test error")
    except Exception as e:
        error_ctx = agent.error_handler.handle_error(e, {"operation": "test"})
        print(f"Error captured: {error_ctx.error_type}")
        print(f"Severity: {error_ctx.severity.name}")
    
    # 错误摘要
    print("\n--- Error Summary ---")
    summary = agent.get_recovery_report()
    print(f"Total errors: {summary['total_errors']}")
    print(f"By severity: {summary.get('by_severity', {})}")
