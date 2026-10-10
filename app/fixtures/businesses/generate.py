"""Deterministic generator for the 4 demo cafes. Run: uv run python app/fixtures/businesses/generate.py

Everything it writes is simulated (demo_data: true). Sales ramp up with the cold season.
"""

import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent
END = date(2026, 10, 9)
DAYS = 90

# (id suffix, name, category, unit, base daily mean, cold-season multiplier at the end, base stock, unit cost)
CATALOG = [
    ("grano", "Cafe en grano 250 g", "cafe-grano", "bolsa", 6, 1.35, 12, 300.0),
    ("filtros", "Filtros de papel V60", "filtros-cafe", "caja", 2, 1.10, 6, 85.0),
    ("vasos", "Vasos 12 oz con tapa", "vasos-desechables", "paquete", 4, 1.20, 10, 120.0),
    ("leche", "Leche entera 1 L", "leche", "litro", 18, 1.25, 30, 27.0),
    ("chai", "Te chai en polvo 1 kg", "te-chai", "bolsa", 3, 1.60, 8, 260.0),
    ("chocolate", "Chocolate en polvo 1 kg", "chocolate-polvo", "bolsa", 3, 1.70, 8, 190.0),
    ("azucar", "Azucar estandar 1 kg", "azucar", "kg", 8, 1.00, 15, 28.0),
    ("jarabe", "Jarabe de vainilla 750 ml", "jarabes", "botella", 2, 1.05, 5, 150.0),
]
BUSINESSES = [
    ("cafe-aurora", "Cafe Aurora", "Roma Norte, CDMX", 6000, 1.0),
    ("cafe-brasa", "Brasa Cafe", "Condesa, CDMX", 5000, 0.8),
    ("cafe-cumbre", "Cumbre Espresso", "Coyoacan, CDMX", 7000, 1.2),
    ("cafe-dulce", "Dulce Taza", "Narvarte, CDMX", 4500, 0.7),
]


def main() -> None:
    rng = random.Random(42)
    businesses, products, sales = [], [], []
    now = datetime(2026, 10, 9, 18, 0).isoformat()
    for bid, name, location, budget, scale in BUSINESSES:
        businesses.append(
            {
                "id": bid,
                "name": name,
                "vertical": "cafeteria",
                "location": location,
                "budget_cap": budget,
                "allowed_substitutions": ["vasos-desechables", "azucar"],
                "demo_data": True,
            }
        )
        for suffix, pname, cat, unit, mean, ramp, base, cost in CATALOG:
            sku = f"{bid}:{suffix}"
            stock = max(1, int(base * scale * rng.uniform(0.3, 0.8)))
            products.append(
                {
                    "id": sku,
                    "business_id": bid,
                    "name": pname,
                    "category": cat,
                    "unit": unit,
                    "base_stock": max(1, round(base * scale)),
                    "min_stock": max(1, round(base * scale * 0.4)),
                    "max_stock": round(base * scale * 3),
                    "current_stock": stock,
                    "unit_cost": round(cost * rng.uniform(0.98, 1.06), 2),
                    "updated_at": now,
                    "demo_data": True,
                }
            )
            for d in range(DAYS):
                day = END - timedelta(days=DAYS - 1 - d)
                season = 1 + (ramp - 1) * (d / (DAYS - 1))
                weekend = 1.25 if day.weekday() >= 5 else 1.0
                qty = max(0, round(mean * scale * season * weekend * rng.uniform(0.7, 1.3)))
                sales.append({"sku_id": sku, "date": day.isoformat(), "qty": qty})
    for fname, rows in (("businesses", businesses), ("products", products), ("sales", sales)):
        (OUT / f"{fname}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=None), encoding="utf-8")
    print(f"businesses={len(businesses)} products={len(products)} sales={len(sales)}")


if __name__ == "__main__":
    main()
