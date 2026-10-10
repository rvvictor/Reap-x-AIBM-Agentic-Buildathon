from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.signals import (
    ExtractionRequest,
    Signal,
    SignalError,
    demo_signals,
    extract_signals,
)

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("", response_model=list[Signal])
def list_signals() -> list[Signal]:
    if not settings.demo_mode:
        raise HTTPException(409, "En vivo, envía fuentes a /api/signals/extract.")
    return demo_signals()


@router.post("/extract", response_model=list[Signal])
async def extract(request: ExtractionRequest) -> list[Signal]:
    try:
        return await extract_signals(request)
    except SignalError as exc:
        raise HTTPException(502, str(exc)) from exc
