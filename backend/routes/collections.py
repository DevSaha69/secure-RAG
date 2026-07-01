# backend/routes/collections.py

from fastapi import APIRouter, HTTPException
from research.retrieval.base import client
from backend.services.rag_service import invalidate_cache

router = APIRouter()


@router.get("/collections")
def list_collections():
    try:
        collections = client.list_collections()
        names = [c.name for c in collections]
        # Always ensure 'gpt2_paper' is at least present in the names list if it's the baseline default
        if "gpt2_paper" not in names:
            names.insert(0, "gpt2_paper")
        return {"collections": names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{name}")
def delete_collection(name: str):
    try:
        if name == "gpt2_paper":
            raise HTTPException(status_code=400, detail="Cannot delete the default 'gpt2_paper' collection.")
        
        client.delete_collection(name)
        invalidate_cache(name)
        return {"status": "success", "message": f"Collection '{name}' has been deleted."}
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
