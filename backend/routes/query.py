# backend/routes/query.py

import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.schemas import QueryRequest, QueryResponse
from backend.database import get_db, QueryLog
from backend.services.rag_service import retrieve
from backend.services.llm_service import generate_answer

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, db: Session = Depends(get_db)):
    start = time.perf_counter()

    chunks, scores = retrieve(req.query, req.strategy, req.top_k, req.collection)
    
    from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError
    from fastapi import HTTPException

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
        answer=answer,
        time_ms=elapsed_ms,
        chunks_used=len(chunks)
    ))
    db.commit()

    return QueryResponse(
        answer=answer,
        chunks=chunks,
        scores=scores,
        strategy=req.strategy,
        time_ms=round(elapsed_ms, 2)
    )
