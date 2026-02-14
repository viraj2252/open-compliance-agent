import asyncio
from compliance_rag.graph.workflow import create_compliance_graph
from compliance_rag.core.gene_pool import SOPGenePool
from compliance_rag.evaluation.judge import evaluate_run
from compliance_rag.agents.evolution import diagnose_failure, evolve_sop

QUERY = "Can I use ChatGPT for personal work?"

async def run_loop():
    print("--- Starting Evolution Loop ---")
    
    # 1. Load the latest 'Gene' (SOP)
    gene_pool = SOPGenePool()
    current_sop = gene_pool.get_latest_sop()
    version_id = "v0" # improving detection logic later
    # find actual version key
    for k, v in gene_pool.sops.items():
        if v == current_sop:
            version_id = k
            break
            
    print(f"Loaded SOP Version: {version_id}")
    
    # Run loop
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n=== Evolution Cycle {iteration}/{max_iterations} (Current SOP: {version_id}) ===")
        
        # 2. Run the Agent Network
        print(f"Running Agent with Query: '{QUERY}'...")
        graph = create_compliance_graph()
        initial_state = {
            "initial_request": QUERY,
            "plan": None,
            "agent_outputs": [],
            "final_response": None,
            "sop": current_sop
        }
        
        final_state = await graph.ainvoke(initial_state)
        response = final_state["final_response"]
        context = "\n".join([o.findings for o in final_state["agent_outputs"]])
        
        print("-" * 50)
        print(f"Agent Response:\n{response}")
        print("-" * 50)
        
        # 3. Evaluate the Run (The Judge)
        print("Evaluating Performance...")
        eval_result = evaluate_run(QUERY, context, response)
        
        print("\n--- Evaluation Scores ---")
        print(f"Accuracy: {eval_result.accuracy.score}/5")
        print(f"Citations: {eval_result.citation_fidelity.score}/5")
        print(f"Completeness: {eval_result.completeness.score}/5")
        print(f"Tone: {eval_result.regulatory_compliance.score}/5")
        
        # 4. Evolution Logic
        # We target ALL scores >= 3.75
        threshold = 3.75
        if (eval_result.accuracy.score < threshold or 
            eval_result.citation_fidelity.score < threshold or
            eval_result.completeness.score < threshold or
            eval_result.regulatory_compliance.score < threshold):
            
            print(f"\n[!] Performance is Sub-Optimal (<{threshold}). Initiating Evolution Protocol...")
            
            # A. Diagnose
            diagnosis = diagnose_failure(QUERY, response, eval_result)
            print(f"\nDiagnosis:\n{diagnosis}")
            
            # B. Evolve
            print("\nEvolving SOP Prompts...")
            new_sop = evolve_sop(current_sop, diagnosis)
            
            # C. Save
            import re
            match = re.search(r"v(\d+)", version_id)
            if match:
                next_version_num = int(match.group(1)) + 1
                version_id = f"v{next_version_num}"
            else:
                version_id = "v1"
            
            gene_pool.add_sop(version_id, new_sop)
            current_sop = new_sop
            print(f"\n[+] Evolution Successful! Saved new genome as '{version_id}'. Looping again...")
            
        else:
            print(f"\n[=] Success! All scores >={threshold}. Stopping evolution.")
            break
            
    if iteration >= max_iterations:
        print("\n[!] Max iterations reached without meeting target. Stopping.")

if __name__ == "__main__":
    asyncio.run(run_loop())
