"""
Exploration Pattern Implementation
Chapter 20: Exploration & Experimentation

探索与实验模式 - 支持 Agent 主动探索未知领域、
测试假设并从实验中学习。
"""

from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import random
from loguru import logger
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ExplorationStrategy(Enum):
    """探索策略"""
    RANDOM = auto()         # 随机探索
    SYSTEMATIC = auto()     # 系统性探索
    GREEDY = auto()         # 贪心探索
    BALANCED = auto()       # 平衡探索
    ADAPTIVE = auto()       # 自适应探索


class ExperimentStatus(Enum):
    """实验状态"""
    PLANNED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    ABORTED = auto()


@dataclass
class Hypothesis:
    """假设"""
    id: str
    statement: str
    confidence: float = 0.5  # 0-1
    tested: bool = False
    validated: Optional[bool] = None
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    
    def update_confidence(self, new_evidence: float):
        """根据新证据更新置信度"""
        # 贝叶斯更新简化版
        self.confidence = (self.confidence + new_evidence) / 2
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class Experiment:
    """实验"""
    id: str
    name: str
    hypothesis_id: str
    description: str
    status: ExperimentStatus = ExperimentStatus.PLANNED
    
    # 实验设计
    variables: Dict[str, Any] = field(default_factory=dict)
    control_group: Dict[str, Any] = field(default_factory=dict)
    test_groups: List[Dict[str, Any]] = field(default_factory=list)
    
    # 执行属性
    func: Optional[Callable] = None
    
    # 结果
    results: List[Dict[str, Any]] = field(default_factory=list)
    conclusion: Optional[str] = None
    
    # 时间
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class KnowledgeSpace:
    """
    知识空间
    表示 Agent 已知和未知的领域
    """
    
    def __init__(self):
        self.known_facts: Set[str] = set()
        self.known_concepts: Dict[str, Dict[str, Any]] = {}
        self.unknown_areas: Set[str] = set()
        self.explored_paths: List[Dict[str, Any]] = []
        self.hypotheses: Dict[str, Hypothesis] = {}
        
        logger.info("KnowledgeSpace initialized")
    
    def add_fact(self, fact: str, confidence: float = 1.0):
        """添加已知事实"""
        self.known_facts.add(fact)
        if confidence < 1.0:
            self.known_concepts[fact] = {"confidence": confidence}
    
    def mark_unknown(self, area: str):
        """标记未知领域"""
        self.unknown_areas.add(area)
        logger.info(f"New unknown area identified: {area}")
    
    def add_hypothesis(self, hypothesis: Hypothesis):
        """添加假设"""
        self.hypotheses[hypothesis.id] = hypothesis
    
    def get_exploration_candidates(self) -> List[str]:
        """获取候选探索领域"""
        # 返回未知领域
        return list(self.unknown_areas)
    
    def get_untested_hypotheses(self) -> List[Hypothesis]:
        """获取未测试的假设"""
        return [h for h in self.hypotheses.values() if not h.tested]
    
    def record_exploration(self, area: str, outcome: Dict[str, Any]):
        """记录探索结果"""
        self.explored_paths.append({
            "area": area,
            "outcome": outcome,
            "timestamp": datetime.now()
        })
        
        # 从未知移到已知
        if area in self.unknown_areas:
            self.unknown_areas.remove(area)
            self.add_fact(area, outcome.get("confidence", 0.5))
    
    def get_coverage(self) -> float:
        """获取知识覆盖率"""
        total = len(self.known_facts) + len(self.unknown_areas)
        if total == 0:
            return 1.0
        return len(self.known_facts) / total


