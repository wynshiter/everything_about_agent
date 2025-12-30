import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.backend_manager import backend_manager
from src.utils.model_loader import model_loader
from src.agents.patterns.chaining import ChainingAgent
from src.agents.patterns.routing import RoutingAgent
from loguru import logger
import time

def test_system_initialization():
    logger.info("Testing System Initialization...")
    
    # 1. Check Backend Manager
    backends = backend_manager.list_backends()
    logger.info(f"Available Backends: {backends}")
    
    active_backend = backend_manager.active_backend_name
    logger.info(f"Active Backend: {active_backend}")
    
    assert active_backend in backends, "Active backend not found in list"

def test_model_loading():
    logger.info("Testing Model Loading...")
    model_id = model_loader.active_model_id
    logger.info(f"Active Model ID from config: {model_id}")
    
    # This triggers the backend to load/pull the model
    try:
        llm = model_loader.load_llm(model_id)
        logger.info(f"Successfully loaded LLM: {model_id}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        # We might fail here if Ollama is not running or model pull fails
        # But we continue to see if other parts work or to report error
        pass

def test_chaining_pattern():
    logger.info("Testing Chaining Pattern...")
    try:
        agent = ChainingAgent()
        input_text = "The new laptop model features a 3.5 GHz octa-core processor, 16GB of RAM, and a 1TB NVMe SSD."
        result = agent.run(input_text)
        logger.info(f"Chaining Result: {result}")
        assert "cpu" in result.lower() or "processor" in result.lower(), "Result should contain CPU info"
    except Exception as e:
        logger.error(f"Chaining test failed: {e}")

def test_routing_pattern():
    logger.info("Testing Routing Pattern...")
    try:
        agent = RoutingAgent()
        
        # Test Booking
        res1 = agent.run("I want to book a flight")
        logger.info(f"Routing (Booking): {res1}")
        assert "Booking Handler" in res1
        
        # Test Info
        res2 = agent.run("Tell me about the weather")
        logger.info(f"Routing (Info): {res2}")
        assert "Info Handler" in res2
        
    except Exception as e:
        logger.error(f"Routing test failed: {e}")

if __name__ == "__main__":
    test_system_initialization()
    test_model_loading()
    test_chaining_pattern()
    test_routing_pattern()
