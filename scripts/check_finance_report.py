"""Check rendered finance report against executed JSON at two viewports."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]


def main():
    report=ROOT/'outputs/finance'
    data=json.loads((report/'results.json').read_text(encoding='utf-8'))
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        for name,width,height in [('desktop',1440,1000),('mobile',390,844)]:
            page.set_viewport_size(dict(width=width,height=height))
            page.goto((report/'index.html').as_uri())
            body=page.locator('body').inner_text()
            assert 'SYNTHETIC' in body
            assert page.locator('h1').count()==1
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert f'{data["orders"]:,}' in body
            assert data['forecast']['selected'] in body
            assert f'{data["forecast"]["holdout"][data["forecast"]["selected"]]["wape"]:.1%}' in body
            assert page.locator('.barrow').count()==24
            for m in data['months']:
                assert f'${m["revenue"]:,.0f}' in body
            assert 'Not mature' in body
            page.screenshot(path=str(report/f'{name}.png'),full_page=True)
            page.get_by_role('link',name='aggregate evidence').click()
            assert 'input_sha256' in page.locator('body').inner_text()
        browser.close()
    assert not errors,errors
    receipt=dict(status='passed',viewports=[1440,390],checks=['synthetic label','headline and monthly figures match JSON','24 revenue bars','immature cohorts marked','no page overflow','evidence link','no JS errors'])
    (report/'browser-validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))


if __name__=='__main__':main()
