# Secure RAG — Next Steps
### Fix imports → Backend → Gemini → Upload → Logging → Frontend scaffold

This guide is matched to your actual repo (`TopKRetriever`, `BM25Retriever`,
`HybridRetriever`, `MMRRetriever` classes in `research/retrieval/`). Do the
steps in order — each one unblocks the next.

---

## Step 1 — Fix the import paths (5 min)

**Why:** Your retrievers currently use `from retrieval.base import ...`, which
only works because your test scripts manually append `research/` to
`sys.path`. FastAPI will import via `research.retrieval.topk`, which breaks
this. Fix it once, now, before building anything else.

```bash
cd secure-rag
touch research/__init__.py
```

**`research/retrieval/topk.py`** — change the import line:

```python
# OLD
from retrieval.base import embed, get_or_create_collection

# NEW
from .base import embed, get_or_create_collection
```

**`research/retrieval/mmr.py`** — same change:

```python
# OLD
from retrieval.base import embed, get_or_create_collection

# NEW
from .base import embed, get_or_create_collection
```

**`research/retrieval/hybrid.py`** — change both imports:

```python
# OLD
from retrieval.bm25 import BM25Retriever
from retrieval.topk import TopKRetriever

# NEW
from .bm25 import BM25Retriever
from .topk import TopKRetriever
```

`research/retrieval/bm25.py` and `research/retrieval/base.py` need no changes
— they don't import from sibling modules.

### Verify the fix works

```bash
cd secure-rag
python -c "from research.retrieval.topk import TopKRetriever; print('OK')"
```

If this prints `OK`, you're unblocked. If it errors, you're running the
command from the wrong directory — it must be run from the project root
(the folder containing `research/`, not from inside `research/`).

### Cleanup while you're in here

```bash
# vector_store.py is dead code (uses EphemeralClient, nothing imports it anymore)
rm research/vector_store.py
```

Add this to `.gitignore` if it isn't already covered:

```
chroma_store/
*.db
.env
```

---

## Step 2 — Install backend dependencies

```bash
pip install fastapi "uvicorn[standard]" python-multipart sqlalchemy google-generativeai aiofiles
```

Add these to `requirements.txt`:

```
python-multipart==0.0.9
sqlalchemy==2.0.30
google-generativeai==0.7.2
aiofiles==24.1.0
```

---

## Step 3 — Build the FastAPI backend

### `backend/__init__.py`

```bash
touch backend/__init__.py
mkdir -p backend/routes
touch backend/routes/__init__.py
```

### `backend/database.py`

```python
# backend/database.py

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///./secure_rag.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class QueryLog(Base):
    __tablename__ = "query_logs"
    id          = Column(Integer, primary_key=True)
    query       = Column(String)
    strategy    = Column(String)
    answer      = Column(String)
    time_ms     = Column(Float)
    chunks_used = Column(Integer)
    created_at  = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `backend/schemas.py`

```python
# backend/schemas.py

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    strategy: str = "topk"      # topk | bm25 | hybrid | mmr
    top_k: int = 3
    collection: str = "gpt2_paper"


class QueryResponse(BaseModel):
    answer: str
    chunks: list[str]
    scores: list[float]
    strategy: str
    time_ms: float


class UploadResponse(BaseModel):
    filename: str
    chunks_stored: int
    collection: str
```

### `backend/services/rag_service.py`

This wraps your actual retriever classes — no changes to your research code,
just an orchestration layer.

```bash
mkdir -p backend/services
touch backend/services/__init__.py
```

```python
# backend/services/rag_service.py

from research.retrieval.topk import TopKRetriever
from research.retrieval.bm25 import BM25Retriever
from research.retrieval.hybrid import HybridRetriever
from research.retrieval.mmr import MMRRetriever
from research.retrieval.base import get_or_create_collection
from research.chunker import chunk_text

# Cache retrievers per collection so we don't rebuild BM25 index every request
_bm25_cache = {}
_hybrid_cache = {}


def _get_all_chunks(collection_name: str) -> list[str]:
    """BM25 and Hybrid need the raw chunk list, not just the vector index."""
    collection = get_or_create_collection(collection_name)
    results = collection.get(include=["documents"])
    return results["documents"]


