"""Budget, substitution, quantity and price rules, plus the audit log."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.policy import (
    PolicyRules,
    PurchaseCheck,
    audit_log,
    evaluate,
    record,
    reset_log,
)

client = TestClient(app)
AT = datetime(2026, 10, 9, 23, 50, tzinfo=UTC)


def rules(**overrides) -> PolicyRules:
    payload = {
        "budget_cap": 100,
        "spent": 0,
        "max_qty": 6,
        "allowed_substitutions": ["cafe-molido"],
    }
    payload.update(overrides)
    return PolicyRules.model_validate(payload)


def check(**overrides) -> PurchaseCheck:
    payload = {
        "business_id": "cafe-aurora",
        "sku_id": "grano-1",
        "qty": 2,
        "unit_price": 10,
        "authorized_unit_price": 10,
        "substitution": None,
        "authorized_by": "owner-aurora",
        "reason": "reposición dentro del plan",
    }
    payload.update(overrides)
    return PurchaseCheck.model_validate(payload)


@pytest.fixture(autouse=True)
def clean_log():
    reset_log()
    yield
    reset_log()


def test_within_rules_allows_and_is_stable():
    verdict = evaluate(rules(), check())
    assert verdict.action == "allow"
    assert verdict.allowed is True
    assert evaluate(rules(), check()) == verdict
    assert audit_log() == []


def test_budget_cap_stops():
    verdict = evaluate(rules(spent=90), check(qty=2, unit_price=10))
    assert verdict.action == "stop"
    assert verdict.rule == "budget"


def test_disallowed_substitution_stops_and_allowed_one_passes():
    blocked = evaluate(rules(), check(substitution="te-negro"))
    assert blocked.rule == "substitution"
    allowed = evaluate(rules(), check(substitution="Cafe-Molido"))
    assert allowed.action == "allow"


def test_max_qty_stops():
    verdict = evaluate(rules(max_qty=1), check(qty=2))
    assert verdict.rule == "max_qty"


def test_price_change_outside_authorization_stops():
    verdict = evaluate(rules(), check(unit_price=12, authorized_unit_price=10))
    assert verdict.action == "stop"
    assert verdict.rule == "price"
    assert "autorizado" in verdict.reason


def test_missing_authorizer_stops():
    verdict = evaluate(rules(), check(authorized_by="  "))
    assert verdict.rule == "authorization"


def test_record_keeps_reason_time_and_authorizer():
    entry = record(rules(), check(), at=AT)
    assert entry["reason"] == "reposición dentro del plan"
    assert entry["at"] == AT.isoformat()
    assert entry["authorized_by"] == "owner-aurora"
    assert entry["demo_data"] is True
    assert audit_log() == [entry]


def test_audit_endpoint_returns_the_log():
    record(rules(), check(unit_price=12, authorized_unit_price=10), at=AT)
    response = client.get("/api/audit")
    assert response.status_code == 200
    body = response.json()
    assert body["demo_data"] is True
    assert len(body["entries"]) == 1
    entry = body["entries"][0]
    assert entry["action"] == "stop"
    assert entry["rule"] == "price"
    assert entry["authorized_by"] == "owner-aurora"
    assert entry["at"] == AT.isoformat()
