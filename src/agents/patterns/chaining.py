from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src.utils.model_loader import model_loader
from loguru import logger

class ChainingAgent:
    """
    Implements the Prompt Chaining pattern.
    Based on Chapter 1: Prompt Chaining.
    Scenario: Extract technical specifications -> Transform to JSON.
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        # If model_id is None, load_llm uses active model. We can fetch it back from llm or query loader.
        # But for logging, let's get the effective ID.
        effective_id = model_id if model_id else model_loader.active_model_id
        self.chain = self._build_chain()
        logger.info(f"🔗 ChainingAgent initialized with model: {effective_id}")

    def _build_chain(self):
        # --- Prompt 1: Extract Information ---
        prompt_extract = ChatPromptTemplate.from_template(
            "Extract the technical specifications from the following text:\n\n{text_input}"
        )
        
        # --- Prompt 2: Transform to JSON ---
        prompt_transform = ChatPromptTemplate.from_template(
            "Transform the following specifications into a JSON object with 'cpu', 'memory', and 'storage' as keys:\n\n{specifications}"
        )
        
        # --- Build the Chain using LCEL ---
        extraction_chain = prompt_extract | self.llm | StrOutputParser()
        
        full_chain = (
            {"specifications": extraction_chain}
            | prompt_transform
            | self.llm
            | StrOutputParser()
        )
        
        return full_chain

    def run(self, text_input: str) -> str:
        logger.info(f"Running chain with input: {text_input[:50]}...")
        return self.chain.invoke({"text_input": text_input})

if __name__ == "__main__":
    # Test block
    agent = ChainingAgent()
    input_text = "The new laptop model features a 3.5 GHz octa-core processor, 16GB of RAM, and a 1TB NVMe SSD."
    result = agent.run(input_text)
    print("\n--- Final JSON Output ---")
    print(result)
