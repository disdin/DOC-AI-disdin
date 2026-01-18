# AI Document Intelligence System (Production-Grade RAG)

## Overview

This project is a **production-ready Retrieval-Augmented Generation (RAG) system** that allows users to upload documents and ask natural language questions grounded strictly in their content. The system is designed to minimize hallucinations, support multi-tenant usage, and run entirely on **free, open-source, local infrastructure**.

The focus is not just on making RAG work, but on **engineering correctness, explainability, and production tradeoffs**.

---

## Problem Statement

Large Language Models are powerful but unreliable when used without grounding — they hallucinate answers and cannot be trusted for document-based reasoning. Businesses need systems that:

* Answer questions **only from provided documents**
* Explain **where the answer came from**
* Work for **multiple users securely**
* Are cost-aware and deployable without vendor lock-in

This project solves that problem using a carefully designed RAG + agent architecture.

---

## High-Level Architecture

```
User
  ↓
FastAPI (JWT Auth)
  ↓
Query Agent (LangGraph)
  ↓
Retriever (FAISS + Filters)
  ↓
Relevant Chunks (MongoDB metadata)
  ↓
LLM (Ollama – Mistral)
  ↓
Answer + Source Citations
```

---

## Core Technologies

| Component           | Technology                    | Reasoning                                |
| ------------------- | ----------------------------- | ---------------------------------------- |
| Backend API         | FastAPI                       | Async, production-ready, Python-native   |
| Auth                | JWT                           | Stateless, simple multi-tenant isolation |
| Metadata Store      | MongoDB                       | Flexible schema for documents & chunks   |
| Vector Store        | FAISS                         | Fast local semantic search, zero cost    |
| Embeddings          | SentenceTransformers (MiniLM) | Open-source, efficient, high quality     |
| LLM                 | Ollama (Mistral)              | Local inference, no API cost             |
| Agent Orchestration | LangGraph                     | Controlled multi-step reasoning          |

---

## Key Features

### 1. Document Ingestion Pipeline

* Upload documents per user
* Text extraction and cleaning
* Overlapping chunking (500 chars, 50 overlap)
* One-time embedding generation
* FAISS vector storage + MongoDB metadata

This ensures efficient, repeatable retrieval without re-embedding.

---

### 2. Semantic Retrieval

* Query is embedded using the same model as documents
* FAISS performs similarity search (384-dim vectors)
* Relevance filtering using distance threshold
* User-level isolation enforced at retrieval

This avoids keyword dependency and retrieves based on meaning.

---

### 3. RAG Answer Generation

* Retrieved chunks are injected into a strict system prompt
* LLM is instructed to answer **only from context**
* Low-temperature generation for determinism

If insufficient context is found, the system explicitly refuses to answer.

---

### 4. LangGraph Agent Workflow

Instead of a linear pipeline, the system uses an agent graph:

```
retrieve → evaluate_context → generate_answer
```

The agent:

* Validates retrieval quality
* Prevents hallucination loops
* Allows future extension (clarification, retries, tools)

---

### 5. Hallucination Prevention

Multiple safeguards are used:

* Semantic relevance thresholds
* Context size limits
* Strict prompting rules
* Explicit fallback responses when confidence is low

This makes the system safer for real-world use.

---

### 6. Source Citations

Every answer is returned with structured source metadata:

* Document ID
* Chunk ID
* Similarity score

This improves trust, debuggability, and auditability.

---

## API Overview

* `POST /auth/login`
* `POST /documents/upload`
* `POST /query`
* `GET /health`

All endpoints are secured and scoped to the authenticated user.

---

## Design Tradeoffs

### Why FAISS over Managed Vector DBs?

FAISS offers excellent performance for local and small-to-medium scale systems without cost or vendor lock-in. For large-scale distributed workloads, managed services could be considered.

### Why Chunk Size = 500 / Overlap = 50?

This balances semantic completeness with retrieval precision. Overlap prevents boundary information loss while keeping embedding cost reasonable.

### Why Local LLMs?

Local inference avoids API cost, improves data privacy, and keeps development reproducible. The system is configurable to support cloud LLMs if required.

---

## Known Limitations

* FAISS index is in-memory and not distributed
* No OCR for scanned PDFs
* No query history or analytics UI

These are conscious tradeoffs for simplicity and cost control.

---

## Future Improvements

* Hybrid keyword + semantic retrieval
* Streaming responses
* Feedback-based retrieval re-ranking
* Horizontal scaling with distributed vector stores

---

## How to Run Locally

1. Start MongoDB
2. Start Ollama with a supported model
3. Install dependencies
4. Run FastAPI server

The system runs fully offline with no paid services.

---

## Why This Project Matters

This project demonstrates not just RAG usage, but **engineering judgment** around reliability, cost, explainability, and extensibility — the same concerns faced by real startups building AI-powered products.
