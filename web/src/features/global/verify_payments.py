"""Integration test against the actual DEMO_MODE backend, without interception."""
import copy
import json
import os
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 page=browser.new_page(viewport={'width':1280,'height':720},reduced_motion='reduce')
 errors=[]
 page.on('pageerror',lambda error:errors.append(str(error)))
 page.goto(f"http://127.0.0.1:{int(os.environ['UAK_PORT'])+1}/#global",wait_until='networkidle')
 section=page.locator('.bodega-global')
 section.get_by_role('combobox').select_option('api')
 with page.expect_response(lambda r:'/global/proposals' in r.url and r.request.method=='POST') as response:
  section.get_by_role('button',name='Recalcular propuesta').click()
 proposal=response.value.json()[0]
 section.get_by_role('button',name='Preparar autorizaciones demo').click()
 expect(section.locator('.business-row')).to_have_count(4)
 expect(section.get_by_role('button',name='Enviar checkout demo')).to_be_disabled()
 for _ in range(4):
  button=section.get_by_role('button',name='Autorizar API demo',exact=True).first
  expect(button).to_be_enabled()
  button.click()
 expect(section.get_by_role('button',name='Autorizado API',exact=True)).to_have_count(4)
 expect(section.get_by_role('button',name='Enviar checkout demo')).to_be_disabled()
 section.get_by_role('textbox',name='Correo del titular').fill('tester@example.com')
 section.get_by_role('textbox',name='URL de regreso HTTPS').fill('https://example.com/return')
 section.get_by_role('button',name='Inscribir demo').click()
 expect(section.get_by_role('button',name='Confirmar ACTIVE demo')).to_be_enabled()
 section.get_by_role('button',name='Confirmar ACTIVE demo').click()
 expect(section.get_by_role('button',name='Enviar checkout demo')).to_be_enabled()
 with page.expect_response(lambda r:'/payments/checkouts' in r.url and r.request.method=='POST') as checkout:
  section.get_by_role('button',name='Enviar checkout demo').click()
 result=checkout.value
 assert result.status==200,(result.status,result.text())
 ledger=result.json()
 assert ledger['proposal_id']==proposal['id'] and ledger['status']=='reconciled',ledger
 assert ledger['demo_data'] and ledger['final_amount']==ledger['authorized_total']==proposal['total'],ledger
 assert ledger['order_id'] and all(row['approved'] for row in ledger['shares'])
 expect(section.locator('.payment-order')).to_have_count(4)
 expect(section.locator('.savings-status')).to_contain_text('Pagada según API')
 expect(section.get_by_role('button',name='Enviar checkout demo',include_hidden=True)).to_be_disabled()
 section.get_by_role('button',name='Consultar pedido').click()
 endpoint=f"http://127.0.0.1:{os.environ['UAK_PORT']}/api/payments/ledgers/{proposal['id']}"
 assert page.request.get(endpoint).json()==ledger
 expect(section.get_by_text('finalAmount del servidor:',exact=False)).to_contain_text('4,524')
 page.locator('#global').evaluate("element => element.scrollIntoView({block:'start',behavior:'instant'})")
 footer=section.locator('.global-footer').bounding_box()
 assert footer['y']+footer['height']<=720,footer
 page.screenshot(path='/tmp/hack010-payments-real.png',full_page=False)
 page.set_viewport_size({'width':390,'height':844})
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.screenshot(path='/tmp/hack010-payments-mobile.png',full_page=True)
 page.set_viewport_size({'width':1280,'height':720})
 # A remount must read the stored result, and must not enable another charge.
 section.get_by_role('button',name='Recalcular propuesta').click()
 expect(section.locator('.payment-order')).to_have_count(4)
 expect(section.locator('.savings-status')).to_contain_text('Pagada según API')
 expect(section.get_by_role('button',name='Enviar checkout demo',include_hidden=True)).to_be_disabled()
 # Client-only ambiguous-outcome regression, separate from the real flow above.
 ambiguous=browser.new_page(viewport={'width':1280,'height':720},reduced_motion='reduce')
 draft=copy.deepcopy(ledger)
 draft.update(status='ready',order_id=None,checkout_id=None,final_amount=None)
 ambiguous.route('**/api/payments/ledgers',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(draft)))
 ambiguous.route('**/api/payments/ledgers/*',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(draft)))
 checkout_attempts=[]
 def abort_checkout(route):
  checkout_attempts.append(route.request.post_data_json)
  route.abort('failed')
 ambiguous.route('**/api/payments/checkouts',abort_checkout)
 ambiguous.goto(f"http://127.0.0.1:{int(os.environ['UAK_PORT'])+1}/#global",wait_until='networkidle')
 area=ambiguous.locator('.bodega-global')
 area.get_by_role('combobox').select_option('api')
 area.get_by_role('button',name='Recalcular propuesta').click()
 area.get_by_role('button',name='Preparar autorizaciones demo').click()
 area.get_by_role('textbox',name='Correo del titular').fill('tester@example.com')
 area.get_by_role('textbox',name='URL de regreso HTTPS').fill('https://example.com/return')
 area.get_by_role('button',name='Inscribir demo').click()
 area.get_by_role('button',name='Confirmar ACTIVE demo').click()
 expect(area.get_by_role('button',name='Enviar checkout demo')).to_be_enabled()
 area.get_by_role('button',name='Enviar checkout demo').click()
 expect(area.get_by_role('button',name='Consultar pedido')).to_be_enabled()
 expect(area.get_by_role('button',name='Enviar checkout demo',include_hidden=True)).to_be_disabled()
 area.get_by_role('button',name='Recalcular propuesta').click()
 expect(area.get_by_role('button',name='Consultar pedido')).to_be_enabled()
 area.get_by_role('button',name='Consultar pedido').click()
 expect(area.get_by_role('button',name='Enviar checkout demo',include_hidden=True)).to_be_disabled()
 assert len(checkout_attempts)==1,checkout_attempts
 ambiguous.close()
 negative=browser.new_page(viewport={'width':1280,'height':720},reduced_motion='reduce')
 sent=[]
 negative.on('request',lambda request:sent.append(request.url) if '/api/payments/' in request.url and request.method=='POST' else None)
 negative.route('**/api/config',lambda route:route.fulfill(status=200,content_type='application/json',body='{"demo_mode":false}'))
 negative.goto(f"http://127.0.0.1:{int(os.environ['UAK_PORT'])+1}/#global",wait_until='networkidle')
 target=negative.locator('.bodega-global')
 target.get_by_role('combobox').select_option('api')
 target.get_by_role('button',name='Recalcular propuesta').click()
 expect(target.get_by_role('button',name='Preparar autorizaciones demo')).to_be_enabled()
 negative.wait_for_load_state('networkidle')
 sent.clear()
 target.get_by_role('button',name='Preparar autorizaciones demo').click()
 expect(target.get_by_role('alert')).to_contain_text('únicamente DEMO_MODE')
 assert not sent,sent
 negative.close()
 assert not errors,errors
 print(json.dumps({'result':'PASS','demo_data':True,'order_id':ledger['order_id'],'final_amount':ledger['final_amount'],'desktop_footer':footer,'negative_client_checks':'simulated aborted checkout then remount: exactly1POST; simulated configfalse: zero feature payment writes','checks':'actual server: four authorizations, checkout gated before all approvals and ACTIVE, EXTERNAL demo enrollment/confirmation, reconciled order and GET, duplicate checkout disabled after remount, no interception or JS errors'}))
 browser.close()
