"""Internal split, enrollment gate, and checkout reconciliation."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import Allocation, Business, Proposal
from app.services.global_agent import proposal_store
from app.services.payments import (
    PaymentError,
    authorize,
    checkout,
    confirm_enrollment,
    enroll,
    open_ledger,
    reset_state,
)

client = TestClient(app)
NOW = datetime(2026, 10, 9, tzinfo=UTC)
VARIANT = "3c90c3cc-0d44-4b50-8888-8dd25736052a"
HTTPS = "https://bodega.demo/payments/return"


class FakeReap:
    def __init__(self) -> None:
        self.demo_mode = True
        self.demo_authorized_amount: float | None = None
        self.calls: list[str] = []
        self.enrollment_status = "REQUIRES_ACTION"
        self.quote_amount: float | None = None
        self.quote_expires = "2099-01-01T00:00:00Z"
        self.quote_status = "OPEN"
        self.final_amount: float | None = None
        self.checkout_status = "COMPLETED"
        self.enroll_payload: dict | None = None

    def create_enrollment(self, *, owner_id, email, return_url, idempotency_key):
        self.calls.append("enroll")
        self.enroll_payload = {
            "source": "EXTERNAL",
            "owner_id": owner_id,
            "email": email,
            "return_url": return_url,
            "idempotency_key": idempotency_key,
        }
        return {
            "status": 200,
            "body": {
                "id": "enr-1",
                "status": "REQUIRES_ACTION",
                "source": "EXTERNAL",
                "presentation": {"type": "REDIRECT", "returnUrl": return_url},
            },
        }

    def get_enrollment(self, enrollment_id):
        self.calls.append("get_enrollment")
        return {"status": 200, "body": {"id": enrollment_id, "status": self.enrollment_status}}

    def activate_demo(self, enrollment_id):
        self.enrollment_status = "ACTIVE"

    def create_quote(self, variant_id, *, email, idempotency_key=None):
        self.calls.append("quote")
        amount = self.demo_authorized_amount if self.quote_amount is None else self.quote_amount
        return {
            "status": 200,
            "body": {
                "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "status": self.quote_status,
                "expiresAt": self.quote_expires,
                "amount": {"amount": amount, "currency": "MXN"},
            },
        }

    def create_checkout(self, quote_id, enrollment_id, *, idempotency_key=None, return_url=None):
        self.calls.append("checkout")
        amount = self.demo_authorized_amount if self.final_amount is None else self.final_amount
        self._order = {
            "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "status": self.checkout_status,
            "quoteId": quote_id,
            "enrollmentId": enrollment_id,
            "orderId": "order-1",
            "finalAmount": {"amount": amount, "currency": "MXN"},
        }
        return {"status": 200, "body": self._order}

    def get_checkout(self, checkout_id):
        self.calls.append("get_checkout")
        return {"status": 200, "body": self._order}


def proposal() -> Proposal:
    return Proposal(
        id="proposal-test",
        category="cafe-grano",
        supplier="demo",
        total=30,
        individual_total=40,
        savings_total=10,
        allocations=[
            Allocation(
                business_id="cafe-aurora",
                sku_id="cafe-aurora:grano",
                qty=1,
                cost=10,
                individual_cost=15,
                savings=5,
            ),
            Allocation(
                business_id="cafe-brasa",
                sku_id="cafe-brasa:grano",
                qty=2,
                cost=20,
                individual_cost=25,
                savings=5,
            ),
        ],
        demo_data=True,
    )


def businesses() -> list[Business]:
    return [
        Business(id="cafe-aurora", name="Aurora", vertical="cafeteria", location="CDMX", budget_cap=15),
        Business(id="cafe-brasa", name="Brasa", vertical="cafeteria", location="CDMX", budget_cap=25),
    ]


@pytest.fixture(autouse=True)
def clean():
    reset_state()
    proposal_store.pop("proposal-test", None)
    yield
    reset_state()
    proposal_store.pop("proposal-test", None)


def ready_ledger():
    ledger = open_ledger(proposal(), businesses())
    authorize(ledger["proposal_id"], "cafe-aurora")
    authorize(ledger["proposal_id"], "cafe-brasa")
    return ledger


def test_http_return_url_is_rejected_before_enrollment():
    fake = FakeReap()
    with pytest.raises(PaymentError, match="HTTPS"):
        enroll(fake, owner_id="bodega", email="ops@bodega.example", return_url="http://localhost/return")
    assert fake.calls == []


def test_enrollment_is_external_and_inactive_until_confirmed():
    fake = FakeReap()
    created = enroll(fake, owner_id="bodega", email="ops@bodega.example", return_url=HTTPS)
    assert fake.enroll_payload["source"] == "EXTERNAL"
    assert fake.enroll_payload["return_url"] == HTTPS
    with pytest.raises(PaymentError, match="ACTIVE"):
        confirm_enrollment(fake, created["id"])
    confirmed = confirm_enrollment(fake, created["id"], demo_return=True)
    assert confirmed["status"] == "ACTIVE"


def test_checkout_requires_every_authorization_and_an_active_enrollment():
    fake = FakeReap()
    ledger = open_ledger(proposal(), businesses())
    authorize(ledger["proposal_id"], "cafe-aurora")
    enroll(fake, owner_id="bodega", email="ops@bodega.example", return_url=HTTPS)
    confirm_enrollment(fake, "enr-1", demo_return=True)
    with pytest.raises(PaymentError, match="authorization"):
        checkout(fake, ledger["proposal_id"], "enr-1", variant_id=VARIANT, email="ops@bodega.example", now=NOW)
    authorize(ledger["proposal_id"], "cafe-brasa")
    fake.enrollment_status = "REQUIRES_ACTION"
    with pytest.raises(PaymentError, match="ACTIVE"):
        checkout(fake, ledger["proposal_id"], "enr-1", variant_id=VARIANT, email="ops@bodega.example", now=NOW)
    assert "checkout" not in fake.calls


def test_share_above_budget_cap_cannot_be_authorized():
    tight = businesses()
    tight[0] = tight[0].model_copy(update={"budget_cap": 9})
    ledger = open_ledger(proposal(), tight)
    with pytest.raises(PaymentError, match="budget cap"):
        authorize(ledger["proposal_id"], "cafe-aurora")
    assert ledger["shares"][0]["approved"] is False


def test_reconciles_order_final_amount_against_the_internal_split():
    fake = FakeReap()
    ledger = ready_ledger()
    enroll(fake, owner_id="bodega", email="ops@bodega.example", return_url=HTTPS)
    confirm_enrollment(fake, "enr-1", demo_return=True)
    done = checkout(fake, ledger["proposal_id"], "enr-1", variant_id=VARIANT, email="ops@bodega.example", now=NOW)
    assert done["status"] == "reconciled"
    assert done["final_amount"] == 30
    assert done["order_id"] == "order-1"
    assert done["authorized_total"] == 30
    assert fake.calls[-2:] == ["checkout", "get_checkout"]


def test_expired_quote_stops_before_checkout_and_asks_for_approval():
    fake = FakeReap()
    fake.quote_expires = "2020-01-01T00:00:00Z"
    ledger = ready_ledger()
    enroll(fake, owner_id="bodega", email="ops@bodega.example", return_url=HTTPS)
    confirm_enrollment(fake, "enr-1", demo_return=True)
    stopped = checkout(fake, ledger["proposal_id"], "enr-1", variant_id=VARIANT, email="ops@bodega.example", now=NOW)
    assert stopped["status"] == "needs_approval"
    assert stopped["reason"] == "quote expired"
    assert all(row["approved"] is False for row in stopped["shares"])
    assert "checkout" not in fake.calls


def test_final_amount_outside_authorization_asks_for_approval():
    fake = FakeReap()
    fake.final_amount = 31
    ledger = ready_ledger()
    enroll(fake, owner_id="bodega", email="ops@bodega.example", return_url=HTTPS)
    confirm_enrollment(fake, "enr-1", demo_return=True)
    stopped = checkout(fake, ledger["proposal_id"], "enr-1", variant_id=VARIANT, email="ops@bodega.example", now=NOW)
    assert stopped["status"] == "needs_approval"
    assert stopped["reason"] == "finalAmount differs from authorized split"
    assert stopped["final_amount"] == 31
    assert "get_checkout" in fake.calls


def test_router_demo_checkout_uses_the_reap_client(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    proposal_store["proposal-test"] = proposal()
    # Budget caps on the fixture businesses are higher than these shares.
    open_ledger(proposal())
    authorize("proposal-test", "cafe-aurora")
    authorize("proposal-test", "cafe-brasa")
    created = client.post(
        "/api/payments/enrollments",
        json={"owner_id": "bodega", "email": "ops@bodega.example", "return_url": HTTPS},
    )
    assert created.status_code == 200
    body = created.json()
    assert body["source"] == "EXTERNAL"
    assert body["status"] == "REQUIRES_ACTION"
    blocked = client.post(
        "/api/payments/checkouts",
        json={
            "proposal_id": "proposal-test",
            "enrollment_id": body["id"],
            "variant_id": VARIANT,
            "email": "ops@bodega.example",
            "return_url": HTTPS,
        },
    )
    assert blocked.status_code == 422
    confirmed = client.post(
        f"/api/payments/enrollments/{body['id']}/confirm",
        json={"demo_return": True},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "ACTIVE"
    paid = client.post(
        "/api/payments/checkouts",
        json={
            "proposal_id": "proposal-test",
            "enrollment_id": body["id"],
            "variant_id": VARIANT,
            "email": "ops@bodega.example",
            "return_url": HTTPS,
        },
    )
    assert paid.status_code == 200
    ledger = paid.json()
    assert ledger["status"] == "reconciled"
    assert ledger["final_amount"] == ledger["authorized_total"]
    assert ledger["order_id"]
    assert ledger["demo_data"] is True
