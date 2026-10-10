"""Loads the simulated fixtures (demo_data) shipped in app/fixtures/."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.models import Business, Product, SalesRecord

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _read(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_businesses(folder: str = "businesses") -> list[Business]:
    return [Business(**row) for row in _read(FIXTURES / folder / "businesses.json")]


def load_products(folder: str = "businesses", business_id: str | None = None) -> list[Product]:
    items = [Product(**row) for row in _read(FIXTURES / folder / "products.json")]
    return [p for p in items if business_id in (None, p.business_id)]


def load_sales(folder: str = "businesses", business_id: str | None = None) -> list[SalesRecord]:
    rows = [SalesRecord(**row) for row in _read(FIXTURES / folder / "sales.json")]
    if business_id is None:
        return rows
    sku_ids = {p.id for p in load_products(folder, business_id)}
    return [r for r in rows if r.sku_id in sku_ids]
