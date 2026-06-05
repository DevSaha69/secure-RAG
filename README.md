# Secure-RAG

Secure-RAG is a security-focused Retrieval-Augmented Generation (RAG) research platform designed to study, evaluate, and defend against attacks on modern RAG systems.

The project aims to simulate real-world attacks such as Prompt Injection, Knowledge Base Poisoning, Context Stuffing, and Resource Exhaustion while benchmarking different retrieval strategies and defense mechanisms.

---

## Project Objectives

* Build an end-to-end RAG pipeline from scratch
* Evaluate retrieval performance using multiple retrieval methods
* Simulate attacks on RAG systems
* Develop and benchmark defense strategies
* Analyze security implications of retrieval techniques
* Conduct research on secure and robust RAG architectures

---

## Current Progress

### Phase 1: Foundation Setup ✅

* Repository Setup
* Python Environment Setup
* GitHub Collaboration Setup

### Phase 2: Document Processing ✅

* PDF Loading
* Text Extraction using PyPDF
* Text Chunking

### Phase 3: Embeddings & Retrieval ✅

* Sentence Transformer Embeddings
* ChromaDB Integration
* Vector Storage
* Semantic Similarity Search
* Top-K Retrieval

### Current Pipeline

```text
GPT2.pdf
    ↓
Text Extraction
    ↓
Chunking
    ↓
Embeddings
    ↓
ChromaDB
    ↓
User Query
    ↓
Similarity Search
    ↓
Top Retrieved Chunks
```

---

## Project Structure

```text
secure-rag/

├── backend/
├── frontend/
├── docs/

├── research/
│   ├── attacks/
│   ├── defenses/
│   ├── evaluation/
│   ├── datasets/
│   ├── pdf_loader.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── vector_store.py
│   └── rag_pipeline.py

├── README.md
├── .gitignore
└── requirements.txt
```

---

## Technologies Used

### AI & Machine Learning

* Sentence Transformers
* ChromaDB
* Vector Embeddings

### NLP

* Semantic Search
* Text Chunking
* Information Retrieval

### Development

* Python 3.11
* Git
* GitHub

---

## Implemented Components

### PDF Loader

Extracts textual content from PDF documents.

### Chunking Engine

Splits large documents into manageable chunks for retrieval.

### Embedding Generator

Converts text chunks into vector representations using Sentence Transformers.

### Vector Database

Stores and indexes embeddings using ChromaDB.

### Retrieval Engine

Performs semantic similarity search and retrieves the most relevant chunks for a given query.

---

## Upcoming Milestones

### Week 2

* BM25 Retrieval
* Hybrid Retrieval
* MMR (Maximal Marginal Relevance)

### Week 3

* Gemini Integration
* Full RAG Pipeline
* RAGAS Evaluation

### Week 4

* Prompt Injection Attacks
* Knowledge Base Poisoning

### Week 5

* Context Stuffing Attacks
* Resource Exhaustion Attacks
* Defense Mechanisms

### Week 6

* Benchmarking
* Performance Analysis
* Research Report

---

## Contributors

* Anshul Chandra (23CS3010)
* Dev Saha (23CS3022)

Under the guidance of Dr. Akash Yadav.

---

## Status

🚧 Active Development

Current Version: Retrieval Pipeline v1.0