class ExperimentRunner:
    """
    实验运行器
    管理和执行实验
    """
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.results_history: List[Dict[str, Any]] = []
        logger.info("ExperimentRunner initialized")
    
    def design_experiment(self, hypothesis: Hypothesis, 
                         name: str = None) -> Experiment:
        """设计实验"""
        exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        return Experiment(
            id=exp_id,
            name=name or f"Test {hypothesis.statement[:30]}",
            hypothesis_id=hypothesis.id,
            description=f"Test hypothesis: {hypothesis.statement}",
            variables={"hypothesis_confidence": hypothesis.confidence}
        )
    
    def register_experiment(self, experiment: Experiment) -> str:
        """注册实验"""
        self.experiments[experiment.id] = experiment
        logger.info(f"Experiment registered: {experiment.name}")
        return experiment.id
    
    def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """运行实验"""
        exp = self.experiments.get(experiment_id)
        if not exp:
            return {"error": "Experiment not found"}
        
        if exp.status == ExperimentStatus.RUNNING:
            return {"error": "Experiment already running"}
        
        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.now()
        
        logger.info(f"Running experiment: {exp.name}")
        
        try:
            # 执行实验函数
            if exp.func:
                results = []
                for group in exp.test_groups:
                    result = exp.func(**group)
                    results.append({"group": group, "result": result})
                exp.results = results
            else:
                # 模拟实验结果
                exp.results = [{"group": g, "result": random.random()} 
                              for g in exp.test_groups]
            
            exp.status = ExperimentStatus.COMPLETED
            exp.completed_at = datetime.now()
            
            # 生成结论
            exp.conclusion = self._generate_conclusion(exp)
            
            result_summary = {
                "experiment_id": experiment_id,
                "status": "completed",
                "results_count": len(exp.results)
            }
            
            self.results_history.append(result_summary)
            return result_summary
            
        except Exception as e:
            exp.status = ExperimentStatus.FAILED
            logger.error(f"Experiment failed: {e}")
            return {"error": str(e)}
    
    def _generate_conclusion(self, experiment: Experiment) -> str:
        """生成实验结论"""
        if not experiment.results:
            return "No results available"
        
        # 简化分析
        avg_result = sum(r["result"] for r in experiment.results) / len(experiment.results)
        
        if avg_result > 0.7:
            return f"Strong positive result (avg: {avg_result:.2f})"
        elif avg_result > 0.4:
            return f"Mixed results (avg: {avg_result:.2f})"
        else:
            return f"Weak or negative result (avg: {avg_result:.2f})"
    
    def get_experiment_report(self, experiment_id: str) -> Dict[str, Any]:
        """获取实验报告"""
        exp = self.experiments.get(experiment_id)
        if not exp:
            return {"error": "Not found"}
        
        return {
            "id": exp.id,
            "name": exp.name,
            "status": exp.status.name,
            "hypothesis": exp.hypothesis_id,
            "duration": (exp.completed_at - exp.started_at).total_seconds() 
                       if exp.completed_at and exp.started_at else None,
            "results_summary": exp.conclusion
        }


