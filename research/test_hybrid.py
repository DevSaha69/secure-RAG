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
from retrieval.hybrid import HybridRetriever


# -------------------------------
# Load PDF
# -------------------------------

base_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(base_dir, "datasets", "gpt2.pdf")

reader = PdfReader(pdf_path)

text = ""

for page in reader.pages:

    extracted = page.extract_text()

    if extracted:
        text += extracted


# -------------------------------
# Create Chunks
# -------------------------------

chunks = chunk_text(text)

print(f"Total Chunks: {len(chunks)}")


# -------------------------------
# Create Hybrid Retriever
# -------------------------------

retriever = HybridRetriever(
    chunks
)


# -------------------------------
# Query
# -------------------------------

query = "What is GPT-2?"

results = retriever.retrieve(
    query,
    top_k=5
)


# -------------------------------
# Display Results
# -------------------------------

print("\nHybrid Results:\n")

for i, (chunk, score) in enumerate(
    results,
    start=1
):

    print(f"\nResult {i}")
    print(f"Score: {score:.4f}")

    safe_chunk = chunk[:500].encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
    print(safe_chunk)

    print("-" * 50)