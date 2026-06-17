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

#### Document Processing

* PDF Loading
* Text Extraction using PyPDF
* Word-Based Chunking
* Overlapping Chunk Strategy

#### Embedding Layer

* Sentence Transformers (all-MiniLM-L6-v2)
* Explicit Embedding Generation

#### Vector Database

* ChromaDB Integration
* Persistent ChromaDB Storage
* Collection Management

#### Retrieval Systems

* Semantic Retrieval (Vector Search)
* BM25 Keyword Retrieval
* Hybrid Retrieval (BM25 + Vector Search)
* Top-K Retrieval

#### Software Engineering

* Modular Retrieval Architecture
* Reusable Retrieval Components
* GitHub Collaboration Workflow

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
│ ├── base.py
│ ├── bm25.py
│ ├── hybrid.py
│ ├── mmr.py
│ └── topk.py
│
├── attacks/
├── defenses/
├── evaluation/
│
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

Retrieval Foundation Completed ✅

Security Research Phase Starting 🚀