class ExplorationAgent:
    """
    探索 Agent
    主动探索未知领域并验证假设
    """
    
    def __init__(self, model_id: str = None, 
                 strategy: ExplorationStrategy = ExplorationStrategy.BALANCED):
        self.llm = model_loader.load_llm(model_id)
        self.strategy = strategy
        self.knowledge = KnowledgeSpace()
        self.experiment_runner = ExperimentRunner()
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🔍 ExplorationAgent initialized with model: {effective_id}")
    
    def identify_unknown(self, domain_description: str) -> List[str]:
        """
        使用 LLM 识别未知领域
        
        Args:
            domain_description: 领域描述
        
        Returns:
            未知领域列表
        """
        prompt = ChatPromptTemplate.from_template("""
基于以下领域描述，识别需要进一步探索的未知领域或问题:

领域: {domain}

请列出 3-5 个尚未明确或需要验证的方面。
每行一个，简洁描述。
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        response = chain.invoke({"domain": domain_description})
        
        unknowns = [line.strip("- ") for line in response.split("\n") if line.strip()]
        
        for u in unknowns:
            self.knowledge.mark_unknown(u)
        
        return unknowns
    
    def generate_hypothesis(self, area: str) -> Hypothesis:
        """
        为未知领域生成假设
        
        Args:
            area: 探索领域
        
        Returns:
            Hypothesis 对象
        """
        prompt = ChatPromptTemplate.from_template("""
针对以下领域，生成一个可验证的假设:

领域: {area}

请生成一个具体的、可测试的假设陈述。
假设应该能用实验验证真假。

假设:
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        statement = chain.invoke({"area": area}).strip()
        
        hypothesis_id = f"hypo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        hypothesis = Hypothesis(
            id=hypothesis_id,
            statement=statement
        )
        
        self.knowledge.add_hypothesis(hypothesis)
        logger.info(f"Hypothesis generated: {statement[:50]}...")
        
        return hypothesis
    
    def explore(self, focus_area: str = None) -> Dict[str, Any]:
        """
        执行探索
        
        Args:
            focus_area: 特定关注领域（可选）
        
        Returns:
            探索结果
        """
        # 1. 选择探索目标
        if focus_area:
            target = focus_area
        else:
            candidates = self.knowledge.get_exploration_candidates()
            if not candidates:
                return {"status": "no_candidates", "message": "No unknown areas to explore"}
            
            # 根据策略选择
            if self.strategy == ExplorationStrategy.RANDOM:
                target = random.choice(candidates)
            else:
                target = candidates[0]  # 默认取第一个
        
        logger.info(f"Exploring: {target}")
        
        # 2. 生成假设
        hypothesis = self.generate_hypothesis(target)
        
        # 3. 设计并运行实验
        experiment = self.experiment_runner.design_experiment(hypothesis)
        experiment.test_groups = [
            {"condition": "test", "parameters": {}},
            {"condition": "control", "parameters": {}}
        ]
        
        exp_id = self.experiment_runner.register_experiment(experiment)
        
        # 4. 运行实验
        result = self.experiment_runner.run_experiment(exp_id)
        
        # 5. 更新知识
        self.knowledge.record_exploration(target, {
            "hypothesis": hypothesis.statement,
            "experiment": exp_id,
            "result": result
        })
        
        hypothesis.tested = True
        
        return {
            "area": target,
            "hypothesis": hypothesis.statement,
            "experiment_id": exp_id,
            "result": result
        }
    
    def get_exploration_summary(self) -> Dict[str, Any]:
        """获取探索摘要"""
        return {
            "strategy": self.strategy.name,
            "knowledge_coverage": self.knowledge.get_coverage(),
            "known_facts": len(self.knowledge.known_facts),
            "unknown_areas": len(self.knowledge.unknown_areas),
            "active_hypotheses": len(self.knowledge.hypotheses),
            "untested_hypotheses": len(self.knowledge.get_untested_hypotheses()),
            "experiments_count": len(self.experiment_runner.experiments),
            "completed_experiments": len([e for e in self.experiment_runner.experiments.values() 
                                         if e.status == ExperimentStatus.COMPLETED])
        }


if __name__ == "__main__":
    print("=" * 60)
    print("Exploration Pattern Demo")
    print("=" * 60)
    
    # 创建探索 Agent
    agent = ExplorationAgent()
    
    # 识别未知领域
    print("\n--- Identifying Unknown Areas ---")
    domain = "如何提高代码质量和开发效率"
    unknowns = agent.identify_unknown(domain)
    print(f"Domain: {domain}")
    print("Unknown areas:")
    for i, u in enumerate(unknowns, 1):
        print(f"  {i}. {u}")
    
    # 生成假设
    print("\n--- Generating Hypotheses ---")
    if unknowns:
        hypothesis = agent.generate_hypothesis(unknowns[0])
        print(f"Hypothesis: {hypothesis.statement}")
    
    # 执行探索
    print("\n--- Running Exploration ---")
    result = agent.explore()
    print(f"Explored: {result.get('area')}")
    print(f"Hypothesis: {result.get('hypothesis')}")
    print(f"Experiment: {result.get('experiment_id')}")
    
    # 摘要
    print("\n--- Exploration Summary ---")
    summary = agent.get_exploration_summary()
    print(f"Strategy: {summary['strategy']}")
    print(f"Knowledge Coverage: {summary['knowledge_coverage']:.1%}")
    print(f"Known Facts: {summary['known_facts']}")
    print(f"Unknown Areas: {summary['unknown_areas']}")
    print(f"Hypotheses: {summary['active_hypotheses']}")
    print(f"Experiments: {summary['experiments_count']}")
