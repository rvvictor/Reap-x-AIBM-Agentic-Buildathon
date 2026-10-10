"""Real MCP lifecycle/tools over subprocess stdio, without HTTP interception."""

import sys
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from time import sleep

import anyio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.mcp import server as server_module
from app.schemas import Proposal
from app.schemas.loader import load_products

ROOT = Path(__file__).resolve().parents[2]


def need(qty=10, product=None):
    product = product or next(p for p in load_products() if p.category == "cafe-grano")
    return {"business_id": product.business_id, "sku_id": product.id,
            "product_name": product.name, "category": product.category, "qty": qty,
            "needed_by": (date.today() + timedelta(days=2)).isoformat()}


@asynccontextmanager
async def client(demo="true"):
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "app.mcp"], cwd=str(ROOT),
        env={"DEMO_MODE": demo},
    )
    with anyio.fail_after(20):
        async with stdio_client(params) as streams, ClientSession(*streams) as session:
            await session.initialize()
            yield session


async def call(session, name, args=None):
    result = await session.call_tool(name, args or {})
    assert not result.is_error, result.content
    assert result.structured_content is not None
    return result.structured_content


def test_local_need_reaches_global_via_real_mcp_and_replay_is_stable():
    async def scenario():
        async with client() as session:
            tools = (await session.list_tools()).tools
            assert {t.name for t in tools} == {
                "publicar_faltas", "consultar_ofertas", "proponer_compra",
            }
            assert all(t.annotations.open_world_hint is False for t in tools)
            assert next(t for t in tools if t.name == "consultar_ofertas").annotations.read_only_hint
            assert await call(session, "proponer_compra") == {"proposals": [], "demo_data": True}
            published = await call(session, "publicar_faltas", {"faltas": [need()]})
            assert published == {"received": 1, "pending": 1, "demo_data": True}
            assert await call(session, "publicar_faltas", {"faltas": [need()]}) == published
            offers = await call(session, "consultar_ofertas", {"category": "cafe-grano"})
            assert offers["offers"] and all(o["demo_data"] for o in offers["offers"])
            result = await call(session, "proponer_compra")
            assert len(result["proposals"]) == 1
            proposal = Proposal.model_validate(result["proposals"][0])
            assert proposal.demo_data and sum(a.qty for a in proposal.allocations) == need()["qty"]
            assert proposal.allocations[0].business_id == need()["business_id"]
            assert proposal.savings_total > 0 and not proposal.allocations[0].approved
            assert await call(session, "proponer_compra") == result
        # A different launcher cannot see this coordinator's queue or proposals.
        async with client() as other:
            assert await call(other, "proponer_compra") == {"proposals": [], "demo_data": True}
    anyio.run(scenario)


@pytest.mark.parametrize("change", [
    {"business_id": "another-business"}, {"category": "unknown"},
    {"sku_id": "unknown"}, {"qty": 0}, {"qty": True},
    {"sales": [999], "margin": 0.9},
    {"needed_by": "2000-01-01"}, {"accepted_equivalents": ["unknown"]},
])
def test_invalid_or_private_publication_is_atomic(change):
    async def scenario():
        async with client() as session:
            valid = need()
            await call(session, "publicar_faltas", {"faltas": [valid]})
            before = await call(session, "proponer_compra")
            invalid = await session.call_tool("publicar_faltas", {"faltas": [valid | change]})
            assert invalid.is_error
            assert await call(session, "proponer_compra") == before
    anyio.run(scenario)


def test_duplicate_and_empty_batches_fail_without_publishing():
    async def scenario():
        async with client() as session:
            for batch in ([], [need(), need()], [need()] * 101):
                result = await session.call_tool("publicar_faltas", {"faltas": batch})
                assert result.is_error
            assert await call(session, "proponer_compra") == {"proposals": [], "demo_data": True}
    anyio.run(scenario)


def test_every_tool_rejects_live_mode():
    async def scenario():
        async with client("false") as session:
            for name, args in (("publicar_faltas", {"faltas": [need()]}),
                               ("consultar_ofertas", {}), ("proponer_compra", {})):
                result = await session.call_tool(name, args)
                assert result.is_error
    anyio.run(scenario)


def test_concurrent_local_publications_reach_global_without_lost_updates(monkeypatch):
    real_validation = server_module.generate_proposals

    def slow_validation(*args, **kwargs):
        # Force overlap at the old read/validate/write gap in the SDK worker threads.
        sleep(0.05)
        return real_validation(*args, **kwargs)

    monkeypatch.setattr(server_module, "generate_proposals", slow_validation)
    monkeypatch.setattr(server_module.settings, "demo_mode", True)
    server = server_module.create_server()
    products = [p for p in load_products() if p.category == "cafe-grano"]

    async def scenario():
        receipts = []

        async def publish(product):
            receipts.append(await call(server, "publicar_faltas", {"faltas": [need(product=product)]}))

        async with anyio.create_task_group() as group:
            for product in products:
                group.start_soon(publish, product)
        assert sorted(r["pending"] for r in receipts) == list(range(1, len(products) + 1))
        result = await call(server, "proponer_compra")
        allocations = [a for p in result["proposals"] for a in p["allocations"]]
        assert {a["business_id"] for a in allocations} == {p.business_id for p in products}
    anyio.run(scenario)
