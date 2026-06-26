# backend/routes/upload.py

import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader

from backend.schemas import UploadResponse
from research.chunker import chunk_text
from research.retrieval.base import get_or_create_collection, embed
from backend.services.rag_service import invalidate_cache

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...), collection: str = "gpt2_paper"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    reader = PdfReader(tmp_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    os.unlink(tmp_path)

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No extractable text was found in the uploaded PDF. Please make sure it is a text-based PDF, not a scanned image."
        )

    coll = get_or_create_collection(collection)
    embeddings = embed(chunks)
    ids = [f"{file.filename}_chunk_{i}" for i in range(len(chunks))]

    coll.add(documents=chunks, embeddings=embeddings, ids=ids)

    # BM25/Hybrid must rebuild their index now that new chunks exist
    invalidate_cache(collection)

    return UploadResponse(
        filename=file.filename,
        chunks_stored=len(chunks),
        collection=collection
    )
