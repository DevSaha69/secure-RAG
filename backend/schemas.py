# backend/schemas.py

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    strategy: str = "topk"      # topk | bm25 | hybrid | mmr
    top_k: int = 3
    collection: str = "gpt2_paper"


class QueryResponse(BaseModel):
    answer: str
    chunks: list[str]
    scores: list[float]
    strategy: str
    time_ms: float


class UploadResponse(BaseModel):
    filename: str
    chunks_stored: int
    collection: str
