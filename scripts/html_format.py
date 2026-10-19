"""Apply the project's pinned Prettier configuration to generated HTML."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

FORMATTER = Path(__file__).with_name('format_html.mjs')
_formatted_html = {}


def format_html_documents(documents):
    pending = {path: source for path, source in documents.items()
               if path.endswith('.html') and source not in _formatted_html}
    if pending:
        try:
            result = subprocess.run(['node', str(FORMATTER)], input=json.dumps(pending),
                                    capture_output=True, text=True, timeout=120)
        except FileNotFoundError as error:
            raise RuntimeError('HTML generation requires Node.js and Prettier; install Node.js and run npm ci.') from error
        if result.returncode:
            raise RuntimeError('HTML formatting failed; run npm ci to install pinned Prettier.\n' + result.stderr)
        formatted = json.loads(result.stdout)
        _formatted_html.update((source, formatted[path]) for path, source in pending.items())
    return {path: _formatted_html[source] if path.endswith('.html') else source
            for path, source in documents.items()}
