import os
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")

# Resolve chroma_store path relative to the project root (two levels up from this file)
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_chroma_path = os.path.join(_project_root, "chroma_store")

client = chromadb.PersistentClient(path=_chroma_path)


def get_or_create_collection(name: str):
    return client.get_or_create_collection(name)


def embed(texts: list) -> list:
    embeddings: np.ndarray = model.encode(texts)  # type: ignore[assignment]
    return embeddings.tolist()