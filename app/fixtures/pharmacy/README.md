# Farmacia · datos sintéticos (`demo_data: true`)

Una farmacia, 10 productos, 30 días completos por producto (300 ventas) y dos señales sintéticas. Negocio, ubicación, costos, inventario, ventas y señales son inventados; no son datos de pacientes ni precios observados. El catálogo incluye claritromicina solo como SKU ilustrativo; no implica una recomendación de uso, sustitución o dispensación.

Las tres matrices JSON (`businesses`, `products`, `sales`) tienen el mismo formato que las cafeterías y se cargan con `app.schemas.loader`, indicando `folder="pharmacy"`. Las señales usan el contrato `Signal` existente y se envían al forecast sin modificar su motor, esquemas ni router.

## Escenario reproducible

- Fecha de evaluación: **2026-10-09**; historial del 2026-09-10 al 2026-10-09. No se utiliza el reloj actual.
- Stock base: 10; mínimo 2 y máximo 40, sin fijar los límites al resultado esperado.
- Antigripal: 7 días a 8 unidades/día, seguidos de 23 a 16 durante un pico de frío **sintético**. EWMA (`alpha=0.3`) ≈15.9978; señal adicional `up=0.25`: `ceil(15.9978×1.25×1+0)=20`.
- Antiácido (categoría digestivos): 10 unidades/día; señal **independiente e inventada** `down=0.5`: `ceil(10×0.5×1+0)=5`. No se afirma una relación clínica con el frío.
- Sin las señales, los objetivos son 16 y 10. Este ejemplo combina historial y escenarios futuros; no duplica una medición real de clima.
- Horizonte de entrega 1 día y colchón 0 (valores por defecto del motor). El presupuesto sintético de $10,000 MXN se pasa explícitamente como 1,000,000 centavos; el endpoint no carga automáticamente el negocio.

El escenario está calibrado para ilustrar **10→20 y 10→5**, no para demostrar precisión predictiva, resultados de backtest ni ahorro medido. La confianza del motor es una heurística no calibrada.

## Ejecutar con el motor existente

Desde la raíz del repositorio:

```bash
uv run python app/fixtures/pharmacy/generate.py
uv run python - <<'PY'
import json
from pathlib import Path
from app.schemas.loader import load_businesses, load_products, load_sales
from app.services.forecast import ForecastInput, forecast
business = load_businesses("pharmacy")[0]
request = ForecastInput.model_validate({
    "products": [p.model_dump(mode="json") for p in load_products("pharmacy", business.id)],
    "sales": [s.model_dump(mode="json") for s in load_sales("pharmacy", business.id)],
    "signals": json.loads(Path("app/fixtures/pharmacy/signals.json").read_text()),
    "as_of": "2026-10-09", "alpha": 0.3, "demo_data": True,
    "budget_cap_cents": round(business.budget_cap * 100), "currency": "MXN",
})
for row in forecast(request):
    print(row["sku_id"], row["base"], "->", row["target"], "demo_data:", row["demo_data"])
PY
uv run pytest -q app/tests/test_pharmacy_fixture.py
```

El mismo body JSON puede enviarse a `POST /api/businesses/farmacia-demo/forecast`; la prueba lo verifica. Este fixture no añade una pantalla de farmacia, ni cambia el catálogo de cafeterías o conecta estas necesidades a pagos.
