"""
FastAPI Production API for the Self-Improving Compliance Assistant.
Provides REST endpoints for querying, evaluation, and evolution.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from compliance_rag.graph.workflow import create_compliance_graph
from compliance_rag.core.gene_pool import SOPGenePool
from compliance_rag.evaluation.judge import evaluate_run
from compliance_rag.agents.evolution import diagnose_failure, evolve_sop
from compliance_rag.utils.logger import setup_logger

# Setup logging
setup_logger("compliance_rag", level="INFO")
logger = logging.getLogger("compliance_rag.api")

# Initialize FastAPI
app = FastAPI(
    title="Compliance RAG API",
    description="Self-Improving Agentic RAG for Corporate Compliance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gene Pool on startup
gene_pool = SOPGenePool()


# ── Request / Response Models ──────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., description="The compliance question to ask")
    sop_version: Optional[str] = Field(None, description="Specific SOP version to use (e.g. 'v0'). Defaults to latest.")

class QueryResponse(BaseModel):
    answer: str
    sop_version: str
    agent_outputs: list
    timestamp: str

class EvalRequest(BaseModel):
    question: str
    response: str
    context: str

class EvalResponse(BaseModel):
    accuracy: int
    citations: int
    completeness: int
    tone: int
    details: dict

class EvolutionResponse(BaseModel):
    old_version: str
    new_version: str
    diagnosis: str
    scores: dict

class HealthResponse(BaseModel):
    status: str
    sop_version: str
    total_generations: int
    timestamp: str


# ── Endpoints ──────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    return HealthResponse(
        status="healthy",
        sop_version=gene_pool.get_latest_version_id(),
        total_generations=len(gene_pool.sops),
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/query", response_model=QueryResponse, tags=["Core"])
async def query_compliance(req: QueryRequest):
    """
    Ask a compliance question. Uses the latest evolved SOP by default.
    """
    logger.info(f"Query received: {req.question}")
    
    # Load SOP
    if req.sop_version:
        sop = gene_pool.get_sop(req.sop_version)
        if not sop:
            raise HTTPException(status_code=404, detail=f"SOP version '{req.sop_version}' not found.")
        version_id = req.sop_version
    else:
        sop = gene_pool.get_latest_sop()
        version_id = gene_pool.get_latest_version_id()
    
    # Run the agent network
    try:
        graph = create_compliance_graph()
        initial_state = {
            "initial_request": req.question,
            "plan": None,
            "agent_outputs": [],
            "final_response": None,
            "sop": sop
        }
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"Agent network failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
    
    agent_outputs = [
        {"agent": o.agent_name, "findings": str(o.findings)[:500]}
        for o in final_state["agent_outputs"]
    ]
    
    return QueryResponse(
        answer=final_state["final_response"],
        sop_version=version_id,
        agent_outputs=agent_outputs,
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/evaluate", response_model=EvalResponse, tags=["Evaluation"])
async def evaluate_response(req: EvalRequest):
    """
    Evaluate a compliance response using the LLM Judge.
    """
    logger.info(f"Evaluation requested for: {req.question[:50]}...")
    
    try:
        result = evaluate_run(req.question, req.response, req.context)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
    
    return EvalResponse(
        accuracy=result.accuracy.score,
        citations=result.citation_fidelity.score,
        completeness=result.completeness.score,
        tone=result.regulatory_compliance.score,
        details={
            "accuracy_reasoning": result.accuracy.reasoning,
            "citation_reasoning": result.citation_fidelity.reasoning,
            "completeness_reasoning": result.completeness.reasoning,
            "tone_reasoning": result.regulatory_compliance.reasoning
        }
    )


@app.post("/evolve", response_model=EvolutionResponse, tags=["Evolution"])
async def trigger_evolution(req: QueryRequest):
    """
    Run one cycle of the evolution loop:
    Query -> Evaluate -> Diagnose -> Evolve -> Save
    """
    logger.info(f"Evolution triggered for: {req.question}")
    
    sop = gene_pool.get_latest_sop()
    old_version = gene_pool.get_latest_version_id()
    
    # 1. Run Agent
    try:
        graph = create_compliance_graph()
        initial_state = {
            "initial_request": req.question,
            "plan": None,
            "agent_outputs": [],
            "final_response": None,
            "sop": sop
        }
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
    
    response = final_state["final_response"]
    context = "\n".join([o.findings for o in final_state["agent_outputs"]])
    
    # 2. Evaluate
    eval_result = evaluate_run(req.question, response, context)
    
    scores = {
        "accuracy": eval_result.accuracy.score,
        "citations": eval_result.citation_fidelity.score,
        "completeness": eval_result.completeness.score,
        "tone": eval_result.regulatory_compliance.score
    }
    
    # 3. Diagnose
    diagnosis = diagnose_failure(req.question, response, eval_result)
    
    # 4. Evolve
    new_sop = evolve_sop(sop, diagnosis)
    
    # 5. Save
    import re
    match = re.search(r"v(\d+)", old_version)
    next_num = int(match.group(1)) + 1 if match else 1
    new_version = f"v{next_num}"
    
    gene_pool.add_sop(new_version, new_sop)
    
    return EvolutionResponse(
        old_version=old_version,
        new_version=new_version,
        diagnosis=diagnosis[:500],
        scores=scores
    )


@app.get("/sop/versions", tags=["SOP Management"])
async def list_sop_versions():
    """List all available SOP versions."""
    versions = sorted(
        gene_pool.sops.keys(),
        key=lambda x: int(x[1:]) if x.startswith("v") and x[1:].isdigit() else 0
    )
    return {
        "versions": versions,
        "latest": gene_pool.get_latest_version_id(),
        "total": len(versions)
    }


@app.get("/sop/{version}", tags=["SOP Management"])
async def get_sop_detail(version: str):
    """Get the details of a specific SOP version."""
    sop = gene_pool.get_sop(version)
    if not sop:
        raise HTTPException(status_code=404, detail=f"SOP version '{version}' not found.")
    
    if hasattr(sop, "model_dump"):
        return {"version": version, "sop": sop.model_dump()}
    return {"version": version, "sop": sop.dict()}
