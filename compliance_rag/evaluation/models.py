from pydantic import BaseModel, Field
from typing import List, Dict

class GradedScore(BaseModel):
    """A single dimension score from a judge."""
    score: int = Field(description="Score from 1 to 5", ge=1, le=5)
    reasoning: str = Field(description="Justification for the score")

class EvaluationResult(BaseModel):
    """Aggregate evaluation of a compliance assistant run."""
    accuracy: GradedScore
    citation_fidelity: GradedScore
    completeness: GradedScore
    regulatory_compliance: GradedScore
    performance_score: float = Field(description="Normalized latency/cost score", default=1.0)
    
    def to_vector(self) -> List[float]:
        """Convert scores to a float vector for Pareto analysis."""
        return [
            float(self.accuracy.score),
            float(self.citation_fidelity.score),
            float(self.completeness.score),
            float(self.regulatory_compliance.score),
            self.performance_score
        ]
