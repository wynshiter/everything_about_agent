"""
Reflection Pattern Implementation
Chapter 4: Reflection

This module demonstrates the Reflection pattern for self-correction and iterative refinement.
"""

from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from src.utils.model_loader import model_loader
from loguru import logger


class ReflectionAgent:
    """
    Implements the Reflection pattern.
    Uses a Producer-Critic model for iterative refinement.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"🔄 ReflectionAgent initialized with model: {effective_id}")
    
    def generate(self, task: str, history: List = None) -> str:
        """Generate initial output or refine based on critique."""
        if history is None:
            # Initial generation
            prompt = ChatPromptTemplate.from_template(
                "Task: {task}\n\nProvide a complete solution."
            )
        else:
            # Refinement based on critique
            prompt = ChatPromptTemplate.from_template(
                "Task: {task}\n\nPrevious attempt:\n{previous}\n\n"
                "Please refine the solution based on the following critique:\n{critique}"
            )
        
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"task": task})
    
    def reflect(self, task: str, output: str) -> str:
        """Critique the generated output."""
        reflector_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a senior code reviewer and expert.
Critically evaluate the provided solution against the task requirements.
Look for bugs, style issues, missing edge cases, and areas for improvement.
If the solution is perfect, respond with 'CODE_IS_PERFECT'.
Otherwise, provide a bulleted list of your critiques."""),
            HumanMessage(content=f"Task: {task}\n\nSolution:\n{output}")
        ])
        
        chain = reflector_prompt | self.llm | StrOutputParser()
        return chain.invoke({})
    
    def run(self, task: str, max_iterations: int = 3) -> Dict[str, Any]:
        """
        Run reflection loop with iterative refinement.
        
        Args:
            task: The task description
            max_iterations: Maximum refinement iterations
            
        Returns:
            Dictionary with final output and iteration history
        """
        logger.info(f"🔄 Starting reflection loop for task: {task[:50]}...")
        
        current_output = ""
        history = []
        
        for i in range(max_iterations):
            logger.info(f"  Iteration {i + 1}/{max_iterations}")
            
            # Generate or refine
            if i == 0:
                current_output = self.generate(task)
            else:
                current_output = self.generate(task, history)
            
            # Reflect
            critique = self.reflect(task, current_output)
            
            # Check stopping condition
            if "CODE_IS_PERFECT" in critique:
                logger.info("  Reflection complete: Output is perfect")
                break
            
            # Store for next iteration
            history.append({
                "output": current_output,
                "critique": critique
            })
            
            logger.info(f"  Critique: {critique[:100]}...")
        
        return {
            "final_output": current_output,
            "iterations": i + 1,
            "history": history
        }


class SimpleReflectionChain:
    """
    Simpler reflection chain using LCEL.
    Single generate-critique-refine cycle.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        self.chain = self._build_chain()
    
    def _build_chain(self):
        # Generation prompt
        gen_prompt = ChatPromptTemplate.from_template(
            "Write a {content_type} about {topic}."
        )
        
        # Reflection prompt
        reflect_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a critical reviewer.
Evaluate the following content for quality, accuracy, and completeness.
Provide specific feedback for improvement."""),
            HumanMessage(content="Content to review: {content}")
        ])
        
        # Note: Full implementation would use LangGraph for state management
        # This is a conceptual demonstration
        return {
            "generate": gen_prompt | self.llm | StrOutputParser(),
            "reflect": reflect_prompt | self.llm | StrOutputParser()
        }
    
    def generate(self, content_type: str, topic: str) -> str:
        """Generate initial content."""
        return self.chain["generate"].invoke({
            "content_type": content_type,
            "topic": topic
        })
    
    def reflect(self, content: str) -> str:
        """Reflect on generated content."""
        return self.chain["reflect"].invoke({"content": content})


# --- Google ADK Style Implementation ---
class ADKStyleReflectionAgent:
    """
    Conceptual implementation showing Google ADK reflection structure.
    
    In Google ADK, you would use SequentialAgent:
    
    from google.adk.agents import SequentialAgent, LlmAgent
    
    generator = LlmAgent(
        name="Generator",
        model="gemini-2.0-flash",
        instruction="Write content based on the task.",
        output_key="draft"
    )
    
    reviewer = LlmAgent(
        name="Reviewer", 
        model="gemini-2.0-flash",
        instruction="Review the draft in state['draft'] and provide feedback.",
        output_key="review"
    )
    
    reflection_pipeline = SequentialAgent(
        name="ReflectionPipeline",
        sub_agents=[generator, reviewer]
    )
    """
    
    def __init__(self, model_id: str = None):
        logger.info("ADK-style Reflection conceptual implementation")
        logger.info("Use google.adk.agents.SequentialAgent for generator-reviewer flow")
        self.model_id = model_id
    
    def get_structure_example(self) -> Dict[str, Any]:
        return {
            "generator": {
                "type": "LlmAgent",
                "output_key": "draft",
                "instruction": "Generate initial content"
            },
            "reviewer": {
                "type": "LlmAgent", 
                "input_key": "draft",
                "output_key": "review",
                "instruction": "Review and critique the draft"
            },
            "pipeline": {
                "type": "SequentialAgent",
                "sub_agents": ["generator", "reviewer"]
            }
        }


if __name__ == "__main__":
    print("=" * 60)
    print("Reflection Pattern Demo")
    print("=" * 60)
    
    # Demo (requires LLM)
    agent = ReflectionAgent()
    
    test_task = "Write a Python function to calculate factorial with error handling."
    
    print(f"\nTask: {test_task}")
    print("\nNote: Requires LLM backend running for actual execution")
    print("\n--- Structure Example ---")
    
    adk = ADKStyleReflectionAgent()
    import json
    print(json.dumps(adk.get_structure_example(), indent=2))