def retrieve(query: str, strategy: str, top_k: int, collection_name: str):
    """
    Returns (chunks: list[str], scores: list[float])
    Matches the (doc, score) tuple format your retrievers already return.
    """
    if strategy == "topk":
        retriever = TopKRetriever(collection_name)
        results = retriever.retrieve(query, top_k=top_k)

    elif strategy == "bm25":
        if collection_name not in _bm25_cache:
            chunks = _get_all_chunks(collection_name)
            _bm25_cache[collection_name] = BM25Retriever(chunks)
        results = _bm25_cache[collection_name].retrieve(query, top_k=top_k)

    elif strategy == "hybrid":
        if collection_name not in _hybrid_cache:
            chunks = _get_all_chunks(collection_name)
            _hybrid_cache[collection_name] = HybridRetriever(chunks, collection_name)
        results = _hybrid_cache[collection_name].retrieve(query, top_k=top_k)

    elif strategy == "mmr":
        retriever = MMRRetriever(collection_name)
        results = retriever.retrieve(query, top_k=top_k, fetch_k=top_k * 3)

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    if not results:
        return [], []

    chunks, scores = zip(*results)
    return list(chunks), list(scores)


def invalidate_cache(collection_name: str):
    """Call this after uploading new documents so BM25/Hybrid rebuild their index."""
    _bm25_cache.pop(collection_name, None)
    _hybrid_cache.pop(collection_name, None)
```

**Why the cache matters:** `BM25Retriever` and `HybridRetriever` build their
index from scratch in `__init__`. Without caching, every single query would
re-tokenize your entire knowledge base — fine for a 50-chunk PDF, painfully
slow once you've uploaded several documents.

### `backend/services/llm_service.py`

This is the piece your repo is currently missing — nothing generates an
answer yet, retrieval just returns chunks.

```bash
mkdir -p backend/services
```

```python
# backend/services/llm_service.py

import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT_TEMPLATE = """Answer the question using ONLY the context below.
If the context does not contain the answer, say "I don't know based on the provided documents."

Context:
{context}

Question: {question}

Answer:"""


def generate_answer(question: str, chunks: list[str]) -> str:
    if not chunks:
        return "I don't know based on the provided documents."

    context = "\n\n---\n\n".join(chunks)
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)

    response = _model.generate_content(prompt)
    return response.text
```

### `backend/.env`

```
GEMINI_API_KEY=your_key_here
```

Get a free key at https://aistudio.google.com/apikey — never commit this
file. Confirm `.env` is in `.gitignore`.

### `backend/routes/query.py`

```python
# backend/routes/query.py

import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.schemas import QueryRequest, QueryResponse
from backend.database import get_db, QueryLog
from backend.services.rag_service import retrieve
from backend.services.llm_service import generate_answer

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, db: Session = Depends(get_db)):
    start = time.perf_counter()

    chunks, scores = retrieve(req.query, req.strategy, req.top_k, req.collection)
    answer = generate_answer(req.query, chunks)

    elapsed_ms = (time.perf_counter() - start) * 1000

    db.add(QueryLog(
        query=req.query,
        strategy=req.strategy,
        answer=answer,
        time_ms=elapsed_ms,
        chunks_used=len(chunks)
    ))
    db.commit()

    return QueryResponse(
        answer=answer,
        chunks=chunks,
        scores=scores,
        strategy=req.strategy,
        time_ms=round(elapsed_ms, 2)
    )
```

### `backend/routes/upload.py`

```python
# backend/routes/upload.py

import os
import tempfile
from fastapi import APIRouter, UploadFile, File
from pypdf import PdfReader

