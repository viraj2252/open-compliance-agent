from pydantic import BaseModel, Field
from typing import Literal

class ComplianceSOP(BaseModel):
    """
    Standard Operating Procedures for the Compliance Assistant.
    This acts as the dynamic configuration (genome) for the entire RAG workflow.
    """
    
    # SYSTEM PROMPTS
    planner_prompt: str = Field(
        description="The system prompt for the Planner Agent."
    )
    synthesizer_prompt: str = Field(
        description="The system prompt for the Synthesizer Agent."
    )
    
    # RETRIEVAL STRATEGY
    researcher_retriever_k: int = Field(
        description="Number of documents for the Policy Researcher to retrieve.", 
        default=3
    )
    
    # STRATEGY SWITCHES
    conflict_check_enabled: bool = Field(
        description="Whether to use the Conflict Detector agent.", 
        default=True
    )
    
    # MODEL SELECTION (Evolvable)
    # We allow the Director to switch between models for synthesis if needed.
    # Currently only qwen2.5 is configured, but we can add more compliant models.
    synthesizer_model: Literal["qwen2.5"] = Field(
        description="The LLM to use for the Synthesizer.", 
        default="qwen2.5"
    )
