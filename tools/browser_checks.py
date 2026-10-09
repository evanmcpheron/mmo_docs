#!/usr/bin/env python3
"""Exercise selected manual behaviors through file:// in an isolated browser context."""
from __future__ import annotations
import argparse
import json
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]

def run(chromium: str, screenshot_directory: Path | None, base_url: str | None=None) -> dict:
    checks = []
    errors = []
    external_requests = []

    def page_url(path: str) -> str:
        return base_url + path if base_url else (ROOT / path).as_uri()
    examples = ['index.html', 'phases/phase-15.html', 'systems/fishing.html', 'professions/hearthkeeper.html', 'architecture/zone-transfers.html', 'assets/Items/DA_Item_IronOre.html', 'asset-index.html', 'dependency-map.html', 'sources-verification.html', 'walkthroughs/recipe-race.html']
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=chromium, headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        context.on('request', lambda request: external_requests.append(request.url) if request.url.startswith(('https://', 'http://')) and (not (base_url and request.url.startswith(base_url))) else None)
        for path in examples:
            page.goto(page_url(path), wait_until='load')
            assert page.locator('h1').count() == 1, path
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), path + ' desktop overflow'
        checks.append('Ten representative pages loaded; one h1 and no page-width overflow at 1440px.')
        page.goto(page_url('index.html'))
        if screenshot_directory:
            screenshot_directory.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_directory / 'home-desktop.png'), full_page=True)
        page.locator('#theme-toggle').click()
        assert page.locator('html').get_attribute('data-theme') == 'dark'
        page.reload()
        assert page.locator('html').get_attribute('data-theme') == 'dark'
        page.locator('#theme-toggle').click()
        checks.append('Theme changes and persists on reload in tested Chromium.')
        page.goto(page_url('search.html'))
        page.locator('#search-input').fill('fishing')
        assert page.locator('#search-results li').count() > 0
        assert page.locator('#search-results a[href="./systems/fishing.html"]').count() == 1
        page.locator('#search-input').fill('unfindableword987654321')
        assert page.locator('#search-results li').count() == 0
        page.locator('#search-input').fill('lease epoch')
        assert page.locator('#search-results li').count() > 0
        checks.append('Offline search returns a known system, supports multiple terms and handles zero results.')
        page.goto(page_url('asset-index.html'))
        assert page.locator('[data-asset-row]:visible').count() == 205
        page.locator('#asset-query').fill('WatchFitting')
        assert page.locator('[data-asset-row]:visible').count() == 2
        page.locator('#asset-query').fill('')
        page.locator('#asset-status').select_option('blocked')
        assert page.locator('[data-asset-row]:visible').count() > 0
        assert page.locator('[data-asset-row]:visible').evaluate_all('(rows) => rows.every(row => row.dataset.status === "blocked")')
        page.locator('#asset-status').select_option('')
        page.locator('#asset-phase').fill('15')
        assert page.locator('[data-asset-row]:visible').evaluate_all('(rows) => rows.length > 0 && rows.every(row => row.dataset.phase === "15")')
        checks.append('Asset name, status and creation-phase filters select matching rows.')
        page.goto(page_url('checklist.html'))
        page.locator('#check-00').check()
        page.locator('#check-15').check()
        page.reload()
        assert page.locator('#check-00').is_checked() and page.locator('#check-15').is_checked()
        with tempfile.TemporaryDirectory() as directory:
            with page.expect_download() as download_info:
                page.locator('#export-progress').click()
            exported = Path(directory) / 'exported.json'
            download_info.value.save_as(exported)
            value = json.loads(exported.read_text(encoding='utf-8'))
            assert value == {'schemaVersion': 1, 'project': 'Briarwake', 'completed': ['00', '15']}
            invalid = Path(directory) / 'invalid.json'
            invalid.write_text(json.dumps({'schemaVersion': 1, 'project': 'Other', 'completed': ['99']}), encoding='utf-8')
            page.locator('#import-progress').set_input_files(invalid)
            page.wait_for_function('document.getElementById("import-status").textContent.includes("Invalid")')
            assert page.locator('#check-15').is_checked()
            valid = Path(directory) / 'valid.json'
            valid.write_text(json.dumps({'schemaVersion': 1, 'project': 'Briarwake', 'completed': ['02', '31']}), encoding='utf-8')
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#import-progress').set_input_files(valid)
            page.wait_for_function('document.getElementById("check-31").checked')
            assert not page.locator('#check-00').is_checked()
            assert not page.locator('#check-15').is_checked()
            page.once('dialog', lambda dialog: dialog.dismiss())
            page.locator('#reset-progress').click()
            assert page.locator('#check-31').is_checked()
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#reset-progress').click()
            assert not page.locator('#check-31').is_checked()
        checks.append('Progress reload, JSON export, valid replacement import, invalid import rejection and reset confirmation work.')
        page.set_viewport_size({'width': 390, 'height': 844})
        for path in ['index.html', 'phases/phase-15.html', 'assets/Items/DA_Item_IronOre.html', 'asset-index.html', 'checklist.html']:
            page.goto(page_url(path))
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), path + ' mobile overflow'
        page.goto(page_url('index.html'))
        assert not page.locator('#sidebar').is_visible()
        page.locator('#menu-toggle').click()
        assert page.locator('#sidebar').is_visible()
        page.keyboard.press('Escape')
        assert not page.locator('#sidebar').is_visible()
        if screenshot_directory:
            page.screenshot(path=str(screenshot_directory / 'home-mobile.png'), full_page=True)
        checks.append('Five representative pages fit 390px width; mobile navigation opens and Escape closes it.')
        page.set_viewport_size({'width': 1440, 'height': 1000})
        page.goto(page_url('index.html'))
        page.keyboard.press('Tab')
        assert page.evaluate('document.activeElement.classList.contains("skip")')
        page.keyboard.press('Enter')
        assert page.evaluate('location.hash === "#main"')
        checks.append('Keyboard skip link reaches main content.')
        restricted = browser.new_context(viewport={'width': 1440, 'height': 1000})
        restricted.add_init_script('Object.defineProperty(window,"localStorage",{get(){throw new Error("storage disabled for test");}});')
        denied = restricted.new_page()
        denied.on('pageerror', lambda error: errors.append(str(error)))
        denied.goto(page_url('checklist.html'))
        denied.locator('#check-03').check()
        assert denied.locator('#check-03').is_checked()
        assert 'storage is unavailable' in denied.locator('#import-status').inner_text()
        checks.append('Denied localStorage retains in-page checkmarks and presents an export warning.')
        version = browser.version
        browser.close()
    assert not errors, errors
    assert not external_requests, external_requests
    return {'status': 'pass', 'browser': 'Chromium ' + version, 'protocol': 'local HTTP preview' if base_url else 'file://', 'desktop_viewport': '1440x1000', 'mobile_viewport': '390x844', 'checks': checks, 'javascript_errors': errors, 'external_network_requests': external_requests, 'scope': 'Selected documentation UI behaviors only; not a full browser/accessibility matrix or any game test'}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium', default='/usr/bin/chromium')
    parser.add_argument('--screenshots', type=Path, help='Optional external directory; screenshots are not paid game art.')
    parser.add_argument('--serve-local', action='store_true', help='Test via local HTTP when a browser policy blocks file://; this does not verify the file protocol.')
    args = parser.parse_args()
    server = None
    if args.serve_local:

        class QuietHandler(SimpleHTTPRequestHandler):

            def log_message(self, format, *values):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
    base_url = f'http://127.0.0.1:{server.server_port}/' if server else None
    try:
        report = run(args.chromium, args.screenshots, base_url)
    except Exception as error:
        report = {'status': 'fail', 'error': str(error) or type(error).__name__, 'scope': 'Documentation browser checks', 'protocol': 'local HTTP preview' if base_url else 'file://'}
    finally:
        if server:
            server.shutdown()
            server.server_close()
    (ROOT / 'verification/browser.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'pass' else 1
if __name__ == '__main__':
    raise SystemExit(main())
