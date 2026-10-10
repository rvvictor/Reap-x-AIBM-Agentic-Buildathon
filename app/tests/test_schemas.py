import pytest
from pydantic import ValidationError

from app.schemas import Signal
from app.schemas.loader import load_businesses, load_products, load_sales


def test_four_businesses_with_demo_data() -> None:
    businesses = load_businesses()
    assert len(businesses) == 4
    assert all(b.demo_data for b in businesses)


def test_products_share_categories_so_the_global_agent_can_group() -> None:
    products = load_products()
    assert len(products) == 4 * 8
    by_category: dict[str, set[str]] = {}
    for p in products:
        by_category.setdefault(p.category, set()).add(p.business_id)
    assert all(len(owners) == 4 for owners in by_category.values())
    assert all(p.min_stock <= p.base_stock <= p.max_stock for p in products)


def test_sales_history_90_days_per_sku_and_cold_season_ramp() -> None:
    sales = load_sales()
    skus = {p.id for p in load_products()}
    assert len(sales) == len(skus) * 90
    chai = sorted((s for s in sales if s.sku_id == "cafe-aurora:chai"), key=lambda s: s.date)
    first, last = sum(s.qty for s in chai[:30]), sum(s.qty for s in chai[-30:])
    assert last > first


def test_signal_magnitude_is_bounded() -> None:
    with pytest.raises(ValidationError):
        Signal(
            id="x", kind="event", description="d", categories=["cafe-grano"], direction="up",
            magnitude=0.9, source="fixture", valid_from="2026-10-09", valid_to="2026-10-12",
        )
