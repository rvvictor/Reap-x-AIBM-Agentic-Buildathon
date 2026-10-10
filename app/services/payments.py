"""Internal payment book for a group purchase.

Reap stores one card on an enrollment. Each business authorizes only its share,
capped by ``budget_cap``. Checkout calls the HACK-003 client and then reads the
checkout. A price change or an expired quote clears approvals.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol

import httpx

from app.integrations.reap.client import ReapClient, ReapConfigError
from app.schemas import Business, Proposal
from app.schemas.loader import load_businesses
from app.services.global_agent import CENT, money, proposal_store

DEMO_RETURN = "https://bodega.demo/payments/return"


class PaymentError(ValueError):
    """A rule stopped the payment before or after Reap was called."""


class PaymentsClient(Protocol):
    demo_mode: bool
    demo_authorized_amount: float | None

    def create_enrollment(
        self, *, owner_id: str, email: str, return_url: str, idempotency_key: str
    ) -> dict[str, Any]: ...

    def get_enrollment(self, enrollment_id: str) -> dict[str, Any]: ...

    def activate_demo(self, enrollment_id: str) -> None: ...

    def create_quote(
        self, variant_id: str, *, email: str, idempotency_key: str | None = None
    ) -> dict[str, Any]: ...

    def create_checkout(
        self,
        quote_id: str,
        enrollment_id: str,
        *,
        idempotency_key: str | None = None,
        return_url: str | None = None,
    ) -> dict[str, Any]: ...

    def get_checkout(self, checkout_id: str) -> dict[str, Any]: ...


class BodegaReap(ReapClient):
    """ReapClient plus enrollment and checkout reads. Demo mode never hits the network."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.demo_authorized_amount: float | None = None
        self._enrollments: dict[str, dict[str, Any]] = {}
        self._checkouts: dict[str, dict[str, Any]] = {}

    def create_enrollment(
        self, *, owner_id: str, email: str, return_url: str, idempotency_key: str
    ) -> dict[str, Any]:
        require_https(return_url)
        payload = {
            "source": "EXTERNAL",
            "owner": {"type": "CLIENT_REFERENCE", "id": owner_id, "email": email},
            "presentation": {"type": "REDIRECT", "returnUrl": return_url},
        }
        if self.demo_mode:
            enrollment_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"demo-enroll:{idempotency_key}"))
            body = {
                "id": enrollment_id,
                "status": "REQUIRES_ACTION",
                "source": "EXTERNAL",
                "presentation": payload["presentation"],
                "nextAction": {
                    "type": "REDIRECT",
                    "url": "https://sandbox.api.reap.global/demo/enroll",
                    "expiresAt": "2099-01-01T00:00:00Z",
                },
                "demo_data": True,
            }
            self._enrollments[enrollment_id] = body
            return {"status": 200, "body": body, "demo_data": True}
        return self._request(
            "POST", "/agentic/enrollments", payload=payload, idempotency_key=idempotency_key
        )

    def get_enrollment(self, enrollment_id: str) -> dict[str, Any]:
        if self.demo_mode:
            body = self._enrollments.get(enrollment_id)
            if body is None:
                return {"status": 404, "body": {"error": "enrollment not found"}, "demo_data": True}
            return {"status": 200, "body": body, "demo_data": True}
        return self._read(f"/agentic/enrollments/{enrollment_id}")

    def activate_demo(self, enrollment_id: str) -> None:
        if not self.demo_mode:
            raise PaymentError("demo confirmation is only available in DEMO_MODE")
        body = self._enrollments.get(enrollment_id)
        if body is None:
            raise PaymentError("enrollment not found")
        body["status"] = "ACTIVE"
        body["demo_data"] = True

    def create_quote(
        self, variant_id: str, *, email: str, idempotency_key: str | None = None
    ) -> dict[str, Any]:
        recorded = super().create_quote(variant_id, email=email, idempotency_key=idempotency_key)
        if not self.demo_mode or _usable(recorded):
            return recorded
        amount = self.demo_authorized_amount
        if amount is None:
            return recorded
        quote_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"demo-quote:{variant_id}:{amount}"))
        body = {
            "id": quote_id,
            "status": "OPEN",
            "expiresAt": "2099-01-01T00:00:00Z",
            "amount": {"amount": amount, "currency": "MXN"},
            "demo_data": True,
        }
        return {"status": 200, "body": body, "demo_data": True}

    def create_checkout(
        self,
        quote_id: str,
        enrollment_id: str,
        *,
        idempotency_key: str | None = None,
        return_url: str | None = None,
    ) -> dict[str, Any]:
        recorded = super().create_checkout(
            quote_id,
            enrollment_id,
            idempotency_key=idempotency_key,
            return_url=return_url,
        )
        if not self.demo_mode or _usable(recorded):
            return recorded
        amount = self.demo_authorized_amount
        checkout_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"demo-checkout:{quote_id}:{enrollment_id}"))
        body = {
            "id": checkout_id,
            "status": "COMPLETED",
            "quoteId": quote_id,
            "enrollmentId": enrollment_id,
            "orderId": str(uuid.uuid5(uuid.NAMESPACE_URL, f"demo-order:{checkout_id}")),
            "finalAmount": {"amount": amount, "currency": "MXN"},
            "demo_data": True,
        }
        self._checkouts[checkout_id] = body
        return {"status": 200, "body": body, "demo_data": True}

    def get_checkout(self, checkout_id: str) -> dict[str, Any]:
        if self.demo_mode:
            body = self._checkouts.get(checkout_id)
            if body is None:
                return {"status": 404, "body": {"error": "checkout not found"}, "demo_data": True}
            return {"status": 200, "body": body, "demo_data": True}
        return self._read(f"/agentic/checkouts/{checkout_id}")

    def _read(self, path: str) -> dict[str, Any]:
        if not self.api_key:
            raise ReapConfigError("REAP_API_KEY is empty; the key is read only from the environment")
        headers = {"Authorization": f"Bearer {self.api_key}", "Reap-Version": self.version}
        with httpx.Client(base_url=self.base_url, timeout=self._timeout, transport=self._transport) as http:
            response = http.get(path, headers=headers)
        try:
            payload: Any = response.json()
        except ValueError:
            payload = {"raw": response.text}
        return {"status": response.status_code, "body": payload}


