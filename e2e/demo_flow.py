"""E2E del flujo demo (DEMO_MODE, sin red) con movimiento reducido.

Uso (con el servidor corriendo; reinicialo antes: el estado del demo vive en memoria):
  BASE_URL=http://localhost:$UAK_PORT uv run --with playwright python e2e/demo_flow.py
Guarda capturas a 1280x720 y 390x844 en e2e/screens/.
"""
import os
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", f"http://localhost:{os.environ.get('UAK_PORT', '8000')}")
OUT = pathlib.Path(__file__).parent / "screens"
OUT.mkdir(exist_ok=True)


def click_enabled(page, name):
    buttons = page.get_by_role("button", name=name, exact=True)
    for i in range(buttons.count()):
        if buttons.nth(i).is_enabled():
            buttons.nth(i).click()
            return True
    return False


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 720}, reduced_motion="reduce")
    errors = []
    page.on("response", lambda r: errors.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    page.goto(BASE)
    page.wait_for_selector("article")  # inventario y prediccion (pasos 1-2)
    assert "demo_data" in page.inner_text("body")
    page.screenshot(path=OUT / "1-negocio-1280x720.png")

    for _ in range(4):  # autorizacion por negocio (paso 5)
        page.get_by_role("button", name="Autorizar demo").first.click()
    assert "4/4" in page.inner_text("body")
    page.get_by_role("button", name="Preparar propuesta demo").click()
    page.wait_for_selector("text=awaiting_approval")
    for name in ("Autorizar", "Autorizar", "Inscribir tarjeta", "Confirmar ACTIVE", "Cobrar"):
        assert click_enabled(page, name), f"boton no disponible: {name}"
        page.wait_for_timeout(500)
    page.wait_for_selector("text=reconciled")  # estado final
    page.screenshot(path=OUT / "2-agente-global-y-pago-1280x720.png", full_page=True)

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    mobile.goto(BASE)
    mobile.wait_for_selector("article")
    mobile.screenshot(path=OUT / "3-movil-390x844.png", full_page=True)
    browser.close()

if errors:
    print("HTTP errors:", errors)
    sys.exit(1)
print("E2E_PASS")
