"""
Tool Use Pattern Implementation
Chapter 5: Tool Use (Function Calling)

This module demonstrates the Tool Use pattern for enabling agents to interact with external systems.
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from src.utils.model_loader import model_loader
from loguru import logger


# --- Tool Definitions ---

@tool
def search_information(query: str) -> str:
    """
    Provides factual information on a given topic.
    Use this tool to find answers to factual questions.
    
    Args:
        query: The search query
        
    Returns:
        Factual information about the query
    """
    logger.info(f"Tool called: search_information with query: {query}")
    
    simulated_results = {
        "weather in london": "The weather in London is currently cloudy with a temperature of 15°C.",
        "capital of france": "The capital of France is Paris.",
        "population of earth": "The estimated population of Earth is around 8 billion people.",
        "tallest mountain": "Mount Everest is the tallest mountain above sea level.",
    }
    
    result = simulated_results.get(query.lower(), f"No specific information found for: {query}")
    return result


@tool
def calculate(expression: str) -> str:
    """
    Performs mathematical calculations.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Calculation result
    """
    logger.info(f"Tool called: calculate with expression: {expression}")
    
    try:
        # WARNING: eval is dangerous, use with caution!
        # In production, use a safe math parser
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_stock_price(ticker: str) -> float:
    """
    Fetches simulated stock price for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, GOOGL)
        
    Returns:
        Stock price as float
        
    Raises:
        ValueError: If ticker not found
    """
    logger.info(f"Tool called: get_stock_price for {ticker}")
    
    simulated_prices = {
        "AAPL": 178.15,
        "GOOGL": 1750.30,
        "MSFT": 425.50,
        "AMZN": 178.25,
    }
    
    price = simulated_prices.get(ticker.upper())
    if price is not None:
        return price
    else:
        raise ValueError(f"Ticker '{ticker}' not found")


class ToolUseAgent:
    """
    Implements the Tool Use pattern.
    Enables the agent to call external functions to fulfill user requests.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        self.tools = [search_information, calculate, get_stock_price]
        self.agent = self._build_agent()
        effective_id = model_id if model_id else model_loader.active_model_id
        logger.info(f"ToolUseAgent initialized with model: {effective_id}")
    
    def _build_agent(self):
        """Build the tool-calling agent."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant with access to tools."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def run(self, query: str) -> str:
        """
        Execute the agent with a query.
        
        Args:
            query: User query
            
        Returns:
            Agent response
        """
        logger.info(f"Executing query: {query}")
        result = self.agent.invoke({"input": query})
        return result["output"]


class SimpleToolChain:
    """
    Simple tool chain without full agent framework.
    Useful for straightforward tool usage.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        self.tools = [search_information, calculate]
        self._bind_tools()
    
    def _bind_tools(self):
        """Bind tools to the LLM."""
        self.llm = self.llm.bind_tools(self.tools)
    
    def run(self, query: str) -> str:
        """Execute a simple tool call."""
        logger.info(f"Running tool chain for: {query}")
        
        # Get LLM response with tool calls
        response = self.llm.invoke(query)
        
        # Check if LLM wants to call a tool
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                logger.info(f"LLM requested tool: {tool_name}")
                
                # Find and execute the tool
                for tool in self.tools:
                    if tool.name == tool_name:
                        result = tool.invoke(tool_args)
                        logger.info(f"Tool result: {result}")
                        return f"Tool {tool_name} returned: {result}"
        
        return response.content


# --- Google ADK Style Implementation ---
class ADKStyleToolAgent:
    """
    Conceptual implementation showing Google ADK tool usage.
    
    from google.adk.agents import LlmAgent
    from google.adk.tools import google_search
    
    tool_agent = LlmAgent(
        name="SearchAgent",
        model="gemini-2.0-flash",
        instruction="Answer questions using provided tools.",
        tools=[google_search, calculate]
    )
    """
    
    def __init__(self):
        logger.info("ADK-style Tool Agent conceptual implementation")
    
    def get_structure_example(self) -> Dict[str, Any]:
        return {
            "agent": {
                "type": "LlmAgent",
                "tools": ["google_search", "code_execution", "vertex_search"]
            },
            "common_tools": {
                "google_search": "Search the web for information",
                "code_execution": "Execute Python code in sandbox",
                "vertex_search": "Search enterprise datastore"
            }
        }


if __name__ == "__main__":
    print("=" * 60)
    print("Tool Use Pattern Demo")
    print("=" * 60)
    
    # Show available tools
    print("\nAvailable tools:")
    print("- search_information(query: str) -> str")
    print("- calculate(expression: str) -> str")
    print("- get_stock_price(ticker: str) -> float")
    
    print("\nNote: Requires LLM backend running for actual execution")
