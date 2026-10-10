"""Group checkout. One Reap enrollment, one internal book per business."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app.integrations.reap.client import ReapConfigError
from app.services.global_agent import proposal_store
from app.services.payments import (
    PaymentError,
    authorize,
    checkout,
    confirm_enrollment,
    enroll,
    get_client,
    open_ledger,
)
from app.services.payments import ledgers as payment_ledgers

router = APIRouter(prefix="/api/payments", tags=["payments"])


class LedgerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: str


class AuthorizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    business_id: str


class EnrollmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    owner_id: str
    email: str
    return_url: str


class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    demo_return: bool = False


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: str
    enrollment_id: str
    variant_id: str
    email: str
    return_url: str = "https://bodega.demo/payments/return"


def _guard(action):
    try:
        return action()
    except PaymentError as exc:
        raise HTTPException(422, str(exc)) from exc
    except ReapConfigError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/ledgers/{proposal_id}")
def get_ledger(proposal_id: str) -> dict:
    ledger = payment_ledgers.get(proposal_id)
    if ledger is None:
        raise HTTPException(404, "ledger not found")
    return ledger


@router.post("/ledgers")
def create_ledger(request: LedgerRequest) -> dict:
    proposal = proposal_store.get(request.proposal_id)
    if proposal is None:
        raise HTTPException(404, "proposal not found")
    return _guard(lambda: open_ledger(proposal))


@router.post("/ledgers/{proposal_id}/authorizations")
def authorize_share(proposal_id: str, request: AuthorizationRequest) -> dict:
    return _guard(lambda: authorize(proposal_id, request.business_id))


@router.post("/enrollments")
def create_enrollment(request: EnrollmentRequest) -> dict:
    return _guard(
        lambda: enroll(
            get_client(),
            owner_id=request.owner_id,
            email=request.email,
            return_url=request.return_url,
        )
    )


@router.post("/enrollments/{enrollment_id}/confirm")
def confirm(enrollment_id: str, request: ConfirmRequest) -> dict:
    return _guard(
        lambda: confirm_enrollment(get_client(), enrollment_id, demo_return=request.demo_return)
    )


@router.post("/checkouts")
def create_payment(request: CheckoutRequest) -> dict:
    return _guard(
        lambda: checkout(
            get_client(),
            request.proposal_id,
            request.enrollment_id,
            variant_id=request.variant_id,
            email=request.email,
            return_url=request.return_url,
        )
    )
