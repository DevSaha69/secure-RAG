# Secure RAG — Full Stack Integration Guide
### From Python Research Code → Production Website

---

## Table of Contents

1. [Tech Stack Decision](#1-tech-stack-decision)
2. [Final Project Structure](#2-final-project-structure)
3. [Phase 1 — Make Your Research Code a Proper Package](#3-phase-1--make-your-research-code-a-proper-package)
4. [Phase 2 — Build the FastAPI Backend](#4-phase-2--build-the-fastapi-backend)
5. [Phase 3 — Build the React Frontend](#5-phase-3--build-the-react-frontend)
6. [Phase 4 — Connect Frontend to Backend](#6-phase-4--connect-frontend-to-backend)
7. [Phase 5 — Add Attack & Defense Endpoints](#7-phase-5--add-attack--defense-endpoints)
8. [Phase 6 — Security Dashboard UI](#8-phase-6--security-dashboard-ui)
9. [Deployment](#9-deployment)
10. [Week-by-Week Build Order](#10-week-by-week-build-order)

---

## 1. Tech Stack Decision

### Why This Stack

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND                             │
│          React + Vite  +  Tailwind CSS                  │
│                                                          │
│  Why React:   Component model fits a dashboard perfectly │
│  Why Vite:    10x faster than CRA, instant hot reload    │
│  Why Tailwind: Utility-first, great for dashboards       │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP (fetch / axios)
                        │ REST API calls
┌───────────────────────▼─────────────────────────────────┐
│                     BACKEND                              │
│                    FastAPI                               │
│                                                          │
│  Why FastAPI: Written in Python → imports your research  │
│               code directly, no translation needed.      │
│               Async, fast, auto-generates API docs.      │
└───────────────────────┬─────────────────────────────────┘
                        │ direct Python imports
┌───────────────────────▼─────────────────────────────────┐
│                 RESEARCH MODULES                         │
│     chunker.py  embedder.py  retrieval/  attacks/        │
│                  defenses/   evaluate/                   │
└───────────────────────┬─────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
    ChromaDB                        SQLite
  (vector store)                 (query logs,
                                 attack results,
                                  metrics)
```

### Full Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend UI | React 18 + Vite | Chat UI, attack panel, dashboard |
| Styling | Tailwind CSS | Utility classes, fast styling |
| Charts | Recharts | Attack metrics, resource graphs |
| API Client | Axios | HTTP calls from React to FastAPI |
| Backend | FastAPI (Python) | API routes, orchestration |
| Vector DB | ChromaDB (persistent) | Stores document embeddings |
| App DB | SQLite + SQLAlchemy | Logs queries, stores metrics |
| Embeddings | sentence-transformers | `all-MiniLM-L6-v2` |
| LLM | Gemini API | Answer generation |
| Deployment | Render (backend) + Vercel (frontend) | Free tier, easy |

---

## 2. Final Project Structure

Build toward this by end of Week 6:

```
secure-rag/
│
├── backend/                        ← FastAPI app lives here
│   ├── main.py                     ← App entry point
│   ├── database.py                 ← SQLite setup
│   ├── models.py                   ← SQLAlchemy table models
│   ├── schemas.py                  ← Pydantic request/response shapes
│   │
│   ├── routes/
│   │   ├── upload.py               ← POST /upload
│   │   ├── query.py                ← POST /query
│   │   ├── attack.py               ← POST /attack
│   │   ├── defense.py              ← POST /defense
│   │   └── metrics.py              ← GET /metrics
│   │
│   └── services/                   ← Thin wrappers around research/
│       ├── rag_service.py          ← calls retrieval modules
│       ├── attack_service.py       ← calls attack scripts
│       └── defense_service.py      ← calls defense scripts
│
├── research/                       ← Your existing Python AI code
│   ├── __init__.py                 ← Makes it a package (add this!)
│   ├── pdf_loader.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── vector_store.py
│   ├── rag_pipeline.py
│   │
│   ├── retrieval/                  ← Week 2 work
│   │   ├── __init__.py
│   │   ├── topk.py
│   │   ├── bm25.py
│   │   ├── hybrid.py
│   │   └── mmr.py
│   │
│   ├── attacks/                    ← Week 4-5 work
│   │   ├── __init__.py
│   │   ├── prompt_injection.py
│   │   ├── kb_poisoning.py
│   │   ├── context_stuffing.py
│   │   └── resource_exhaustion.py
│   │
│   ├── defenses/                   ← Week 5 work
│   │   ├── __init__.py
│   │   ├── injection_detector.py
│   │   ├── anomaly_detector.py
│   │   └── query_filter.py
│   │
│   └── evaluation/
│       ├── __init__.py
│       └── evaluate.py
│
├── frontend/                       ← React app lives here
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── client.js           ← All axios calls in one place
│       ├── components/
│       │   ├── ChatPanel.jsx       ← Query interface
│       │   ├── AttackPanel.jsx     ← Attack simulation UI
│       │   ├── MetricsChart.jsx    ← Recharts graphs
│       │   ├── UploadZone.jsx      ← PDF upload
│       │   └── StrategySelector.jsx
│       └── pages/
│           ├── Dashboard.jsx
│           ├── AttackSimulator.jsx
│           └── Evaluation.jsx
│
├── docs/
├── .env                            ← GEMINI_API_KEY etc (never commit)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 3. Phase 1 — Make Your Research Code a Proper Package

This is the most important step. FastAPI needs to import your research code cleanly.

### Step 1 — Add `__init__.py` files

```bash
# Run from project root
touch research/__init__.py
touch research/retrieval/__init__.py
touch research/attacks/__init__.py
touch research/defenses/__init__.py
touch research/evaluation/__init__.py
```

### Step 2 — Refactor `chunker.py` to fix character-based chunking

```python
# research/chunker.py

def chunk_text(text: str, chunk_size: int = 200, overlap: int = 30) -> list[str]:
    """
    Word-based chunking with overlap so context isn't cut at word boundaries.
    chunk_size=200 words, overlap=30 words.
    """
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks
```

### Step 3 — Create a shared embedder singleton

```python
# research/embedder.py

from sentence_transformers import SentenceTransformer

# Load once, reuse everywhere — loading is slow
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed(texts: list[str]) -> list[list[float]]:
    model = get_model()
    return model.encode(texts, convert_to_numpy=True).tolist()
```

### Step 4 — Create a persistent vector store wrapper

```python
# research/vector_store.py

import chromadb
from research.embedder import embed

# Use PersistentClient so data survives restarts
_client = chromadb.PersistentClient(path="./chroma_store")

def get_collection(name: str = "secure_rag"):
    return _client.get_or_create_collection(name)

def add_chunks(chunks: list[str], source: str, collection_name: str = "secure_rag"):
    """Store chunks with their embeddings and source metadata."""
    collection = get_collection(collection_name)
    embeddings = embed(chunks)
    ids = [f"{source}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source, "is_poison": False} for _ in chunks]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )
    return len(chunks)

def get_all_chunks(collection_name: str = "secure_rag") -> list[str]:
    collection = get_collection(collection_name)
    results = collection.get(include=["documents"])
    return results["documents"]
```

### Step 5 — Build the 4 retrieval strategies

```python
# research/retrieval/topk.py

from research.vector_store import get_collection
from research.embedder import embed

def topk_retrieve(query: str, k: int = 5, collection_name: str = "secure_rag") -> list[str]:
    collection = get_collection(collection_name)
    query_emb = embed([query])[0]
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=k,
        include=["documents", "metadatas"]
    )
    return results["documents"][0]
```

```python
# research/retrieval/bm25.py

from rank_bm25 import BM25Okapi
from research.vector_store import get_all_chunks

def bm25_retrieve(query: str, k: int = 5, collection_name: str = "secure_rag") -> list[str]:
    all_chunks = get_all_chunks(collection_name)
    if not all_chunks:
        return []

    tokenized_corpus = [doc.lower().split() for doc in all_chunks]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [all_chunks[i] for i in top_indices]
```

```python
# research/retrieval/hybrid.py

from research.retrieval.topk import topk_retrieve
from research.retrieval.bm25 import bm25_retrieve

def hybrid_retrieve(query: str, k: int = 5, alpha: float = 0.5,
                    collection_name: str = "secure_rag") -> list[str]:
    """
    Combine vector (top-k) and BM25 results.
    alpha=0.5 means equal weight; higher alpha = more vector weight.
    """
    vector_results = topk_retrieve(query, k=k * 2, collection_name=collection_name)
    bm25_results = bm25_retrieve(query, k=k * 2, collection_name=collection_name)

    # Score by rank: earlier = higher score
    scores = {}
    for rank, doc in enumerate(vector_results):
        scores[doc] = scores.get(doc, 0) + alpha * (1 / (rank + 1))
    for rank, doc in enumerate(bm25_results):
        scores[doc] = scores.get(doc, 0) + (1 - alpha) * (1 / (rank + 1))

    sorted_docs = sorted(scores, key=scores.get, reverse=True)
    return sorted_docs[:k]
```

```python
# research/retrieval/mmr.py

import numpy as np
from research.vector_store import get_collection
from research.embedder import embed

def mmr_retrieve(query: str, k: int = 5, lambda_param: float = 0.5,
                 fetch_k: int = 20, collection_name: str = "secure_rag") -> list[str]:
    """
    Maximal Marginal Relevance — balances relevance vs diversity.
    lambda_param=1.0 → pure relevance (same as Top-K)
    lambda_param=0.0 → pure diversity
    lambda_param=0.5 → balanced (recommended)
    """
    collection = get_collection(collection_name)
    query_emb = np.array(embed([query])[0])

    # Fetch a larger candidate pool
    results = collection.query(
        query_embeddings=[query_emb.tolist()],
        n_results=min(fetch_k, collection.count()),
        include=["documents", "embeddings"]
    )

    candidate_docs = results["documents"][0]
    candidate_embs = np.array(results["embeddings"][0])

    if not candidate_docs:
        return []

    selected = []
    selected_embs = []

    for _ in range(min(k, len(candidate_docs))):
        if not selected:
            # First pick: highest cosine similarity to query
            sims_to_query = candidate_embs @ query_emb / (
                np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb) + 1e-9
            )
            best_idx = int(np.argmax(sims_to_query))
        else:
            sel_emb_matrix = np.array(selected_embs)
            sims_to_query = candidate_embs @ query_emb / (
                np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb) + 1e-9
            )
            # Redundancy: max similarity to already selected docs
            sims_to_selected = np.max(
                candidate_embs @ sel_emb_matrix.T /
                (np.linalg.norm(candidate_embs, axis=1, keepdims=True) *
                 np.linalg.norm(sel_emb_matrix, axis=1) + 1e-9),
                axis=1
            )
            mmr_scores = lambda_param * sims_to_query - (1 - lambda_param) * sims_to_selected
            best_idx = int(np.argmax(mmr_scores))

        selected.append(candidate_docs[best_idx])
        selected_embs.append(candidate_embs[best_idx])

        # Remove chosen candidate
        candidate_docs = [d for i, d in enumerate(candidate_docs) if i != best_idx]
        candidate_embs = np.delete(candidate_embs, best_idx, axis=0)

    return selected
```

---

## 4. Phase 2 — Build the FastAPI Backend

### Step 1 — Install dependencies

```bash
cd backend
pip install fastapi uvicorn python-multipart sqlalchemy aiofiles google-generativeai
```

### Step 2 — `backend/main.py`

```python
# backend/main.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ^ This lets backend import from research/

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import upload, query, attack, metrics
from backend.database import init_db

app = FastAPI(title="Secure RAG API", version="1.0")

# Allow React (localhost:5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-vercel-domain.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(upload.router, prefix="/api")
app.include_router(query.router,  prefix="/api")
app.include_router(attack.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "Secure RAG API running"}
```

### Step 3 — `backend/database.py`

```python
# backend/database.py

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///./secure_rag.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class QueryLog(Base):
    __tablename__ = "query_logs"
    id          = Column(Integer, primary_key=True)
    query       = Column(String)
    strategy    = Column(String)
    answer      = Column(String)
    attack_type = Column(String, nullable=True)   # null = clean query
    time_ms     = Column(Float)
    cpu_delta   = Column(Float, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

class AttackResult(Base):
    __tablename__ = "attack_results"
    id               = Column(Integer, primary_key=True)
    attack_type      = Column(String)
    strategy         = Column(String)
    success          = Column(Boolean)
    chunks_poisoned  = Column(Integer, default=0)
    answer_before    = Column(String, nullable=True)
    answer_after     = Column(String, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 4 — `backend/schemas.py`

```python
# backend/schemas.py

from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query: str
    strategy: str = "topk"       # topk | bm25 | hybrid | mmr
    k: int = 5
    defense_enabled: bool = False

class QueryResponse(BaseModel):
    answer: str
    chunks: list[str]
    strategy: str
    time_ms: float

class AttackRequest(BaseModel):
    attack_type: str             # injection | poisoning | stuffing | exhaustion
    target_query: Optional[str] = None
    false_info: Optional[str] = None
    n_stuffing_chunks: int = 50

class AttackResponse(BaseModel):
    success: bool
    message: str
    answer_before: Optional[str]
    answer_after: Optional[str]
    attack_success_rate: Optional[float]
```

### Step 5 — `backend/routes/upload.py`

```python
# backend/routes/upload.py

import os, tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader
from research.chunker import chunk_text
from research.vector_store import add_chunks
from research.defenses.injection_detector import filter_safe_chunks

router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), defense: bool = False):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Extract text
    reader = PdfReader(tmp_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    os.unlink(tmp_path)

    # Chunk
    chunks = chunk_text(text)

    # Optionally filter dangerous chunks
    flagged = 0
    if defense:
        chunks, flagged = filter_safe_chunks(chunks)

    # Store in ChromaDB
    count = add_chunks(chunks, source=file.filename)

    return {
        "filename": file.filename,
        "chunks_stored": count,
        "chunks_flagged": flagged
    }
```

### Step 6 — `backend/routes/query.py`

```python
# backend/routes/query.py

import time, os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.schemas import QueryRequest, QueryResponse
from backend.database import get_db, QueryLog
from research.retrieval.topk import topk_retrieve
from research.retrieval.bm25 import bm25_retrieve
from research.retrieval.hybrid import hybrid_retrieve
from research.retrieval.mmr import mmr_retrieve
import google.generativeai as genai

router = APIRouter()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-1.5-flash")

STRATEGIES = {
    "topk":   topk_retrieve,
    "bm25":   bm25_retrieve,
    "hybrid": hybrid_retrieve,
    "mmr":    mmr_retrieve,
}

@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, db: Session = Depends(get_db)):
    start = time.perf_counter()

    # Retrieve chunks using chosen strategy
    retrieve_fn = STRATEGIES.get(req.strategy, topk_retrieve)
    chunks = retrieve_fn(req.query, k=req.k)

    # Build prompt and call Gemini
    context = "\n\n".join(chunks)
    prompt = f"""Answer the question using only the context below.
If the context doesn't contain the answer, say "I don't know."

Context:
{context}

Question: {req.query}
Answer:"""

    response = gemini.generate_content(prompt)
    answer = response.text

    elapsed_ms = (time.perf_counter() - start) * 1000

    # Log to SQLite
    db.add(QueryLog(
        query=req.query,
        strategy=req.strategy,
        answer=answer,
        time_ms=elapsed_ms
    ))
    db.commit()

    return QueryResponse(
        answer=answer,
        chunks=chunks,
        strategy=req.strategy,
        time_ms=elapsed_ms
    )
```

### Step 7 — Run the backend

```bash
# From project root
cd backend
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` — FastAPI auto-generates interactive API docs.
Test every endpoint here before touching the frontend.

---

## 5. Phase 3 — Build the React Frontend

### Step 1 — Create the React app

```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install tailwindcss @tailwindcss/vite axios recharts lucide-react
```

### Step 2 — Configure Tailwind (Vite v4+ way)

```js
// frontend/vite.config.js

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'   // proxy API calls to FastAPI during dev
    }
  }
})
```

```css
/* frontend/src/index.css */
@import "tailwindcss";
```

### Step 3 — Create the API client

```js
// frontend/src/api/client.js

import axios from 'axios'

const api = axios.create({
  baseURL: '/api',              // proxied to FastAPI in dev
  headers: { 'Content-Type': 'application/json' }
})

export const uploadPDF = (file, defense = false) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/upload?defense=${defense}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const queryRAG = (query, strategy = 'topk', k = 5) =>
  api.post('/query', { query, strategy, k })

export const launchAttack = (attackType, options = {}) =>
  api.post('/attack', { attack_type: attackType, ...options })

export const getMetrics = () => api.get('/metrics')

export default api
```

---

## 6. Phase 4 — Connect Frontend to Backend

### The main App layout

```jsx
// frontend/src/App.jsx

import { useState } from 'react'
import ChatPanel from './components/ChatPanel'
import AttackPanel from './components/AttackPanel'
import UploadZone from './components/UploadZone'

export default function App() {
  const [mode, setMode] = useState('chat')           // 'chat' | 'attack'
  const [strategy, setStrategy] = useState('topk')

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-red-400">⚔ Secure RAG</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setMode('chat')}
            className={`px-4 py-1.5 rounded text-sm ${mode === 'chat' ? 'bg-blue-600' : 'bg-gray-800'}`}
          >
            Chat
          </button>
          <button
            onClick={() => setMode('attack')}
            className={`px-4 py-1.5 rounded text-sm ${mode === 'attack' ? 'bg-red-600' : 'bg-gray-800'}`}
          >
            Attack Simulator
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <UploadZone />

        {/* Strategy Selector */}
        <div className="flex gap-2 my-4">
          {['topk', 'bm25', 'hybrid', 'mmr'].map(s => (
            <button
              key={s}
              onClick={() => setStrategy(s)}
              className={`px-3 py-1 rounded text-sm uppercase tracking-wide ${
                strategy === s ? 'bg-green-600' : 'bg-gray-800'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {mode === 'chat'
          ? <ChatPanel strategy={strategy} />
          : <AttackPanel strategy={strategy} />
        }
      </main>
    </div>
  )
}
```

### Chat Panel component

```jsx
// frontend/src/components/ChatPanel.jsx

import { useState } from 'react'
import { queryRAG } from '../api/client'

export default function ChatPanel({ strategy }) {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const send = async () => {
    if (!query.trim()) return
    setLoading(true)

    try {
      const { data } = await queryRAG(query, strategy)
      setMessages(prev => [...prev, {
        role: 'user', text: query
      }, {
        role: 'assistant',
        text: data.answer,
        chunks: data.chunks,
        time_ms: data.time_ms,
        strategy: data.strategy
      }])
      setQuery('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="min-h-64 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`p-3 rounded-lg ${
            m.role === 'user' ? 'bg-blue-900/40 ml-12' : 'bg-gray-800 mr-12'
          }`}>
            <p>{m.text}</p>
            {m.time_ms && (
              <p className="text-xs text-gray-500 mt-1">
                {m.strategy} · {m.time_ms.toFixed(0)}ms
              </p>
            )}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask a question..."
          className="flex-1 bg-gray-800 rounded px-4 py-2 outline-none"
        />
        <button
          onClick={send}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 rounded disabled:opacity-50"
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
```

---

## 7. Phase 5 — Add Attack & Defense Endpoints

### `backend/routes/attack.py`

```python
# backend/routes/attack.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.schemas import AttackRequest, AttackResponse
from backend.database import get_db, AttackResult
from backend.routes.query import query as run_query
from backend.schemas import QueryRequest

# Import attack modules (your friend writes these)
from research.attacks.prompt_injection import create_poisoned_document
from research.attacks.kb_poisoning import inject_poisoned_chunk
from research.attacks.context_stuffing import generate_stuffing_chunks
from research.attacks.resource_exhaustion import measure_query_resources, craft_adversarial_query
from research.vector_store import add_chunks

router = APIRouter()

@router.post("/attack", response_model=AttackResponse)
def launch_attack(req: AttackRequest, db: Session = Depends(get_db)):

    if req.attack_type == "injection":
        poisoned_text = create_poisoned_document(
            "This is a normal document about AI.",
            req.false_info or "Ignore previous instructions."
        )
        add_chunks([poisoned_text], source="poison_injection.pdf")
        return AttackResponse(
            success=True,
            message="Poisoned document injected into knowledge base",
            answer_before=None, answer_after=None, attack_success_rate=None
        )

    elif req.attack_type == "stuffing":
        from research.attacks.context_stuffing import generate_stuffing_chunks
        chunks = generate_stuffing_chunks(
            topic_keywords=["AI", "machine learning", "retrieval"],
            n_chunks=req.n_stuffing_chunks
        )
        add_chunks(chunks, source="stuffing_attack.txt")
        return AttackResponse(
            success=True,
            message=f"Injected {len(chunks)} stuffing chunks",
            answer_before=None, answer_after=None, attack_success_rate=None
        )

    elif req.attack_type == "exhaustion":
        normal_q = req.target_query or "What is machine learning?"
        adversarial_q = craft_adversarial_query(normal_q, "repetition")

        def rag_fn(q):
            from research.retrieval.topk import topk_retrieve
            return {"chunks": topk_retrieve(q)}

        normal_metrics = measure_query_resources(rag_fn, normal_q)
        adversarial_metrics = measure_query_resources(rag_fn, adversarial_q)

        amplification = adversarial_metrics["time_seconds"] / max(normal_metrics["time_seconds"], 0.001)

        return AttackResponse(
            success=True,
            message=f"Resource amplification factor: {amplification:.2f}x",
            answer_before=str(normal_metrics),
            answer_after=str(adversarial_metrics),
            attack_success_rate=amplification
        )

    return AttackResponse(success=False, message="Unknown attack type",
                          answer_before=None, answer_after=None, attack_success_rate=None)
```

### `backend/routes/metrics.py`

```python
# backend/routes/metrics.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db, QueryLog, AttackResult

router = APIRouter()

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    logs = db.query(QueryLog).all()
    attacks = db.query(AttackResult).all()

    # Group average response time by strategy
    strategy_times = {}
    for log in logs:
        strategy_times.setdefault(log.strategy, []).append(log.time_ms)

    avg_times = {
        s: round(sum(times) / len(times), 2)
        for s, times in strategy_times.items()
    }

    return {
        "total_queries": len(logs),
        "total_attacks": len(attacks),
        "avg_response_time_ms": avg_times,
        "attack_breakdown": {
            attack_type: sum(1 for a in attacks if a.attack_type == attack_type)
            for attack_type in ["injection", "poisoning", "stuffing", "exhaustion"]
        }
    }
```

---

## 8. Phase 6 — Security Dashboard UI

### Attack Panel with before/after comparison

```jsx
// frontend/src/components/AttackPanel.jsx

import { useState } from 'react'
import { launchAttack, queryRAG } from '../api/client'

const ATTACKS = [
  { id: 'injection',  label: 'Prompt Injection',       color: 'red' },
  { id: 'poisoning',  label: 'KB Poisoning',            color: 'orange' },
  { id: 'stuffing',   label: 'Context Stuffing',        color: 'yellow' },
  { id: 'exhaustion', label: 'Resource Exhaustion',     color: 'purple' },
]

export default function AttackPanel({ strategy }) {
  const [selectedAttack, setSelectedAttack] = useState(null)
  const [targetQuery, setTargetQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const runAttack = async () => {
    if (!selectedAttack) return
    setLoading(true)

    // Get answer BEFORE attack
    let before = null
    if (targetQuery) {
      const { data } = await queryRAG(targetQuery, strategy)
      before = data.answer
    }

    // Launch attack
    await launchAttack(selectedAttack, {
      target_query: targetQuery,
      n_stuffing_chunks: 100
    })

    // Get answer AFTER attack
    let after = null
    if (targetQuery) {
      const { data } = await queryRAG(targetQuery, strategy)
      after = data.answer
    }

    setResult({ before, after, attack: selectedAttack })
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3">
        {ATTACKS.map(a => (
          <button
            key={a.id}
            onClick={() => setSelectedAttack(a.id)}
            className={`p-4 rounded-lg text-left border-2 transition-all ${
              selectedAttack === a.id
                ? `border-${a.color}-500 bg-${a.color}-900/20`
                : 'border-gray-700 bg-gray-800'
            }`}
          >
            <div className="font-semibold">{a.label}</div>
          </button>
        ))}
      </div>

      <input
        value={targetQuery}
        onChange={e => setTargetQuery(e.target.value)}
        placeholder="Target query to test (optional)"
        className="w-full bg-gray-800 rounded px-4 py-2 outline-none"
      />

      <button
        onClick={runAttack}
        disabled={!selectedAttack || loading}
        className="w-full py-3 bg-red-600 rounded font-semibold disabled:opacity-50"
      >
        {loading ? 'Attacking...' : '⚡ Launch Attack'}
      </button>

      {result && (
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-green-900/20 border border-green-700 rounded">
            <p className="text-xs text-green-400 mb-2">BEFORE ATTACK</p>
            <p className="text-sm">{result.before || 'N/A'}</p>
          </div>
          <div className="p-4 bg-red-900/20 border border-red-700 rounded">
            <p className="text-xs text-red-400 mb-2">AFTER ATTACK</p>
            <p className="text-sm">{result.after || 'N/A'}</p>
          </div>
        </div>
      )}
    </div>
  )
}
```

---

## 9. Deployment

### Backend → Render (Free Tier)

1. Create `backend/requirements.txt`:
```
fastapi
uvicorn[standard]
sqlalchemy
python-multipart
pypdf
sentence-transformers
chromadb
rank-bm25
google-generativeai
aiofiles
numpy
psutil
```

2. Create `render.yaml` in project root:
```yaml
services:
  - type: web
    name: secure-rag-backend
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false          # set this manually in Render dashboard
```

3. Push to GitHub → connect repo to Render → set `GEMINI_API_KEY` in environment variables.

### Frontend → Vercel

1. Update `frontend/src/api/client.js` — change baseURL for production:
```js
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api'
})
```

2. Create `frontend/.env.production`:
```
VITE_API_URL=https://secure-rag-backend.onrender.com/api
```

3. Push frontend to GitHub → import project on Vercel → set `VITE_API_URL` env var.

---

## 10. Week-by-Week Build Order

| Week | Backend task | Frontend task |
|------|-------------|---------------|
| **1** | Refactor research/ into a package, fix chunker, wire embeddings | Set up React + Vite + Tailwind, create `api/client.js` |
| **2** | Implement 4 retrieval strategies in `research/retrieval/` | Build `UploadZone.jsx`, `StrategySelector.jsx` |
| **3** | `main.py` + `/upload` + `/query` routes working, test in `/docs` | Build `ChatPanel.jsx`, wire to backend, verify e2e |
| **4** | `/attack` endpoint + prompt injection & poisoning attack modules | Build `AttackPanel.jsx` with before/after comparison |
| **5** | Context stuffing + resource exhaustion attacks, all 4 defenses | Build `MetricsChart.jsx` with Recharts, defense toggle |
| **6** | `/metrics` endpoint, RAGAS evaluation script | Polish, deploy to Render + Vercel, update README |

---

## Key Rules to Follow Throughout

1. **Never run Python research scripts directly in production.** Always call them through FastAPI service functions.

2. **The `sys.path.append` line in `main.py` is critical.** Without it, `from research.retrieval.topk import ...` fails.

3. **Use `PersistentClient` not `Client` in ChromaDB.** The in-memory client (which your current code uses) loses all data when FastAPI restarts.

4. **Always test new backend routes in `/docs` before building the React component for them.** FastAPI's auto-docs (`localhost:8000/docs`) let you call every endpoint interactively.

5. **One API client file, all axios calls.** Never write `fetch()` or `axios.post()` inside components — always import from `api/client.js`.

6. **Environment variables for secrets.** `GEMINI_API_KEY` never goes in code. Use `.env` locally and Render's dashboard in production.
