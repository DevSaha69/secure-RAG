# backend/routes/attack.py

from fastapi import APIRouter, HTTPException
from backend.schemas import AttackRequest, AttackResponse, CleanupRequest, CleanupResponse
from backend.services.rag_service import retrieve, invalidate_cache
from backend.services.llm_service import generate_answer

router = APIRouter()


@router.post("/attack", response_model=AttackResponse)
def run_attack(req: AttackRequest):
    # Step 1: Get the BEFORE answer (clean system)
    before_chunks, _ = retrieve(req.query, req.strategy, req.top_k, req.collection)
    
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

    # Step 2: Inject the attack
    injected_text = ""
    poisoned_in_top_k = 0

    if req.attack_type == "prompt_injection":
        from research.attacks.attack1_prompt_injection import inject_prompt
        result = inject_prompt(req.collection, req.payload)
        injected_text = result["injected_text"]

    elif req.attack_type == "kb_poisoning":
        from research.attacks.attack2_kb_poisoning import inject_false_fact, measure_poison_retrieval_rank
        result = inject_false_fact(req.collection, req.payload)
        injected_text = result["false_statement"]
        rank_result = measure_poison_retrieval_rank(req.collection, req.query, req.top_k)
        poisoned_in_top_k = rank_result["poisoned_in_top_k"]

    else:
        raise HTTPException(status_code=400, detail=f"Unknown attack type: {req.attack_type}")

    # Invalidate caches so BM25/Hybrid pick up poisoned chunks
    invalidate_cache(req.collection)

    # Step 3: Get the AFTER answer (poisoned system)
    after_chunks, _ = retrieve(req.query, req.strategy, req.top_k, req.collection)
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

    return AttackResponse(
        attack_type=req.attack_type,
        injected_text=injected_text,
        before_answer=before_answer,
        after_answer=after_answer,
        before_chunks=before_chunks,
        after_chunks=after_chunks,
        poisoned_in_top_k=poisoned_in_top_k,
        collection=req.collection,
    )


@router.post("/cleanup", response_model=CleanupResponse)
def cleanup(req: CleanupRequest):
    if req.attack_type == "prompt_injection":
        from research.attacks.attack1_prompt_injection import cleanup_attack1
        removed = cleanup_attack1(req.collection)
    elif req.attack_type == "kb_poisoning":
        from research.attacks.attack2_kb_poisoning import cleanup_attack2
        removed = cleanup_attack2(req.collection)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown attack type: {req.attack_type}")

    invalidate_cache(req.collection)
    return CleanupResponse(removed=removed, attack_type=req.attack_type)


@router.get("/collection-stats")
def get_collection_stats(collection: str = "gpt2_paper"):
    try:
        from research.retrieval.base import get_or_create_collection
        coll = get_or_create_collection(collection)
        count = coll.count()
        return {"collection": collection, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
