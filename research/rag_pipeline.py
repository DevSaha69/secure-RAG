from pypdf import PdfReader
from chunker import chunk_text
import chromadb

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
# STEP 3: Create ChromaDB Collection
# -------------------------------

client = chromadb.Client()

collection = client.get_or_create_collection(
    name="gpt2_paper"
)

# -------------------------------
# STEP 4: Store Chunks
# -------------------------------

for i, chunk in enumerate(chunks):
    collection.add(
        documents=[chunk],
        ids=[f"chunk_{i}"]
    )

print("All chunks stored successfully!")

# -------------------------------
# STEP 5: User Query
# -------------------------------

query = "What is GPT-2?"

results = collection.query(
    query_texts=[query],
    n_results=3
)

# -------------------------------
# STEP 6: Display Results
# -------------------------------

print("\nTop Retrieved Chunks:\n")

for i, doc in enumerate(results["documents"][0], start=1):
    print(f"\nResult {i}:")
    print(doc[:500])
    print("-" * 50)