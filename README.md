# Briarwake Development Guide

**Partial documentation edition — 9 October 2026.** This is an offline build manual, not a generated Unreal game. It contains initial implementation contracts and worked test specifications; it is not complete against the attached master prompt.

Extract the whole directory and open `index.html` in a desktop browser. Keep the folders together. The site is designed for offline use without a web server or CDN. URL-based browser verification was blocked by environment policy; isolated rendering/control checks are recorded separately. Browser storage is best effort; export checkmarks before moving the manual.

## Contents

320 HTML pages, 32 planned phases, 18 system chapters, 205 provisional asset contracts, five vocation routes, six original region-family pages and 15 worked interaction examples. The register is intentionally non-exhaustive. Individual asset pages are initial contracts, not fully specified or compiled implementations.

## Destination and source boundaries

Intended destination: `https://github.com/evanmcpheron/mmo_docs`. The target repository was initially inaccessible (404), then became readable. A create-file attempt was rejected with HTTP 403: Resource not accessible by integration. No remote changes were made. The GitHub connection needs write authorization for mmo_docs; game_docs is unchanged.

The actual art ZIP, multiplayer-plugin ZIP, companion audit documents, installed Unreal Engine 5.8.3 and installed PaperZD were unavailable. Plugin findings are reported by the brief, not independently verified source findings. The original brief is retained unchanged; its tentative `RPG` name is superseded by **Briarwake**.

## Rebuild and validate

Python 3.10+ is sufficient for generation and static checks; no third-party Python packages are needed for them. On Windows, use `py -3` in place of `python3` when appropriate for the installed Python launcher.

```sh
python3 tools/build_manual_indexes.py
python3 tools/build_manual_indexes.py --check
python3 tools/validate_documentation.py
python3 tools/check_phase_integration.py
python3 tools/check_feature_coverage.py
python3 tools/simulate_population_scaling.py
python3 -m unittest discover -s tools/tests -v
```

`python3 tools/check_feature_coverage.py --require-complete` intentionally returns nonzero while the master acceptance conditions are incomplete. Do not weaken this check to make a partial delivery appear complete.

Optional browser QA uses Python Playwright and an installed Chromium executable: `python3 tools/browser_checks.py --chromium /usr/bin/chromium`. This is not required to read or rebuild the site. Both file and local-HTTP navigation were blocked in the delivery environment; `python3 tools/render_checks.py` performs narrower in-memory checks. These do not prove normal navigation, real storage persistence or file downloads.

Read `AGENTS.md` before editing. Current evidence is in `verification/`; source/access limitations and not-run game tests are in `sources/verification.json`. See `DELIVERY_STATUS.md` for unresolved work. No paid art, plugin source/binary, runtime C++, game assets or external font files are included.
