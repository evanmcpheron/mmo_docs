#!/usr/bin/env python3
"""Render trusted generated HTML in memory when URL navigation is restricted.

These checks do not prove file://, HTTP navigation or real localStorage persistence.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screenshots', type=Path)
    args = parser.parse_args()
    checks = []
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))

            def render(path: str) -> None:
                markup = (ROOT / path).read_text(encoding='utf-8')
                markup = re.sub('<script\\b[^>]*>.*?</script>', '', markup, flags=re.S)
                markup = re.sub('<link\\b[^>]*rel="stylesheet"[^>]*>', '', markup)
                page.set_content(markup)
                page.add_style_tag(content=(ROOT / 'site/style.css').read_text(encoding='utf-8'))
                page.add_script_tag(content=(ROOT / 'site/search-data.js').read_text(encoding='utf-8'))
                page.add_script_tag(content=(ROOT / 'site/app.js').read_text(encoding='utf-8'))
                page.evaluate('window.scrollTo(0,0); if(document.activeElement) document.activeElement.blur();')
            for path in ['index.html', 'phases/phase-15.html', 'systems/fishing.html', 'assets/Items/DA_Item_IronOre.html', 'professions/hearthkeeper.html', 'architecture/zone-transfers.html', 'asset-index.html', 'dependency-map.html', 'design/factions-and-allegiance.html', 'architecture/faction-contracts.html', 'walkthroughs/hearthward-campaign.html', 'faction-traceability.html']:
                render(path)
                assert page.locator('h1').count() == 1, path
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), path + ' overflow'
            checks.append('Twelve representative page layouts render without page-width overflow at 1440px.')
            render('index.html')
            if args.screenshots:
                args.screenshots.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(args.screenshots / 'home-desktop.png'), full_page=True)
            page.locator('#theme-toggle').click()
            assert page.locator('html').get_attribute('data-theme') == 'dark'
            if args.screenshots:
                page.screenshot(path=str(args.screenshots / 'home-dark.png'), full_page=True)
            checks.append('Theme changes the in-memory page; persistence not tested.')
            render('search.html')
            page.locator('#search-input').fill('fishing')
            assert page.locator('#search-results li').count() > 0
            assert page.locator('#search-results a[href="./systems/fishing.html"]').count() == 1
            page.locator('#search-input').fill('lease epoch')
            assert page.locator('#search-results li').count() > 0
            page.locator('#search-input').fill('unfindable9876543')
            assert page.locator('#search-results li').count() == 0
            checks.append('Search results, multiple terms and no-results state work with the packaged index in memory.')
            render('asset-index.html')
            page.locator('#asset-query').fill('WatchFitting')
            assert page.locator('[data-asset-row]:visible').count() == 2
            page.locator('#asset-query').fill('')
            page.locator('#asset-status').select_option('blocked')
            assert page.locator('[data-asset-row]:visible').evaluate_all('(rows)=>rows.length>0 && rows.every(row=>row.dataset.status==="blocked")')
            page.locator('#asset-status').select_option('')
            page.locator('#asset-type').select_option('Native enum')
            assert page.locator('[data-asset-row]:visible').evaluate_all('(rows)=>rows.length>0 && rows.every(row=>row.dataset.type==="Native enum")')
            checks.append('Name, type and status asset filters work in memory.')
            render('checklist.html')
            page.locator('#check-00').check()
            page.locator('#check-15').check()
            assert page.locator('#check-00').is_checked() and '2 of 32' in page.locator('#progress-status').inner_text()
            page.evaluate('window.__exportBlobs=[]; window.URL.createObjectURL=(blob)=>{window.__exportBlobs.push(blob);return "blob:test"}; HTMLAnchorElement.prototype.click=function(){};')
            page.locator('#export-progress').click()
            value = page.evaluate('async()=>JSON.parse(await window.__exportBlobs[0].text())')
            assert value == {'schemaVersion': 1, 'project': 'Briarwake', 'completed': ['00', '15']}
            page.locator('#import-progress').set_input_files({'name': 'invalid.json', 'mimeType': 'application/json', 'buffer': json.dumps({'schemaVersion': 1, 'project': 'Other', 'completed': ['99']}).encode()})
            page.wait_for_function('document.getElementById("import-status").textContent.includes("Invalid")')
            assert page.locator('#check-15').is_checked()
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#import-progress').set_input_files({'name': 'valid.json', 'mimeType': 'application/json', 'buffer': json.dumps({'schemaVersion': 1, 'project': 'Briarwake', 'completed': ['02', '31']}).encode()})
            page.wait_for_function('document.getElementById("check-31").checked')
            assert not page.locator('#check-15').is_checked()
            checks.append('Checklist changes, exported JSON Blob content, invalid import rejection and confirmed replacement import work in memory. Actual download and persistence not verified.')
            page.set_viewport_size({'width': 390, 'height': 844})
            for path in ['index.html', 'phases/phase-15.html', 'assets/Items/DA_Item_IronOre.html', 'asset-index.html', 'checklist.html', 'design/factions-and-allegiance.html', 'architecture/faction-contracts.html', 'walkthroughs/hearthward-campaign.html']:
                render(path)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), path + ' mobile overflow'
            render('index.html')
            page.locator('#menu-toggle').click()
            assert page.locator('#sidebar').is_visible()
            page.keyboard.press('Escape')
            assert not page.locator('#sidebar').is_visible()
            page.evaluate('window.scrollTo(0,0); if(document.activeElement) document.activeElement.blur();')
            if args.screenshots:
                page.screenshot(path=str(args.screenshots / 'home-mobile.png'), full_page=True)
            checks.append('Eight layouts fit 390px; mobile menu opens and Escape closes it.')
            if args.screenshots:
                for width, height, suffix in [(1440, 1000, 'desktop'), (390, 844, 'mobile')]:
                    page.set_viewport_size({'width': width, 'height': height})
                    for relative, name in [('design/factions-and-allegiance.html', 'factions'), ('walkthroughs/hearthward-campaign.html', 'campaign')]:
                        render(relative)
                        page.screenshot(path=str(args.screenshots / (name + '-' + suffix + '.png')))
            version = browser.version
            browser.close()
        assert not errors, errors
        report = {'status': 'pass', 'browser': 'Chromium ' + version, 'mode': 'In-memory HTML/CSS/JavaScript injection; no URL navigation', 'checks': checks, 'javascript_errors': errors, 'not_verified': ['file:// operation', 'HTTP page navigation', 'Real localStorage persistence', 'Actual exported-file download', 'Full accessibility/browser matrix', 'All game/runtime behavior']}
    except Exception as error:
        report = {'status': 'fail', 'mode': 'In-memory render checks', 'error': str(error) or type(error).__name__, 'completed_checks': checks, 'javascript_errors': errors}
    (ROOT / 'verification/render.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'pass' else 1
if __name__ == '__main__':
    raise SystemExit(main())
