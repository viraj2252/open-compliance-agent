"""
Self-Improvement Evolution Loop.
Runs the agent, evaluates performance, diagnoses failures, evolves prompts.
Autonomous loop until all scores >= threshold or max iterations reached.
"""
import re
import asyncio
import logging
from compliance_rag.graph.workflow import create_compliance_graph
from compliance_rag.core.gene_pool import SOPGenePool
from compliance_rag.evaluation.judge import evaluate_run
from compliance_rag.agents.evolution import diagnose_failure, evolve_sop
from compliance_rag.utils.logger import setup_logger

# Setup logging
setup_logger("compliance_rag", level="INFO")
logger = logging.getLogger("compliance_rag.evolution_loop")

QUERY = "Can I use ChatGPT for personal work?"
THRESHOLD = 3.75
MAX_ITERATIONS = 5


async def run_loop():
    logger.info("=" * 60)
    logger.info("Starting Evolution Loop")
    logger.info("=" * 60)
    
    # 1. Load the latest 'Gene' (SOP)
    gene_pool = SOPGenePool()
    current_sop = gene_pool.get_latest_sop()
    version_id = gene_pool.get_latest_version_id()
    
    logger.info(f"Loaded SOP Version: {version_id}")
    
    iteration = 0
    
    while iteration < MAX_ITERATIONS:
        iteration += 1
        logger.info(f"Evolution Cycle {iteration}/{MAX_ITERATIONS} (SOP: {version_id})")
        
        # 2. Run the Agent Network
        logger.info(f"Running Agent with Query: '{QUERY}'")
        graph = create_compliance_graph()
        initial_state = {
            "initial_request": QUERY,
            "plan": None,
            "agent_outputs": [],
            "final_response": None,
            "sop": current_sop
        }
        
        try:
            final_state = await graph.ainvoke(initial_state)
        except Exception as e:
            logger.error(f"Agent network failed: {e}")
            logger.info("Skipping to next iteration...")
            continue
            
        response = final_state["final_response"]
        context = "\n".join([o.findings for o in final_state["agent_outputs"]])
        
        logger.info("-" * 50)
        logger.info(f"Agent Response:\n{response}")
        logger.info("-" * 50)
        
        # 3. Evaluate the Run (The Judge)
        # FIXED: Correct argument order is (request, response, context)
        logger.info("Evaluating Performance...")
        try:
            eval_result = evaluate_run(QUERY, response, context)
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            continue
        
        scores = {
            "Accuracy": eval_result.accuracy.score,
            "Citations": eval_result.citation_fidelity.score,
            "Completeness": eval_result.completeness.score,
            "Tone": eval_result.regulatory_compliance.score
        }
        
        logger.info("--- Evaluation Scores ---")
        for dim, score in scores.items():
            logger.info(f"  {dim}: {score}/5")
        
        # 4. Evolution Logic
        all_pass = all(s >= THRESHOLD for s in scores.values())
        
        if all_pass:
            logger.info(f"SUCCESS! All scores >= {THRESHOLD}. Stopping evolution.")
            break
        
        logger.info(f"Sub-Optimal (< {THRESHOLD}). Initiating Evolution Protocol...")
        
        # A. Diagnose
        diagnosis = diagnose_failure(QUERY, response, eval_result)
        logger.info(f"Diagnosis: {diagnosis[:200]}")
        
        # B. Evolve
        logger.info("Evolving SOP Prompts...")
        new_sop = evolve_sop(current_sop, diagnosis)
        
        # C. Save
        match = re.search(r"v(\d+)", version_id)
        next_version_num = int(match.group(1)) + 1 if match else 1
        version_id = f"v{next_version_num}"
        
        gene_pool.add_sop(version_id, new_sop)
        current_sop = new_sop
        logger.info(f"Evolution Successful! Saved genome as '{version_id}'. Looping...")
            
    if iteration >= MAX_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached without meeting target.")
    
    logger.info("=" * 60)
    logger.info("Evolution Loop Complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_loop())
