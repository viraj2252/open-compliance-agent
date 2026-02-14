import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from compliance_rag.config import llm_config
from compliance_rag.evaluation.models import GradedScore, EvaluationResult
from compliance_rag.evaluation.programmatic import verify_citations

def evaluate_run(request: str, response: str, context: str) -> EvaluationResult:
    """
    Evaluates a single run of the Compliance Assistant.
    Combines LLM-as-a-Judge with programmatic checks.
    """
    judge_llm = llm_config["director"]

    def get_score(dimension: str, prompt_logic: str) -> GradedScore:
        prompt = f"""
        You are an expert Corporate Compliance Auditor.
        Evaluate the following response based on the provided context and original request.
        
        Dimension: {dimension}
        Requirement: {prompt_logic}
        
        Original Request: {request}
        Context Provided: {context}
        Assistant Response: {response}
        
        Respond ONLY with a JSON object: {{"score": <1-5>, "reasoning": "..."}}
        """
        
        res = judge_llm.invoke([HumanMessage(content=prompt)])
        try:
            # Clean up potential markdown formatting in response
            content = res.content.strip().replace("```json", "").replace("```", "")
            data = json.loads(content)
            return GradedScore(**data)
        except Exception as e:
            return GradedScore(score=1, reasoning=f"Judge failed to produce valid JSON: {str(e)}")

    # 1. LLM Scores
    accuracy = get_score("Accuracy", "Does the response correctly address the user's scenario?")
    completeness = get_score("Completeness", "Did it miss any constraints from the context?")
    compliance = get_score("Regulatory Compliance", "Is the tone professional and appropriate?")
    
    # 2. Programmatic Citation Score
    citation_score_raw = verify_citations(response, context)
    # Map 0.0-1.0 to 1-5 scale for consistency
    citation_score = int(1 + (citation_score_raw * 4))
    
    citation_fidelity = GradedScore(
        score=citation_score,
        reasoning=f"Programmatic check found {citation_score_raw*100:.0f}% of citation fragments in context."
    )

    return EvaluationResult(
        accuracy=accuracy,
        citation_fidelity=citation_fidelity,
        completeness=completeness,
        regulatory_compliance=compliance
    )
