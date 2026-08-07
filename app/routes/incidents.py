
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Literal
from engine.risk_engine import (
    get_incidents,
    get_incident_by_id,
    update_incident_state,
    update_incident_severity,
    get_incident_history,
)
from app.auth.dependencies import require_viewer, require_admin


logger = logging.getLogger("sentinel.routes.incidents")
router = APIRouter()

# request models
class StateUpdate(BaseModel):
    state: Literal["open", "investigating", "resolved", "false_positive"]


class SeverityUpdate(BaseModel):
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


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