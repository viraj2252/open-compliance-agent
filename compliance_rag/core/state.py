from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel

from compliance_rag.core.sop import ComplianceSOP

class AgentOutput(BaseModel):
    """A structured finding from a specialist agent."""
    agent_name: str
    findings: Any

class ComplianceState(TypedDict):
    """
    The shared state of the Compliance Assistant's workflow.
    Passed between all nodes in the LangGraph.
    """
    initial_request: str           # The user's question
    plan: Optional[Dict[str, Any]] # The step-by-step plan from Planner
    agent_outputs: List[AgentOutput] # Collected findings
    final_response: Optional[str]  # The final answer
    sop: ComplianceSOP             # The active SOP for this run