from backend.schemas import UploadResponse
from research.chunker import chunk_text
from research.retrieval.base import get_or_create_collection, embed
from backend.services.rag_service import invalidate_cache

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...), collection: str = "gpt2_paper"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    reader = PdfReader(tmp_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    os.unlink(tmp_path)

    chunks = chunk_text(text)

    coll = get_or_create_collection(collection)
    embeddings = embed(chunks)
    ids = [f"{file.filename}_chunk_{i}" for i in range(len(chunks))]

    coll.add(documents=chunks, embeddings=embeddings, ids=ids)

    # BM25/Hybrid must rebuild their index now that new chunks exist
    invalidate_cache(collection)

    return UploadResponse(
        filename=file.filename,
        chunks_stored=len(chunks),
        collection=collection
    )
```

### `backend/main.py`

```python
# backend/main.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ^ adds project root to path so "research.*" and "backend.*" both import cleanly

from dotenv import load_dotenv
load_dotenv()  # reads backend/.env — GEMINI_API_KEY

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes import query, upload

app = FastAPI(title="Secure RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(upload.router, prefix="/api")
app.include_router(query.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "Secure RAG API running"}
```

Add `python-dotenv` to requirements:

```bash
pip install python-dotenv
```

### Run it

```bash
# From project root
uvicorn backend.main:app --reload --port 8000
```

Open `http://localhost:8000/docs`. You should see `/api/upload` and
`/api/query`. Test in this order:

1. `POST /api/upload` — upload `research/datasets/gpt2.pdf`, confirm
   `chunks_stored` comes back non-zero.
2. `POST /api/query` — body:
   ```json
   {"query": "What is GPT-2?", "strategy": "mmr", "top_k": 3}
   ```
   Confirm you get a real Gemini-generated `answer`, not just chunks.
3. Repeat the query with `"strategy": "bm25"` and `"strategy": "hybrid"` —
   confirm all 4 strategies respond without error.
4. Check `secure_rag.db` was created in your project root and contains rows
   in `query_logs` (use `sqlite3 secure_rag.db "select * from query_logs;"`
   or a GUI tool like DB Browser for SQLite).

**Do not move to Step 4 until all four checks above pass.**

---

## Step 4 — Scaffold the React frontend

```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install axios
```

### `frontend/vite.config.js`

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

### `frontend/src/api/client.js`

```js
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const uploadPDF = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const queryRAG = (query, strategy = 'mmr', top_k = 3) =>
  api.post('/query', { query, strategy, top_k })

export default api
```

### `frontend/src/App.jsx`

A minimal working chat box — enough to prove the full chain works
end-to-end. Polish comes later.

```jsx
import { useState } from 'react'
import { uploadPDF, queryRAG } from './api/client'

export default function App() {
  const [strategy, setStrategy] = useState('mmr')
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [chunks, setChunks] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploadStatus('Uploading...')
    const { data } = await uploadPDF(file)
    setUploadStatus(`Stored ${data.chunks_stored} chunks from ${data.filename}`)
  }

  const handleQuery = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const { data } = await queryRAG(query, strategy)
      setAnswer(data.answer)
      setChunks(data.chunks)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: '40px auto', fontFamily: 'sans-serif' }}>
      <h1>Secure RAG</h1>

      <input type="file" accept=".pdf" onChange={handleUpload} />
      <p>{uploadStatus}</p>

      <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
        <option value="topk">Top-K</option>
        <option value="bm25">BM25</option>
        <option value="hybrid">Hybrid</option>
        <option value="mmr">MMR</option>
      </select>

      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input
          style={{ flex: 1 }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          placeholder="Ask a question..."
        />
        <button onClick={handleQuery} disabled={loading}>
          {loading ? '...' : 'Ask'}
        </button>
      </div>

      {answer && (
        <div style={{ marginTop: 20, padding: 12, background: '#f4f4f4' }}>
          <strong>Answer:</strong>
          <p>{answer}</p>
        </div>
      )}

      {chunks.length > 0 && (
        <details style={{ marginTop: 12 }}>
          <summary>Retrieved chunks ({chunks.length})</summary>
          {chunks.map((c, i) => (
            <p key={i} style={{ fontSize: 12, color: '#555' }}>{c.slice(0, 200)}...</p>
          ))}
        </details>
      )}
    </div>
  )
}
```

### Run it

```bash
npm run dev
```

Open `http://localhost:5173`. Upload the GPT-2 PDF, type a question, hit Ask.
You should see a real generated answer with retrieved chunks underneath.

---

## Checklist — what "done" looks like after this guide

- [ ] `research/__init__.py` exists, relative imports fixed in `topk.py`, `mmr.py`, `hybrid.py`
- [ ] `python -c "from research.retrieval.topk import TopKRetriever"` runs with no error from project root
- [ ] `vector_store.py` removed, `chroma_store/` and `.env` in `.gitignore`
- [ ] `uvicorn backend.main:app --reload` starts with no import errors
- [ ] `/docs` shows `/api/upload` and `/api/query`
- [ ] Uploading a PDF returns a non-zero `chunks_stored`
- [ ] Querying with all 4 strategies (`topk`, `bm25`, `hybrid`, `mmr`) returns a real Gemini answer, not an error
- [ ] `secure_rag.db` exists and has rows in `query_logs` after querying
- [ ] React app at `localhost:5173` can upload a PDF and get an answer back

Once every box is checked, you have a true end-to-end RAG web app — this is
the foundation Week 4's attack panel gets built on top of.

---

## What comes right after this (Week 4 preview)

With the chain above working, your friend's job becomes straightforward:
write `research/attacks/prompt_injection.py` and
`research/attacks/kb_poisoning.py` as plain functions that call
`get_or_create_collection()` and inject chunks — same pattern as
`upload.py` above. Your job becomes a `backend/routes/attack.py` that calls
those functions and a React `AttackPanel.jsx` with a before/after query
comparison, reusing `queryRAG()` from `api/client.js` that you already built
in this step. Ask for that guide once the checklist above is fully green.
