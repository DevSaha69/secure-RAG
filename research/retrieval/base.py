from sentence_transformers import SentenceTransformer
import chromadb

model=SentenceTransformer("all-MiniLM-L6-v2")
client=chromadb.PersistentClient(path="./chroma_store") #persistent, not in memory

def get_or_create_collection(name:str):
    return client.get_or_create_collection(name)

def embed(texts:list[str])->list:       
    return model.encode(texts).tolist()