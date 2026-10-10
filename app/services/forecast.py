"""Deterministic stock planning. Provisional IDEA.md adapter pending HACK-002."""

from datetime import date, datetime
from math import ceil, fsum, sqrt

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ProductInput(InputModel):
    id: str = Field(min_length=1)
    business_id: str = Field(min_length=1)
    name: str | None = None
    category: str = Field(min_length=1)
    unit: str | None = None
    base_stock: int = Field(ge=0)
    min: int = Field(ge=0, validation_alias=AliasChoices("min_stock", "min"))
    max: int = Field(ge=0, validation_alias=AliasChoices("max_stock", "max"))
    current_stock: int = Field(ge=0)
    lead_days: float = Field(default=1, gt=0, le=365)
    safety_stock: int = Field(default=0, ge=0)
    capacity: int | None = Field(default=None, ge=0)
    unit_price_cents: int | None = Field(default=None, gt=0)
    unit_cost: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    updated_at: datetime | None = None
    demo_data: bool = True

    @property
    def price_cents(self) -> int | None:
        if self.unit_price_cents is not None:
            return self.unit_price_cents
        if self.unit_cost is not None and self.unit_cost > 0:
            cents = round(self.unit_cost * 100)
            return cents if cents > 0 else None
        return None

    @model_validator(mode="after")
    def valid_bounds(self):
        if self.min > self.max or (self.capacity is not None and self.capacity < self.min):
            raise ValueError("min exceeds max or capacity")
        return self


class SaleInput(InputModel):
    sku_id: str
    date: date
    qty: float = Field(ge=0, le=1_000_000_000)
    demo_data: bool = True


class SignalInput(InputModel):
    id: str
    kind: str = Field(pattern="^(season|event|weather)$")
    description: str = Field(min_length=1)
    categories: list[str]
    direction: str = Field(pattern="^(up|down)$")
    magnitude: float = Field(ge=0, le=0.5)
    source: str = Field(min_length=1)
    valid_from: date
    valid_to: date
    demo_data: bool = False

    @model_validator(mode="after")
    def valid_window(self):
        if self.valid_from > self.valid_to:
            raise ValueError("signal validity window is reversed")
        return self


class ForecastInput(InputModel):
    products: list[ProductInput] = Field(min_length=1, max_length=100)
    sales: list[SaleInput] = Field(default_factory=list, max_length=50000)
    signals: list[SignalInput] = Field(default_factory=list, max_length=100)
    as_of: date
    alpha: float = Field(default=0.3, gt=0, le=1)
    budget_cap_cents: int | None = Field(default=None, ge=0)
    currency: str = Field(default="MXN", pattern="^[A-Z]{3}$")
    demo_data: bool = False

    @model_validator(mode="after")
    def valid_references(self):
        ids = [p.id for p in self.products]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate SKU IDs")
        if any(s.sku_id not in ids for s in self.sales):
            raise ValueError("sales reference an unknown SKU")
        if len({s.id for s in self.signals}) != len(self.signals):
            raise ValueError("duplicate signal IDs")
        if self.budget_cap_cents is not None and any(p.price_cents is None for p in self.products):
            raise ValueError("budget requires unit_price_cents for every product in the request currency")
        return self


def forecast(request: ForecastInput) -> list[dict]:
    """Missing days are unknown, not zero; future sales never inform the estimate.

    Budget first reserves every SKU's minimum, then funds extra stock in sorted
    SKU order. Confidence is a descriptive heuristic, not a calibrated probability.
    """
    results = []
    products = sorted(request.products, key=lambda p: p.id)
    for product in products:
        daily: dict[date, list[float]] = {}
        for sale in request.sales:
            if sale.sku_id == product.id and sale.date <= request.as_of:
                daily.setdefault(sale.date, []).append(sale.qty)
        values = [fsum(sorted(daily[day])) for day in sorted(daily)]
        ewma = values[0] if values else product.base_stock / product.lead_days
        for qty in values[1:]:
            ewma = request.alpha * qty + (1 - request.alpha) * ewma
        reasons = [f"EWMA: {ewma:.2f} unidades/día; {len(values)} días observados; días ausentes desconocidos."]
        if not values:
            reasons.append("Sin historial: se usa stock base como objetivo de respaldo.")
        factor = 1.0
        applied = []
        for signal in sorted(request.signals, key=lambda s: s.id):
            if product.category in signal.categories and signal.valid_from <= request.as_of <= signal.valid_to:
                multiplier = 1 + signal.magnitude if signal.direction == "up" else 1 - signal.magnitude
                factor *= multiplier
                applied.append(signal)
                reasons.append(f"{signal.kind} {signal.id}: factor {multiplier:.2f}; fuente: {signal.source}.")
        upper = min(product.max, product.capacity if product.capacity is not None else product.max)
        target = max(product.min, min(upper, ceil(ewma * factor * product.lead_days + product.safety_stock)))
        reasons.append(f"Entrega {product.lead_days:g} días; colchón {product.safety_stock}; límites {product.min}–{upper}.")
        mean = sum(values) / len(values) if values else 0
        variation = sqrt(sum((v - mean) ** 2 for v in values) / len(values)) / mean if mean else 0
        confidence = round(min(0.95, len(values) / 30) / (1 + variation), 3) if values else 0
        results.append({"sku_id": product.id, "base": product.base_stock, "target": target,
                        "reasons": reasons, "confidence": confidence,
                        "confidence_kind": "uncalibrated_history_heuristic",
                            "demo_data": (request.demo_data or product.demo_data
                                          or any(s.demo_data for s in applied)
                                          or any(sale.demo_data for sale in request.sales if sale.sku_id == product.id
                                                 and sale.date <= request.as_of))})
    if request.budget_cap_cents is not None:
        minimum_cost = sum(max(0, p.min - p.current_stock) * p.price_cents for p in products)
        if minimum_cost > request.budget_cap_cents:
            raise ValueError("budget cannot fund minimum replenishment across all products")
        remaining = request.budget_cap_cents - minimum_cost
        for product, result in zip(products, results):
            desired_purchase = max(0, result["target"] - product.current_stock)
            reserved = max(0, product.min - product.current_stock)
            extra = min(max(0, desired_purchase - reserved), remaining // product.price_cents)
            remaining -= extra * product.price_cents
            funded_target = product.current_stock + reserved + extra
            if funded_target < result["target"]:
                result["target"] = funded_target
                result["reasons"].append("Acotado por presupuesto compartido; mínimos primero, extras por SKU ordenado.")
    return results
