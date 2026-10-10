"""Data contract for Bodega. Every consumer imports from here; the owner is HACK-002."""

from app.schemas.models import (
    Allocation,
    Business,
    Forecast,
    Need,
    Product,
    Proposal,
    SalesRecord,
    Signal,
    SupplierOffer,
)

__all__ = [
    "Allocation",
    "Business",
    "Forecast",
    "Need",
    "Product",
    "Proposal",
    "SalesRecord",
    "Signal",
    "SupplierOffer",
]
