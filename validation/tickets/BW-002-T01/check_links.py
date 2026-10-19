from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


DOCS_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = DOCS_ROOT.parent
DOCUMENT = WORKSPACE_ROOT / "briarwake/docs/architecture/authority-boundaries.md"


class HtmlAnchors(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: set[str] = set()

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        for name, value in attributes:
            if value and (name == "id" or (tag == "a" and name == "name")):
                self.anchors.add(value)


def main() -> int:
    source = DOCUMENT.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]\n]+\]\(([^)\s]+)\)", source)
    checked: list[dict[str, str]] = []
    failures: list[str] = []
    for link in links:
        parsed = urlsplit(link)
        target = (DOCUMENT.parent / unquote(parsed.path)).resolve()
        failure = ""
        if parsed.scheme or parsed.netloc or parsed.query:
            failure = "Expected a local workspace reference"
        elif not target.is_relative_to(WORKSPACE_ROOT) or not target.is_file():
            failure = "Target is missing or outside the workspace"
        elif parsed.fragment:
            if target.suffix != ".html":
                failure = "Unsupported fragment target"
            else:
                parser = HtmlAnchors()
                parser.feed(target.read_text(encoding="utf-8"))
                if unquote(parsed.fragment) not in parser.anchors:
                    failure = "HTML fragment is missing"
        if failure:
            failures.append(f"{link}: {failure}")
        checked.append({"link": link, "result": "Failed" if failure else "Passed"})
    if not links:
        failures.append("No Markdown links found")
    print(json.dumps({
        "document": DOCUMENT.relative_to(WORKSPACE_ROOT).as_posix(),
        "sha256": hashlib.sha256(DOCUMENT.read_bytes()).hexdigest(),
        "link_count": len(links),
        "unique_link_count": len(set(links)),
        "checked": checked,
        "failures": failures,
        "result": "Failed" if failures else "Passed",
        "scope": "Local file and HTML-fragment checks only; no semantic or runtime test",
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
