import sys
import os

# Ensure src is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.utils.model_loader import model_loader
from loguru import logger

def practice_basic_chaining():
    """
    Practice 1: Basic Extraction Pipeline
    Scenario: Extract technical specifications -> Transform to JSON
    """
    logger.info("--- Practice 1: Basic Extraction Pipeline ---")
    
    # 1. Load the model
    llm = model_loader.load_llm()
    logger.info(f"Using model: {model_loader.active_model_id}")

    # 2. Define Prompts
    # Step 1: Extract raw info
    prompt_extract = ChatPromptTemplate.from_template(
        "Extract the technical specifications from the following text:\n\n{text_input}"
    )
    
    # Step 2: Format to JSON
    prompt_transform = ChatPromptTemplate.from_template(
        "Transform the following specifications into a JSON object with 'cpu', 'memory', and 'storage' as keys:\n\n{specifications}"
    )

    # 3. Build Chain using LCEL
    # chain 1: extract
    extraction_chain = prompt_extract | llm | StrOutputParser()
    
    # full chain: input -> extract -> transform -> output
    full_chain = (
        {"specifications": extraction_chain}
        | prompt_transform
        | llm
        | StrOutputParser()
    )

    # 4. Run
    input_text = "The new laptop model features a 3.5 GHz octa-core processor, 16GB of RAM, and a 1TB NVMe SSD."
    logger.info(f"Input Text: {input_text}")
    
    result = full_chain.invoke({"text_input": input_text})
    
    print("\n--- Final JSON Output ---")
    print(result)
    print("-------------------------\n")


def practice_creative_writing_pipeline():
    """
    Practice 2: Creative Writing Pipeline
    Scenario: Topic -> Title -> Outline -> Introduction
    Demonstrates sequential dependency where each step builds on the previous one.
    """
    logger.info("--- Practice 2: Creative Writing Pipeline ---")
    
    # 1. Load the model
    llm = model_loader.load_llm()

    # 2. Define Prompts
    # Step 1: Generate Title
    prompt_title = ChatPromptTemplate.from_template(
        "Generate a catchy blog post title about {topic}."
    )
    
    # Step 2: Generate Outline (takes title)
    prompt_outline = ChatPromptTemplate.from_template(
        "Write a brief 3-point outline for a blog post titled: '{title}'."
    )
    
    # Step 3: Write Intro (takes title and outline)
    prompt_intro = ChatPromptTemplate.from_template(
        "Write an engaging introduction paragraph for the blog post '{title}', following this outline:\n{outline}"
    )

    # 3. Build Chain
    # We will chain them manually to show the flow explicitly, 
    # but you can also use RunnablePassthrough for more complex chains.
    
    # Chain 1: Topic -> Title
    chain_title = prompt_title | llm | StrOutputParser()
    
    # Chain 2: Title -> Outline
    chain_outline = prompt_outline | llm | StrOutputParser()
    
    # Chain 3: Title + Outline -> Intro
    chain_intro = prompt_intro | llm | StrOutputParser()

    # 4. Run Pipeline
    topic = "The Future of AI Agents"
    logger.info(f"Topic: {topic}")

    # Step 1
    title = chain_title.invoke({"topic": topic})
    print(f"\n[Step 1] Generated Title:\n{title}")

    # Step 2
    outline = chain_outline.invoke({"title": title})
    print(f"\n[Step 2] Generated Outline:\n{outline}")

    # Step 3
    intro = chain_intro.invoke({"title": title, "outline": outline})
    print(f"\n[Step 3] Final Introduction:\n{intro}")
    print("-------------------------\n")

if __name__ == "__main__":
    print("==================================================")
    print("   Chapter 1: Prompt Chaining - Practice Code")
    print("==================================================")
    
    practice_basic_chaining()
    practice_creative_writing_pipeline()
