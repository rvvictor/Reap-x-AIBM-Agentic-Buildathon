"""Draft group purchases. No authorization, payment or live price authority here.

Product.unit_cost is the recorded per-unit delivered MXN price to beat.
SupplierOffer.shipping and tax are fixed MXN charges for one grouped purchase.
An offer's product_id must resolve to catalog metadata, including its unit.
"""

import json
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from hashlib import sha256

from app.schemas import Allocation, Business, Need, Product, Proposal, SupplierOffer
from app.schemas.loader import load_businesses

CENT = Decimal("0.01")
proposal_store: dict[str, Proposal] = {}


def money(value: float) -> Decimal:
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0:
        raise ValueError("Money must be finite and nonnegative")
    if amount > Decimal(1000000000000):
        raise ValueError("Money exceeds supported demo quote limit")
    return amount


def key(product: Product) -> tuple[str, str, str]:
    return product.category, product.name.strip().casefold(), product.unit


def allocate(total: Decimal, needs: list[Need]) -> list[Decimal]:
    """Largest remainder allocation, with stable business/SKU ties."""
    cents = int(total * 100)
    quantity = sum(n.qty for n in needs)
    shares = [Decimal(cents) * n.qty / quantity for n in needs]
    floors = [int(share) for share in shares]
    order = sorted(
        range(len(needs)),
        key=lambda i: (-(shares[i] - floors[i]), needs[i].business_id, needs[i].sku_id),
    )
    for i in order[: cents - sum(floors)]:
        floors[i] += 1
    return [Decimal(value) / 100 for value in floors]


