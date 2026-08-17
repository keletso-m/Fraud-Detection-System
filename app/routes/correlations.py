import logging
from fastapi import APIRouter, Depends

from engine.correlator import correlate
from app.auth.dependencies import require_viewer

logger = logging.getLogger("sentinel.routes.correlations")
router = APIRouter()


@router.get("/", summary="Run correlation analysis on recent incidents")
def get_correlations(_=Depends(require_viewer)):
    """
    Analyse incidents from the last 60 minutes and return correlated groups
    """
    groups = correlate()
    return {
        "window_minutes": 60,
        "group_count":    len(groups),
        "correlations":   groups,
    }