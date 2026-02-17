import json
import logging
from langchain_core.messages import HumanMessage
from compliance_rag.config import llm_config
from compliance_rag.core.sop import ComplianceSOP
from compliance_rag.evaluation.models import EvaluationResult
from compliance_rag.utils.json_parser import parse_llm_json

logger = logging.getLogger("compliance_rag.evolution")


def diagnose_failure(request: str, response: str, evaluation: EvaluationResult) -> str:
    """
    The Performance Diagnostician Agent.
    Analyzes a failed run and explains WHY it failed based on the evaluation scores.
    """
    director = llm_config["director"]
    
    # Identify which dimensions failed (score < 4)
    failures = []
    if evaluation.accuracy.score < 4:
        failures.append(f"Accuracy ({evaluation.accuracy.score}/5): {evaluation.accuracy.reasoning}")
    if evaluation.citation_fidelity.score < 4:
        failures.append(f"Citations ({evaluation.citation_fidelity.score}/5): {evaluation.citation_fidelity.reasoning}")
    if evaluation.completeness.score < 4:
        failures.append(f"Completeness ({evaluation.completeness.score}/5): {evaluation.completeness.reasoning}")
    if evaluation.regulatory_compliance.score < 4:
        failures.append(f"Tone ({evaluation.regulatory_compliance.score}/5): {evaluation.regulatory_compliance.reasoning}")
        
    failure_text = "\n".join(failures)
    
    prompt = f"""
    You are a Senior Compliance Auditor and System Diagnostician.
    A junior AI assistant failed to answer a compliance question correctly.
    
    User Request: {request}
    Assistant Response: {response}
    
    Auditor's Feedback:
    {failure_text}
    
    Diagnose the root cause. Was it:
    1. A failure to Retrieve the right policy? (Search Gap)
    2. A failure to Plan the right steps? (Planner Gap)
    3. A failure to Synthesize the answer correctly? (Writer Gap)
    
    Provide a concise diagnosis (max 2 sentences) explaining exactly what instruction was missing or misinterpreted.
    """
    
    try:
        diagnosis = director.invoke([HumanMessage(content=prompt)]).content
        logger.info(f"Diagnosis complete: {diagnosis[:100]}...")
        return diagnosis
    except Exception as e:
        logger.error(f"Diagnosis failed: {e}")
        return f"Diagnosis unavailable due to error: {str(e)}"


def evolve_sop(current_sop: ComplianceSOP, diagnosis: str) -> ComplianceSOP:
    """
    The SOP Architect Agent.
    Rewrites the SOP (System Prompts) to prevent the diagnosed failure in the future.
    """
    director = llm_config["director"]
    
    prompt = f"""
    You are the Architect of a Compliance AI System.
    The current system failed a recent test.
    
    Diagnosis of Failure:
    {diagnosis}
    
    Current Planner Prompt:
    "{current_sop.planner_prompt}"
    
    Current Synthesizer Prompt:
    "{current_sop.synthesizer_prompt}"
    
    Your Task:
    Rewrite ONE or BOTH of the prompts to fix this failure.
    - If the Planner missed a step, update the Planner Prompt.
    - If the Synthesizer missed a constraint, update the Synthesizer Prompt.
    - Keep the rest of the instructions.
    - Be specific and directive.
    
    Respond in JSON format with the new prompts:
    {{
        "planner_prompt": "...",
        "synthesizer_prompt": "..."
    }}
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = director.invoke([HumanMessage(content=prompt)])
            data = parse_llm_json(response.content)
            
            if not data:
                logger.warning(f"Evolution attempt {attempt + 1}/{max_retries}: Empty JSON response. Retrying...")
                continue
            
            new_sop = ComplianceSOP(
                planner_prompt=data.get("planner_prompt", current_sop.planner_prompt),
                synthesizer_prompt=data.get("synthesizer_prompt", current_sop.synthesizer_prompt),
                researcher_retriever_k=current_sop.researcher_retriever_k,
                conflict_check_enabled=current_sop.conflict_check_enabled,
                synthesizer_model=current_sop.synthesizer_model
            )
            logger.info("SOP evolution successful.")
            return new_sop
            
        except Exception as e:
            logger.warning(f"Evolution attempt {attempt + 1}/{max_retries} failed: {e}")
    
    logger.error(f"All {max_retries} evolution attempts failed. Returning current SOP unchanged.")
    return current_sop
