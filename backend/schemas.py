# backend/schemas.py

from typing import Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    strategy: str = "topk"      # topk | bm25 | hybrid | mmr
    top_k: int = 3
    collection: str = "gpt2_paper"
    include_llm: bool = True     # False = retrieval only (no Gemini calls)


class QueryResponse(BaseModel):
    answer: Optional[str]        # null when include_llm=False
    chunks: list[str]
    scores: list[float]
    strategy: str
    time_ms: float
    include_llm: bool            # Whether LLM generation was included


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
    template_index: int = 0   # For prompt injection: which template (0–4)
    include_llm: bool = True   # False = retrieval metrics only (no Gemini calls)


class AttackResponse(BaseModel):
    attack_type: str
    injected_text: str              # The exact text injected into the KB
    before_answer: Optional[str]     # LLM answer on the CLEAN system (null if include_llm=False)
    after_answer: Optional[str]      # LLM answer on the POISONED system (null if include_llm=False)
    before_chunks: list[str]         # Chunks retrieved before attack
    after_chunks: list[str]          # Chunks retrieved after attack
    poisoned_in_top_k: int           # How many of top_k chunks are poisoned
    poison_ratio: float              # poisoned_in_top_k / top_k
    attack_succeeded: Optional[bool] # True if after_answer differs significantly (null if include_llm=False)
    include_llm: bool                # Whether LLM generation was included
    collection: str


class CleanupRequest(BaseModel):
    attack_type: str
    collection: str = "gpt2_paper"


class CleanupResponse(BaseModel):
    removed: int
    attack_type: str
    collection: str
