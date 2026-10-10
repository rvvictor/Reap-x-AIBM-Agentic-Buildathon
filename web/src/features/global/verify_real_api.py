import os,json
from playwright.sync_api import sync_playwright,expect
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 page=b.new_page(viewport={"width":1280,"height":720},reduced_motion="reduce")
 errors=[]
 page.on("pageerror",lambda error:errors.append(str(error)))
 page.goto(f"http://127.0.0.1:{int(os.environ['UAK_PORT'])+1}/#global",wait_until="networkidle")
 page.get_by_role("combobox").select_option("api")
 with page.expect_response(lambda response:'/api/global/proposals' in response.url and response.request.method=='POST') as response:
  page.get_by_role("button",name="Recalcular propuesta").click()
 result=response.value
 assert result.status==200,(result.status,result.text())
 payload=result.json()
 assert len(payload)==1,payload
 proposal=payload[0]
 assert proposal['total']==4524 and proposal['savings_total']==1560.15,proposal
 assert len(proposal['allocations'])==4 and all(not a['approved'] for a in proposal['allocations'])
 expect(page.locator('.business-row')).to_have_count(4)
 expect(page.get_by_role('button',name='No disponible',exact=True)).to_have_count(4)
 expect(page.get_by_role('button',name='No disponible',exact=True).first).to_be_disabled()
 assert page.get_by_role('alert').count()==0
 base=f"http://127.0.0.1:{os.environ['UAK_PORT']}/api/global/proposals"
 assert page.request.get(base+'/'+proposal['id']).json()==proposal
 assert page.request.get(base).json()==payload
 with page.expect_response(lambda response:'/api/global/proposals' in response.url and response.request.method=='POST') as replay:
  page.get_by_role('button',name='Recalcular propuesta').click()
 assert replay.value.json()==payload
 assert not errors,errors
 page.screenshot(path='/tmp/hack010-real-api.png',full_page=True)
 print(json.dumps({'result':'PASS','total':proposal['total'],'savings':proposal['savings_total'],'checks':'real POST via Vite proxy, frontend parser/render, 4 allocations, disabled checkout, GET/list, stable replay, no JS errors; no interception'}))
 b.close()
