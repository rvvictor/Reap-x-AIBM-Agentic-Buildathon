from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import Business, Need, Product, SupplierOffer
from app.services.global_agent import generate_proposals

TODAY = date(2026, 10, 10)


def product(sku, business, baseline=20, name="Coffee", unit="bag"):
    return Product(
        id=sku,
        business_id=business,
        name=name,
        category="coffee",
        unit=unit,
        base_stock=10,
        min_stock=0,
        max_stock=100,
        current_stock=0,
        unit_cost=baseline,
        updated_at=datetime(2026, 10, 9),
    )


def need(p, qty=1, equivalents=None):
    return Need(
        business_id=p.business_id,
        sku_id=p.id,
        product_name=p.name,
        category=p.category,
        qty=qty,
        needed_by=date(2030, 1, 1),
        accepted_equivalents=equivalents or [],
    )


def offer(p, price=10, shipping=0, tax=0, **kwargs):
    return SupplierOffer(
        supplier=kwargs.pop("supplier", "supplier"),
        product_id=p.id,
        name=p.name,
        category=p.category,
        unit_price=price,
        shipping=shipping,
        tax=tax,
        eta_days=1,
        **kwargs,
    )


def run(needs, products, offers):
    businesses = [
        Business(id=bid, name=bid, vertical="cafe", location="MX", budget_cap=10000)
        for bid in sorted({p.business_id for p in products})
    ]
    return generate_proposals(
        needs, products, offers, today=TODAY, businesses=businesses
    )


def test_cross_business_skus_group_and_choose_delivered_price():
    a, b = product("a", "A"), product("b", "B")
    proposals = run(
        [need(a, 2), need(b, 2)],
        [a, b],
        [
            offer(a, 1, 100, supplier="cheap unit"),
            offer(b, 5, 4, 2, supplier="delivered winner"),
        ],
    )
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.supplier == "delivered winner"
    assert proposal.total == 26
    assert proposal.savings_total == 54
    assert {a.business_id for a in proposal.allocations} == {"A", "B"}
    assert proposal.status == "draft" and proposal.demo_data
    assert all(not a.approved for a in proposal.allocations)
    assert any("cheap unit" in note for note in proposal.notes)


def test_explicit_substitution_and_unknown_offer_units():
    a, b = product("a", "A", name="Arabica"), product("b", "B", name="Robusta")
    proposals = run([need(a, equivalents=[b.id]), need(b)], [a, b], [offer(b)])
    assert len(proposals) == 1 and len(proposals[0].allocations) == 2
    unknown = offer(a).model_copy(update={"product_id": "unknown-external-id"})
    assert run([need(a)], [a], [unknown]) == []
    with pytest.raises(ValueError, match="known matching"):
        run([need(a, equivalents=["unknown"])], [a], [])
    incompatible = product("c", "C", unit="kg")
    with pytest.raises(ValueError, match="known matching"):
        run([need(a, equivalents=[incompatible.id])], [a, incompatible], [])


def test_exclude_business_then_recompute_volume_tier():
    a, b = product("a", "A", 5), product("b", "B", 30)
    proposals = run(
        [need(a, 5), need(b, 5)], [a, b], [offer(a, 8, min_qty=10), offer(a, 12)]
    )
    assert len(proposals) == 1
    proposal = proposals[0]
    assert [(a.business_id, a.cost) for a in proposal.allocations] == [("B", 60)]
    assert proposal.total == 60 and proposal.savings_total == 90
    assert any("Excluded" in note and "A" in note for note in proposal.notes)
    assert proposal.demo_data  # simulated tiers cannot lose their label


def test_aggregate_savings_per_business_before_excluding():
    a, a2, b = product("a", "A", 2), product("a2", "A", 30), product("b", "B", 20)
    proposal = run([need(a), need(a2), need(b)], [a, a2, b], [offer(a, 10)])[0]
    assert len(proposal.allocations) == 3
    assert sum(x.savings for x in proposal.allocations if x.business_id == "A") == 12
    assert proposal.allocations[0].savings < 0


def test_exclusion_recomputes_remaining_allowed_products():
    a = product("a", "A", 2, name="Arabica")
    b = product("b", "B", 30, name="Robusta")
    c = product("c", "C", 30, name="Blend")
    proposal = run(
        [need(a, equivalents=[b.id]), need(b, equivalents=[c.id])],
        [a, b, c],
        [offer(b, 10), offer(c, 5)],
    )[0]
    assert proposal.total == 5
    assert [allocation.business_id for allocation in proposal.allocations] == ["B"]


def test_cent_conservation_and_permutation_invariance():
    products = [product(letter, letter.upper()) for letter in "abc"]
    needs = [need(p) for p in products]
    offers = [
        offer(products[0], 1, 0.01, supplier="z"),
        offer(products[1], 1, 0.01, supplier="a"),
    ]
    first = run(needs, products, offers)[0]
    second = run(needs[::-1], products[::-1], offers[::-1])[0]
    assert first.supplier == second.supplier == "a"
    assert first.allocations == second.allocations
    assert first.notes == second.notes
    assert first.id == second.id
    assert (
        sum(Decimal(str(a.cost)) for a in first.allocations)
        == Decimal(str(first.total))
        == Decimal("3.01")
    )
    assert [a.cost for a in first.allocations] == [1.01, 1, 1]


