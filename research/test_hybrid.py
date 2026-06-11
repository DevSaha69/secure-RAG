from pypdf import PdfReader

from chunker import chunk_text
from retrieval.hybrid import HybridRetriever


# -------------------------------
# Load PDF
# -------------------------------

reader = PdfReader(
    "research/datasets/gpt2.pdf"
)

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

for i, chunk in enumerate(
    results,
    start=1
):

    print(f"\nResult {i}")

    print(chunk[:500])

    print("-" * 50)