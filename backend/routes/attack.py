# backend/routes/attack.py
#
# Exposes two endpoints:
#   POST /api/attack   — run an attack, return before/after answers
#   POST /api/cleanup  — remove all poisoned chunks from a collection

from fastapi import APIRouter, HTTPException

from backend.schemas import (
    AttackRequest,
    AttackResponse,
    CleanupRequest,
    CleanupResponse,
)
from backend.services.rag_service import retrieve, invalidate_cache
from backend.services.llm_service import generate_answer

router = APIRouter()


def _answer_changed(before: str, after: str) -> bool:
    """
    Simple heuristic: if the two answers share fewer than 40% of their
    words, the attack likely succeeded in changing the LLM's behaviour.
    """
    before_words = set(before.lower().split())
    after_words = set(after.lower().split())
    if not before_words or not after_words:
        return False
    overlap = len(before_words & after_words)
    union = len(before_words | after_words)
    jaccard = overlap / union
    return jaccard < 0.40


@router.post("/attack", response_model=AttackResponse)
def run_attack(req: AttackRequest):
    """
    Runs a full attack simulation:
      1. Retrieves chunks from the CLEAN system.
      2. (Optional) Generates a baseline LLM answer.
      3. Injects the malicious content.
      4. Retrieves chunks from the POISONED system.
      5. (Optional) Generates a poisoned LLM answer.
      6. Returns retrieval metrics + optional answer comparison.

    When include_llm=False, steps 2 and 5 are skipped entirely —
    no Gemini API calls are made, so quota is preserved.
    """

    # ── Step 1: Baseline retrieval from the CLEAN system ───────────
    before_chunks, _ = retrieve(
        req.query, req.strategy, req.top_k, req.collection
    )

    # ── Step 1b: Optional LLM generation on clean chunks ──────────
    before_answer = None
    if req.include_llm:
        from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError
        try:
            before_answer = generate_answer(req.query, before_chunks)
        except ResourceExhausted:
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit or quota exceeded. You have exceeded your free tier limits (20 requests per day per project). Please wait a while before trying again, or configure a different API key."
            )
        except GoogleAPICallError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API error: {str(e)}"
            )

    # ── Step 2: Inject the attack ───────────────────────────────────
    injected_text = ""
    poisoned_in_top_k = 0
    poison_ratio = 0.0

    if req.attack_type == "prompt_injection":
        from research.attacks.attack1_prompt_injection import (
            inject_prompt,
            measure_attack_success,
        )
        result = inject_prompt(
            req.collection,
            req.payload,
            template_index=req.template_index,
        )
        injected_text = result["injected_text"]

        # Measure how many poisoned chunks appear in top-k
        metrics = measure_attack_success(req.collection, req.query, req.top_k)
        poisoned_in_top_k = metrics["poisoned_count"]
        poison_ratio = metrics["poison_ratio"]

    elif req.attack_type == "kb_poisoning":
        from research.attacks.attack2_kb_poisoning import (
            inject_false_fact,
            measure_poison_retrieval_rank,
        )
        result = inject_false_fact(
            req.collection,
            req.payload,
            target_query=req.query,
        )
        injected_text = result["false_statement"]

        # Measure retrieval rank of the poison chunk
        metrics = measure_poison_retrieval_rank(
            req.collection, req.query, req.top_k
        )
        poisoned_in_top_k = metrics["poisoned_count"]
        poison_ratio = metrics["poison_ratio"]

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown attack_type '{req.attack_type}'. "
                   f"Valid options: 'prompt_injection', 'kb_poisoning'",
        )

    # Invalidate BM25/Hybrid caches so they see the new poisoned chunk
    invalidate_cache(req.collection)

    # ── Step 3: Retrieve from the POISONED system ──────────────────
    after_chunks, _ = retrieve(
        req.query, req.strategy, req.top_k, req.collection
    )

    # ── Step 3b: Optional LLM generation on poisoned chunks ────────
    after_answer = None
    succeeded = None
    if req.include_llm:
        from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError
        try:
            after_answer = generate_answer(req.query, after_chunks)
        except ResourceExhausted:
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit or quota exceeded. You have exceeded your free tier limits (20 requests per day per project). Please wait a while before trying again, or configure a different API key."
            )
        except GoogleAPICallError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API error: {str(e)}"
            )

        # ── Step 4: Determine if the attack changed the answer ─────
        succeeded = _answer_changed(before_answer, after_answer)

    return AttackResponse(
        attack_type=req.attack_type,
        injected_text=injected_text,
        before_answer=before_answer,
        after_answer=after_answer,
        before_chunks=before_chunks,
        after_chunks=after_chunks,
        poisoned_in_top_k=poisoned_in_top_k,
        poison_ratio=round(poison_ratio, 2),
        attack_succeeded=succeeded,
        include_llm=req.include_llm,
        collection=req.collection,
    )


@router.post("/cleanup", response_model=CleanupResponse)
def cleanup(req: CleanupRequest):
    """
    Removes all injected/poisoned chunks from the collection.
    Pass attack_type="all" to remove every attack type at once.
    """
    total_removed = 0

    if req.attack_type in ("prompt_injection", "all"):
        from research.attacks.attack1_prompt_injection import cleanup_attack1
        total_removed += cleanup_attack1(req.collection)

    if req.attack_type in ("kb_poisoning", "all"):
        from research.attacks.attack2_kb_poisoning import cleanup_attack2
        total_removed += cleanup_attack2(req.collection)

    if req.attack_type not in ("prompt_injection", "kb_poisoning", "all"):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown attack_type '{req.attack_type}'. "
                   f"Valid: 'prompt_injection', 'kb_poisoning', 'all'",
        )

    invalidate_cache(req.collection)

    return CleanupResponse(
        removed=total_removed,
        attack_type=req.attack_type,
        collection=req.collection,
    )


@router.get("/collection-stats")
def get_collection_stats(collection: str = "gpt2_paper"):
    try:
        from research.retrieval.base import get_or_create_collection
        coll = get_or_create_collection(collection)
        count = coll.count()
        return {"collection": collection, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
