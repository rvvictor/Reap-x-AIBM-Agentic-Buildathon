"""Stateless calculation endpoint; caller supplies recorded fixtures, never keys.

Provisional adapter until HACK-002 lands. Inputs are not persisted inventory or
authorization to purchase. Prices and budget share request.currency.
"""

from fastapi import APIRouter, HTTPException

from app.services.forecast import ForecastInput, forecast

router = APIRouter(prefix="/api/businesses", tags=["forecast"])


@router.post("/{business_id}/forecast")
def business_forecast(business_id: str, request: ForecastInput):
    if any(product.business_id != business_id for product in request.products):
        raise HTTPException(422, "every product must belong to the requested business")
    try:
        forecasts = forecast(request)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"business_id": business_id, "as_of": request.as_of, "forecasts": forecasts,
            "demo_data": request.demo_data or any(f["demo_data"] for f in forecasts)}
