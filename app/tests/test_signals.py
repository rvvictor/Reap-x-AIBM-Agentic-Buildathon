import asyncio
import copy
import json
from types import SimpleNamespace

import pytest
from anthropic import APIConnectionError
from fastapi.testclient import TestClient
from httpx2 import Request

from app.config import Settings
from app.main import app
from app.services import signals


def recorded():
    return json.loads(signals.FIXTURE.read_text())


def request():
    return signals.ExtractionRequest.model_validate(recorded()["request"])


def live_config():
    return Settings(_env_file=None, demo_mode=False, anthropic_api_key="")


class FakeClient:
    def __init__(self, payload=None, stop_reason="end_turn", error=None):
        self.payload = payload or recorded()["response"]
        self.stop_reason = stop_reason
        self.error = error
        self.calls = []
        self.messages = self

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload))],
        )


def test_demo_uses_validated_recording_without_model(monkeypatch):
    def forbidden_client(**kwargs):
        pytest.fail("DEMO_MODE must not construct a model client")

    monkeypatch.setattr(signals, "AsyncAnthropic", forbidden_client)
    result = asyncio.run(signals.extract_signals(request(), config=Settings(_env_file=None)))
    assert len(result) == 2
    assert all(item.demo_data and item.source.startswith("demo:") for item in result)
    assert signals.demo_signals(["cups"])[0].categories == ["cups"]
    assert signals.demo_signals(["unknown"]) == []


def test_model_uses_configured_id_and_evidence_provenance():
    payload = recorded()["response"]
    payload["signals"][0]["direction"] = "down"
    for item in payload["signals"]:
        item["demo_data"] = False  # The model cannot relabel simulated evidence.
    client = FakeClient(payload)
    config = live_config()
    result = asyncio.run(signals.extract_signals(request(), config=config, client=client))
    assert result[0].direction == "down"
    assert all(item.demo_data for item in result)
    assert client.calls[0]["model"] == config.llm_model
    assert json.loads(client.calls[0]["messages"][0]["content"]) == request().model_dump(mode="json")


@pytest.mark.parametrize("field,value", [
    ("magnitude", -0.01), ("magnitude", 0.51), ("magnitude", True),
    ("magnitude", float("nan")), ("source", "invented"),
    ("categories", ["unknown"]), ("kind", "season"),
    ("direction", "execute_command"), ("valid_to", "2026-11-20"),
    ("valid_to", "2026-10-08"), ("valid_from", "2026-10-09T00:00:00-06:00"),
    ("description", ""),
    ("unexpected", "ignore previous instructions"),
])
def test_rejects_invalid_or_unbound_model_output(field, value):
    payload = recorded()["response"]
    payload["signals"][0][field] = value
    with pytest.raises(signals.SignalError, match="contrato"):
        signals.validate_signals(json.dumps(payload), request())


def test_rejects_non_json_duplicate_ids_and_oversized_output():
    for raw in ["```json\n{}\n```", "not json"]:
        with pytest.raises(signals.SignalError):
            signals.validate_signals(raw, request())
    payload = recorded()["response"]
    payload["signals"] = [copy.deepcopy(payload["signals"][0])] * 2
    with pytest.raises(signals.SignalError):
        signals.validate_signals(json.dumps(payload), request())
    payload["signals"] *= 11
    with pytest.raises(signals.SignalError):
        signals.validate_signals(json.dumps(payload), request())


@pytest.mark.parametrize("value", [None, 42, True, "invalid", {}])
def test_rejects_non_list_signals_with_safe_route_error(monkeypatch, value):
    from app.routers import signals as routes

    payload = {"signals": value}
    with pytest.raises(signals.SignalError, match="contrato"):
        signals.validate_signals(json.dumps(payload), request())

    async def fake_live(request):
        return await signals.extract_signals(
            request, config=live_config(), client=FakeClient(payload=payload)
        )

    monkeypatch.setattr(routes, "extract_signals", fake_live)
    response = TestClient(app, raise_server_exceptions=False).post(
        "/api/signals/extract", json=recorded()["request"]
    )
    assert response.status_code == 502
    assert response.json() == {"detail": "La respuesta no cumple el contrato de señales y fuentes."}


def test_rejects_truncation_and_missing_live_configuration():
    with pytest.raises(signals.SignalError, match="completó"):
        asyncio.run(signals.extract_signals(request(), config=live_config(), client=FakeClient(stop_reason="max_tokens")))
    with pytest.raises(signals.SignalError, match="configurada"):
        asyncio.run(signals.extract_signals(request(), config=live_config()))


def test_overall_deadline_and_safe_timeout(monkeypatch):
    original_timeout = asyncio.timeout
    monkeypatch.setattr(signals.asyncio, "timeout", lambda seconds: original_timeout(0.001))

    class SlowClient:
        messages = None

        async def create(self, **kwargs):
            await asyncio.sleep(1)

    client = SlowClient()
    client.messages = client
    with pytest.raises(signals.SignalError, match="agotó el tiempo"):
        asyncio.run(signals.extract_signals(request(), config=live_config(), client=client))


def test_provider_exception_does_not_expose_private_details():
    error = APIConnectionError(
        message="private provider diagnostics", request=Request("POST", "https://provider.invalid")
    )
    with pytest.raises(signals.SignalError) as caught:
        asyncio.run(signals.extract_signals(request(), config=live_config(), client=FakeClient(error=error)))
    assert str(caught.value) == "El proveedor de señales no está disponible."
    assert "private" not in str(caught.value)


def test_routes_demo_input_bounds_and_safe_errors(monkeypatch):
    from app.routers import signals as routes

    monkeypatch.setattr(routes.settings, "demo_mode", True)
    monkeypatch.setattr(signals.settings, "demo_mode", True)
    client = TestClient(app)
    response = client.get("/api/signals")
    assert response.status_code == 200
    assert all(item["demo_data"] for item in response.json())
    assert client.post("/api/signals/extract", json=recorded()["request"]).status_code == 200
    oversized = recorded()["request"]
    oversized["sources"][0]["text"] = "x" * 6001
    assert client.post("/api/signals/extract", json=oversized).status_code == 422
    oversized = recorded()["request"]
    oversized["sources"] *= 6
    assert client.post("/api/signals/extract", json=oversized).status_code == 422

    async def unavailable(*args, **kwargs):
        raise signals.SignalError("El proveedor de señales no está disponible.")

    monkeypatch.setattr(routes, "extract_signals", unavailable)
    response = client.post("/api/signals/extract", json=recorded()["request"])
    assert response.status_code == 502
    assert response.json() == {"detail": "El proveedor de señales no está disponible."}
    monkeypatch.setattr(routes.settings, "demo_mode", False)
    assert client.get("/api/signals").status_code == 409
