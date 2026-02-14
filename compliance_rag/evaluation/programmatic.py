import re
from typing import List

def verify_citations(response: str, context: str) -> float:
    """
    Programmatically verifies if citations in the response correspond to 
    text actually found in the context.
    Returns a score from 0.0 to 1.0.
    """
    # Simple heuristic: Look for [POL-XXX] or similar and check if 
    # the proceeding sentence fragments exist in context.
    
    # Extract sentences preceding a bracketed citation
    citations = re.findall(r"([^.]+)\[POL-\d+\]", response)
    
    if not citations:
        return 1.0 # No citations to verify (neutral)
        
    hits = 0
    for text in citations:
        # Clean up text and check if substring in context (loose match)
        clean_text = text.strip().lower()
        if clean_text in context.lower():
            hits += 1
            
    return hits / len(citations)
