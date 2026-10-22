"""Apply the repository's pinned HTML formatter to generated pages in one process."""
from functools import lru_cache
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=4)
def _formatted_pages(pages):
    try:
        result = subprocess.run(['node', str(ROOT / 'scripts/format_html.mjs')],
                                input=json.dumps(dict(pages)), capture_output=True, text=True, cwd=ROOT)
    except OSError as error:
        raise RuntimeError('HTML formatting requires Node and npm ci: ' + str(error)) from error
    if result.returncode:
        raise RuntimeError('HTML formatting failed; run npm ci to install pinned Prettier:\n' + result.stderr)
    return tuple(json.loads(result.stdout).items())


def format_pages(pages):
    return dict(_formatted_pages(tuple(pages.items())))
