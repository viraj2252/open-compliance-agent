# Compliance Assistant Architecture - Phase 3

This document explains the system we have built so far. It combines an **Agentic RAG** (Retrieval-Augmented Generation) with a **Multi-Dimensional Evaluation System**.

## 1. The Knowledge Layer (Our Brain)

We have two ways of remembering information:

### A. The Vector Store (Unstructured)

* **What it is:** A FAISS database containing your policy documents (`.md` files).
* **How it works:** We chunk documents into small pieces, turn them into numbers (embeddings), and search for similar content when you ask a question.
* **Code:** `compliance_rag/ingestion.py` builds it; `compliance_rag/tools/retrieval.py` searches it.
* **Use Case:** Answering "What are the rules for..." or "How do I..." questions.

### B. The Metadata Store (Structured)

* **What it is:** A DuckDB SQL database containing specific facts about policies.
* **Schema for `policies` table:**
  * `policy_id`: e.g., POL-001
  * `owner`: e.g., Sarah Chen
  * `version`: e.g., 1.2
  * `last_updated`: e.g., 2024-01-15
* **Use Case:** Answering "Who owns..." or "When was..." questions.

## 2. The Inner Agent Network (The Team)

We use **LangGraph** to coordinate a team of specialized AI agents.

### The Planner (`planner_node`)

* **Role:** The Project Manager.
* **Job:** Breaks your question into tasks. Decides if we need to search text (Researcher) or query the database (SQL Analyst).
* **Model:** Llama 3.1 (8B)

### The Researcher (`researcher_node`)

* **Role:** The Librarian.
* **Job:** Uses the Vector Store to find relevant policy snippets.

### The SQL Analyst (`sql_analyst_node`)

* **Role:** The Data Analyst.
* **Job:** Writes and executes DuckDB SQL queries to find policy metadata.
* **Model:** Qwen 2.5 (7B)

### The Synthesizer (`synthesizer_node`)

* **Role:** The Writer.
* **Job:** Takes all findings and writes a professional, cited answer.
* **Model:** Qwen 2.5 (7B)

## 3. The Evaluation System (The Judge)

We built a system to check our own work before we deploy.

### The Judge (`compliance_rag/evaluation/judge.py`)

* **Role:** The Auditor.
* **Job:** Reads the User Request, the Context, and our Final Answer, then scores us on 4 dimensions:
    1. **Accuracy (1-5):** Did we answer correctly?
    2. **Citation Fidelity (1-5):** Did we hallucinate citations? (Checked programmatically)
    3. **Completeness (1-5):** Did we miss constraints?
    4. **Tone (1-5):** Is it professional?
* **Output:** A vector like `[2.0, 5.0, 2.0, 2.0, 1.0]` that tells us exactly where we failed.

## 4. How to Run It

We have created test scripts for each layer:

| Component | Command | What it Tests |
|-----------|---------|---------------|
| **Search** | `docker compose exec app python -m compliance_rag.validate_indexing` | Can we find docs? |
| **Agents** | `docker compose exec app python -m compliance_rag.test_run` | Can agents collaborate? |
| **Judge** | `docker compose exec app python -m compliance_rag.test_evaluation` | Can we score ourselves? |

## Next Steps: Self-Improvement

We are now ready for **Phase 4**. We will build the **Evolution Loop**:

1. **Diagnostician:** Analyzes *why* we got a low score (e.g., "Synthesizer missed the 'prohibited' clause").
2. **SOP Architect:** Rewrites our system prompts to fix the error.
3. **Gene Pool:** Saves the new, better prompts as `v2`.
