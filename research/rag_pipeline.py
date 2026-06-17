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

from retrieval.base import (
    get_or_create_collection,
    embed
)

# -------------------------------
# STEP 1: Load PDF
# -------------------------------

# Resolve PDF path relative to this file
base_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(base_dir, "datasets", "gpt2.pdf")

reader = PdfReader(pdf_path)


text = ""

for page in reader.pages:
    extracted = page.extract_text()

    if extracted:
        text += extracted

# -------------------------------
# STEP 2: Create Chunks
# -------------------------------

chunks = chunk_text(text)

print(f"Total Chunks: {len(chunks)}")

# -------------------------------
# STEP 3: Generate Embeddings
# -------------------------------

embeddings = embed(chunks)

print("Embeddings Generated!")

# -------------------------------
# STEP 4: Create Collection
# -------------------------------

collection = get_or_create_collection(
    "gpt2_paper"
)

# -------------------------------
# STEP 5: Store Chunks
# -------------------------------

ids = [f"chunk_{i}" for i in range(len(chunks))]

try:
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )

    print("All chunks stored successfully!")

except Exception:
    print("Chunks already exist. Skipping insert.")

# -------------------------------
# STEP 6: Query
# -------------------------------

query = "What is GPT-2?"

results = collection.query(
    query_texts=[query],
    n_results=3
)

# -------------------------------
# STEP 7: Display Results
# -------------------------------

print("\nTop Retrieved Chunks:\n")

if not results or not results.get("documents") or not results["documents"][0]:
    print("No results returned from the collection.")
else:
    for i, doc in enumerate(
        results["documents"][0],
        start=1
    ):
        print(f"\nResult {i}:")
        # Safely encode to console encoding, replacing unencodable characters
        safe_doc = doc[:500].encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
        print(safe_doc)
        print("-" * 50)