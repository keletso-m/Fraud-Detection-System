
import logging
from fastapi import APIRouter, HTTPException, Query

from engine.risk_engine import get_incidents, get_incident_by_id

logger = logging.getLogger("sentinel.routes.incidents")
router = APIRouter()


@router.get("/", summary="List recent incidents")
def list_incidents(
    limit:     int = Query(50,  ge=1, le=500, description="Max incidents to return"),
    min_score: int = Query(0,   ge=0, le=100, description="Minimum risk score filter"),
):
    """
    Return recent incidents from the database, newest first.

    Use `min_score` to filter — e.g. `?min_score=75` returns only CRITICAL incidents.
    """
    incidents = get_incidents(limit=limit, min_score=min_score)
    return {"count": len(incidents), "incidents": incidents}


@router.get("/{incident_id}", summary="Get one incident by ID")
def get_incident(incident_id: str):
    """Return a single incident record by its UUID."""
    incident = get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    return incident