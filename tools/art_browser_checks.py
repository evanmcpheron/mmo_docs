"""Exercise the Art Bible through file URLs with an isolated Chromium context."""
from __future__ import annotations
import argparse
import base64
import json
from pathlib import Path
import traceback

ROOT = Path(__file__).resolve().parents[1]


def run(chromium=None, output=None):
    from playwright.sync_api import sync_playwright
    output = output or Path('/tmp/briarwake-art-browser')
    output.mkdir(parents=True, exist_ok=True)
    report = {'status': 'fail', 'scope': 'Art Bible file-URL browser QA; no engine testing', 'checks': [], 'errors': [], 'external_requests': [], 'screenshots': []}
    pages = json.loads((ROOT / 'sources/art-bible/chapters.json').read_text())['pages']
    with sync_playwright() as playwright:
        options = {'headless': True}
        if chromium:
            options['executable_path'] = chromium
        browser = playwright.chromium.launch(**options)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda error: report['errors'].append(str(error)))
        context.on('request', lambda request: report['external_requests'].append(request.url) if request.url.startswith(('http:', 'https:')) else None)

        def visit(name):
            page.goto((ROOT / ('art-style/' + name + '.html')).as_uri(), wait_until='load')

        try:
            for width in [1440, 390]:
                page.set_viewport_size({'width': width, 'height': 1000})
                for record in pages:
                    page.goto((ROOT / record['path']).as_uri(), wait_until='load')
                    assert page.locator('h1').count() == 1, record['path']
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'{record["path"]}: {width}px overflow'
                    page.evaluate("document.querySelectorAll('img').forEach(i => i.loading = 'eager')")
                    page.evaluate("Promise.all(Array.from(document.images, i => i.decode()))")
                report['checks'].append(f'All {len(pages)} pages, headings, local images and overflow checked at {width}px')
            visit('index')
            page.locator('#menu-toggle').click()
            assert page.locator('#menu-toggle').get_attribute('aria-expanded') == 'true'
            page.keyboard.press('Escape')
            assert page.locator('#menu-toggle').get_attribute('aria-expanded') == 'false'
            report['checks'].append('Mobile navigation opens and closes with Escape')
            page.screenshot(path=str(output / 'home-mobile.png'), full_page=True)
            preview = page.screenshot(path=str(output / 'home-mobile-viewport.png'))
            print('ART_BIBLE_MOBILE_PREVIEW=' + base64.b64encode(preview).decode())
            report['screenshots'].append('home-mobile.png')
            page.set_viewport_size({'width':1440, 'height':1000})
            visit('index')
            page.screenshot(path=str(output / 'home-desktop.png'), full_page=True)
            preview = page.screenshot(path=str(output / 'home-desktop-viewport.png'))
            print('ART_BIBLE_DESKTOP_PREVIEW=' + base64.b64encode(preview).decode())
            report['screenshots'].append('home-desktop.png')
            page.locator('.art-search summary').click()
            page.locator('#art-search').fill('terrain')
            assert page.locator('#art-search-results li').count() > 0
            page.locator('#art-search').fill('zzzz_no_such_reference')
            assert page.locator('#art-search-results li').count() == 0
            page.locator('#theme-toggle').click()
            assert page.locator('html').get_attribute('data-theme') == 'dark'
            page.locator('#theme-toggle').click()
            report['checks'].append('Offline search and theme controls work')
            visit('palette')
            page.locator('[data-copy]').first.click()
            page.wait_for_function("document.querySelector('.copy-status').textContent.includes('#')")
            report['checks'].append('Palette copy reports copied value or explicit fallback')
            visit('gallery')
            viewer = page.locator('.pixel-viewer').first
            viewer.locator('[data-zoom]').select_option('8')
            assert viewer.locator('.pixel-stage').evaluate('(e) => e.clientWidth') == 2048
            viewer.locator('[data-pixel-grid]').check()
            viewer.locator('[data-tile-grid]').check()
            assert viewer.locator('.pixel-grid').is_visible()
            assert viewer.locator('.tile-grid').is_visible()
            viewer.locator('[data-checker]').uncheck()
            assert 'no-checker' in viewer.locator('.pixel-stage').get_attribute('class')
            report['checks'].append('Nearest zoom, pixel grid, tile grid and checkerboard controls work')
            visit('animation')
            assert page.locator('.animation-viewer').evaluate("e => e.classList.contains('ready')")
            before = page.locator('[data-frame-label]').inner_text()
            page.locator('[data-step="1"]').click()
            assert page.locator('[data-frame-label]').inner_text() != before
            page.locator('[data-facing]').select_option('1')
            assert 'NE' in page.locator('[data-frame-label]').inner_text()
            page.locator('[data-speed]').select_option('0.5')
            page.locator('[data-play]').click()
            page.wait_for_timeout(250)
            page.locator('[data-pause]').click()
            stopped = page.locator('[data-frame-label]').inner_text()
            page.wait_for_timeout(250)
            assert page.locator('[data-frame-label]').inner_text() == stopped
            page.locator('[data-animation-zoom]').select_option('8')
            assert page.locator('.animation-stage').evaluate('e => e.clientWidth') == 512
            page.locator('[data-animation-grid]').check()
            page.locator('[data-animation-tile-grid]').check()
            page.locator('[data-animation-checker]').uncheck()
            page.locator('[data-registration]').uncheck()
            assert page.locator('.registration-marker').is_hidden()
            page.screenshot(path=str(output / 'animation.png'), full_page=True)
            report['screenshots'].append('animation.png')
            report['checks'].append('Real local frames: step, facing, speed, play/pause, zoom, grids and registration')
            visit('lighting')
            page.locator('[data-condition]').select_option('night')
            assert page.locator('[data-condition-image]').get_attribute('src').endswith('light-night.png')
            page.locator('[data-before-after]').fill('50')
            assert page.locator('.day-overlay').evaluate('e => getComputedStyle(e).opacity') == '0.5'
            visit('review')
            page.locator('[data-crowd]').select_option('30')
            assert page.locator('[data-crowd-image]').get_attribute('src').endswith('crowd-30.png')
            visit('ui')
            page.locator('[data-item="Potion"]').click()
            assert 'Potion' in page.locator('[data-item-detail]').inner_text()
            report['checks'].append('Lighting comparison, crowd selection and icon inspection work')
            visit('handoff')
            page.locator('[data-art-check]').first.check()
            page.emulate_media(media='print')
            assert page.locator('.sidebar').is_hidden()
            assert page.locator('.art-checklist').first.is_visible()
            page.pdf(path=str(output / 'checklists.pdf'), format='A4', print_background=True)
            report['checks'].append('Printable checklist layout rendered to PDF')
            if report['external_requests']:
                raise AssertionError('Unexpected external browser requests')
            if report['errors']:
                raise AssertionError('Browser page errors')
            report['status'] = 'pass'
        except Exception as error:
            report['errors'].append(str(error))
            page.screenshot(path=str(output / 'failure.png'), full_page=True)
        finally:
            browser.close()
    (output / 'art-bible-browser.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        return run(args.chromium, args.output)['status'] != 'pass'
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
