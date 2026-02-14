from compliance_rag.evaluation.judge import evaluate_run

def test_judge():
    print("--- Running Evaluation Judge Test ---")
    
    request = "Can I use ChatGPT for personal work?"
    context = "Policy POL-001: Employees may use approved AI tools for company work. Personal use of company devices for AI is prohibited."
    response = "Yes, you can use ChatGPT as long as it is for personal work on your own device. [POL-001]"
    
    # Note: This response is slightly 'wrong' according to policy (should mention prohibited on company devices)
    # The judge should catch this.
    
    result = evaluate_run(request, response, context)
    
    print(f"\nEvaluation Results for: '{request}'")
    print(f"Accuracy: {result.accuracy.score}/5 - {result.accuracy.reasoning}")
    print(f"Citations: {result.citation_fidelity.score}/5 - {result.citation_fidelity.reasoning}")
    print(f"Completeness: {result.completeness.score}/5 - {result.completeness.reasoning}")
    print(f"Tone: {result.regulatory_compliance.score}/5 - {result.regulatory_compliance.reasoning}")
    print(f"\nVector: {result.to_vector()}")

if __name__ == "__main__":
    test_judge()
