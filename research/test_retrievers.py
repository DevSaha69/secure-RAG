import io
import os
import sys

# Fix Unicode output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    cast_stdout = sys.stdout
    if isinstance(cast_stdout, io.TextIOWrapper):
        cast_stdout.reconfigure(encoding='utf-8', errors='replace')

# Add the directory of this file to sys.path so chunker and retrieval modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pypdf import PdfReader
from chunker import chunk_text
from retrieval.base import get_or_create_collection, embed
from retrieval.topk import TopKRetriever
from retrieval.bm25 import BM25Retriever
from retrieval.hybrid import HybridRetriever
from retrieval.mmr import MMRRetriever

# 1. Load PDF and Chunk
base_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(base_dir, "datasets", "gpt2.pdf")
print(f"Reading PDF from {pdf_path}...")
reader = PdfReader(pdf_path)

text = ""
for page in reader.pages:
    extracted = page.extract_text()
    if extracted:
        text += extracted

chunks = chunk_text(text)
print(f"Total Chunks: {len(chunks)}")

# 2. Store in Chroma
print("Storing chunks in ChromaDB...")
collection = get_or_create_collection("gpt2_paper")
embeddings = embed(chunks)
ids = [f"chunk_{i}" for i in range(len(chunks))]

try:
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )
    print("Chunks stored successfully!")
except Exception as e:
    print(f"Note: Chunks already exist or were skipped. Details: {e}")

# 3. Query using all 4 retrievers
query = "What is the key architecture of the model?"

print(f"\n--- Running Retrievers for Query: '{query}' ---\n")

# Top-K
print("[1] Top-K Vector Search:")
topk_ret = TopKRetriever("gpt2_paper")
results_topk = topk_ret.retrieve(query, top_k=3)
for idx, (doc, score) in enumerate(results_topk, 1):
    safe_doc = doc[:150].strip().encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
    print(f"  {idx}. [Score: {score:.4f}] {safe_doc}...")

# BM25
print("\n[2] BM25 Lexical Search:")
bm25_ret = BM25Retriever(chunks)
results_bm25 = bm25_ret.retrieve(query, top_k=3)
for idx, (doc, score) in enumerate(results_bm25, 1):
    safe_doc = doc[:150].strip().encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
    print(f"  {idx}. [Score: {score:.4f}] {safe_doc}...")

# Hybrid
print("\n[3] Hybrid Search (BM25 + Vector):")
hybrid_ret = HybridRetriever(chunks, "gpt2_paper")
results_hybrid = hybrid_ret.retrieve(query, top_k=3)
for idx, (doc, score) in enumerate(results_hybrid, 1):
    safe_doc = doc[:150].strip().encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
    print(f"  {idx}. [Score: {score:.4f}] {safe_doc}...")

# MMR
print("\n[4] MMR Diverse Search:")
mmr_ret = MMRRetriever("gpt2_paper", lambda_param=0.5)
results_mmr = mmr_ret.retrieve(query, top_k=3, fetch_k=10)
for idx, (doc, score) in enumerate(results_mmr, 1):
    safe_doc = doc[:150].strip().encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
    print(f"  {idx}. [Score: {score:.4f}] {safe_doc}...")
