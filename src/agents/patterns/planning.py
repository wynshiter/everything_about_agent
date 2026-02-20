"""
Planning Pattern Implementation
Chapter 6: Planning

This module demonstrates the Planning pattern for breaking down complex tasks into steps.
"""

from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.utils.model_loader import model_loader
from loguru import logger


class PlanningAgent:
    """
    Implements the Planning pattern.
    Breaks down complex tasks into executable steps.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"PlanningAgent initialized with model: {effective_id}")
    
    def create_plan(self, task: str) -> List[str]:
        """Create a plan by breaking down the task into steps."""
        planning_prompt = ChatPromptTemplate.from_template(
            """Break down the following task into a numbered list of steps.
            Each step should be a clear, actionable item.
            
            Task: {task}
            
            Return a numbered list (1., 2., 3., etc.)"""
        )
        
        chain = planning_prompt | self.llm | StrOutputParser()
        result = chain.invoke({"task": task})
        
        # Parse steps
        steps = []
        for line in result.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                steps.append(line)
        
        return steps
    
    def execute_plan(self, task: str) -> Dict[str, Any]:
        """Create and execute a plan."""
        logger.info(f"Creating plan for: {task}")
        
        steps = self.create_plan(task)
        logger.info(f"Created plan with {len(steps)} steps")
        
        results = []
        for i, step in enumerate(steps):
            logger.info(f"Executing step {i+1}: {step}")
            # In a full implementation, execute each step
            results.append({"step": step, "status": "completed"})
        
        return {
            "task": task,
            "steps": steps,
            "results": results
        }


class ReActPlanningAgent:
    """
    Implements ReAct (Reasoning + Acting) planning.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
    
    def reason_and_act(self, task: str, max_iterations: int = 5) -> str:
        """Execute reasoning and action loops."""
        context = ""
        
        for i in range(max_iterations):
            # Reason
            reasoning_prompt = f"""
            Task: {task}
            Context so far: {context}
            
            What is the next step to take? Just describe the action.
            """
            # This is a simplified version
            # Full implementation would interleave reasoning and tool use
            
            context += f"\nIteration {i+1}: Thinking..."
            
            if "complete" in context.lower():
                break
        
        return context


# --- Google ADK Style ---
class ADKStylePlanningAgent:
    """
    Conceptual implementation for Google ADK.
    
    from google.adk.agents import LoopAgent, LlmAgent
    
    planner = LlmAgent(
        name="Planner",
        instruction="Create a plan for the task",
        output_key="plan"
    )
    
    executor = LlmAgent(
        name="Executor",
        instruction="Execute step: {current_step}"
    )
    
    # Use LoopAgent for iterative execution
    """
    
    def get_structure_example(self):
        return {
            "planner": {"output_key": "plan"},
            "executor": {"input_key": "current_step"},
            "loop": {"max_iterations": 10}
        }


if __name__ == "__main__":
    print("=" * 60)
    print("Planning Pattern Demo")
    print("=" * 60)
    
    agent = PlanningAgent()
    task = "Plan a trip to Japan"
    
    print(f"\nTask: {task}")
    print("\nPlan (requires LLM):")
    # print(agent.create_plan(task))
