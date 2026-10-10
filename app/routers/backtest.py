"""Read-only backtest of the shipped synthetic business history."""

from datetime import date

from fastapi import APIRouter, HTTPException

from app.schemas.loader import load_businesses, load_products, load_sales
from app.services.backtest import backtest
from app.services.forecast import ForecastInput

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.get("/{business_id}")
def business_backtest(business_id: str):
    if business_id not in {business.id for business in load_businesses()}:
        raise HTTPException(404, "Business not found in simulated fixtures")
    products = load_products(business_id=business_id)
    if not products:
        raise HTTPException(422, "No products in simulated business history")
    sales = load_sales(business_id=business_id)
    request = ForecastInput.model_validate({
        "products": [product.model_dump() for product in products],
        "sales": [sale.model_dump() for sale in sales],
        "as_of": max((sale.date for sale in sales), default=date(1970, 1, 1)),
        "demo_data": True,
    })
    return {"business_id": business_id, **backtest(request)}
