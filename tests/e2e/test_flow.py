"""Real local DEMO_MODE API/UI coverage; see README.md for missing flow steps."""

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = Path(__file__).parent / "artifacts"


def read_fixture(name):
    return json.loads((ROOT / "app/fixtures" / name).read_text(encoding="utf-8"))


def api_json(response, status=200):
    assert response.status == status, (response.status, response.text())
    return response.json()


@pytest.fixture(scope="module")
def built_web():
    """Build current sources, never use a stale dist as evidence."""
    node = shutil.which("node")
    assert node, "Install Node before running the E2E suite."
    for script, args in (("typescript/lib/tsc.js", ["-b"]),
                         ("vite/bin/vite.js", ["build"])):
        target = ROOT / "web/node_modules" / script
        assert target.is_file(), "Run npm --prefix web ci before Verify."
        result = subprocess.run([node, str(target), *args], cwd=ROOT / "web",
                                capture_output=True, text=True, timeout=90)
        assert result.returncode == 0, result.stdout + result.stderr
    assert (ROOT / "web/dist/index.html").is_file()


def task_port():
    configured = os.environ.get("UAK_PORT")
    identity = ROOT / ".uak-env"
    if not configured and identity.is_file():
        configured = next((line.split("=", 1)[1] for line in
                           identity.read_text().splitlines() if line.startswith("UAK_PORT=")), None)
    if configured:
        return int(configured)
    # A clean CI checkout has no task identity: ask the OS for an available port.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def demo_url(built_web, tmp_path):
    """An isolated real app per test; stop only the process we created."""
    port = task_port()
    with socket.socket() as probe:
        probe.settimeout(0.2)
        # Windows may retain closed connections in TIME_WAIT between cases.
        # A successful connection identifies a listener, not residual sockets.
        if probe.connect_ex(("127.0.0.1", port)) == 0:
            pytest.fail(f"Task port {port} is occupied; do not reuse another process.")
    url = f"http://127.0.0.1:{port}"
    environment = dict(os.environ, DEMO_MODE="true", REAP_API_KEY="",
                       ANTHROPIC_API_KEY="", REAP_RETURN_URL="https://example.invalid/return")
    log_path = tmp_path / "server.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-u", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
             "--port", str(port)], cwd=ROOT, env=environment, stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                assert process.poll() is None, log_path.read_text(encoding="utf-8")
                try:
                    with urlopen(url + "/api/config", timeout=1) as response:
                        assert json.load(response)["demo_mode"] is True
                    assert process.poll() is None, "The launched server stopped during readiness."
                    break
                except (URLError, TimeoutError):
                    time.sleep(0.1)
            else:
                pytest.fail("App did not become ready: " + log_path.read_text(encoding="utf-8"))
            yield url
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def test_actual_forecast_needs_and_http_global_fallback(demo_url):
    """API chain uses canonical sales/stock; UI does not yet expose this chain."""
    products = read_fixture("businesses/products.json")
    sales = read_fixture("businesses/sales.json")
    businesses = read_fixture("businesses/businesses.json")
    signals = read_fixture("signals/demo.json")["response"]["signals"]
    as_of = max(row["date"] for row in sales)
    needs = []
    with sync_playwright() as playwright:
        request = playwright.request.new_context(base_url=demo_url)
        try:
            for business in businesses:
                catalog = [row for row in products if row["business_id"] == business["id"]]
                ids = {row["id"] for row in catalog}
                payload = {"products": catalog, "sales": [row for row in sales if row["sku_id"] in ids],
                           "signals": signals, "as_of": as_of, "demo_data": True}
                result = api_json(request.post(f"/api/businesses/{business['id']}/forecast", data=payload))
                assert result["demo_data"] is True
                assert len(result["forecasts"]) == len(catalog)
                lookup = {row["id"]: row for row in catalog}
                for predicted in result["forecasts"]:
                    product = lookup[predicted["sku_id"]]
                    assert product["min_stock"] <= predicted["target"] <= product["max_stock"]
                    assert predicted["reasons"] and predicted["demo_data"] is True
                    qty = max(predicted["target"] - product["current_stock"], 0)
                    if qty:
                        needs.append({"business_id": business["id"], "sku_id": product["id"],
                                      "product_name": product["name"], "category": product["category"],
                                      "qty": qty, "needed_by": "2099-01-01", "accepted_equivalents": []})
            assert needs, "Real forecast must produce at least one shortage in the fixture scenario."
            proposals = api_json(request.post("/api/global/proposals", data={"needs": needs}))
            assert proposals, "Global HTTP fallback must consume forecast-derived shortages."
            published = {(row["business_id"], row["sku_id"]): row["qty"] for row in needs}
            for proposal in proposals:
                assert proposal["demo_data"] is True
                assert proposal["allocations"]
                assert proposal["total"] <= proposal["individual_total"]
                for allocation in proposal["allocations"]:
                    assert allocation["qty"] <= published[allocation["business_id"], allocation["sku_id"]]
                    assert allocation["savings"] >= 0 and allocation["approved"] is False
                assert api_json(request.get(f"/api/global/proposals/{proposal['id']}")) == proposal
        finally:
            request.dispose()


