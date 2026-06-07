from pypdf import PdfReader

from chunker import chunk_text
from retrieval.bm25 import BM25Retriever


reader = PdfReader(
    "research/datasets/gpt2.pdf"
)

text = ""

for page in reader.pages:

    extracted = page.extract_text()

    if extracted:
        text += extracted


chunks = chunk_text(text)

print(
    f"Total Chunks: {len(chunks)}"
)

retriever = BM25Retriever(chunks)

results = retriever.retrieve(
    "What is GPT-2?",
    top_k=3
)

print("\nTop BM25 Results:\n")

for rank, (chunk, score) in enumerate(
    results,
    start=1
):
    print(
        f"\nResult {rank}"
    )
    print(
        f"Score: {score:.4f}"
    )
    print(
        chunk[:500]
    )
    print("-" * 50)