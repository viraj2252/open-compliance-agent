from compliance_rag.graph.workflow import create_compliance_graph
from compliance_rag.core.defaults import get_baseline_sop

def run_test_query(query: str):
    """Runs a single query through the compliance assistant."""
    print(f"\n--- TESTING QUERY: '{query}' ---")
    
    app = create_compliance_graph()
    
    # Initialize state
    initial_state = {
        "initial_request": query,
        "plan": None,
        "agent_outputs": [],
        "final_response": None,
        "sop": get_baseline_sop()
    }
    
    # Run graph
    for event in app.stream(initial_state):
        for node_name, output in event.items():
            print(f"\n[NODE: {node_name}]")
            # Clear output for readability
            if 'agent_outputs' in output:
                 last_output = output['agent_outputs'][-1]
                 print(f"Agent {last_output.agent_name} generated findings.")
            elif 'plan' in output:
                 print(f"Planner generated {len(output['plan'].get('tasks', []))} tasks.")
            elif 'final_response' in output:
                 print(f"SYNTHESIZED RESPONSE:\n{output['final_response']}")

if __name__ == "__main__":
    # Test 1: Content Research
    run_test_query("What are the rules for using ChatGPT at work?")
    
    # Test 2: Metadata Lookup
    run_test_query("Who is the owner of the Remote Work Policy and when was it last updated?")
