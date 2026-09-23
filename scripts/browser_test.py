"""Desktop/mobile functional review against the built GitHub Pages artifact."""
import functools, http.server, json, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def main():
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT/'dist')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
    out=ROOT/'outputs/screenshots'; out.mkdir(parents=True,exist_ok=True)
    snapshot=json.loads((ROOT/'dist/data.json').read_text())
    errors=[]; checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base); page.wait_for_selector('#funnel .funnel-row')
        assert 'SYNTHETIC FIXTURE' in page.locator('.banner').inner_text()
        for size in [('desktop',1440,1100),('mobile',390,844)]:
            label,width,height=size; page.set_viewport_size({'width':width,'height':height})
            for route in ['overview','retention','opportunities','experiment','quality','methodology']:
                page.goto(base+'#'+route); page.wait_for_selector('h1')
                assert page.locator('h1').count()==1
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'Overflow: {label}/{route}'
                page.screenshot(path=str(out/f'{label}-{route}.png'),full_page=True)
                checks.append(f'{label}/{route}: rendered without document overflow')
        page.goto(base+'#overview'); page.wait_for_selector('#mode')
        page.select_option('#mode','user'); page.select_option('#device','mobile'); page.select_option('#channel','Organic search')
        selected=next(f for f in snapshot['funnels'] if f['mode']=='user' and f['device']=='mobile' and f['channel']=='Organic search')
        assert str(selected['n']) in page.locator('#funnel').inner_text()
        assert page.locator('.funnel-row').count()==4
        # Keyboard native select and focus traversal remain usable.
        page.locator('#mode').focus(); page.keyboard.press('Tab')
        assert page.evaluate('document.activeElement.id')=='device'
        checks.append('Intersected filters and keyboard focus: passed')
        page.goto(base+'#experiment'); page.wait_for_selector('#calc-result strong')
        assert page.locator('#calc-result strong').inner_text()==f"{snapshot['experiment']['per_arm']:,}"
        page.fill('#mde','1'); assert int(page.locator('#calc-result strong').inner_text().replace(',',''))>snapshot['experiment']['per_arm']
        page.fill('#baseline','99'); page.fill('#mde','3'); assert 'below 100%' in page.locator('#calc-result').inner_text()
        checks.append('Calculator agrees with Python; sensitivity and invalid-input states passed')
        page.goto(base+'#methodology'); page.wait_for_selector('h1')
        for a in page.locator('a[href]').all():
            href=a.get_attribute('href')
            if href and not href.startswith(('http','#')):
                assert page.request.get(base+href).status==200,href
        checks.append('Local artifact links return HTTP 200')
        empty=json.loads(json.dumps(snapshot))
        for f in empty['funnels']: f.update(n=0,k=0,counts=[0,0,0,0],rate=None,ci=[None,None])
        page.route('**/data.json',lambda route:route.fulfill(json=empty))
        page.goto(base+'#overview'); page.reload(); page.wait_for_selector('.empty')
        assert 'No eligible product viewers' in page.locator('.empty').inner_text()
        checks.append('Empty filter population shows an explicit empty state')
        # 200% text enlargement at narrow desktop equivalent.
        page.unroute('**/data.json'); page.goto(base+'#overview');page.reload();page.wait_for_selector('.funnel-row')
        page.set_viewport_size({'width':800,'height':900});page.add_style_tag(content='html{font-size:200%}')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        checks.append('Enlarged text: no document overflow')
        browser.close()
    server.shutdown()
    assert not errors,errors
    result=dict(status='passed',checks=checks,console_errors=errors)
    (ROOT/'outputs/browser-validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
