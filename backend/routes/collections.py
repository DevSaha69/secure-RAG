# backend/routes/collections.py

from fastapi import APIRouter, HTTPException
from research.retrieval.base import client
from backend.services.rag_service import invalidate_cache
from backend.schemas import CollectionHealthResponse

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


@router.get("/health", response_model=CollectionHealthResponse)
def collection_health(collection: str = "gpt2_paper"):
    from research.defenses.defense3_collection_health import get_collection_health
    try:
        return get_collection_health(collection)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomaly-scan")
def anomaly_scan(collection: str = "gpt2_paper"):
    from research.defenses.defense2_anomaly_detection import scan_collection_for_anomalies
    try:
        flagged = scan_collection_for_anomalies(collection)
        return {"collection": collection, "flagged_count": len(flagged), "flagged": flagged}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

