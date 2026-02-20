"""
Multi-Agent Collaboration Pattern Implementation
Chapter 7: Multi-Agent Collaboration

This module demonstrates the Multi-Agent Collaboration pattern.
"""

from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.utils.model_loader import model_loader
from loguru import logger


class MultiAgentCollaboration:
    """
    Implements Multi-Agent Collaboration.
    Multiple agents work together to solve complex tasks.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        self.agents = {}
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"MultiAgentCollaboration initialized with model: {effective_id}")
    
    def add_agent(self, name: str, role: str, goal: str):
        """Add a specialized agent to the collaboration."""
        self.agents[name] = {
            "role": role,
            "goal": goal,
            "llm": self.llm
        }
        logger.info(f"Added agent: {name} with role: {role}")
    
    def run_sequential(self, task: str) -> str:
        """Execute task through sequential agent handoffs."""
        context = task
        
        for name, agent_info in self.agents.items():
            prompt = ChatPromptTemplate.from_template(
                "Role: {role}\nGoal: {goal}\n\nContext: {context}\n\nYour task:"
            )
            
            chain = prompt | agent_info["llm"] | StrOutputParser()
            context = chain.invoke({
                "role": agent_info["role"],
                "goal": agent_info["goal"],
                "context": context
            })
            
            logger.info(f"Agent {name} processed task")
        
        return context
    
    def run_parallel(self, task: str) -> Dict[str, str]:
        """Execute task in parallel with multiple agents."""
        results = {}
        
        for name, agent_info in self.agents.items():
            prompt = ChatPromptTemplate.from_template(
                "Role: {role}\nGoal: {goal}\n\nTask: {task}\n\nYour contribution:"
            )
            
            chain = prompt | agent_info["llm"] | StrOutputParser()
            results[name] = chain.invoke({
                "role": agent_info["role"],
                "goal": agent_info["goal"],
                "task": task
            })
        
        return results
    
    def run_hierarchical(self, task: str) -> str:
        """Execute task with supervisor-worker hierarchy."""
        # Supervisor creates plan
        supervisor_prompt = "Analyze this task and delegate to specialists: {task}"
        # Worker executes
        # This is conceptual
        return f"Hierarchical execution for: {task}"


class CrewAIStyleAgent:
    """
    Conceptual CrewAI-style implementation.
    
    from crewai import Agent, Task, Crew
    
    researcher = Agent(role='Researcher', goal='Research topic')
    writer = Agent(role='Writer', goal='Write content')
    
    research_task = Task(description='Research AI', agent=researcher)
    write_task = Task(description='Write article', agent=writer, context=[research_task])
    
    crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])
    result = crew.kickoff()
    """
    
    def get_structure_example(self) -> Dict[str, Any]:
        return {
            "agents": [
                {"role": "Researcher", "goal": "Find information"},
                {"role": "Writer", "goal": "Create content"},
                {"role": "Editor", "goal": "Review and refine"}
            ],
            "process": "sequential | parallel | hierarchical"
        }


# --- Google ADK Style ---
class ADKStyleMultiAgent:
    """
    Conceptual Google ADK multi-agent implementation.
    
    from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent
    
    researcher1 = LlmAgent(name="Researcher1", output_key="result1")
    researcher2 = LlmAgent(name="Researcher2", output_key="result2")
    
    parallel = ParallelAgent(sub_agents=[researcher1, researcher2])
    merger = LlmAgent(name="Merger", instruction="Combine {result1} and {result2}")
    
    pipeline = SequentialAgent(sub_agents=[parallel, merger])
    """
    
    def get_structure_example(self) -> Dict[str, Any]:
        return {
            "structures": [
                "SequentialAgent: Sequential handoffs",
                "ParallelAgent: Parallel execution",
                "Hierarchical: Supervisor-worker"
            ],
            "communication": "Shared state via output_key"
        }


if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Agent Collaboration Demo")
    print("=" * 60)
    
    collab = MultiAgentCollaboration()
    collab.add_agent("researcher", "Research Analyst", "Find and summarize information")
    collab.add_agent("writer", "Content Writer", "Create engaging content")
    
    print("\nAdded agents: researcher, writer")
    print("Ready for collaboration (requires LLM)")