def require_https(return_url: str) -> None:
    if not return_url.startswith("https://"):
        raise PaymentError("returnUrl must be HTTPS")


def payload_of(response: dict[str, Any]) -> dict[str, Any]:
    body = response.get("body")
    if isinstance(body, dict):
        return body
    return response


def amount_of(payload: dict[str, Any]) -> Decimal | None:
    for key in ("finalAmount", "amount", "total"):
        if key not in payload:
            continue
        value = payload[key]
        if isinstance(value, dict) and "amount" in value:
            return money(value["amount"]).quantize(CENT, rounding=ROUND_HALF_UP)
        if isinstance(value, (int, float, str)):
            return money(value).quantize(CENT, rounding=ROUND_HALF_UP)
    return None


def is_expired(payload: dict[str, Any], now: datetime) -> bool:
    if str(payload.get("status", "")).upper() == "EXPIRED":
        return True
    raw = payload.get("expiresAt")
    if not raw:
        return False
    expires = datetime.fromisoformat(str(raw))
    current = now if now.tzinfo else now.replace(tzinfo=UTC)
    return current >= expires


def _usable(response: dict[str, Any]) -> bool:
    body = payload_of(response)
    return response.get("status") == 200 and not response.get("blocked") and not body.get("error")


def cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


ledgers: dict[str, dict[str, Any]] = {}
_client: BodegaReap | None = None


def reset_state() -> None:
    global _client
    ledgers.clear()
    _client = None


def get_client() -> BodegaReap:
    global _client
    if _client is None:
        _client = BodegaReap()
    return _client


def _businesses(businesses: list[Business] | None) -> dict[str, Business]:
    rows = load_businesses() if businesses is None else businesses
    owners = {row.id: row for row in rows}
    if len(owners) != len(rows):
        raise PaymentError("duplicate business ids")
    return owners


def open_ledger(
    proposal: Proposal, businesses: list[Business] | None = None
) -> dict[str, Any]:
    existing = ledgers.get(proposal.id)
    if existing is not None:
        return existing
    owners = _businesses(businesses)
    shares = []
    for allocation in proposal.allocations:
        owner = owners.get(allocation.business_id)
        if owner is None:
            raise PaymentError(f"unknown business {allocation.business_id}")
        shares.append(
            {
                "business_id": allocation.business_id,
                "sku_id": allocation.sku_id,
                "amount": float(cents(money(allocation.cost))),
                "budget_cap": float(cents(money(owner.budget_cap))),
                "approved": False,
            }
        )
    ledger = {
        "proposal_id": proposal.id,
        "currency": proposal.currency,
        "shares": shares,
        "authorized_total": float(cents(sum((money(row["amount"]) for row in shares), Decimal(0)))),
        "status": "awaiting_approval",
        "reason": None,
        "enrollment_id": None,
        "quote_id": None,
        "checkout_id": None,
        "order_id": None,
        "quoted_amount": None,
        "final_amount": None,
        "demo_data": True,
    }
    ledgers[proposal.id] = ledger
    return ledger


def _ledger(proposal_id: str) -> dict[str, Any]:
    ledger = ledgers.get(proposal_id)
    if ledger is None:
        raise PaymentError("ledger not found")
    return ledger


def _business_total(ledger: dict[str, Any], business_id: str) -> Decimal:
    shares = [row for row in ledger["shares"] if row["business_id"] == business_id]
    if not shares:
        raise PaymentError(f"business {business_id} has no share")
    return cents(sum((money(row["amount"]) for row in shares), Decimal(0)))


