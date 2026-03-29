"""
Evaluation Pattern Implementation
Chapter 18: Evaluation & Metrics

评估模式 - 系统性评估 Agent 性能和质量。
支持多种评估指标、基准测试和自动评估流程。
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import statistics
from loguru import logger
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class MetricType(Enum):
    """指标类型"""
    ACCURACY = auto()       # 准确性
    RELEVANCE = auto()      # 相关性
    COHERENCE = auto()      # 连贯性
    COMPLETENESS = auto()   # 完整性
    HELPFULNESS = auto()    # 有用性
    SAFETY = auto()         # 安全性
    LATENCY = auto()        # 延迟
    TOKEN_USAGE = auto()    # Token 使用量
    CUSTOM = auto()         # 自定义


@dataclass
class EvalMetric:
    """评估指标"""
    name: str
    metric_type: MetricType
    score: float  # 0-1
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class EvalResult:
    """评估结果"""
    test_case_id: str
    input_data: Any
    expected_output: Any
    actual_output: Any
    metrics: List[EvalMetric] = field(default_factory=list)
    passed: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    def overall_score(self) -> float:
        if not self.metrics:
            return 0.0
        total_weight = sum(m.weight for m in self.metrics)
        if total_weight == 0:
            return 0.0
        return sum(m.weighted_score() for m in self.metrics) / total_weight


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    input_data: Any
    expected_output: Any
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCalculator:
    """指标计算器"""
    
    @staticmethod
    def exact_match(predicted: str, expected: str) -> float:
        """精确匹配分数"""
        return 1.0 if predicted.strip().lower() == expected.strip().lower() else 0.0
    
    @staticmethod
    def contains_match(predicted: str, expected: str) -> float:
        """包含匹配分数"""
        pred_lower = predicted.lower()
        exp_lower = expected.lower()
        if exp_lower in pred_lower:
            return 1.0
        # 部分匹配
        words = exp_lower.split()
        matches = sum(1 for w in words if w in pred_lower)
        return matches / len(words) if words else 0.0
    
    @staticmethod
    def semantic_similarity(predicted: str, expected: str) -> float:
        """语义相似度（简化版，实际应使用嵌入模型）"""
        # 简单的词重叠计算
        pred_words = set(predicted.lower().split())
        exp_words = set(expected.lower().split())
        
        if not pred_words or not exp_words:
            return 0.0
        
        intersection = pred_words & exp_words
        union = pred_words | exp_words
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def response_length_score(response: str, min_len: int = 10, max_len: int = 1000) -> float:
        """响应长度评分"""
        length = len(response)
        if length < min_len:
            return length / min_len
        elif length > max_len:
            return max(0.0, 1.0 - (length - max_len) / max_len)
        return 1.0


class Evaluator:
    """
    评估器
    管理测试用例和评估指标
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.test_cases: List[TestCase] = []
        self.results: List[EvalResult] = []
        self.metrics_calculator = MetricsCalculator()
        self.custom_evaluators: Dict[str, Callable] = {}
        logger.info(f"📊 Evaluator '{name}' initialized")
    
    def add_test_case(self, test_case: TestCase):
        """添加测试用例"""
        self.test_cases.append(test_case)
        logger.info(f"Added test case: {test_case.name}")
    
    def add_test_cases(self, cases: List[Dict[str, Any]]):
        """批量添加测试用例"""
        for case in cases:
            tc = TestCase(
                id=case.get("id", f"tc_{len(self.test_cases)}"),
                name=case.get("name", "unnamed"),
                input_data=case.get("input"),
                expected_output=case.get("expected"),
                tags=case.get("tags", [])
            )
            self.add_test_case(tc)
    
    def register_custom_evaluator(self, name: str, func: Callable):
        """注册自定义评估函数"""
        self.custom_evaluators[name] = func
        logger.info(f"Registered custom evaluator: {name}")
    
    def evaluate(self, agent_func: Callable, 
                 test_case_filter: str = None) -> List[EvalResult]:
        """
        执行评估
        
        Args:
            agent_func: 被测试的 Agent 函数
            test_case_filter: 测试用例过滤标签
        
        Returns:
            评估结果列表
        """
        results = []
        
        test_cases = self.test_cases
        if test_case_filter:
            test_cases = [tc for tc in test_cases if test_case_filter in tc.tags]
        
        logger.info(f"Running evaluation on {len(test_cases)} test cases")
        
        for tc in test_cases:
            try:
                # 执行 Agent
                actual_output = agent_func(tc.input_data)
                
                # 计算指标
                metrics = self._calculate_metrics(
                    str(actual_output), 
                    str(tc.expected_output)
                )
                
                # 判断是否通过
                overall = sum(m.score * m.weight for m in metrics) / sum(m.weight for m in metrics) if metrics else 0
                passed = overall >= 0.7  # 阈值
                
                result = EvalResult(
                    test_case_id=tc.id,
                    input_data=tc.input_data,
                    expected_output=tc.expected_output,
                    actual_output=actual_output,
                    metrics=metrics,
                    passed=passed
                )
                
                results.append(result)
                self.results.append(result)
                
            except Exception as e:
                logger.error(f"Evaluation failed for {tc.id}: {e}")
                results.append(EvalResult(
                    test_case_id=tc.id,
                    input_data=tc.input_data,
                    expected_output=tc.expected_output,
                    actual_output=f"ERROR: {e}",
                    passed=False
                ))
        
        return results
    
    def _calculate_metrics(self, predicted: str, expected: str) -> List[EvalMetric]:
        """计算评估指标"""
        metrics = []
        
        # 精确匹配
        metrics.append(EvalMetric(
            name="exact_match",
            metric_type=MetricType.ACCURACY,
            score=self.metrics_calculator.exact_match(predicted, expected),
            weight=0.3
        ))
        
        # 包含匹配
        metrics.append(EvalMetric(
            name="contains_match",
            metric_type=MetricType.ACCURACY,
            score=self.metrics_calculator.contains_match(predicted, expected),
            weight=0.3
        ))
        
        # 语义相似度
        metrics.append(EvalMetric(
            name="semantic_similarity",
            metric_type=MetricType.RELEVANCE,
            score=self.metrics_calculator.semantic_similarity(predicted, expected),
            weight=0.4
        ))
        
        return metrics
    
    def generate_report(self) -> Dict[str, Any]:
        """生成评估报告"""
        if not self.results:
            return {"error": "No evaluation results available"}
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        
        # 按指标聚合
        metric_scores: Dict[str, List[float]] = {}
        for result in self.results:
            for metric in result.metrics:
                if metric.name not in metric_scores:
                    metric_scores[metric.name] = []
                metric_scores[metric.name].append(metric.score)
        
        metric_summary = {
            name: {
                "mean": statistics.mean(scores),
                "median": statistics.median(scores),
                "min": min(scores),
                "max": max(scores)
            }
            for name, scores in metric_scores.items()
        }
        
        return {
            "evaluator": self.name,
            "total_test_cases": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "metrics_summary": metric_summary,
            "overall_score": statistics.mean([r.overall_score() for r in self.results]) if self.results else 0
        }


