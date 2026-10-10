"""Pydantic models of the Bodega contract (see IDEA.md §6). Money is in MXN unless `currency` says otherwise.

Every simulated record carries `demo_data: true` so the UI can label it.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class Business(BaseModel):
    id: str
    name: str
    vertical: str  # e.g. "cafeteria", "pharmacy"
    location: str
    budget_cap: float = Field(ge=0, description="Max spend per purchase cycle, MXN")
    allowed_substitutions: list[str] = Field(default_factory=list, description="Category/brand substitutions the owner accepts")
    demo_data: bool = True


class Product(BaseModel):
    """A SKU of one business. `base_stock` is the owner's static target; the forecast makes it dynamic."""

    id: str
    business_id: str
    name: str
    category: str  # shared across businesses so the global agent can group, e.g. "cafe-grano"
    unit: str
    base_stock: int = Field(ge=0)
    min_stock: int = Field(ge=0)
    max_stock: int = Field(ge=0)
    current_stock: int = Field(ge=0)
    unit_cost: float = Field(ge=0, description="What the business pays today (its 'price to beat'), MXN")
    updated_at: datetime
    demo_data: bool = True


class SalesRecord(BaseModel):
    sku_id: str
    date: date
    qty: int = Field(ge=0)
    demo_data: bool = True


class Signal(BaseModel):
    """A structured demand signal. The LLM may produce it but it is validated against this schema; magnitude is bounded."""

    id: str
    kind: Literal["season", "event", "weather"]
    description: str
    categories: list[str]
    direction: Literal["up", "down"]
    magnitude: float = Field(ge=0, le=0.5, description="Fractional change, 0.2 = +/-20%")
    source: str = Field(description="Where the signal comes from (URL or fixture name)")
    valid_from: date
    valid_to: date
    demo_data: bool = True


class Forecast(BaseModel):
    sku_id: str
    base: int
    target: int
    reasons: list[str]
    confidence: float = Field(ge=0, le=1)


class Need(BaseModel):
    """What a local agent publishes to the global agent. Sales, margins and recipes stay private."""

    business_id: str
    sku_id: str
    product_name: str
    category: str
    qty: int = Field(gt=0)
    needed_by: date
    accepted_equivalents: list[str] = Field(default_factory=list)


class SupplierOffer(BaseModel):
    supplier: str
    product_id: str
    variant_id: str | None = None  # Reap variant id when the offer comes from Reap
    name: str
    category: str
    unit_price: float = Field(ge=0)
    shipping: float = Field(ge=0)
    tax: float = Field(ge=0)
    currency: str = "MXN"
    eta_days: int = Field(ge=0)
    min_qty: int = Field(default=1, ge=1)
    source: Literal["reap_sandbox", "simulated"] = "simulated"
    demo_data: bool = True


class Allocation(BaseModel):
    business_id: str
    sku_id: str
    qty: int
    cost: float = Field(description="What this business pays in the group purchase, delivered")
    individual_cost: float = Field(description="What it would pay alone (price to beat)")
    savings: float
    approved: bool = False


class Proposal(BaseModel):
    id: str
    category: str
    supplier: str
    status: Literal["draft", "pending_approval", "approved", "paid", "stopped", "failed"] = "draft"
    total: float
    individual_total: float
    savings_total: float
    currency: str = "MXN"
    allocations: list[Allocation]
    notes: list[str] = Field(default_factory=list)
    demo_data: bool = True
