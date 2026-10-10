"""Reproducible synthetic pharmacy catalog and a calibrated illustration, not a backtest."""

import json
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent
AS_OF = date(2026, 10, 9)
DAYS = 30
COLD_START = AS_OF - timedelta(days=22)
BUSINESS_ID = "farmacia-demo"
# suffix, name, category, illustrative MXN unit cost, warm daily sales, cold daily sales
CATALOG = [
    ("paracetamol", "Paracetamol", "analgesicos", 35, 6, 12),
    ("antigripal", "Antigripal", "antigripales", 80, 8, 16),
    ("claritromicina", "Claritromicina", "antibioticos", 180, 2, 2),
    ("antiacido", "Antiácido", "digestivos", 60, 10, 10),
    ("ibuprofeno", "Ibuprofeno", "analgesicos", 45, 4, 6),
    ("loratadina", "Loratadina", "antihistaminicos", 40, 3, 3),
    ("suero", "Suero oral", "hidratacion", 25, 4, 4),
    ("vitamina-c", "Vitamina C", "vitaminas", 70, 3, 5),
    ("gasas", "Gasas", "curacion", 20, 2, 2),
    ("termometro", "Termómetro", "instrumentos", 100, 1, 2),
]


def fixture_data() -> dict[str, list[dict]]:
    """Same flat JSON arrays as the cafe fixtures; no randomness or wall clock."""
    businesses = [{"id": BUSINESS_ID, "name": "Farmacia Demo", "vertical": "pharmacy",
                   "location": "Ubicación sintética, CDMX", "budget_cap": 10000,
                   "allowed_substitutions": [], "demo_data": True}]
    products, sales = [], []
    for suffix, name, category, cost, warm, cold in CATALOG:
        sku = f"{BUSINESS_ID}:{suffix}"
        products.append({"id": sku, "business_id": BUSINESS_ID, "name": name,
                         "category": category, "unit": "unidad de inventario demo",
                         "base_stock": 10, "min_stock": 2, "max_stock": 40,
                         "current_stock": 3, "unit_cost": cost,
                         "updated_at": f"{AS_OF.isoformat()}T12:00:00Z", "demo_data": True})
        for offset in range(DAYS):
            day = AS_OF - timedelta(days=DAYS - 1 - offset)
            sales.append({"sku_id": sku, "date": day.isoformat(),
                          "qty": cold if day >= COLD_START else warm, "demo_data": True})
    source = "app/fixtures/pharmacy/signals.json · escenario sintético calibrado"
    signals = [
        {"id": "pharmacy-cold-demo", "kind": "season",
         "description": "Escenario de frío simulado: incremento adicional en antigripales",
         "categories": ["antigripales"], "direction": "up", "magnitude": 0.25,
         "source": source, "valid_from": COLD_START.isoformat(),
         "valid_to": AS_OF.isoformat(), "demo_data": True},
        {"id": "pharmacy-digestive-demo", "kind": "event",
         "description": "Escenario independiente simulado: menor demanda digestiva",
         "categories": ["digestivos"], "direction": "down", "magnitude": 0.5,
         "source": source, "valid_from": COLD_START.isoformat(),
         "valid_to": AS_OF.isoformat(), "demo_data": True},
    ]
    return {"businesses": businesses, "products": products, "sales": sales, "signals": signals}


def main() -> None:
    for name, records in fixture_data().items():
        (OUT / f"{name}.json").write_text(
            json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
        )
    print("PHARMACY_FIXTURE: 1 business, 10 products, 300 sales, 2 synthetic signals")


if __name__ == "__main__":
    main()
