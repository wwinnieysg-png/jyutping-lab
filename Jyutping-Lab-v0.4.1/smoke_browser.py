"""Headless in-memory browser smoke test (Playwright)."""
import pathlib
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).parent
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    for width,height,name in [(1440,900,'desktop'),(390,844,'mobile')]:
        page = browser.new_page(viewport={'width':width,'height':height})
        errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content((root/'preview.html').read_text(encoding='utf-8'))
        page.wait_for_timeout(500)
        print('status',page.locator('#data-status').inner_text()[:90])
        page.locator('#search-input').fill('行')
        page.wait_for_timeout(300)
        assert page.locator('.pron-item').count()>=2
        assert page.locator('[data-speak], .action-listen').count()==0
        assert page.evaluate("typeof window.speechSynthesis === 'undefined' || document.querySelector('[data-speak]')===null")
        page.locator('#search-input').fill('銀行')
        page.wait_for_timeout(300)
        assert page.locator('.word-result').count()==1
        assert 'ngan4 hong4' in page.locator('.word-result').inner_text()
        page.locator('#copy-format').select_option('annotate')
        page.wait_for_timeout(180)
        assert '銀行(ngan4 hong4)' in page.locator('.word-result').inner_text()
        page.locator('#convert-btn').click()
        assert '我哋' in page.locator('#script-input').input_value()
        page.locator('#script-input').evaluate("el => {let i=el.value.indexOf('行街');el.focus();el.setSelectionRange(i,i+1);el.dispatchEvent(new Event('select',{bubbles:true}));}")
        assert page.locator('#selection-panel [data-apply="haang4"]').count()==1
        page.locator('#selection-panel [data-apply="haang4"]').click()
        assert '(haang4)街' in page.locator('#script-input').input_value()
        page.locator('#undo-btn').click()
        assert '(haang4)街' not in page.locator('#script-input').input_value()
        page.screenshot(path=str(root/f'preview-{name}.png'),full_page=True)
        assert not errors, errors
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), ('overflow',width)
        print(name, 'PASS: search, word search, format, convert, annotate, undo, layout')
        page.close()
    browser.close()
