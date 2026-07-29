
import logging
from fastapi import APIRouter, HTTPException, Query, Depends

from engine.risk_engine import get_incidents, get_incident_by_id
from app.auth.dependencies import require_viewer

logger = logging.getLogger("sentinel.routes.incidents")
router = APIRouter()


@router.get("/", summary="List recent incidents")
def list_incidents(
    limit:     int = Query(50,  ge=1, le=500, description="Max incidents to return"),
    min_score: int = Query(0,   ge=0, le=100, description="Minimum risk score filter"),
     _=Depends(require_viewer),
):
    
    # returns recent incidents from the database the newest first


    incidents = get_incidents(limit=limit, min_score=min_score)
    return {"count": len(incidents), "incidents": incidents}


@router.get("/{incident_id}", summary="Get one incident by ID")
def get_incident(incident_id: str, _=Depends(require_viewer)):
    """Return a single incident record by its UUID."""
    incident = get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    return incident