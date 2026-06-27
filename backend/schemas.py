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


class AttackRequest(BaseModel):
    attack_type: str          # "prompt_injection" | "kb_poisoning"
    collection: str = "gpt2_paper"
    payload: str              # The injected text / false fact
    query: str                # The query to test attack success with
    strategy: str = "topk"   # Which retrieval strategy to test
    top_k: int = 3


class AttackResponse(BaseModel):
    attack_type: str
    injected_text: str
    before_answer: str        # Answer BEFORE attack (clean)
    after_answer: str         # Answer AFTER attack (poisoned)
    before_chunks: list[str]
    after_chunks: list[str]
    poisoned_in_top_k: int    # For KB poisoning: how many poison chunks retrieved
    collection: str


class CleanupRequest(BaseModel):
    attack_type: str
    collection: str = "gpt2_paper"


class CleanupResponse(BaseModel):
    removed: int
    attack_type: str
