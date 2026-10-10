import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

port = int(os.environ['UAK_PORT']) + 1
out = Path('/tmp/hack010-browser')
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width':1280,'height':720}, reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(f'http://127.0.0.1:{port}', wait_until='networkidle')
    expect(page.get_by_role('heading', name='Juntos, el café cuesta menos.')).to_be_visible()
    section = page.locator('.bodega-global')
    footer = page.locator('.global-footer')
    desktop_footer = footer.bounding_box()
    assert desktop_footer['y'] + desktop_footer['height'] <= 720, desktop_footer
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(out/'desktop.png'), full_page=True)
    buttons = page.get_by_role('button',name='Autorizar demo',exact=True)
    assert buttons.count() == 4
    cap = page.get_by_role('spinbutton',name='Tope de Café Aurora')
    cap.fill('1')
    expect(buttons.first).to_be_disabled()
    expect(page.get_by_text('El tope debe cubrir')).to_be_visible()
    cap.fill('6000')
    for _ in range(4):
        page.get_by_role('button',name='Autorizar demo',exact=True).first.click()
    expect(page.get_by_text('Demo autorizada · todavía sin pagar')).to_be_visible()
    page.get_by_role('button',name='Origen Café',exact=True).click()
    expect(page.get_by_role('button',name='Autorizar demo',exact=True)).to_have_count(4)
    page.get_by_role('button',name='Recalcular propuesta').click()
    expect(page.get_by_role('status')).to_be_visible()
    expect(page.locator('.business-row')).to_have_count(4)
    page.get_by_role('combobox').select_option('api')
    expect(page.get_by_role('heading',name='Aún no hay una propuesta conectada')).to_be_visible()
    page.get_by_role('button',name='Recalcular propuesta').click()
    expect(page.get_by_role('alert')).to_contain_text('espera el servicio')
    page.get_by_role('button',name='Explorar propuesta de demo').click()
    page.get_by_role('button',name='Recalcular propuesta').focus()
    page.keyboard.press('Enter')
    expect(page.locator('.business-row')).to_have_count(4)
    page.get_by_role('button',name='Recalcular propuesta').click()
    page.get_by_role('combobox').select_option('api')
    page.wait_for_timeout(250)
    expect(page.get_by_role('heading',name='Aún no hay una propuesta conectada')).to_be_visible()
    expect(page.locator('.supplier-panel')).to_have_count(0)
    page.get_by_role('button',name='Explorar propuesta de demo').click()
    page.set_viewport_size({'width':390,'height':844})
    expect(section).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(out/'mobile.png'), full_page=True)
    assert not errors, errors
    print(json.dumps({'result':'PASS','desktop_footer':desktop_footer,'screenshots':[str(out/'desktop.png'),str(out/'mobile.png')],'checks':'desktop viewport, mobile overflow, cap rejection, approvals, reset, loading, empty, error, mode-switch race, keyboard, JS errors'}))
    browser.close()
