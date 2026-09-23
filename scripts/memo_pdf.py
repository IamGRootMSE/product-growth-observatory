"""Optional PDF export; Playwright is required, generated HTML is the source."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page()
    page.goto((ROOT/'docs/decision-memo.html').as_uri())
    page.pdf(path=str(ROOT/'outputs/product-decision-memo.pdf'),format='A4',print_background=True,prefer_css_page_size=True)
    browser.close()
print('Exported outputs/product-decision-memo.pdf')
