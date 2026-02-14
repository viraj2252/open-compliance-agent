import os
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

# Centralized LLM Foundry
# Based on the tutorial's `llm_config`
# Maps agent roles to specific specialized models for optimal performance

llm_config = {
    # Planner: Needs strong instruction following to break down complex compliance queries
    "planner": ChatOllama(
        model="llama3.1", 
        base_url=OLLAMA_BASE_URL,
        temperature=0.0, 
        format="json"
    ),

    # Synthesizer: Needs to write clear, professional, and well-cited answers
    "synthesizer": ChatOllama(
        model="qwen2.5", 
        base_url=OLLAMA_BASE_URL,
        temperature=0.2
    ),

    # SQL Analyst: Needs to generate valid SQL for structured metadata queries
    "sql_analyst": ChatOllama(
        model="qwen2.5", 
        base_url=OLLAMA_BASE_URL,
        temperature=0.0
    ),

    # Director: Switched to gpt-4o-mini (OpenAI) for superior reasoning
    # This model handles judging, diagnosis, and prompt evolution.
    "director": ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0.0
    ),

    # Embeddings: High-performance vector embeddings for retrieval
    "embedding_model": OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=OLLAMA_BASE_URL
    )
}

# Knowledge Store Paths
DATA_DIR = os.getenv("DATA_DIR", "./data")
VECTOR_STORE_PATH = os.path.join(DATA_DIR, "vector_store")
METADATA_DB_PATH = os.path.join(DATA_DIR, "policy_metadata.db")
