import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

port = int(os.environ["UAK_PORT"]) + 1
out = Path("/tmp/hack010-browser")
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        viewport={"width": 1280, "height": 720}, reduced_motion="reduce"
    )
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    api_response = {"status": 503, "payload": {"error": "unavailable"}}
    submitted = []

    def proposals_route(route):
        submitted.append(route.request.post_data_json)
        route.fulfill(
            status=api_response["status"],
            content_type="application/json",
            body=json.dumps(api_response["payload"]),
        )

    page.route("**/api/global/proposals", proposals_route)
    page.goto(f"http://127.0.0.1:{port}/#global", wait_until="networkidle")
    expect(
        page.get_by_role("heading", name="Juntos, el café cuesta menos.")
    ).to_be_visible()
    section = page.locator(".bodega-global")
    footer = page.locator(".global-footer")
    desktop_footer = footer.bounding_box()
    assert desktop_footer["y"] + desktop_footer["height"] <= 720, desktop_footer
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(out / "desktop.png"), full_page=True)
    buttons = page.get_by_role("button", name="Autorizar demo", exact=True)
    assert buttons.count() == 4
    cap = page.get_by_role("spinbutton", name="Tope de Café Aurora")
    cap.fill("1")
    expect(buttons.first).to_be_disabled()
    expect(page.get_by_text("El tope debe cubrir")).to_be_visible()
    cap.fill("6000")
    for _ in range(4):
        page.get_by_role("button", name="Autorizar demo", exact=True).first.click()
    expect(page.get_by_text("Demo autorizada · todavía sin pagar")).to_be_visible()
    page.get_by_role("button", name="Origen Café", exact=True).click()
    expect(page.get_by_role("button", name="Autorizar demo", exact=True)).to_have_count(
        4
    )
    page.get_by_role("button", name="Recalcular propuesta").click()
    expect(page.get_by_role("status")).to_be_visible()
    expect(page.locator(".business-row")).to_have_count(4)
    page.get_by_role("combobox").select_option("api")
    expect(page.get_by_role("heading", name="Aún no hay una propuesta")).to_be_visible()
    page.get_by_role("button", name="Recalcular propuesta").click()
    expect(page.get_by_role("alert")).to_contain_text("503")
    api_response["status"] = 200
    api_response["payload"] = [
        {
            "id": "api-demo",
            "category": "cafe-grano",
            "supplier": "Colectivo Tostador",
            "status": "pending_approval",
            "total": 4524,
            "individual_total": 5892,
            "savings_total": 1368,
            "currency": "MXN",
            "demo_data": True,
            "notes": ["Backend fixture baseline"],
            "allocations": [
                {
                    "business_id": business,
                    "sku_id": business + ":grano",
                    "qty": 5,
                    "cost": 1131,
                    "individual_cost": 1473,
                    "savings": 342,
                    "approved": False,
                }
                for business in [
                    "cafe-aurora",
                    "cafe-brasa",
                    "cafe-cumbre",
                    "cafe-dulce",
                ]
            ],
        }
    ]
    page.get_by_role("button", name="Reintentar").click()
    expect(page.locator(".business-row")).to_have_count(4)
    expect(page.get_by_role("button", name="No disponible", exact=True)).to_have_count(
        4
    )
    expect(
        page.get_by_role("button", name="No disponible", exact=True).first
    ).to_be_disabled()
    assert len(submitted[-1]["needs"]) == 4
    assert all(offer["demo_data"] for offer in submitted[-1]["offers"])
    api_response["payload"][0]["demo_data"] = False
    page.get_by_role("button", name="Recalcular propuesta").click()
    expect(page.get_by_role("alert")).to_contain_text("no corresponde")
    api_response["payload"] = []
    page.get_by_role("button", name="Reintentar").click()
    expect(page.get_by_role("heading", name="Aún no hay una propuesta")).to_be_visible()
    page.get_by_role("button", name="Explorar propuesta de demo").click()
    page.get_by_role("button", name="Recalcular propuesta").focus()
    page.keyboard.press("Enter")
    expect(page.locator(".business-row")).to_have_count(4)
    page.get_by_role("button", name="Recalcular propuesta").click()
    page.get_by_role("combobox").select_option("api")
    page.wait_for_timeout(250)
    expect(page.get_by_role("heading", name="Aún no hay una propuesta")).to_be_visible()
    expect(page.locator(".supplier-panel")).to_have_count(0)
    page.get_by_role("button", name="Explorar propuesta de demo").click()
    page.set_viewport_size({"width": 390, "height": 844})
    expect(section).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(out / "mobile.png"), full_page=True)
    assert not errors, errors
    print(
        json.dumps(
            {
                "result": "PASS",
                "desktop_footer": desktop_footer,
                "screenshots": [str(out / "desktop.png"), str(out / "mobile.png")],
                "checks": "desktop viewport, mobile overflow, cap rejection, approvals, reset, loading, empty, error, mode-switch race, keyboard, JS errors",
            }
        )
    )
    browser.close()
