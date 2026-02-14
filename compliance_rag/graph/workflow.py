from langgraph.graph import StateGraph, START, END
from compliance_rag.core.state import ComplianceState
from compliance_rag.agents.specialists import (
    planner_node, 
    researcher_node, 
    sql_analyst_node, 
    synthesizer_node
)

def create_compliance_graph():
    """
    Builds the LangGraph workflow for the Compliance Assistant.
    """
    workflow = StateGraph(ComplianceState)
    
    # 1. Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("sql_analyst", sql_analyst_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    # 2. Define Edges
    # For the baseline, we use a simple linear progression.
    # We can evolve this into parallel execution or conditional routing later.
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "sql_analyst")
    workflow.add_edge("sql_analyst", "synthesizer")
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

# Example usage for testing
if __name__ == "__main__":
    from compliance_rag.core.defaults import get_baseline_sop
    
    graph = create_compliance_graph()
    
    # Dummy run
    initial_state = {
        "initial_request": "How long should I keep AI usage logs?",
        "plan": None,
        "agent_outputs": [],
        "final_response": None,
        "sop": get_baseline_sop()
    }
    
    # Note: This will require LLMs and vector store access to run
    # for output in graph.stream(initial_state):
    #     print(output)