def generate_proposals(
    needs: list[Need],
    products: list[Product],
    offers: list[SupplierOffer],
    *,
    today: date | None = None,
    businesses: list[Business] | None = None,
) -> list[Proposal]:
    today = today or date.today()
    catalog = {p.id: p for p in products}
    businesses = load_businesses() if businesses is None else businesses
    owners = {b.id: b for b in businesses}
    if len(owners) != len(businesses):
        raise ValueError("Duplicate business IDs")
    remaining = {
        bid: money(b.budget_cap).quantize(CENT, rounding=ROUND_HALF_UP)
        for bid, b in owners.items()
    }
    if len(catalog) != len(products):
        raise ValueError("Duplicate product IDs")
    for product in products:
        money(product.unit_cost)
    for offer in offers:
        if offer.eta_days > 3650:
            raise ValueError("ETA exceeds supported demo delivery limit")
        for amount in (offer.unit_price, offer.shipping, offer.tax):
            money(amount)
    seen = set()
    equivalents_by_need = {}
    groups: list[tuple[list[Need], set[tuple[str, str, str]]]] = []
    for need in sorted(needs, key=lambda n: (n.category, n.business_id, n.sku_id)):
        if need.qty > 1000000000:
            raise ValueError("Quantity exceeds supported demo limit")
        identity = (need.business_id, need.sku_id)
        if identity in seen:
            raise ValueError("Duplicate business/SKU need")
        seen.add(identity)
        product = catalog.get(need.sku_id)
        if (
            product is None
            or need.business_id not in owners
            or product.business_id != need.business_id
            or product.category != need.category
            or product.name != need.product_name
        ):
            raise ValueError("Need must match catalog SKU, owner, category and name")
        if need.needed_by < today:
            raise ValueError("Need deadline is before today")
        accepted = {key(product)}
        for equivalent in need.accepted_equivalents:
            alternative = catalog.get(equivalent)
            if (
                alternative is None
                or alternative.category != product.category
                or alternative.unit != product.unit
            ):
                raise ValueError(
                    "Equivalent must have known matching category and unit"
                )
            accepted.add(key(alternative))
        equivalents_by_need[identity] = accepted.copy()
        for group, common in groups:
            if common & accepted:
                group.append(need)
                common.intersection_update(accepted)
                break
        else:
            groups.append(([need], accepted))
    result = []
    for original, common in groups:
        active = original[:]
        excluded: list[str] = []
        while active:
            common = set.intersection(
                *(equivalents_by_need[(n.business_id, n.sku_id)] for n in active)
            )
            qty = sum(n.qty for n in active)
            eligible = []
            for offer in offers:
                product = catalog.get(offer.product_id)
                if (
                    product is None
                    or key(product) not in common
                    or offer.category != product.category
                    or offer.currency != "MXN"
                    or offer.min_qty > qty
                ):
                    continue
                if any(
                    today + timedelta(days=offer.eta_days) > n.needed_by for n in active
                ):
                    continue
                total = (
                    money(offer.unit_price) * qty
                    + money(offer.shipping)
                    + money(offer.tax)
                ).quantize(CENT, rounding=ROUND_HALF_UP)
                eligible.append((total, offer))
            if not eligible:
                break
            total, selected = min(
                eligible,
                key=lambda item: (
                    item[0],
                    item[1].supplier,
                    item[1].product_id,
                    item[1].variant_id or "",
                    item[1].min_qty,
                    item[1].eta_days,
                    item[1].demo_data,
                    item[1].source,
                    json.dumps(item[1].model_dump(mode="json"), sort_keys=True),
                ),
            )
            costs = allocate(total, active)
            baselines = [
                (money(catalog[n.sku_id].unit_cost) * n.qty).quantize(
                    CENT, rounding=ROUND_HALF_UP
                )
                for n in active
            ]
            savings: dict[str, Decimal] = {}
            business_costs: dict[str, Decimal] = {}
            for need, baseline, cost in zip(active, baselines, costs, strict=True):
                savings[need.business_id] = (
                    savings.get(need.business_id, Decimal(0)) + baseline - cost
                )
                business_costs[need.business_id] = (
                    business_costs.get(need.business_id, Decimal(0)) + cost
                )
            losers = {
                business
                for business, saving in savings.items()
                if saving < 0 or business_costs[business] > remaining[business]
            }
            if losers:
                excluded.extend(sorted(losers))
                active = [n for n in active if n.business_id not in losers]
                continue
            allocations = [
                Allocation(
                    business_id=n.business_id,
                    sku_id=n.sku_id,
                    qty=n.qty,
                    cost=float(cost),
                    individual_cost=float(base),
                    savings=float(base - cost),
                    approved=False,
                )
                for n, cost, base in zip(active, costs, baselines, strict=True)
            ]
            individual = sum(baselines, Decimal(0))
            comparisons = [
                f"{o.supplier} / {o.product_id} / min_qty={o.min_qty}: MXN {t:.2f} delivered"
                for t, o in sorted(
                    eligible,
                    key=lambda item: (
                        item[0],
                        item[1].supplier,
                        item[1].product_id,
                        item[1].min_qty,
                    ),
                )
            ]
            notes = [
                "Baseline: qty × recorded Product.unit_cost (delivered MXN/unit). Shipping and tax: fixed group charges.",
                *comparisons,
            ]
            if excluded:
                notes.append(
                    "Excluded negative-saving businesses; quantities, tiers and delivery rechecked: "
                    + ", ".join(excluded)
                )
            simulated = (
                selected.source == "simulated"
                or selected.demo_data
                or any(catalog[n.sku_id].demo_data for n in active)
            )
            if simulated:
                notes.append(
                    "Simulated prices/volume tiers; demo_data: true. Requote and owner approval required before payment."
                )
            identity = {
                "today": today.isoformat(),
                "offer": selected.model_dump(mode="json"),
                "needs": [n.model_dump(mode="json") for n in active],
                "allocations": [a.model_dump() for a in allocations],
            }
            proposal_id = (
                "proposal-"
                + sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
            )
            result.append(
                Proposal(
                    id=proposal_id,
                    category=active[0].category,
                    supplier=selected.supplier,
                    status="draft",
                    total=float(total),
                    individual_total=float(individual),
                    savings_total=float(individual - total),
                    currency="MXN",
                    allocations=allocations,
                    notes=notes,
                    demo_data=simulated,
                )
            )
            for bid, cost in business_costs.items():
                remaining[bid] -= cost
            break
    return result


def demo_offers(products: list[Product]) -> list[SupplierOffer]:
    """Explicit simulated scale prices; no claim that Reap supports volume tiers."""
    representatives: dict[tuple[str, str, str], Product] = {}
    for product in sorted(products, key=lambda p: p.id):
        if (
            key(product) not in representatives
            or product.unit_cost < representatives[key(product)].unit_cost
        ):
            representatives[key(product)] = product
    return [
        SupplierOffer(
            supplier=supplier,
            product_id=p.id,
            name=p.name,
            category=p.category,
            unit_price=float((money(p.unit_cost) * factor).quantize(CENT)),
            shipping=shipping,
            tax=0,
            currency="MXN",
            eta_days=1,
            min_qty=minimum,
            source="simulated",
            demo_data=True,
        )
        for p in representatives.values()
        for supplier, factor, shipping, minimum in [
            ("Proveedor demo A", Decimal("0.85"), 10, 1),
            ("Proveedor demo A", Decimal("0.75"), 10, 10),
            ("Proveedor demo B", Decimal("0.80"), 25, 1),
        ]
    ]
