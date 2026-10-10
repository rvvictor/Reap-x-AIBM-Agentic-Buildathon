from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.backtest import backtest
from app.services.forecast import ForecastInput


def scenario(quantities, **product_changes):
    return {
        "products": [{"id": "coffee", "business_id": "cafe-test", "category": "coffee",
                      "unit": "bag", "base_stock": 10, "min": 0, "max": 100,
                      "current_stock": 50, **product_changes}],
        "sales": [{"sku_id": "coffee", "date": f"2026-10-{day:02}", "qty": qty}
                  for day, qty in enumerate(quantities, 1)],
        "as_of": "2026-10-20", "alpha": 1,
    }


def run(payload):
    return backtest(ForecastInput.model_validate(payload))


def test_known_arithmetic_and_dynamic_can_be_worse():
    result = run(scenario([4, 8, 0]))
    product = result["products"][0]
    assert [day["dynamic_target"] for day in product["daily"]] == [10, 4, 8]
    assert product["fixed"] == {"lost_sales": 0, "surplus": 18}
    assert product["dynamic"] == {"lost_sales": 4, "surplus": 14}
    assert product["difference"] == {"lost_sales": -4, "surplus": 4}
    assert result["demo_data"] is True and result["source"] == "simulated"
    assert set(result["formula"]) == {"dynamic_target", "fixed_target", "lost_sales", "surplus", "difference"}


def test_dynamic_reduces_lost_sales_in_a_known_synthetic_case():
    product = run(scenario([12, 12, 12]))["products"][0]
    assert product["fixed"]["lost_sales"] == 6
    assert product["dynamic"]["lost_sales"] == 2
    assert product["difference"]["lost_sales"] == 4


def test_current_day_and_future_sales_cannot_change_earlier_decisions():
    payload = scenario([4, 8, 0])
    before = run(payload)["products"][0]["daily"]
    payload["sales"][1]["qty"] = 999
    payload["sales"].append({"sku_id": "coffee", "date": "2026-10-21", "qty": 9999})
    after = run(payload)["products"][0]["daily"]
    assert after[0] == before[0]
    assert after[1]["dynamic_target"] == before[1]["dynamic_target"] == 4
    assert after[2]["dynamic_target"] == 100  # Yesterday's spike is now eligible.
    assert len(after) == 3  # Future record beyond as_of is excluded entirely.
    assert all(day["history_through"] < day["date"] for day in after)


def test_gaps_duplicates_and_order_are_handled_without_filling_zero_days():
    payload = scenario([4])
    payload["sales"] += [{"sku_id": "coffee", "date": "2026-10-01", "qty": 2},
                         {"sku_id": "coffee", "date": "2026-10-05", "qty": 0}]
    expected = run(payload)
    payload["sales"].reverse()
    assert run(payload) == expected
    days = expected["products"][0]["daily"]
    assert len(days) == 2 and days[0]["demand"] == 6
    assert days[1]["dynamic_target"] == 6


def test_units_stay_per_sku_and_inventory_snapshot_does_not_leak():
    payload = scenario([4, 8])
    other = deepcopy(payload["products"][0])
    other.update(id="filters", unit="box", current_stock=0)
    payload["products"].append(other)
    before = run(payload)
    payload["products"][0].update(current_stock=999, updated_at="2030-01-01T12:00:00")
    payload["products"].reverse()
    assert run(payload) == before
    assert before["products"][1]["unit"] == "box"
    assert before["products"][1]["observed_days"] == 0


def test_both_policies_respect_same_bounds_and_engine_uses_alpha():
    payload = scenario([4, 8, 100], min=3, max=20, capacity=12)
    payload["alpha"] = 0.5
    days = run(payload)["products"][0]["daily"]
    assert [day["dynamic_target"] for day in days] == [10, 4, 6]
    assert all(3 <= day[strategy] <= 12 for day in days
               for strategy in ("fixed_target", "dynamic_target"))
    assert run(scenario([100], base_stock=50, capacity=12))["products"][0]["daily"][0]["fixed_target"] == 12


def test_empty_history_is_explicit_zero_observations():
    product = run(scenario([]))["products"][0]
    assert product["observed_days"] == 0 and product["daily"] == []
    assert product["fixed"] == product["dynamic"] == {"lost_sales": 0, "surplus": 0}


def test_minimum_date_is_rejected_clearly_instead_of_overflowing():
    payload = scenario([4])
    payload["sales"][0]["date"] = "0001-01-01"
    with pytest.raises(ValueError, match="previous calendar day"):
        run(payload)


def test_signals_and_budgets_are_rejected_instead_of_assuming_historical_authority():
    payload = scenario([4], unit_price_cents=100)
    payload["budget_cap_cents"] = 1000
    with pytest.raises(ValueError, match="backtest excludes"):
        run(payload)
    payload.pop("budget_cap_cents")
    payload["signals"] = [{"id": "cold", "kind": "weather", "description": "Synthetic",
                           "categories": ["coffee"], "direction": "up", "magnitude": 0.2,
                           "source": "simulated", "valid_from": "2026-10-01", "valid_to": "2026-10-20"}]
    with pytest.raises(ValueError, match="backtest excludes"):
        run(payload)


def test_endpoint_is_registered_and_returns_simulated_per_sku_comparison():
    client = TestClient(app)
    response = client.get("/api/backtest/cafe-aurora")
    assert response.status_code == 200
    result = response.json()
    assert result["business_id"] == "cafe-aurora" and result["demo_data"] is True
    assert result["formula"] and result["assumptions"]
    assert len(result["products"]) == 8
    assert all(product["observed_days"] == 90 and product["demo_data"]
               for product in result["products"])
    for product in result["products"]:
        for strategy in ("fixed", "dynamic"):
            for metric in ("lost_sales", "surplus"):
                assert product[strategy][metric] == sum(day[strategy][metric] for day in product["daily"])
    assert client.get("/api/backtest/not-a-business").status_code == 404
