"""Record an agent decision and expose the audit log. No payment is sent."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app.services.policy import (
    PolicyError,
    PolicyRules,
    PurchaseCheck,
    audit_log,
    record,
)

router = APIRouter(tags=["policy"])


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: PolicyRules
    check: PurchaseCheck


@router.post("/api/policy/decisions")
def create_decision(request: DecisionRequest) -> dict:
    try:
        entry = record(request.rules, request.check, at=datetime.now(UTC))
    except PolicyError as exc:
        raise HTTPException(422, str(exc)) from exc
    return entry


@router.get("/api/audit")
def get_audit() -> dict:
    entries = audit_log()
    return {"entries": entries, "demo_data": True}
