# Secure-RAG

## Attack Simulation & Defense on Retrieval-Augmented Generation Systems

A security-focused Retrieval-Augmented Generation (RAG) research platform for studying, simulating, and defending against attacks on modern RAG systems.

**Team Members**

* Anshul Chandra (23CS3010)
* Dev Saha (23CS3022)

**Guide**

* Dr. Akash Yadav

---

## Project Overview

Secure-RAG aims to build an end-to-end RAG system from scratch and evaluate its security against various attack vectors including prompt injection, knowledge poisoning, context stuffing, and resource exhaustion attacks.

The project focuses on both retrieval quality and security robustness.

---

## Current Progress

### Phase 1: Foundation & Retrieval Layer ✅
* **Document Processing**: PDF loading, text extraction (PyPDF), word-based overlapping chunks.
* **Embedding Layer**: Sentence Transformers (`all-MiniLM-L6-v2`) embed generation.
* **Vector Database**: Persistent ChromaDB store & collection management.
* **Retrieval**: Semantic vector search, BM25 keyword search, Hybrid search (RRF), Top-K results.

### Phase 2: Advanced Retrieval ✅
* **Maximal Marginal Relevance (MMR)**: Diverse retrieval strategy to avoid redundancy.
* **Algorithm Comparison**: Baseline measurements across different indexing methods.

### Phase 3: LLM Integration ✅
* **Gemini LLM**: Integrated `gemini-2.5-flash` model for generating response answers.
* **Pipeline API**: Created FastAPI backend `/upload` and `/query` endpoints.
* **Web UI Dashboard**: Built React interface displaying document upload status, retrieval strategies, latency, and source chunks.

### Phase 4: Security Attacks (Attack Layer) ✅
* **Prompt Injection**: Automated injection payloads (`IGNORE ALL PREVIOUS INSTRUCTIONS...`) to override LLM behavior.
* **Knowledge Base Poisoning**: Injected false facts into ChromaDB and tracked retrieval poisoning ranks in Top-K.
* **API Simulation Endpoints**: Added `/api/attack` and `/api/cleanup` endpoints to execute attacks and clean databases synchronously.
* **Attack Simulation UI**: Integrated comparison dashboard with side-by-side Before/After cards, success/resisted status badges, and top-K poison gauges.
* **Dynamic Named Collections**: Added support for creating custom collection targets on PDF ingestion, switching collections dynamically from a global selector banner, viewing collection-specific chunk statistics, and deleting collections permanently.

---

## Current Architecture

GPT2.pdf
↓
Text Extraction
↓
Word Chunking + Overlap
↓
Embedding Generation
↓
Persistent ChromaDB
↓
BM25 Retrieval
↓
Vector Retrieval
↓
Hybrid Retrieval
↓
Top-K Results

---

## Project Structure

secure-rag/

backend/
frontend/
docs/

research/
├── retrieval/
│   ├── base.py
│   ├── bm25.py
│   ├── hybrid.py
│   ├── mmr.py
│   └── topk.py
├── attacks/
│   ├── __init__.py
│   ├── attack1_prompt_injection.py
│   └── attack2_kb_poisoning.py
├── defenses/
├── evaluation/
├── pdf_loader.py
├── chunker.py
├── embedder.py
├── vector_store.py
├── rag_pipeline.py
├── test_bm25.py
└── test_hybrid.py

---

## Upcoming Roadmap

### Phase 2: Advanced Retrieval

* MMR (Maximal Marginal Relevance)
* Retrieval Optimization
* Ranking Fusion
* Context Compression

### Phase 3: LLM Integration

* Gemini Integration
* End-to-End RAG Pipeline
* Query Answer Generation
* Context-Aware Prompting

### Phase 4: Security Attacks

* Prompt Injection Attacks
* Knowledge Base Poisoning
* Context Stuffing Attacks
* Resource Exhaustion Attacks

### Phase 5: Defense Mechanisms

* Prompt Sanitization
* Input Filtering
* Retrieval Validation
* Context Verification
* Poison Detection

### Phase 6: Evaluation

* Retrieval Metrics
* Security Metrics
* RAGAS Evaluation
* Comparative Benchmarking

---

## Current Status

## Current Status

Security Attacks Phase (Phase 4) Completed ✅

Next Phase: Defense Mechanisms (Phase 5) Starting 🚀
