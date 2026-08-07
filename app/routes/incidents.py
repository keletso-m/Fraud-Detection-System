
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

# routes for incident management
@router.get("/", summary="List recent incidents")
def list_incidents(
    limit:     int = Query(50,  ge=1, le=500, description="Max incidents to return"),
    min_score: int = Query(0,   ge=0, le=100, description="Minimum risk score filter"),
     _=Depends(require_viewer),
):
    
    # returns recent incidents from the database the newest first


    incidents = get_incidents(limit=limit, min_score=min_score)
    return {"count": len(incidents), "incidents": incidents}

# return a single incident record by it s UUID
@router.get("/{incident_id}", summary="Get one incident by ID")
def get_incident(incident_id: str, _=Depends(require_viewer)):
    incident = get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    return incident

# return update incident state and severity
@router.patch("/{incident_id}/state", summary="Update incident state")
def patch_state(
    incident_id: int,
    body: StateUpdate,
    user: dict = Depends(require_admin),
): # transition the incident state and record in history
    ok = update_incident_state(incident_id, body.state, changed_by=user["username"])
    if not ok:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    return {"incident_id": incident_id, "state": body.state, "updated_by": user["username"]}

# return update incident severity
@router.patch("/{incident_id}/severity", summary="Update incident severity")
def patch_severity(
    incident_id: int,
    body: SeverityUpdate,
    user: dict = Depends(require_admin),
):
    #manually escalate or downgrade an incident's severity.

    ok = update_incident_severity(incident_id, body.severity, changed_by=user["username"])
    if not ok:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    return {"incident_id": incident_id, "severity": body.severity, "updated_by": user["username"]}

# return the full state and severity change history for an incident
@router.get("/{incident_id}/history", summary="Get incident audit trail")
def get_history(incident_id: int, _=Depends(require_viewer)):
    history = get_incident_history(incident_id)
    return {"incident_id": incident_id, "count": len(history), "history": history}