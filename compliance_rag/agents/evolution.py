import json
from langchain_core.messages import HumanMessage
from compliance_rag.config import llm_config
from compliance_rag.core.sop import ComplianceSOP
from compliance_rag.evaluation.models import EvaluationResult

def diagnose_failure(request: str, response: str, evaluation: EvaluationResult) -> str:
    """
    The Performance Diagnostician Agent.
    Analyzes a failed run and explains WHY it failed based on the evaluation scores.
    """
    director = llm_config["director"] # Uses Llama 3.1
    
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
    
    diagnosis = director.invoke([HumanMessage(content=prompt)]).content
    return diagnosis

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
    
    response = director.invoke([HumanMessage(content=prompt)])
    try:
        data = json.loads(response.content)
        
        # Return a new SOP object with the updated prompts
        # We keep other settings (k, models) the same for now
        return ComplianceSOP(
            planner_prompt=data.get("planner_prompt", current_sop.planner_prompt),
            synthesizer_prompt=data.get("synthesizer_prompt", current_sop.synthesizer_prompt),
            researcher_retriever_k=current_sop.researcher_retriever_k,
            conflict_check_enabled=current_sop.conflict_check_enabled,
            synthesizer_model=current_sop.synthesizer_model
        )
    except Exception as e:
        print(f"Error evolving SOP: {e}")
        return current_sop