def test_no_losing_business_late_delivery_or_currency_mixing():
    a = product("a", "A", 2)
    assert run([need(a)], [a], [offer(a, 5)]) == []
    urgent = need(a).model_copy(update={"needed_by": TODAY})
    assert run([urgent], [a], [offer(a, 1)]) == []
    assert run([need(a)], [a], [offer(a, 1, currency="USD")]) == []


def test_invalid_inputs_rejected_before_arithmetic():
    a = product("a", "A")
    with pytest.raises(ValueError, match="Duplicate"):
        run([need(a), need(a)], [a], [])
    with pytest.raises(ValueError, match="owner"):
        run([need(a).model_copy(update={"business_id": "B"})], [a], [])
    for value in [float("inf"), float("nan")]:
        with pytest.raises(ValueError, match="finite"):
            run([need(a)], [a], [offer(a).model_copy(update={"unit_price": value})])


def test_post_canonical_list_and_get_stored_draft():
    client = TestClient(app)
    a, b = product("a", "A"), product("b", "B")
    body = {
        "needs": [need(a).model_dump(mode="json"), need(b).model_dump(mode="json")],
        "products": [p.model_dump(mode="json") for p in [a, b]],
        "offers": [offer(a).model_dump(mode="json")],
        "businesses": [
            Business(
                id=bid, name=bid, vertical="cafe", location="MX", budget_cap=1000
            ).model_dump(mode="json")
            for bid in ["A", "B"]
        ],
    }
    response = client.post("/api/global/proposals", json=body)
    assert response.status_code == 200
    proposal = response.json()[0]
    assert proposal["demo_data"] and proposal["status"] == "draft"
    assert client.get(f"/api/global/proposals/{proposal['id']}").json() == proposal
    assert proposal in client.get("/api/global/proposals").json()
    assert client.get("/api/global/proposals/missing").status_code == 404
    assert client.post("/api/global/proposals", json={"needs": []}).json() == []
    assert client.post("/api/global/proposals", json={}).status_code == 422
    body["needs"].append(body["needs"][0])
    assert client.post("/api/global/proposals", json=body).status_code == 422


def test_live_route_cannot_accept_caller_price_authority(monkeypatch):
    from app.routers.global_agent import settings

    monkeypatch.setattr(settings, "demo_mode", False)
    assert TestClient(app).get("/api/global/proposals").status_code == 422
    assert TestClient(app).get("/api/global/proposals/missing").status_code == 422
    assert (
        TestClient(app).post("/api/global/proposals", json={"needs": []}).status_code
        == 422
    )


def test_budget_across_groups_and_duplicate_businesses():
    a = product("coffee-a", "A", 20)
    b = product("tea-a", "A", 20, name="Tea")
    businesses = [
        Business(id="A", name="A", vertical="cafe", location="MX", budget_cap=15)
    ]
    proposals = generate_proposals(
        [need(a), need(b)],
        [a, b],
        [offer(a), offer(b)],
        today=TODAY,
        businesses=businesses,
    )
    assert len(proposals) == 1
    assert sum(p.total for p in proposals) <= 15
    with pytest.raises(ValueError, match="Duplicate business"):
        generate_proposals(
            [need(a)], [a], [offer(a)], today=TODAY, businesses=businesses * 2
        )


@pytest.mark.parametrize("field,value", [("eta_days", 10**12), ("unit_price", 1e100)])
def test_extreme_quote_inputs_return_422(field, value):
    a = product("extreme", "A")
    body = {
        "needs": [need(a).model_dump(mode="json")],
        "products": [a.model_dump(mode="json")],
        "offers": [offer(a).model_dump(mode="json")],
        "businesses": [
            Business(
                id="A", name="A", vertical="cafe", location="MX", budget_cap=100
            ).model_dump(mode="json")
        ],
    }
    body["offers"][0][field] = value
    assert TestClient(app).post("/api/global/proposals", json=body).status_code == 422


def test_equal_delivered_quotes_with_different_splits_have_stable_id():
    a = product("tie", "A")
    offers = [offer(a, price=5, shipping=5), offer(a, price=10, shipping=0)]
    assert run([need(a)], [a], offers)[0].id == run([need(a)], [a], offers[::-1])[0].id


def test_replay_preserves_status_and_approval():
    from app.services.global_agent import proposal_store

    proposal_store.clear()
    a = product("replay", "A")
    body = {
        "needs": [need(a).model_dump(mode="json")],
        "products": [a.model_dump(mode="json")],
        "offers": [offer(a).model_dump(mode="json")],
        "businesses": [
            Business(
                id="A", name="A", vertical="cafe", location="MX", budget_cap=100
            ).model_dump(mode="json")
        ],
    }
    client = TestClient(app)
    proposal = client.post("/api/global/proposals", json=body).json()[0]
    proposal_store[proposal["id"]].status = "approved"
    proposal_store[proposal["id"]].allocations[0].approved = True
    replay = client.post("/api/global/proposals", json=body).json()[0]
    assert replay["id"] == proposal["id"] and replay["status"] == "approved"
    assert replay["allocations"][0]["approved"]
    proposal_store.clear()
