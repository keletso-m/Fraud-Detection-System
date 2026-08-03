"""
    Submit a financial transaction for fraud scoring.
    Runs through transaction_scorer to risk_engine to alert_handler.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.auth.dependencies import require_admin
from engine.activity_detector import analyse as activity_analyse
from engine.transaction_scorer import score as tx_score
from engine.risk_engine import evaluate
from alerts.alert_handler import dispatch

# add slowapi imports for rate limiting
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger("sentinel.routes.transactions")
router = APIRouter()


# Request model

class TransactionEvent(BaseModel):
    account_id:      str        = Field(...,  example="ACC-001")
    amount:          float      = Field(...,  ge=0, example=25000.00)
    currency:        str        = Field("ZAR", example="ZAR")
    location:        str        = Field("",   example="London")
    last_location:   str        = Field("",   example="Johannesburg")
    device_id:       str        = Field("",   example="device-XYZ")
    known_devices:   list[str]  = Field([],   example=["device-ABC"])
    recent_tx_count: int        = Field(0,    ge=0, example=4)
    timestamp:       str        = Field(...,  example="2024-11-01T03:45:00")
    # Optional context fields
    username:        str        = Field("unknown", example="bob")
    ip_address:      str        = Field("unknown", example="10.0.0.1")


#  Route 

@router.post("/transaction", summary="Submit a financial transaction event")
def submit_transaction(event: TransactionEvent, _=Depends(require_admin)):
    """
    Score a financial transaction for fraud signals.

    Returns the full risk result including score, alert level, and reasons.
    The incident is persisted to the database automatically.
    """
    try:
        transaction_result = tx_score(event.model_dump())

        # Activity scorer gets a zero-score placeholder when only
        # a transaction event is submitted.
        activity_result = activity_analyse({
            "username":      event.username,
            "ip_address":    event.ip_address,
            "timestamp":     event.timestamp,
            "failed_logins": 0,
            "command":       "",
        })

        result = evaluate(
            activity_result,
            transaction_result,
            context={"username": event.username, "ip_address": event.ip_address},
        )

        dispatch(result)

        logger.info(
            "Transaction event processed | account=%s amount=%.2f score=%d level=%s",
            event.account_id, event.amount, result.risk_score, result.alert_level,
        )

        return result.to_dict()

    except Exception as exc:
        logger.error("Error processing transaction event: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to process transaction event.")