"""Trusted coordinator's demo-only MCP bridge; state is isolated per process."""

from threading import Lock
from typing import Annotated, Any

from fastapi import HTTPException
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import ConfigDict, Field

from app.config import settings
from app.routers.global_agent import ProposalRequest, proposals
from app.schemas import Need
from app.schemas.loader import load_products
from app.services.global_agent import demo_offers, generate_proposals


class PublishedNeed(Need):
    """Only the shared minimal contract; private sales/margins are rejected."""

    model_config = ConfigDict(extra="forbid")
    qty: int = Field(gt=0, le=1_000_000_000, strict=True)
    accepted_equivalents: list[str] = Field(default_factory=list, max_length=32)


def create_server() -> MCPServer:
    server = MCPServer(
        "Bodega demo coordinator",
        instructions="Trusted global coordinator only. Simulated drafts, never payment authorization.",
    )
    pending: dict[tuple[str, str], Need] = {}
    pending_lock = Lock()

    def require_demo() -> None:
        if not settings.demo_mode:
            raise ToolError("MCP bridge requires DEMO_MODE=true; no live or multi-tenant access.")

    @server.tool(annotations=ToolAnnotations(
        read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False,
    ))
    def publicar_faltas(
        faltas: Annotated[list[PublishedNeed], Field(min_length=1, max_length=100)],
    ) -> dict[str, Any]:
        """Publish minimal demo needs atomically; replay replaces the same business/SKU."""
        require_demo()
        identities = [(n.business_id, n.sku_id) for n in faltas]
        if len(set(identities)) != len(identities):
            raise ToolError("Duplicate business/SKU in publication.")
        # MCP executes sync tools in threads; validation and replacement are one transaction.
        with pending_lock:
            candidate = pending | dict(zip(identities, faltas))
            if len(candidate) > 100:
                raise ToolError("At most 100 pending needs per coordinator process.")
            try:
                generate_proposals(list(candidate.values()), load_products(), [])
            except ValueError as exc:
                raise ToolError(str(exc)) from exc
            pending.clear()
            pending.update(candidate)
            return {"received": len(faltas), "pending": len(pending), "demo_data": True}

    @server.tool(annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False,
    ))
    def consultar_ofertas(category: str | None = None) -> dict[str, Any]:
        """Read simulated canonical catalog offers; no Reap or LLM calls."""
        require_demo()
        offers = demo_offers(load_products())
        return {"offers": [o.model_dump(mode="json") for o in offers
                           if category is None or o.category == category], "demo_data": True}

    @server.tool(annotations=ToolAnnotations(
        read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False,
    ))
    def proponer_compra() -> dict[str, Any]:
        """Global coordinator receives all pending demo needs and creates canonical drafts."""
        require_demo()
        with pending_lock:
            needs = [pending[k] for k in sorted(pending)]
            try:
                generated = proposals(ProposalRequest(needs=needs))
            except HTTPException as exc:
                raise ToolError(str(exc.detail)) from exc
        return {"proposals": [p.model_dump(mode="json") for p in generated],
                "demo_data": True}

    return server
