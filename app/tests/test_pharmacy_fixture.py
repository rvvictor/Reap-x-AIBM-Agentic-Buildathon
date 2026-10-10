import json
import runpy
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import Signal
from app.schemas.loader import load_businesses, load_products, load_sales
from app.services.forecast import ForecastInput, forecast

FOLDER = Path(__file__).resolve().parents[1] / "fixtures" / "pharmacy"
BID = "farmacia-demo"
AS_OF = date(2026, 10, 9)


def request_data():
    business = load_businesses("pharmacy")[0]
    return ForecastInput.model_validate({
        "products": [p.model_dump(mode="json") for p in load_products("pharmacy", BID)],
        "sales": [s.model_dump(mode="json") for s in load_sales("pharmacy", BID)],
        "signals": [Signal.model_validate(s).model_dump(mode="json")
                    for s in json.loads((FOLDER / "signals.json").read_text())],
        "as_of": AS_OF, "alpha": 0.3, "currency": "MXN",
        "budget_cap_cents": round(business.budget_cap * 100), "demo_data": True,
    })


def targets(request):
    return {r["sku_id"]: r["target"] for r in forecast(request)}


def test_canonical_catalog_and_demo_provenance():
    businesses = load_businesses("pharmacy")
    products = load_products("pharmacy", BID)
    assert len(businesses) == 1 and businesses[0].vertical == "pharmacy"
    assert businesses[0].id == BID and businesses[0].demo_data is True
    assert len(products) == len({p.id for p in products}) == 10
    assert {"Paracetamol", "Antigripal", "Claritromicina", "Antiácido"} <= {p.name for p in products}
    assert all(p.business_id == BID and p.demo_data is True for p in products)
    assert all(p.base_stock == 10 and p.min_stock == 2 and p.max_stock == 40 for p in products)
    assert load_products("pharmacy", "not-a-business") == []
    assert load_sales("pharmacy", "not-a-business") == []


def test_complete_unique_history_and_synthetic_cold_peak():
    request = request_data()
    assert len(request.sales) == len({(s.sku_id, s.date) for s in request.sales}) == 300
    assert all(s.demo_data is True and s.date <= AS_OF for s in request.sales)
    for p in request.products:
        days = {s.date for s in request.sales if s.sku_id == p.id}
        assert len(days) == 30 and min(days) == date(2026, 9, 10) and max(days) == AS_OF
    cold_start = date(2026, 9, 17)
    antigripal = [s for s in request.sales if s.sku_id == f"{BID}:antigripal"]
    assert {s.qty for s in antigripal if s.date < cold_start} == {8}
    assert {s.qty for s in antigripal if s.date >= cold_start} == {16}
    assert all(s.demo_data is True and s.valid_from == cold_start and s.valid_to == AS_OF
               and "sintético" in s.source for s in request.signals)


def test_same_engine_reaches_twenty_and_five_without_clamping():
    request = request_data()
    result = forecast(request)
    assert targets(request)[f"{BID}:antigripal"] == 20
    assert targets(request)[f"{BID}:antiacido"] == 5
    products = {p.id: p for p in request.products}
    for row in result:
        assert row["base"] == 10 and row["demo_data"] is True
        assert products[row["sku_id"]].min <= row["target"] <= products[row["sku_id"]].max
        assert 0 <= row["confidence"] <= 1
    assert any("pharmacy-cold-demo" in reason for row in result for reason in row["reasons"])
    assert any("pharmacy-digestive-demo" in reason for row in result for reason in row["reasons"])


def test_signals_are_effective_and_category_scoped():
    request = request_data()
    with_signals = targets(request)
    without_signals = targets(request.model_copy(update={"signals": []}))
    assert without_signals[f"{BID}:antigripal"] == 16
    assert without_signals[f"{BID}:antiacido"] == 10
    for sku in without_signals.keys() - {f"{BID}:antigripal", f"{BID}:antiacido"}:
        assert with_signals[sku] == without_signals[sku]
    expired = [s.model_copy(update={"valid_to": date(2026, 10, 8)}) for s in request.signals]
    assert targets(request.model_copy(update={"signals": expired})) == without_signals


def test_budget_and_existing_http_forecast_contract():
    request = request_data()
    result = forecast(request)
    products = {p.id: p for p in request.products}
    replenishment = sum(max(0, r["target"] - products[r["sku_id"]].current_stock)
                        * products[r["sku_id"]].price_cents for r in result)
    assert replenishment <= request.budget_cap_cents == 1_000_000
    with TestClient(app) as client:
        response = client.post(f"/api/businesses/{BID}/forecast", json=request.model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json()["business_id"] == BID and response.json()["demo_data"] is True
    assert response.json()["forecasts"] == result


@pytest.mark.parametrize("budget_cents", [0, 12000])
def test_binding_budget_reduces_pharmacy_replenishment(budget_cents):
    request = request_data()
    original = targets(request)
    products = {p.id: p for p in request.products}
    original_spend = sum(max(0, target - products[sku].current_stock)
                         * products[sku].price_cents for sku, target in original.items())
    assert original_spend > budget_cents
    limited = targets(request.model_copy(update={"budget_cap_cents": budget_cents}))
    assert any(limited[sku] < original[sku] for sku in limited)
    spend = sum(max(0, target - products[sku].current_stock)
                * products[sku].price_cents for sku, target in limited.items())
    assert spend <= budget_cents
    assert all(products[sku].min <= target <= products[sku].max for sku, target in limited.items())


def test_generator_reproduces_only_pharmacy_files(tmp_path):
    cafe = FOLDER.parent / "businesses"
    cafe_before = {p.name: p.read_bytes() for p in cafe.glob("*.json")}
    generator = runpy.run_path(str(FOLDER / "generate.py"))
    generated = generator["fixture_data"]()
    assert generated == generator["fixture_data"]()
    for name, records in generated.items():
        assert records == json.loads((FOLDER / f"{name}.json").read_text())
    generator["main"].__globals__["OUT"] = tmp_path
    generator["main"]()
    assert {p.name for p in tmp_path.iterdir()} == {f"{name}.json" for name in generated}
    assert all(json.loads((tmp_path / f"{name}.json").read_text()) == records
               for name, records in generated.items())
    assert {p.name: p.read_bytes() for p in cafe.glob("*.json")} == cafe_before
