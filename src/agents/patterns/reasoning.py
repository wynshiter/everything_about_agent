"""
Reasoning Pattern Implementation
Chapter 16: Reasoning (Chain-of-Thought / ReAct)

推理模式 - 让 Agent 展示思考过程，提高推理质量和可解释性。
支持 Chain-of-Thought、ReAct、Tree of Thoughts 等推理方法。
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from loguru import logger
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class ReasoningMethod(Enum):
    """推理方法"""
    CHAIN_OF_THOUGHT = auto()      # 思维链
    REACT = auto()                 # Reasoning + Acting
    TREE_OF_THOUGHTS = auto()      # 思维树
    STEP_BY_STEP = auto()          # 逐步推理
    FEW_SHOT = auto()              # 少样本推理
    ZERO_SHOT = auto()             # 零样本推理


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_number: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    conclusion: Optional[str] = None


@dataclass
class ReasoningTrace:
    """推理轨迹"""
    question: str
    method: ReasoningMethod
    steps: List[ReasoningStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    confidence: float = 0.0


class ChainOfThoughtReasoner:
    """
    思维链推理器
    引导模型逐步思考问题
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🧠 ChainOfThoughtReasoner initialized with model: {effective_id}")
    
    def reason(self, question: str, show_working: bool = True) -> ReasoningTrace:
        """
        执行思维链推理
        
        Args:
            question: 问题
            show_working: 是否展示推理过程
        
        Returns:
            推理轨迹
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""你是一个善于思考的助手。请逐步分析问题，展示你的思考过程。
在回答之前，请先列出你的思考步骤，然后给出最终答案。
使用以下格式：
思考1: [你的第一步思考]
思考2: [你的第二步思考]
...
最终答案: [你的答案]"""),
            HumanMessage(content="问题: {question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({"question": question})
        
        # 解析推理步骤
        steps = self._parse_reasoning_steps(response)
        final_answer = self._extract_final_answer(response)
        
        trace = ReasoningTrace(
            question=question,
            method=ReasoningMethod.CHAIN_OF_THOUGHT,
            steps=steps,
            final_answer=final_answer,
            confidence=0.8 if final_answer else 0.0
        )
        
        if show_working:
            self._display_trace(trace)
        
        return trace
    
    def _parse_reasoning_steps(self, response: str) -> List[ReasoningStep]:
        """解析推理步骤"""
        steps = []
        lines = response.split('\n')
        step_num = 1
        
        for line in lines:
            line = line.strip()
            if line.startswith('思考') or line.startswith('Step') or line.startswith('思考'):
                thought = line.split(':', 1)[-1].strip()
                steps.append(ReasoningStep(
                    step_number=step_num,
                    thought=thought
                ))
                step_num += 1
            elif ':' in line and not line.startswith('最终答案'):
                # 可能是一个推理步骤
                thought = line.split(':', 1)[-1].strip()
                if len(thought) > 20:  # 过滤掉太短的行
                    steps.append(ReasoningStep(
                        step_number=step_num,
                        thought=thought
                    ))
                    step_num += 1
        
        return steps
    
    def _extract_final_answer(self, response: str) -> Optional[str]:
        """提取最终答案"""
        markers = ['最终答案:', 'Final Answer:', '答案:', 'Answer:']
        for marker in markers:
            if marker in response:
                return response.split(marker)[-1].strip()
        
        # 如果没有标记，返回最后一段
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        return paragraphs[-1] if paragraphs else response
    
    def _display_trace(self, trace: ReasoningTrace):
        """显示推理轨迹"""
        print(f"\n{'='*60}")
        print(f"问题: {trace.question}")
        print(f"方法: {trace.method.name}")
        print(f"{'='*60}")
        for step in trace.steps:
            print(f"\n步骤 {step.step_number}:")
            print(f"  思考: {step.thought}")
        print(f"\n最终答案: {trace.final_answer}")
        print(f"置信度: {trace.confidence}")


class ReActReasoner:
    """
    ReAct 推理器 (Reasoning + Acting)
    交替进行思考和行动
    """
    
    def __init__(self, model_id: str = None, tools: Dict[str, Callable] = None):
        self.llm = model_loader.load_llm(model_id)
        self.tools = tools or {}
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🔄 ReActReasoner initialized with model: {effective_id}")
    
    def reason(self, question: str, max_iterations: int = 5) -> ReasoningTrace:
        """
        执行 ReAct 推理
        
        Args:
            question: 问题
            max_iterations: 最大迭代次数
        
        Returns:
            推理轨迹
        """
        steps = []
        context = ""
        
        for i in range(max_iterations):
            # 思考步骤
            thought = self._think(question, context)
            
            # 决定行动
            action_result = self._act(thought)
            
            step = ReasoningStep(
                step_number=i + 1,
                thought=thought,
                action=action_result.get("action"),
                observation=action_result.get("observation")
            )
            steps.append(step)
            
            # 更新上下文
            if action_result.get("observation"):
                context += f"\n观察: {action_result['observation']}"
            
            # 检查是否已完成
            if action_result.get("finish"):
                break
        
        # 生成最终答案
        final_answer = self._generate_answer(question, steps)
        
        return ReasoningTrace(
            question=question,
            method=ReasoningMethod.REACT,
            steps=steps,
            final_answer=final_answer,
            confidence=0.85 if final_answer else 0.5
        )
    
    def _think(self, question: str, context: str) -> str:
        """思考步骤"""
        prompt = ChatPromptTemplate.from_template("""
问题: {question}

当前上下文: {context}

你应该:
1. 分析已知信息
2. 确定下一步需要什么信息或行动
3. 如果需要，指定要使用的工具（可用工具: {tools}）

思考（用一句话描述你的思考和计划）:
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "question": question,
            "context": context or "无",
            "tools": ", ".join(self.tools.keys()) or "无"
        }).strip()
    
    def _act(self, thought: str) -> Dict[str, Any]:
        """执行行动"""
        # 检查是否需要使用工具
        for tool_name, tool_func in self.tools.items():
            if tool_name.lower() in thought.lower():
                try:
                    observation = tool_func()
                    return {
                        "action": tool_name,
                        "observation": str(observation),
                        "finish": False
                    }
                except Exception as e:
                    return {
                        "action": tool_name,
                        "observation": f"Error: {e}",
                        "finish": False
                    }
        
        # 如果没有使用工具，检查是否已有答案
        if "答案" in thought or "answer" in thought.lower():
            return {
                "action": "conclude",
                "observation": thought,
                "finish": True
            }
        
        return {
            "action": "think",
            "observation": None,
            "finish": False
        }
    
    def _generate_answer(self, question: str, steps: List[ReasoningStep]) -> str:
        """基于推理步骤生成答案"""
        prompt = ChatPromptTemplate.from_template("""
基于以下推理过程，给出最终答案:

问题: {question}

推理步骤:
{steps}

最终答案（简洁）:
""")
        
        chain = prompt | self.llm | StrOutputParser()
        
        steps_text = "\n".join([
            f"{i+1}. {s.thought}"
            for i, s in enumerate(steps)
        ])
        
        return chain.invoke({
            "question": question,
            "steps": steps_text
        }).strip()


class TreeOfThoughtsReasoner:
    """
    思维树推理器
    探索多个推理路径
    """
    
    def __init__(self, model_id: str = None, beam_width: int = 3):
        self.llm = model_loader.load_llm(model_id)
        self.beam_width = beam_width
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🌲 TreeOfThoughtsReasoner initialized with model: {effective_id}")
    
    def reason(self, question: str, depth: int = 3) -> ReasoningTrace:
        """
        执行思维树推理
        
        Args:
            question: 问题
            depth: 搜索深度
        
        Returns:
            最佳推理轨迹
        """
        # 简化的实现：生成多个候选答案并选择最好的
        candidates = []
        
        for i in range(self.beam_width):
            prompt = ChatPromptTemplate.from_template("""
问题: {question}

请从不同的角度思考这个问题，提供第 {angle} 种分析角度和答案。

分析:
""")
            
            chain = prompt | self.llm | StrOutputParser()
            
            response = chain.invoke({
                "question": question,
                "angle": i + 1
            })
            
            candidates.append({
                "angle": i + 1,
                "reasoning": response,
                "score": self._evaluate_reasoning(response)
            })
        
        # 选择最佳候选
        best = max(candidates, key=lambda x: x["score"])
        
        steps = [ReasoningStep(
            step_number=1,
            thought=f"探索了 {len(candidates)} 个思考角度",
            conclusion=f"选择角度 {best['angle']} 作为最佳答案"
        )]
        
        return ReasoningTrace(
            question=question,
            method=ReasoningMethod.TREE_OF_THOUGHTS,
            steps=steps,
            final_answer=best["reasoning"],
            confidence=best["score"]
        )
    
    def _evaluate_reasoning(self, reasoning: str) -> float:
        """评估推理质量（简化版）"""
        # 基于长度、结构化程度等启发式评分
        score = 0.5
        
        # 有结构化标记加分
        if any(m in reasoning for m in ['思考', 'Step', '分析', '因为', '所以']):
            score += 0.2
        
        # 有结论加分
        if any(m in reasoning for m in ['结论', '答案', '因此']):
            score += 0.2
        
        # 长度适中加分
        if 100 < len(reasoning) < 1000:
            score += 0.1
        
        return min(score, 1.0)


class ReasoningAgent:
    """
    推理 Agent
    支持多种推理方法的统一接口
    """
    
    def __init__(self, model_id: str = None, default_method: ReasoningMethod = ReasoningMethod.CHAIN_OF_THOUGHT):
        self.default_method = default_method
        self.cot_reasoner = ChainOfThoughtReasoner(model_id)
        self.react_reasoner = ReActReasoner(model_id)
        self.tot_reasoner = TreeOfThoughtsReasoner(model_id)
        logger.info(f"🧠 ReasoningAgent initialized with default method: {default_method.name}")
    
    def solve(self, question: str, method: ReasoningMethod = None, show_working: bool = True) -> ReasoningTrace:
        """
        解决问题
        
        Args:
            question: 问题
            method: 推理方法（默认使用初始化时设置的方法）
            show_working: 是否展示推理过程
        
        Returns:
            推理轨迹
        """
        method = method or self.default_method
        
        if method == ReasoningMethod.CHAIN_OF_THOUGHT:
            return self.cot_reasoner.reason(question, show_working)
        elif method == ReasoningMethod.REACT:
            return self.react_reasoner.reason(question)
        elif method == ReasoningMethod.TREE_OF_THOUGHTS:
            return self.tot_reasoner.reason(question)
        else:
            # 默认使用 CoT
            return self.cot_reasoner.reason(question, show_working)
    
    def compare_methods(self, question: str) -> Dict[str, ReasoningTrace]:
        """比较不同推理方法的结果"""
        results = {}
        for method in [ReasoningMethod.CHAIN_OF_THOUGHT, ReasoningMethod.TREE_OF_THOUGHTS]:
            trace = self.solve(question, method, show_working=False)
            results[method.name] = trace
        return results


if __name__ == "__main__":
    print("=" * 60)
    print("Reasoning Pattern Demo")
    print("=" * 60)
    
    # 创建推理 Agent
    agent = ReasoningAgent()
    
    # 示例问题
    questions = [
        "如果一个苹果5元，3个苹果多少钱？请展示你的思考过程。",
        "解释为什么天空是蓝色的。"
    ]
    
    print("\n--- Chain-of-Thought Reasoning ---")
    for q in questions:
        trace = agent.cot_reasoner.reason(q, show_working=True)
    
    print("\n--- Note ---")
    print("Full reasoning requires LLM backend running")
