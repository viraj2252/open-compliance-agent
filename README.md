# Self-Improving Agentic RAG for Compliance 🧠

A production-grade, self-improving RAG system that uses a **Guild of Specialist Agents** to answer complex compliance questions. It features an autonomous **Evolution Loop** where a "Director" agent evaluates performance and rewrites the system's own prompts (SOPs) to fix failures in real-time.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)

---

## 🚀 Key Features

* **Self-Improving Architecture**: The system diagnoses its own failures (e.g., "Answer was vague") and rewrites its prompt instructions to fix them.
* **Agent Guild**:
  * **Planner**: Breaks down questions into research tasks.
  * **Researcher**: Performs semantic search on unstructured policy documents (PDF/MD).
  * **SQL Analyst**: Queries structured metadata (DuckDB) for policy owners, dates, and versions.
  * **Synthesizer**: Combines findings into a professional, cited response.
  * **Director (Judge/Architect)**: Evaluates quality and evolves the system.
* **Hybrid Intelligence**: Uses local LLMs (`Llama 3.1`, `Qwen 2.5`) for privacy-sensitive tasks and Cloud LLMs (`GPT-4o-mini`) for high-level reasoning and evaluation.
* **Production Ready**: Validated with a FastAPI backend, Docker containerization, structured logging, and health checks.

---

## 🛠️ Technology Stack

* **Orchestration**: LangGraph, LangChain
* **LLMs**: Ollama (Local), OpenAI (Cloud)
* **Database**: DuckDB (SQL), FAISS (Vector Store)
* **API**: FastAPI
* **Container**: Docker & Docker Compose

---

## ⚡️ Quick Start

### Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed.
* [Ollama](https://ollama.ai/) installed on your host machine.
* Pull the required local models:

    ```bash
    ollama pull llama3.1
    ollama pull qwen2.5
    ollama pull nomic-embed-text
    ```

### Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-repo/compliance-rag.git
    cd compliance-rag
    ```

2. **Configure Environment**:
    Create a `.env` file with your API keys:

    ```bash
    cp .env.example .env
    ```

    Edit `.env` and add your `OPENAI_API_KEY`.

3. **Build and Run**:

    ```bash
    docker compose up --build -d
    ```

4. **Verify Status**:
    Check the health endpoint:

    ```bash
    curl http://localhost:8000/health
    ```

    Output: `{"status": "healthy", "sop_version": "v1", ...}`

---

## 📖 Usage Guide

### 1. Ask a Question (RAG Query)

The system uses the latest evolved SOP to answer your question.

**Interactive UI:** Go to `http://localhost:8000/docs` and try the `/query` endpoint.

**Curl:**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Can I use ChatGPT for personal work?"}'
```

### 2. Trigger Self-Improvement (Evolution)

Force the system to run a diagnosis cycle. If the answer quality is below the threshold (3.75/5), it will evolve its prompt instructions.

```bash
curl -X POST http://localhost:8000/evolve \
  -H "Content-Type: application/json" \
  -d '{"question": "Can I use ChatGPT for personal work?"}'
```

### 3. View System "Genome" (SOP Versions)

See the history of prompt evolutions.

```bash
curl http://localhost:8000/sop/versions
```

---

## 🏗️ Architecture

### The "Inner" Agent Network

A graph of specialist agents working together:

1. **Planner**: Receives query -> Plans steps (Search vs SQL).
2. **Researcher**: Executes vector search on `data/vector_store`.
3. **SQL Analyst**: Executes SQL on `data/policy_metadata.db`.
4. **Synthesizer**: Aggregates findings and writes the final answer.

### The "Outer" Evolution Loop

An autonomous feedback loop for quality control:

1. **Run**: Execute the Inner Network.
2. **Evaluate**: The **Judge** (Director) scores the answer (Accuracy, Citations, Tone).
3. **Diagnose**: If scores are low, the Diagnostician identifies the root cause (e.g., "Planner missed searching for restrictions").
4. **Evolve**: The **Architect** rewrites the `planner_prompt` or `synthesizer_prompt`.
5. **Save**: The new SOP (Standard Operating Procedure) version is saved to the Gene Pool (`sop_gene_pool.json`).

---

## 📂 Project Structure

```
├── app.py                     # FastAPI Entrypoint
├── docker-compose.yml         # Container orchestration
├── compliance_rag/
│   ├── agents/
│   │   ├── specialists.py     # Planner, Researcher, SQL Analyst, Synthesizer
│   │   └── evolution.py       # Diagnostician, Architect
│   ├── core/
│   │   ├── gene_pool.py       # SOP Version Control
│   │   └── sop.py             # Pydantic models for Prompts
│   ├── evaluation/
│   │   └── judge.py           # LLM-as-a-Judge Logic
│   ├── graph/                 # LangGraph Workflow
│   └── utils/                 # Logger, JSON Parser
├── data/                      # Persistent storage (Vector DB, DuckDB, Gene Pool)
└── docs/                      # Detailed documentation
```

---

## 🛡️ License

MIT License. See `LICENSE` for details.
