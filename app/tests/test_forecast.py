from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.services.forecast import ForecastInput, forecast


@pytest.fixture
def recorded_input():
    return {"as_of": "2026-10-09", "demo_data": True,
            "products": [{"id": "coffee", "business_id": "cafe-1", "name": "Coffee",
                          "category": "coffee", "unit": "bag", "base_stock": 10,
                          "min_stock": 2, "max_stock": 20, "current_stock": 3,
                          "unit_cost": 4.25, "updated_at": "2026-10-09T12:00:00", "demo_data": True}],
            "sales": [{"sku_id": "coffee", "date": f"2026-10-{day:02}", "qty": 10,
                       "demo_data": True} for day in range(1, 10)],
            "signals": []}


def signal(direction="up", **changes):
    return dict({"id": "cold", "kind": "weather", "description": "Recorded cold weather signal",
                 "categories": ["coffee"], "direction": direction, "magnitude": 0.5,
                 "source": "Recorded synthetic weather fixture",
                 "valid_from": "2026-10-01", "valid_to": "2026-10-20", "demo_data": True}, **changes)


def run(data):
    return forecast(ForecastInput.model_validate(data))


def test_cold_raises_inverse_lowers_and_bounds(recorded_input):
    assert run(recorded_input)[0]["target"] == 10
    recorded_input["signals"] = [signal()]
    result = run(recorded_input)[0]
    assert result["target"] == 15 and result["demo_data"]
    assert any("Recorded synthetic" in reason for reason in result["reasons"])
    assert 0 <= result["confidence"] <= 1
    recorded_input["signals"] = [signal("down")]
    assert run(recorded_input)[0]["target"] == 5
    recorded_input["signals"] = [signal("down", id=f"down-{i}") for i in range(3)]
    assert run(recorded_input)[0]["target"] == 2
    recorded_input["signals"] = [signal(magnitude=0.5)]
    recorded_input["products"][0]["capacity"] = 12
    assert run(recorded_input)[0]["target"] == 12


@pytest.mark.parametrize("changes", [{"categories": ["filters"]}, {"valid_to": "2026-10-08"},
                                      {"valid_from": "2026-10-10"}])
def test_unrelated_or_inactive_signal_ignored(recorded_input, changes):
    recorded_input["signals"] = [signal(**changes)]
    assert run(recorded_input)[0]["target"] == 10


def test_duplicates_future_missing_days_and_order(recorded_input):
    recorded_input["sales"] = [{"sku_id": "coffee", "date": "2026-10-01", "qty": 4},
                               {"sku_id": "coffee", "date": "2026-10-01", "qty": 6},
                               {"sku_id": "coffee", "date": "2026-10-09", "qty": 20},
                               {"sku_id": "coffee", "date": "2026-10-10", "qty": 999}]
    assert run(recorded_input)[0]["target"] == 13  # 0.3*20 + 0.7*10; no zero-filled gap
    recorded_input["signals"] = [signal(), signal("down", id="event", kind="event")]
    first = run(recorded_input)
    recorded_input["sales"].reverse()
    recorded_input["signals"].reverse()
    assert run(recorded_input) == first == run(recorded_input)


def test_empty_history_and_safety_lead_time(recorded_input):
    recorded_input["sales"] = []
    assert run(recorded_input)[0]["target"] == 10
    assert run(recorded_input)[0]["confidence"] == 0
    recorded_input["sales"] = [{"sku_id": "coffee", "date": "2026-10-09", "qty": 4}]
    recorded_input["products"][0].update(lead_days=2, safety_stock=3)
    assert run(recorded_input)[0]["target"] == 11


def test_shared_budget_minimums_and_permutation(recorded_input):
    first = recorded_input["products"][0]
    first.update(current_stock=0, unit_price_cents=100)
    second = deepcopy(first)
    second["id"] = "filters"
    recorded_input["products"].append(second)
    recorded_input["budget_cap_cents"] = 700
    result = run(recorded_input)
    assert [r["target"] for r in result] == [5, 2]
    assert sum(r["target"] * 100 for r in result) <= 700
    recorded_input["products"].reverse()
    assert run(recorded_input) == result
    recorded_input["budget_cap_cents"] = 399
    with pytest.raises(ValueError, match="cannot fund minimum"):
        run(recorded_input)


@pytest.mark.parametrize("mutate", [
    lambda d: d["products"][0].update(min=21),
    lambda d: d["products"][0].update(capacity=1),
    lambda d: d["products"].append(deepcopy(d["products"][0])),
    lambda d: d["sales"][0].update(qty=float("nan")),
    lambda d: d["sales"][0].update(qty=-1),
    lambda d: d["sales"][0].update(sku_id="unknown"),
    lambda d: (d["products"][0].pop("unit_cost"), d.update(budget_cap_cents=100)),
    lambda d: d.update(signals=[signal(magnitude=0.6)]),
])
def test_reject_invalid_inputs(recorded_input, mutate):
    mutate(recorded_input)
    with pytest.raises(ValidationError):
        run(recorded_input)


def test_endpoint(recorded_input):
    client = TestClient(app)
    response = client.post("/api/businesses/cafe-1/forecast", json=recorded_input)
    assert response.status_code == 200
    assert response.json()["forecasts"][0]["target"] == 10
    assert response.json()["demo_data"] is True
    assert client.post("/api/businesses/other/forecast", json=recorded_input).status_code == 422
    recorded_input.update(budget_cap_cents=0)
    recorded_input["products"][0].update(current_stock=0, unit_price_cents=100)
    assert client.post("/api/businesses/cafe-1/forecast", json=recorded_input).status_code == 422