def authorize(proposal_id: str, business_id: str) -> dict[str, Any]:
    ledger = _ledger(proposal_id)
    if ledger["status"] == "reconciled":
        raise PaymentError("payment is already reconciled")
    total = _business_total(ledger, business_id)
    cap = cents(money(next(row["budget_cap"] for row in ledger["shares"] if row["business_id"] == business_id)))
    if total > cap:
        raise PaymentError(f"{business_id} share {total} exceeds budget cap {cents(cap)}")
    for row in ledger["shares"]:
        if row["business_id"] == business_id:
            row["approved"] = True
    ledger["reason"] = None
    ledger["status"] = "ready" if all(row["approved"] for row in ledger["shares"]) else "awaiting_approval"
    return ledger


def _stop(ledger: dict[str, Any], reason: str, **fields: Any) -> dict[str, Any]:
    for row in ledger["shares"]:
        row["approved"] = False
    ledger["status"] = "needs_approval"
    ledger["reason"] = reason
    ledger.update(fields)
    stored = proposal_store.get(ledger["proposal_id"])
    if stored is not None:
        stored.status = "pending_approval"
    return ledger


def enroll(
    client: PaymentsClient, *, owner_id: str, email: str, return_url: str
) -> dict[str, Any]:
    require_https(return_url)
    response = client.create_enrollment(
        owner_id=owner_id,
        email=email,
        return_url=return_url,
        idempotency_key=str(uuid.uuid4()),
    )
    body = payload_of(response)
    if response.get("status") not in (None, 200, 201) or not body.get("id"):
        raise PaymentError("enrollment was not created")
    if body.get("source") not in (None, "EXTERNAL"):
        raise PaymentError("enrollment must use source EXTERNAL")
    return {
        "id": body["id"],
        "status": body.get("status"),
        "source": body.get("source", "EXTERNAL"),
        "return_url": return_url,
        "next_action": body.get("nextAction"),
        "demo_data": bool(body.get("demo_data", client.demo_mode)),
    }


def confirm_enrollment(
    client: PaymentsClient, enrollment_id: str, *, demo_return: bool = False
) -> dict[str, Any]:
    if demo_return:
        client.activate_demo(enrollment_id)
    response = client.get_enrollment(enrollment_id)
    body = payload_of(response)
    status = body.get("status")
    if status != "ACTIVE":
        raise PaymentError(f"enrollment is {status or 'unknown'}, not ACTIVE")
    return {
        "id": enrollment_id,
        "status": status,
        "demo_data": bool(body.get("demo_data", client.demo_mode)),
    }


def checkout(
    client: PaymentsClient,
    proposal_id: str,
    enrollment_id: str,
    *,
    variant_id: str,
    email: str,
    return_url: str = DEMO_RETURN,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    require_https(return_url)
    ledger = _ledger(proposal_id)
    if ledger["status"] == "reconciled":
        return ledger
    if not all(row["approved"] for row in ledger["shares"]):
        raise PaymentError("checkout requires every business authorization")
    for business_id in {row["business_id"] for row in ledger["shares"]}:
        total = _business_total(ledger, business_id)
        cap = cents(money(next(row["budget_cap"] for row in ledger["shares"] if row["business_id"] == business_id)))
        if total > cap:
            raise PaymentError(f"{business_id} share {total} exceeds budget cap {cap}")
    enrollment = payload_of(client.get_enrollment(enrollment_id))
    if enrollment.get("status") != "ACTIVE":
        raise PaymentError("enrollment must be ACTIVE before checkout")
    authorized = cents(money(ledger["authorized_total"]))
    client.demo_authorized_amount = float(authorized)
    quote = payload_of(
        client.create_quote(variant_id, email=email, idempotency_key=str(uuid.uuid4()))
    )
    quoted = amount_of(quote)
    ledger["quote_id"] = quote.get("id")
    ledger["quoted_amount"] = None if quoted is None else float(quoted)
    if is_expired(quote, now):
        return _stop(ledger, "quote expired")
    if quoted is None or quoted != authorized:
        return _stop(ledger, "quoted amount differs from authorized split")
    created = payload_of(
        client.create_checkout(
            str(quote["id"]),
            enrollment_id,
            idempotency_key=str(uuid.uuid4()),
            return_url=return_url,
        )
    )
    checkout_id = str(created["id"])
    order = payload_of(client.get_checkout(checkout_id))
    final = amount_of(order)
    ledger["enrollment_id"] = enrollment_id
    ledger["checkout_id"] = checkout_id
    ledger["order_id"] = order.get("orderId")
    ledger["final_amount"] = None if final is None else float(final)
    if is_expired(order, now) or str(order.get("status", "")).upper() == "EXPIRED":
        return _stop(ledger, "checkout expired")
    if final is None or final != authorized or str(order.get("status", "")).upper() != "COMPLETED":
        return _stop(ledger, "finalAmount differs from authorized split")
    ledger["status"] = "reconciled"
    ledger["reason"] = None
    ledger["demo_data"] = bool(order.get("demo_data", client.demo_mode))
    stored = proposal_store.get(proposal_id)
    if stored is not None:
        stored.status = "paid"
    return ledger
