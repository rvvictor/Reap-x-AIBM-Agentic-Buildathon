"""Walk-forward comparison on synthetic demand, not evidence of real sales saved."""

from datetime import date, timedelta
from math import fsum

from app.services.forecast import ForecastInput, forecast

FORMULA = {
    "dynamic_target": "clip(ceil(EWMA(previous observed daily qty, alpha) * lead_days + safety_stock), min, min(max, capacity))",
    "fixed_target": "clip(base_stock, min, min(max, capacity))",
    "lost_sales": "max(0, simulated_demand - target)",
    "surplus": "max(0, target - simulated_demand)",
    "difference": "fixed_total - dynamic_total (positive means fewer units with dynamic)",
}


def backtest(request: ForecastInput) -> dict:
    """Replenish independently to each target before every observed SKU-day.

    Missing days are unknown; explicit zero records are observations. Inventory
    snapshots, signals without publication timestamps, budgets and actual payment
    flows cannot reconstruct historical decisions and are excluded here.
    """
    if request.signals or request.budget_cap_cents is not None:
        raise ValueError("backtest excludes signals without known-at timestamps and purchase budgets")
    products = sorted(request.products, key=lambda product: product.id)
    sales = [sale for sale in request.sales if sale.date <= request.as_of]
    if any(sale.date == date.min for sale in sales):
        raise ValueError("evaluated dates must allow a previous calendar day")
    daily = {}
    for sale in sales:
        daily.setdefault((sale.date, sale.sku_id), []).append(sale.qty)
    observations = {key: fsum(sorted(values)) for key, values in daily.items()}
    rows = {product.id: [] for product in products}
    for day in sorted({day for day, _ in observations}):
        # The forecast engine includes as_of itself, hence explicitly use yesterday.
        previous = [sale for sale in sales if sale.date < day]
        historical_request = ForecastInput(
            products=[product.model_copy(update={"current_stock": 0, "updated_at": None})
                      for product in products],
            sales=previous,
            as_of=day - timedelta(days=1),
            alpha=request.alpha,
            demo_data=True,
        )
        targets = {row["sku_id"]: row["target"] for row in forecast(historical_request)}
        for product in products:
            if (day, product.id) not in observations:
                continue
            demand = observations[day, product.id]
            upper = min(product.max, product.capacity if product.capacity is not None else product.max)
            fixed = max(product.min, min(upper, product.base_stock))
            dynamic = targets[product.id]
            rows[product.id].append({
                "date": day.isoformat(), "history_through": (day - timedelta(days=1)).isoformat(),
                "demand": demand, "fixed_target": fixed, "dynamic_target": dynamic,
                "fixed": {"lost_sales": max(0, demand - fixed), "surplus": max(0, fixed - demand)},
                "dynamic": {"lost_sales": max(0, demand - dynamic), "surplus": max(0, dynamic - demand)},
                "demo_data": True,
            })
    results = []
    for product in products:
        days = rows[product.id]
        totals = {strategy: {metric: fsum(day[strategy][metric] for day in days)
                             for metric in ("lost_sales", "surplus")}
                  for strategy in ("fixed", "dynamic")}
        results.append({
            "sku_id": product.id, "unit": product.unit,
            "parameters": {"base_stock": product.base_stock, "min": product.min,
                           "max": product.max, "capacity": product.capacity,
                           "lead_days": product.lead_days, "safety_stock": product.safety_stock},
            "observed_days": len(days), "daily": days, **totals,
            "difference": {metric: totals["fixed"][metric] - totals["dynamic"][metric]
                           for metric in ("lost_sales", "surplus")},
            "demo_data": True,
        })
    return {
        "demo_data": True, "source": "simulated", "as_of": request.as_of.isoformat(),
        "alpha": request.alpha, "formula": FORMULA.copy(), "products": results,
        "assumptions": [
            "Synthetic recorded sales are treated as demand; unobserved demand is not measured.",
            "Each observed SKU-day starts at its target with instant replenishment; no carryover or delivery simulation.",
            "Only earlier sales inform EWMA; without history the dynamic target uses base stock plus safety_stock, clipped to bounds.",
            "Missing SKU-days are unknown, not zero; duplicate records on a day are summed.",
            "Both policies share fixed product bounds; dynamic lead_days and safety_stock stay constant throughout the evaluation.",
            "Current inventory snapshots, external signals, purchase budgets, costs and payments are excluded.",
            "Totals remain per SKU/unit; surplus is summed daily unused stock, not final inventory or waste.",
            "Differences may be negative; these simulated results do not establish real accuracy or savings.",
        ],
    }
