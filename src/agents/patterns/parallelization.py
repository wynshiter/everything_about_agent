"""
Parallelization Pattern Implementation
Chapter 3: Parallelization

This module demonstrates the Parallelization pattern for executing independent tasks concurrently.
It includes implementations for both LangChain LCEL and conceptual Google ADK approaches.
"""

import asyncio
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from src.utils.model_loader import model_loader
from loguru import logger


class ParallelizationAgent:
    """
    Implements the Parallelization pattern.
    Executes independent tasks concurrently to reduce overall latency.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        effective_id = model_id if model_id else model_loader.active_model_id
        self.chain = self._build_chain()
        logger.info(f"⚡ ParallelizationAgent initialized with model: {effective_id}")
    
    def _build_chain(self):
        """Build a parallel processing chain with three parallel branches."""
        
        # --- Branch 1: Summarizer ---
        summarize_prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize the following topic concisely in 2-3 sentences:"),
            ("user", "{topic}")
        ])
        summarize_chain = summarize_prompt | self.llm | StrOutputParser()
        
        # --- Branch 2: Question Generator ---
        questions_prompt = ChatPromptTemplate.from_messages([
            ("system", "Generate three interesting questions about the following topic:"),
            ("user", "{topic}")
        ])
        questions_chain = questions_prompt | self.llm | StrOutputParser()
        
        # --- Branch 3: Key Terms Extractor ---
        terms_prompt = ChatPromptTemplate.from_messages([
            ("system", "Identify 5-10 key terms from the topic, separated by commas:"),
            ("user", "{topic}")
        ])
        terms_chain = terms_prompt | self.llm | StrOutputParser()
        
        # --- Parallel Execution ---
        # RunnableParallel executes all branches concurrently
        map_chain = RunnableParallel(
            {
                "summary": summarize_chain,
                "questions": questions_chain,
                "key_terms": terms_chain,
                "original_topic": RunnablePassthrough()  # Pass through original input
            }
        )
        
        # --- Synthesis Step ---
        synthesis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Based on the following parallel analysis:
            
Summary: {summary}

Related Questions: {questions}

Key Terms: {key_terms}

Synthesize a comprehensive response that incorporates all these elements."""),
            ("user", "Topic: {original_topic}")
        ])
        
        # --- Full Chain ---
        full_chain = map_chain | synthesis_prompt | self.llm | StrOutputParser()
        
        return full_chain
    
    def run(self, topic: str) -> str:
        """Execute the parallel chain with a given topic."""
        logger.info(f"⚡ Processing topic in parallel: {topic}")
        return self.chain.invoke(topic)


class ParallelizationWithMap:
    """
    Alternative implementation using map() for batch processing.
    Useful when you have multiple independent inputs to process.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        self.chain = self._build_chain()
    
    def _build_chain(self):
        prompt = ChatPromptTemplate.from_template(
            "Provide a brief analysis of: {item}"
        )
        return prompt | self.llm | StrOutputParser()
    
    def run_batch(self, items: List[str]) -> List[str]:
        """Process multiple items in parallel."""
        logger.info(f"⚡ Processing {len(items)} items in parallel")
        # Use ainvoke for async parallel execution
        return asyncio.run(self._run_batch_async(items))
    
    async def _run_batch_async(self, items: List[str]) -> List[str]:
        """Async helper for batch processing."""
        tasks = [self.chain.ainvoke(item) for item in items]
        results = await asyncio.gather(*tasks)
        return list(results)


# --- Google ADK Style Implementation (Conceptual) ---
# Note: This shows the conceptual structure for Google ADK ParallelAgent
# Actual ADK implementation requires google-adk package

class ADKStyleParallelAgent:
    """
    Conceptual implementation showing Google ADK ParallelAgent structure.
    
    In Google ADK, you would use:
    
    from google.adk.agents import ParallelAgent, LlmAgent
    
    researcher_1 = LlmAgent(
        name="Researcher1",
        model="gemini-2.0-flash",
        instruction="Research topic A",
        output_key="result_a"
    )
    
    researcher_2 = LlmAgent(
        name="Researcher2", 
        model="gemini-2.0-flash",
        instruction="Research topic B",
        output_key="result_b"
    )
    
    parallel_agent = ParallelAgent(
        name="ParallelResearch",
        sub_agents=[researcher_1, researcher_2]
    )
    
    merger_agent = LlmAgent(
        name="Merger",
        instruction="Synthesize {result_a} and {result_b}"
    )
    """
    
    def __init__(self, model_id: str = None):
        logger.info("📦 ADK-style ParallelAgent conceptual implementation")
        logger.info("   Use google.adk.agents.ParallelAgent for actual implementation")
        self.model_id = model_id
    
    def get_structure_example(self) -> Dict[str, Any]:
        """Returns the conceptual structure for ADK implementation."""
        return {
            "parallel_agent": {
                "type": "ParallelAgent",
                "sub_agents": [
                    {"name": "Researcher1", "output_key": "result_a"},
                    {"name": "Researcher2", "output_key": "result_b"},
                    {"name": "Researcher3", "output_key": "result_c"}
                ]
            },
            "merger_agent": {
                "type": "LlmAgent",
                "instruction": "Synthesize results: {result_a}, {result_b}, {result_c}"
            }
        }


if __name__ == "__main__":
    # Demo with mock data (no actual LLM call)
    print("=" * 60)
    print("Parallelization Pattern Demo")
    print("=" * 60)
    
    # This demonstrates the structure; actual execution requires LLM
    agent = ParallelizationAgent()
    
    # Test topics
    test_topics = [
        "The history of space exploration",
        "Artificial intelligence in healthcare"
    ]
    
    print("\n--- Parallel Processing Demo ---")
    for topic in test_topics:
        print(f"\n📌 Topic: {topic}")
        # Note: In production, uncomment the line below
        # result = agent.run(topic)
        # print(f"Result: {result}")
        print("(Requires LLM to be running for actual execution)")
    
    # Show ADK structure
    print("\n--- ADK Structure Example ---")
    adk_agent = ADKStyleParallelAgent()
    import json
    print(json.dumps(adk_agent.get_structure_example(), indent=2))