class LLMBasedEvaluator:
    """
    基于 LLM 的评估器
    使用 LLM 进行智能评估
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🤖 LLMBasedEvaluator initialized with model: {effective_id}")
    
    def evaluate_response(self, query: str, response: str, 
                         criteria: List[str] = None) -> Dict[str, Any]:
        """
        使用 LLM 评估响应质量
        
        Args:
            query: 原始查询
            response: Agent 响应
            criteria: 评估标准
        
        Returns:
            评估结果
        """
        default_criteria = [
            "准确性 (Accuracy)",
            "相关性 (Relevance)",
            "完整性 (Completeness)",
            "清晰度 (Clarity)"
        ]
        criteria = criteria or default_criteria
        
        prompt = ChatPromptTemplate.from_template("""
请评估以下 AI 回复的质量:

用户问题: {query}

AI 回复: {response}

评估标准:
{criteria}

请以 JSON 格式输出评分 (1-10):
{{
    "scores": {{
        "准确性": 8,
        "相关性": 9,
        ...
    }},
    "overall": 8.5,
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["改进点1"],
    "explanation": "评估解释"
}}

只输出 JSON，不要其他文字。
""")
        
        criteria_text = "\n".join([f"- {c}" for c in criteria])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({
                "query": query[:500],
                "response": response[:1000],
                "criteria": criteria_text
            })
            
            # 解析结果
            eval_data = eval(result)
            return {
                "success": True,
                "scores": eval_data.get("scores", {}),
                "overall": eval_data.get("overall", 0),
                "feedback": {
                    "strengths": eval_data.get("strengths", []),
                    "weaknesses": eval_data.get("weaknesses", [])
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class EvaluationAgent:
    """
    评估 Agent
    集成多种评估方法
    """
    
    def __init__(self, model_id: str = None):
        self.model_id = model_id
        self.evaluator = Evaluator()
        self.llm_evaluator = LLMBasedEvaluator(model_id)
        logger.info(f"📊 EvaluationAgent initialized")
    
    def run_benchmark(self, agent_func: Callable, 
                     test_suite: str = "default") -> Dict[str, Any]:
        """
        运行基准测试
        
        Args:
            agent_func: 被测试的 Agent 函数
            test_suite: 测试套件名称
        
        Returns:
            评估报告
        """
        # 加载测试套件
        if test_suite == "default":
            self._load_default_test_suite()
        
        # 执行评估
        results = self.evaluator.evaluate(agent_func)
        
        # 生成报告
        report = self.evaluator.generate_report()
        
        return {
            "test_suite": test_suite,
            "report": report,
            "detailed_results": [
                {
                    "test_case_id": r.test_case_id,
                    "passed": r.passed,
                    "score": r.overall_score(),
                    "metrics": {m.name: m.score for m in r.metrics}
                }
                for r in results
            ]
        }
    
    def _load_default_test_suite(self):
        """加载默认测试套件"""
        default_cases = [
            {
                "id": "basic_1",
                "name": "Greeting",
                "input": "Hello",
                "expected": "hello",
                "tags": ["basic"]
            },
            {
                "id": "basic_2",
                "name": "Simple Question",
                "input": "What is 2+2?",
                "expected": "4",
                "tags": ["basic", "math"]
            }
        ]
        self.evaluator.add_test_cases(default_cases)
    
    def evaluate_single(self, query: str, response: str) -> Dict[str, Any]:
        """评估单个响应"""
        return self.llm_evaluator.evaluate_response(query, response)


if __name__ == "__main__":
    print("=" * 60)
    print("Evaluation Pattern Demo")
    print("=" * 60)
    
    # 创建评估 Agent
    agent = EvaluationAgent()
    
    # 添加测试用例
    test_cases = [
        {
            "id": "tc_1",
            "name": "Capital of France",
            "input": "What is the capital of France?",
            "expected": "Paris",
            "tags": ["geography"]
        },
        {
            "id": "tc_2",
            "name": "Programming Language",
            "input": "What language is this: print('hello')?",
            "expected": "Python",
            "tags": ["programming"]
        }
    ]
    
    agent.evaluator.add_test_cases(test_cases)
    
    # 示例评估函数
    def dummy_agent(query: str) -> str:
        """模拟 Agent"""
        responses = {
            "France": "Paris",
            "Python": "Python"
        }
        for key, value in responses.items():
            if key.lower() in query.lower():
                return value
        return "I don't know"
    
    # 执行评估
    print("\n--- Running Evaluation ---")
    results = agent.evaluator.evaluate(dummy_agent)
    
    for r in results:
        print(f"\nTest Case: {r.test_case_id}")
        print(f"  Expected: {r.expected_output}")
        print(f"  Actual: {r.actual_output}")
        print(f"  Passed: {r.passed}")
        print(f"  Score: {r.overall_score():.2f}")
    
    # 生成报告
    print("\n--- Evaluation Report ---")
    report = agent.evaluator.generate_report()
    print(f"Total: {report['total_test_cases']}")
    print(f"Passed: {report['passed']}")
    print(f"Pass Rate: {report['pass_rate']:.1%}")
    print(f"Overall Score: {report['overall_score']:.2f}")
