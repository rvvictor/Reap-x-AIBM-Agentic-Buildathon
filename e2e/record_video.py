"""Graba la demo de Bodega (pantalla real, solo texto en pantalla en español de México, sin audio).

Uso (servidor recién reiniciado con DEMO_MODE=true: el estado del demo vive en memoria):
  BASE_URL=http://127.0.0.1:$UAK_PORT uv run --with playwright python e2e/record_video.py
Salida: docs/demo-planb.mp4 (1280x720, ~1:40). Requiere ffmpeg.
"""
import os
import pathlib
import shutil
import subprocess
import tempfile

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", f"http://127.0.0.1:{os.environ.get('UAK_PORT', '8000')}")
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "demo-planb.mp4"

OVERLAY_JS = """
(() => {
  if (document.getElementById('rec-cap')) return;
  const st = document.createElement('style');
  st.textContent = `
    body { padding-bottom: 150px !important; }
    #rec-cap { position: fixed; left: 0; right: 0; bottom: 0; z-index: 99999; padding: 14px 40px 16px;
      background: rgba(15,23,42,.94); color: #fff; font: 600 23px/1.3 system-ui, sans-serif; text-align: center;
      min-height: 96px; display: block; }
    #rec-cap small { display: block; font: 700 13px system-ui, sans-serif; color: #fbbf24; margin-bottom: 4px; }
    #rec-dot { position: fixed; z-index: 99998; width: 22px; height: 22px; border-radius: 50%; left: -50px; top: -50px;
      background: rgba(239,68,68,.55); border: 3px solid #ef4444; pointer-events: none; }
  `;
  document.head.appendChild(st);
  const c = document.createElement('div'); c.id = 'rec-cap'; document.body.appendChild(c);
  const d = document.createElement('div'); d.id = 'rec-dot'; document.body.appendChild(d);
})();
"""


def caption(page, text, secs):
    page.evaluate(OVERLAY_JS)
    page.evaluate(
        "t => { document.getElementById('rec-cap').innerHTML = '<small>DEMO · datos y checkout simulados · sin dinero real</small>' + t; }",
        text,
    )
    page.wait_for_timeout(int(max(secs * 0.8, 3) * 1000))


def point(page, locator):
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    page.evaluate(
        "([x, y]) => { const d = document.getElementById('rec-dot'); d.style.left = (x - 11) + 'px'; d.style.top = (y - 11) + 'px'; }",
        [box["x"] + box["width"] / 2, box["y"] + box["height"] / 2],
    )
    page.wait_for_timeout(700)


def click(page, locator):
    point(page, locator)
    locator.click()


def click_enabled(page, name):
    buttons = page.get_by_role("button", name=name, exact=True)
    for i in range(buttons.count()):
        if buttons.nth(i).is_enabled():
            click(page, buttons.nth(i))
            return
    raise AssertionError(f"botón no disponible: {name}")


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="bodega-rec-"))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            reduced_motion="reduce",
            record_video_dir=str(tmp),
            record_video_size={"width": 1280, "height": 720},
        )
        page = ctx.new_page()
        errors = []
        page.on("response", lambda r: errors.append(f"{r.status} {r.url}") if r.status >= 400 else None)
        page.goto(BASE)
        page.wait_for_selector("article")
        page.evaluate(OVERLAY_JS)

        caption(page, "Bodega: stock objetivo por producto y compras en grupo más baratas para negocios pequeños", 6)
        caption(page, "Agente local de Café Aurora: calcula el objetivo de cada producto con temporada, eventos y clima", 6)
        row = page.locator("article").first
        point(page, row)
        caption(page, "Café en grano: base 12 → objetivo 16 · Temporada fría +20% y evento local de fin de semana", 6)
        caption(page, "Cada objetivo trae sus motivos y su confianza. El cálculo lo hace código determinista, no el LLM", 6)
        caption(page, "El LLM solo convierte eventos y clima en señales validadas contra un esquema", 5)

        page.get_by_text("Juntos, el café cuesta menos.").scroll_into_view_if_needed()
        caption(page, "Agente global: recibe las faltas de 4 cafeterías y las agrupa en un solo pedido de 20 bolsas", 6)
        page.get_by_text("Costo entregado del pedido").scroll_into_view_if_needed()
        caption(page, "Compara proveedores por costo entregado, con envío e IVA incluidos", 6)
        page.get_by_text("Comprando por separado").scroll_into_view_if_needed()
        caption(page, "Por separado: $5,892 · En grupo: $4,524 · Ahorro compartido simulado: $1,368 (23.2%)", 7)

        sel = page.locator("select").first
        point(page, sel)
        sel.select_option("api")
        page.wait_for_timeout(800)
        caption(page, "Modo API: el servidor local recalcula la propuesta con datos de ejemplo", 4)
        click(page, page.get_by_role("button", name="Recalcular propuesta"))
        page.wait_for_function("!document.body.innerText.includes('Comparando')", timeout=15000)
        caption(page, "Propuesta recalculada por el backend (el precio individual viene de fixtures del servicio)", 6)
        sel.select_option(index=0)
        page.wait_for_timeout(600)

        page.get_by_text("Cada dueño tiene la última palabra").scroll_into_view_if_needed()
        caption(page, "Cada dueño tiene la última palabra: autoriza su parte dentro de su tope de presupuesto", 6)
        for _ in range(4):
            click(page, page.get_by_role("button", name="Autorizar demo").first)
            page.wait_for_timeout(500)
        assert "4/4" in page.inner_text("body")
        caption(page, "Los 4 negocios autorizaron. Si cambia el tope o el proveedor, la autorización se reinicia", 6)

        click(page, page.get_by_role("button", name="Preparar propuesta demo"))
        page.wait_for_selector("text=awaiting_approval")
        page.get_by_text("Cada negocio autoriza su parte.").scroll_into_view_if_needed()
        caption(page, "Pago agéntico con el Agentic module de Reap: una tarjeta cobra el total y el libro interno reparte el costo (aquí, respuestas simuladas)", 8)
        caption(page, "El agente nunca ve datos de tarjeta, y ningún dato de tarjeta llega a un LLM", 5)
        click_enabled(page, "Autorizar")
        page.wait_for_timeout(700)
        click_enabled(page, "Autorizar")
        caption(page, "Cada negocio aprueba su parte del cobro", 3)
        click_enabled(page, "Inscribir tarjeta")
        page.wait_for_timeout(700)
        caption(page, "Se inscribe la tarjeta del grupo y se confirma ACTIVE", 4)
        click_enabled(page, "Confirmar ACTIVE")
        page.wait_for_timeout(700)
        click_enabled(page, "Cobrar")
        page.wait_for_selector("text=reconciled", timeout=15000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        caption(page, "Pedido conciliado (simulado): el cobro se reparte según lo que cada negocio autorizó", 7)
        caption(page, "Bodega · Todo simulado con DEMO_MODE: sin dinero real. El checkout completado en el sandbox de Reap sigue pendiente de verificar", 7)
        assert not errors, errors

        video = page.video
        ctx.close()
        src = pathlib.Path(video.path())
        browser.close()
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "26", "-r", "25", "-an", "-movflags", "+faststart", str(OUT)],
        check=True,
    )
    shutil.rmtree(tmp, ignore_errors=True)
    print("OK", OUT)


if __name__ == "__main__":
    main()
