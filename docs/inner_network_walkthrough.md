# Walkthrough: Building the Inner Compliance Network

This document details **Phase 2** of our project: the **Inner Compliance Agent Network**.
In the reference tutorial, this is called the "Inner Trial Design Network".

## 1. The Concept

We are building a "Guild" of specialized AI agents that work together to answer a compliance question. Instead of one big LLM trying to do everything, we split the job:

* **Planner:** The Manager (Decides what to do).
* **Researcher:** The Librarian (Finds text).
* **SQL Analyst:** The Data Scientist (Finds facts/stats).
* **Synthesizer:** The Writer (Compiles the report).

## 2. The Shared State (`compliance_rag/core/state.py`)

Just like a real team needs a shared whiteboard, our agents share a `ComplianceState`.
Every agent receives this state, reads from it, and writes their output to it.

```python
class ComplianceState(TypedDict):
    initial_request: str           # The user's original question
    plan: Optional[Dict[str, Any]] # The plan created by the Planner
    agent_outputs: List[AgentOutput] # A list of findings from Researcher/SQL Analyst
    final_response: Optional[str]  # The final answer written by the Synthesizer
    sop: ComplianceSOP             # The "instructions" (Genome) for this run
```

## 3. The "Genome" (`compliance_rag/core/sop.py`)

The **SOP (Standard Operating Procedure)** contains the prompts and settings that control the agents.

* **Why is this important?** In Phase 4 (Self-Improvement), we won't change the *code* of the agents; we will only change this *SOP*. By rewriting the prompts in the SOP, the system evolves.

```python
class ComplianceSOP(BaseModel):
    planner_prompt: str      # System instruction for the Planner
    synthesizer_prompt: str  # System instruction for the Synthesizer
    researcher_retriever_k: int # How many docs to read
```

## 4. The Specialist Agents (`compliance_rag/agents/specialists.py`)

### A. The Planner Agent

* **Model:** `llama3.1:8b-instruct` (Good at following complex instructions).
* **Input:** User Request + `planner_prompt`.
* **Output:** A JSON plan listing specific tasks for other agents.
* **Logic:**

    ```python
    # Example Output
    {
        "tasks": [
            {"agent": "researcher", "query": "AI usage policy company devices"},
            {"agent": "sql_analyst", "query": "SELECT owner FROM policies WHERE title='AI Usage From'"}
        ]
    }
    ```

### B. The Researcher Agent

* **Tool:** `policy_search_tool` (Vector Search).
* **Logic:** content search. It takes the queries from the Planner and searches the FAISS database.
* **Output:** "I found this text in 'ai_usage_policy.md': ..."

### C. The SQL Analyst Agent

* **Model:** `qwen2.5:7b` (Good at coding/SQL).
* **Tool:** `policy_metadata_tool` (DuckDB).
* **Logic:** It translates English questions ("Who owns the policy?") into SQL (`SELECT owner FROM...`) and runs them.
* **Output:** "The owner is Sarah Chen."

### D. The Synthesizer Agent

* **Model:** `qwen2.5:7b` (Good at professional writing).
* **Input:** The User Request + All Findings from Researcher/Analyst.
* **Logic:** it combines the facts into a coherent answer with citations.

## 5. The Workflow Graph (`compliance_rag/graph/workflow.py`)

We use **LangGraph** to wire these agents together.
Currently, we use a simple **Sequential flow**:

`Start` -> `Planner` -> `Researcher` -> `SQL Analyst` -> `Synthesizer` -> `End`

In the future, we can make this parallel (Researcher and Analyst running at the same time).

## 6. How to Run It

We created a test script `compliance_rag/test_run.py`.

**To run the network:**

```bash
docker compose exec app python -m compliance_rag.test_run
```

This will:

1. Initialize the State with a sample question.
2. Pass it to the Planner.
3. Execute the plan.
4. Print the final Synthesized answer.
