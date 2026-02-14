# File Manifest: Open Compliance Agent

This manifest lists all files created for the project and explains their purpose in the RAG pipeline.

## 1. Project Root (`/`)

* `Dockerfile`: Defines the Python 3.12 environment for our app.
* `docker-compose.yml`: Runs the app container and connects it to local volumes.
* `pyproject.toml`: The Poetry dependency file (manages Python packages).
* `.env`: Stores your API keys and configuration (Local LLM URL, LangSmith Key).

## 2. Core Logic (`compliance_rag/core/`)

* `sop.py`: Defines the **ComplianceSOP** (Standard Operating Procedure). This is the "genome" config that evolves.
* `state.py`: Defines the **ComplianceState**. This is the shared memory passed between agents.
* `defaults.py`: Stores the baseline (v0) prompts for the Planner and Synthesizer.
* `gene_pool.py`: **[Phase 4]** Persistent storage for the SOP history (versions v0, v1, v2...).

## 3. The Agents (`compliance_rag/agents/`)

* `specialists.py`: Contains the **Planner**, **Researcher**, **SQL Analyst**, and **Synthesizer** node functions. These are the "workers" in our LangGraph.
* `evolution.py`: **[Phase 4]** Contains the **Diagnostician** and **Architect** agents for the self-improvement loop.

## 4. Tools (`compliance_rag/tools/`)

* `retrieval.py`:
  * `policy_search_tool`: Uses FAISS to find text in policies.
  * `policy_metadata_tool`: Uses SQL to query the DuckDB metadata store.

## 5. Knowledge Management (`compliance_rag/`)

* `ingestion.py`: Reads PDFs/MDs from `./data`, chunks them, and builds the FAISS vector index.
* `metadata_db.py`: Creates/populates the DuckDB database with structured policy info.
* `validate_indexing.py`: A script to test if the search is working correctly.

## 6. Evaluation (`compliance_rag/evaluation/`)

* `judge.py`: The **LLM-as-a-Judge** logic using Llama 3.1 (Director role).
* `models.py`: Pydantic models for scores (`GradedScore`, `EvaluationResult`).
* `programmatic.py`: Code to verify citations exist in the text without an LLM.

## 7. Testing Scripts (`compliance_rag/`)

* `test_run.py`: Runs a full end-to-end question ("Can I use ChatGPT?").
* `test_evaluation.py`: Runs the Judge against a sample Q&A to see if it catches errors.

## 8. Data (`data/`)

* `vector_store/`: The folder where FAISS saves its index.
* `policy_metadata.db`: The DuckDB file.
* `*.md`: The raw policy documents.
