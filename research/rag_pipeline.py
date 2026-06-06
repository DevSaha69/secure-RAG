from pypdf import PdfReader
from chunker import chunk_text

from retrieval.base import (
    get_or_create_collection,
    embed
)

# -------------------------------
# STEP 1: Load PDF
# -------------------------------

reader = PdfReader("research/datasets/gpt2.pdf")

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

for i, doc in enumerate(
    results["documents"][0],
    start=1
):
    print(f"\nResult {i}:")
    print(doc[:500])
    print("-" * 50)