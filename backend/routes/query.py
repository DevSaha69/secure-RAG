# backend/routes/query.py

import time
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from backend.schemas import QueryRequest, QueryResponse
from backend.database import get_db, QueryLog
from backend.services.rag_service import retrieve
from backend.services.llm_service import generate_answer

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, request: Request, db: Session = Depends(get_db)):
    start = time.perf_counter()

    # Defense 4: Client rate limiting and query complexity check
    if req.defense_enabled:
        from research.defenses.defense4_rate_limiter import check_rate_limit, score_query_complexity
        client_ip = request.client.host if request.client else "127.0.0.1"
        rate_result = check_rate_limit(client_ip)
        if not rate_result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {rate_result['limit']} requests per {rate_result['window_seconds']}s window allowed."
            )
        
        complexity = score_query_complexity(req.query)
        if complexity["blocked"]:
            raise HTTPException(
                status_code=400,
                detail=f"Query blocked by complexity guard: {complexity['reason']}"
            )

    chunks, scores = retrieve(req.query, req.strategy, req.top_k, req.collection)

    # Defense 1: Prompt Sanitization (Filter out injected triggers)
    if req.defense_enabled:
        from research.defenses.defense1_prompt_sanitization import sanitize_chunks
        chunks, filtered_count = sanitize_chunks(chunks)
        # Re-align scores list length if some chunks were removed
        if filtered_count > 0:
            scores = scores[:len(chunks)]

    # Only call Gemini if include_llm is True
    answer = None
    if req.include_llm:
        from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError

        try:
            answer = generate_answer(req.query, chunks)
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

    elapsed_ms = (time.perf_counter() - start) * 1000

    db.add(QueryLog(
        query=req.query,
        strategy=req.strategy,
        answer=answer or "(retrieval only)",
        time_ms=elapsed_ms,
        chunks_used=len(chunks)
    ))
    db.commit()

    return QueryResponse(
        answer=answer,
        chunks=chunks,
        scores=scores,
        strategy=req.strategy,
        time_ms=round(elapsed_ms, 2),
        include_llm=req.include_llm,
    )