@pytest.mark.parametrize("width,height", [(1280, 720), (390, 844)])
def test_real_ui_authorizes_checkout_and_reads_final_order(demo_url, width, height):
    """Actual current UI's own example basket; no intercepted or replaced responses."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": width, "height": height},
                                      reduced_motion="reduce", locale="es-MX")
        page = context.new_page()
        errors = []
        external = []
        checkouts = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: external.append(request.url)
                if not request.url.startswith((demo_url + "/", "data:", "blob:")) else None)
        page.on("request", lambda request: checkouts.append(request.url)
                if request.url.endswith("/api/payments/checkouts") and request.method == "POST" else None)
        try:
            page.goto(demo_url + "/#global", wait_until="networkidle")
            assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
            expect(page.locator(".bz article.row")).to_have_count(5)
            expect(page.locator(".bz .badge").first).to_have_text("demo_data")
            section = page.locator("#global")
            section.get_by_role("combobox").select_option("api")
            with page.expect_response(lambda response: response.url.endswith("/api/global/proposals")
                                      and response.request.method == "POST") as comparison:
                section.get_by_role("button", name="Recalcular propuesta").click()
            proposals = api_json(comparison.value)
            assert len(proposals) == 1
            proposal = proposals[0]
            assert proposal["demo_data"] is True
            assert len(proposal["allocations"]) == 4
            assert all(not row["approved"] for row in proposal["allocations"])
            assert round(sum(row["cost"] for row in proposal["allocations"]), 2) == proposal["total"]
            section.get_by_role("button", name="Preparar autorizaciones demo").click()
            expect(section.locator(".business-row")).to_have_count(4)
            submit = section.get_by_role("button", name="Enviar checkout demo", include_hidden=True)
            expect(submit).to_be_disabled()

            def activate_card():
                section.get_by_role("textbox", name="Correo del titular").fill("e2e@example.invalid")
                section.get_by_role("textbox", name="URL de regreso HTTPS").fill("https://example.invalid/return")
                section.get_by_role("button", name="Inscribir demo").click()
                confirm = section.get_by_role("button", name="Confirmar ACTIVE demo")
                expect(confirm).to_be_enabled()
                expect(submit).to_be_disabled()
                confirm.click()

            # Independently exercise both gates, rather than masking missing
            # business approvals with an inactive card in every viewport case.
            if width == 1280:
                activate_card()
                expect(section.locator(".payment-checkout")).to_contain_text("ACTIVE")
                expect(submit).to_be_disabled()
            for index in range(4):
                section.get_by_role("button", name="Autorizar API demo", exact=True).first.click()
                expect(section.get_by_role("button", name="Autorizado API", exact=True)).to_have_count(index + 1)
                if index < 3 or width == 390:
                    expect(submit).to_be_disabled()
            if width == 390:
                activate_card()
            expect(submit).to_be_enabled()
            with page.expect_response(lambda response: response.url.endswith("/api/payments/checkouts")
                                      and response.request.method == "POST") as payment:
                submit.click()
            ledger = api_json(payment.value)
            assert ledger["proposal_id"] == proposal["id"]
            assert ledger["status"] == "reconciled" and ledger["demo_data"] is True
            assert ledger["final_amount"] == ledger["authorized_total"] == proposal["total"]
            assert ledger["order_id"] and ledger["checkout_id"]
            assert {(row["business_id"], row["sku_id"]) for row in ledger["shares"]} == {
                (row["business_id"], row["sku_id"]) for row in proposal["allocations"]}
            costs = {(row["business_id"], row["sku_id"]): row["cost"] for row in proposal["allocations"]}
            for share in ledger["shares"]:
                assert share["amount"] == costs[share["business_id"], share["sku_id"]]
            assert round(sum(row["amount"] for row in ledger["shares"]), 2) == ledger["authorized_total"]
            assert all(row["approved"] and row["amount"] <= row["budget_cap"] for row in ledger["shares"])
            expect(section.locator(".payment-order")).to_have_count(4)
            expect(section.locator(".savings-status")).to_contain_text("Pagada según API")
            expect(submit).to_be_disabled()
            with page.expect_response(lambda response: response.url.endswith(f"/api/payments/ledgers/{proposal['id']}")) as read:
                section.get_by_role("button", name="Consultar pedido").click()
            assert api_json(read.value) == ledger
            assert api_json(page.request.get(f"{demo_url}/api/payments/ledgers/{proposal['id']}")) == ledger
            expect(section.get_by_role("alert")).to_have_count(0)
            expect(section.get_by_role("button", name="Consultar pedido")).to_be_enabled()
            section.scroll_into_view_if_needed()
            ARTIFACTS.mkdir(exist_ok=True)
            page.screenshot(path=str(ARTIFACTS / f"checkout-{width}x{height}.png"),
                            full_page=False, animations="disabled")
            # Remount uses sessionStorage and the same authoritative server ledger.
            page.reload(wait_until="networkidle")
            section.get_by_role("combobox").select_option("api")
            section.get_by_role("button", name="Recalcular propuesta").click()
            expect(section.locator(".payment-order")).to_have_count(4)
            expect(section.locator(".savings-status")).to_contain_text("Pagada según API")
            expect(section.get_by_role("button", name="Enviar checkout demo", include_hidden=True)).to_be_disabled()
            assert api_json(page.request.get(f"{demo_url}/api/payments/ledgers/{proposal['id']}")) == ledger
            assert len(checkouts) == 1
            assert not errors, errors
            assert not external, external
        finally:
            context.close()
            browser.close()
