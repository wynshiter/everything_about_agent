from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch
from src.utils.model_loader import model_loader
from loguru import logger

class RoutingAgent:
    """
    Implements the Routing pattern.
    Based on Chapter 2: Routing.
    Scenario: Classify intent (booking vs info) and route to specific handler.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        effective_id = model_id if model_id else model_loader.active_model_id
        self.chain = self._build_chain()
        logger.info(f"🔀 RoutingAgent initialized with model: {effective_id}")

    def _booking_handler(self, request: str) -> str:
        return f"✈️ Booking Handler processed: '{request}'. Result: Simulated booking action."

    def _info_handler(self, request: str) -> str:
        return f"ℹ️ Info Handler processed: '{request}'. Result: Simulated info retrieval."

    def _unclear_handler(self, request: str) -> str:
        return f"❓ Unclear Handler: Could not determine intent for '{request}'."

    def _build_chain(self):
        # --- Router Prompt ---
        router_prompt = ChatPromptTemplate.from_template(
            """Analyze the user's request and determine which specialist handler should process it.
            - If the request is related to booking flights or hotels, output 'booker'.
            - For all other general information questions, output 'info'.
            
            Return ONLY the single word classification (booker or info).
            
            Request: {request}
            """
        )
        
        router_chain = router_prompt | self.llm | StrOutputParser()
        
        # --- Branching Logic ---
        branch = RunnableBranch(
            (lambda x: "booker" in x["topic"].lower(), lambda x: self._booking_handler(x["request"])),
            (lambda x: "info" in x["topic"].lower(), lambda x: self._info_handler(x["request"])),
            lambda x: self._unclear_handler(x["request"])
        )
        
        # --- Full Chain ---
        # We first run the router to get the topic, then pass both topic and original request to the branch
        full_chain = (
            {
                "topic": router_chain,
                "request": lambda x: x["request"]
            }
            | branch
        )
        
        return full_chain

    def run(self, request: str) -> str:
        logger.info(f"Routing request: {request}")
        return self.chain.invoke({"request": request})

if __name__ == "__main__":
    agent = RoutingAgent()
    
    reqs = [
        "I want to book a flight to Paris",
        "What is the capital of France?",
        "Hello there"
    ]
    
    for req in reqs:
        print(f"\nInput: {req}")
        print(f"Output: {agent.run(req)}")
