import logging
from fastapi import APIRouter, HTTPException, Query, Depends

from engine.risk_engine import get_entity_history
from app.auth.dependencies import require_viewer

logger = logging.getLogger("sentinel.routes.entities")
router = APIRouter()


@router.get("/users/{username}", summary="Get incident history for a user")
def get_user_history(
    username: str,
    limit: int = Query(50, ge=1, le=500, description="Max incidents to return"),
    _=Depends(require_viewer),
):
    """Return all incidents and aggregated statistics for a given username."""
    result = get_entity_history("username", username, limit=limit)
    if result["count"] == 0:
        raise HTTPException(status_code=404, detail=f"No incidents found for user '{username}'")
    return result


@router.get("/ips/{ip_address}", summary="Get incident history for an IP address")
def get_ip_history(
    ip_address: str,
    limit: int = Query(50, ge=1, le=500, description="Max incidents to return"),
    _=Depends(require_viewer),
):
    """Return all incidents and aggregated stats for a given IP address"""
    result = get_entity_history("ip_address", ip_address, limit=limit)
    if result["count"] == 0:
        raise HTTPException(status_code=404, detail=f"No incidents found for IP '{ip_address}'")
    return result