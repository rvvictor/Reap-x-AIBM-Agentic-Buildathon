"""HTTP client for the Reap Agentic Payments sandbox.

Live calls read ``app.config.Settings``, which loads ``.env``. Recorded
responses in ``app/fixtures/reap/`` are used when ``DEMO_MODE`` is true.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings

DOCUMENTED_REAP_VERSION = "2025-02-14"
DEFAULT_BASE_URL = "https://sandbox.api.reap.global"
FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "reap"


class ReapConfigError(RuntimeError):
    """Raised when a live call cannot be made because configuration is missing."""


class ReapClient:
    def __init__(
        self,
        *,
        transport: httpx.BaseTransport | None = None,
        environ: Mapping[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        if environ is None:
            cfg = Settings()
            self.api_key = cfg.reap_api_key
            self.version = cfg.reap_version or DOCUMENTED_REAP_VERSION
            self.base_url = cfg.reap_base_url.rstrip("/")
            self.return_url = cfg.reap_return_url
            self.demo_mode = cfg.demo_mode
        else:
            self.api_key = environ.get("REAP_API_KEY", "")
            self.version = environ.get("REAP_VERSION") or DOCUMENTED_REAP_VERSION
            self.base_url = (environ.get("REAP_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
            self.return_url = environ.get("REAP_RETURN_URL") or "https://example.invalid/return"
            self.demo_mode = environ.get("DEMO_MODE", "true").strip().lower() in {"1", "true", "yes"}
        self._timeout = timeout
        self._transport = transport

    def search_coffee(self) -> dict[str, Any]:
        """Search merchant catalogs for coffee.

        The public search body has no category field. ``Coffee & Tea`` is the
        merchant vertical from the event brief; the request query is ``coffee``.
        """
        if self.demo_mode:
            return self._fixture("search_coffee.json")
        return self._request(
            "POST",
            "/agentic/products/search",
            payload={
                "query": "coffee",
                "context": {"country": "US", "currency": "USD"},
                "filters": {"availability": "AVAILABLE_ONLY"},
                "pagination": {"limit": 5},
            },
        )

    def create_quote(
        self,
        variant_id: str,
        *,
        email: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if self.demo_mode:
            return self._fixture("quote.json")
        return self._request(
            "POST",
            "/agentic/quotes",
            payload={"items": [{"variantId": variant_id, "quantity": 1}], "email": email},
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )

    def create_checkout(
        self,
        quote_id: str,
        enrollment_id: str,
        *,
        idempotency_key: str | None = None,
        return_url: str | None = None,
    ) -> dict[str, Any]:
        if self.demo_mode:
            return self._fixture("checkout.json")
        return self._request(
            "POST",
            "/agentic/checkouts",
            payload={
                "quoteId": quote_id,
                "enrollmentId": enrollment_id,
                "presentation": {
                    "type": "REDIRECT",
                    "returnUrl": return_url or self.return_url,
                },
            },
            idempotency_key=idempotency_key or str(uuid.uuid4()),
            simulate_checkout=True,
        )

    def _fixture(self, name: str) -> dict[str, Any]:
        path = FIXTURE_DIR / name
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
        simulate_checkout: bool = False,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise ReapConfigError(
                "REAP_API_KEY is empty; the key is read only from the environment"
            )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Reap-Version": self.version,
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        if simulate_checkout:
            headers["X-Simulate-Checkout"] = "COMPLETED"
        with httpx.Client(
            base_url=self.base_url,
            timeout=self._timeout,
            transport=self._transport,
        ) as http:
            response = http.request(method, path, headers=headers, json=payload)
        try:
            body: Any = response.json()
        except json.JSONDecodeError:
            body = {"raw": response.text}
        return {"status": response.status_code, "body": body}
