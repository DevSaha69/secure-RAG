import chromadb

client = chromadb.Client()

collection = client.create_collection(
    name="gpt2_paper"
)

collection.add(
    documents=[
        "GPT-2 is a language model developed by OpenAI."
    ],
    ids=["chunk1"]
)

print("Stored Successfully")
results = collection.query(
    query_texts=[
        "What is GPT-2?"
    ],
    n_results=1
)

print(results)