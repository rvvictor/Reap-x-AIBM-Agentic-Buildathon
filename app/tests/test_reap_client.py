import json
from pathlib import Path

import httpx
import pytest

from app.integrations.reap.client import (
    DOCUMENTED_REAP_VERSION,
    FIXTURE_DIR,
    ReapClient,
    ReapConfigError,
)

LIVE = {"DEMO_MODE": "false", "REAP_API_KEY": "test-key-not-a-secret", "REAP_VERSION": ""}


def test_demo_mode_reads_recorded_search_without_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected request {request.url}")

    client = ReapClient(transport=httpx.MockTransport(handler), environ={"DEMO_MODE": "true"})
    recorded = client.search_coffee()
    assert recorded["blocked"] is True
    assert recorded["demo_data"] is False
    assert recorded["status"] == 401
    assert recorded["body"]["error"]["code"] == "INVALID_AUTH_HEADER"
    assert recorded["request"]["query"] == "coffee"


def test_demo_mode_reads_quote_and_checkout_fixtures() -> None:
    client = ReapClient(environ={"DEMO_MODE": "true", "REAP_API_KEY": ""})
    quote = client.create_quote("var_probe", email="probe@example.invalid")
    checkout = client.create_checkout(
        "00000000-0000-4000-8000-000000000001",
        "00000000-0000-4000-8000-000000000002",
    )
    assert quote["status"] == 401
    assert checkout["body"]["error"]["code"] == "INVALID_AUTH_HEADER"
    assert "X-Simulate-Checkout: COMPLETED" in checkout["request"]["headers"]


def test_empty_key_never_calls_sandbox() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("empty key must not be sent")

    client = ReapClient(
        transport=httpx.MockTransport(handler),
        environ={"DEMO_MODE": "false", "REAP_API_KEY": ""},
    )
    with pytest.raises(ReapConfigError, match="REAP_API_KEY"):
        client.search_coffee()


def test_live_headers_for_search_quote_and_checkout() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    client = ReapClient(transport=httpx.MockTransport(handler), environ=LIVE)
    client.search_coffee()
    client.create_quote("var_1", email="a@example.invalid", idempotency_key="quote-key")
    client.create_checkout(
        "00000000-0000-4000-8000-000000000001",
        "00000000-0000-4000-8000-000000000002",
        idempotency_key="checkout-key",
    )

    search, quote, checkout = seen
    assert search.headers["Authorization"] == "Bearer test-key-not-a-secret"
    assert search.headers["Reap-Version"] == DOCUMENTED_REAP_VERSION
    assert "Idempotency-Key" not in search.headers
    assert json.loads(search.content)["query"] == "coffee"

    assert quote.headers["Idempotency-Key"] == "quote-key"
    assert quote.headers["Reap-Version"] == DOCUMENTED_REAP_VERSION
    assert "X-Simulate-Checkout" not in quote.headers

    assert checkout.headers["Idempotency-Key"] == "checkout-key"
    assert checkout.headers["X-Simulate-Checkout"] == "COMPLETED"
    assert checkout.headers["Authorization"].startswith("Bearer ")


def test_recorded_fixtures_match_files_on_disk() -> None:
    for name in ("search_coffee.json", "quote.json", "checkout.json"):
        payload = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
        assert payload["reap_version"] == DOCUMENTED_REAP_VERSION
        assert payload["blocked"] is True
        assert "REAP_API_KEY" not in json.dumps(payload)
        assert Path(FIXTURE_DIR / name).is_file()
