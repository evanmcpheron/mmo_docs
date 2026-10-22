# Documentation verification

Run from the mmo_docs Git root. This is the authoritative policy; README, skills and
CI refer here. Documentation verification never certifies Unreal or gameplay.

```sh
python3 validation/validate.py                         # QUICK, routine local work
python3 validation/validate.py --explain               # inspect impact and outstanding work
python3 validation/validate.py --gate                  # focused PR content + required freshness
python3 validation/validate.py --mode integration --gate # changed UI/template/browser behavior
python3 validation/validate.py --mode full             # intentional comprehensive regression
```

`--mode fast` is a compatibility alias for QUICK, with no native or FULL fallback.
Git selection includes branch commits since the merge base of origin/main, index,
worktree, deletions, renames and untracked files. `--base REF` must describe the real
task base. Never change it to hide task changes. Unknown dependencies or failed Git
detection run safe lightweight checks, print unresolved impact, and return **2**
with `--gate`. They never launch FULL. An empty clean scope checks whitespace only.
Exit 1 means an executed check failed; unavailable commands cannot pass.

| Mode | Coverage | Trigger |
| --- | --- | --- |
| QUICK | Changed JSON/Python parses; applicable roadmap graph, exact epic AC references, completion evidence, source-contract invariants and static links/search | Routine wording, ticket/planning, data and tooling work |
| NATIVE | Not supported; exits 2 and points to the game runner | Implementation belongs in the game checkout |
| INTEGRATION | QUICK plus representative real Chrome navigation, search, responsive layout, print and no-JavaScript checks when UI/template/browser inputs change | CSS, JS, rendering template or browser harness changes |
| FULL | Full formatting, data calculations/2,940 allocations, all Python regressions, both generators' freshness, site links/search, representative browser behavior, cleanup and engine-artifact audit | Affected broad harness changes, milestones, explicit requests, weekly CI |

`--gate` adds both generators' freshness once for affected source/output changes.
It adds current data invariants for changed shipped JSON; allocation searches run
only for catalog/talent/class/specialization/allocation inputs. QUICK roadmap source edits defer unchanged rendered-site link scanning until the
PR freshness check. Validator and
generator code changes select regression modules through their Python imports;
content edits do not run tests of validator implementation. QUICK does not prove
rendering; a UI change with `--gate` requires INTEGRATION or FULL. Static required
links, anchors, canonical epic pages and AC rendering are checked across all pages;
the browser samples shared templates rather than revisiting every epic twice.

Python 3.10+ and Git support wording/roadmap QUICK. Generation/freshness requires
Node and the pinned Prettier (`npm ci` once when its lockfile changes). Browser
verification needs Node 22+ and installed Chrome/Chromium; set
`BRIARWAKE_CHROME_BIN` if necessary. Missing tools are **Not Run**, never a pass.

## Generate once, verify once

Canonical JSON owns contracts and planning. After actually reviewing a roadmap edit:

```sh
python3 scripts/build_development_roadmap.py
python3 scripts/build_data_inventory.py --review-roadmap
python3 validation/validate.py --gate
```

Builders write only changed bytes. `--review-roadmap` records the reviewed generated
planning references; it is not a read-only validation workaround. For a feature
HTML edit, format that file only (`npx --no-install prettier --write guide/PAGE.html`),
review its contract associations, then use the existing `--review-page PATH` option.
Do not format the entire site during routine work. Generator freshness already
compares formatted output, so the PR gate does not add a duplicate whole-site
formatter pass. FULL intentionally retains the repository-wide formatting audit.

After a game ticket, reuse its applicable revision/input/environment evidence,
update only justified canonical status/evidence, review affected generated views,
generate once, then run `--gate`. No additional game build or documentation FULL
is implied by a status change. Missing AC evidence or incomplete dependencies keep
a ticket unfinished. The roadmap validator still rejects unsupported completion.

## Manual browser acceptance

Purpose: judge readability and visual presentation that structural checks cannot
establish. Prerequisites: installed browser, freshly generated local site. Setup:
open `guide/development-roadmap.html` from this checkout. Execution: open the affected
epic/ticket through its actual links; at 1440px and 390px widths read its longest AC,
open navigation, use search, print preview, then disable JavaScript and reload.
Expected: readable text, usable links/navigation, no horizontal body overflow,
criteria visible in print and without JS. Negative cases: empty/unmatched search
must show no incorrect destination; missing required links are failures. Cleanup:
close preview, restore JS and viewport; do not alter sources. Evidence: record
browser version, changed pages, widths, observed results, and at most one screenshot
per distinct failure or material presentation claim. Limitations: this does not
prove all pages, accessibility conformance, game runtime or authority behavior.
Record **Not Run** when the interface is unavailable. Game procedures and the common
nine-field record are in the companion game's `docs/manual-testing.md`.

## Evidence and performance controls

Commands are read-only by default. Use `--report-dir .git/validation-evidence/RUN`
for local details, or the existing Actions artifact upload (14-day retention).
Retain one compact reviewed summary with revision, changed-input digest, scope,
environment, commands, results, limitations and stable artifact reference for a
completed ticket. Long-term acceptance evidence must remain accessible beyond CI
artifact expiry. Do not replace a durable roadmap reference with an expiring link.
Keep historical referenced evidence; do not commit routine logs, screenshots,
packages, duplicate reports or source snapshots. No automatic cleanup of user work.

A previous pass may be reused only if relevant source/output content, selected
verification, validator and environment identity still match. A timestamp or Git
revision alone is insufficient. Current sources/outputs and explicitly changed files are hashed; unchanged historical
ticket/epic/performance detail archives are not reread just to hash a wording edit.
Their durable acceptance records remain revision-specific. No persistent validation cache is introduced.
Rerun only invalidated stages; record their successful identity and scope in review.

Budget on the documented M2 Max host: common QUICK <5s, small PR gate ideally
15–20s. Cold builds/browser setup are distinct workloads. Measure end-to-end wall
time (including startup/selection) for a representative edit; disclose exceeded
budgets and fix the largest redundant work before adding caching. Comprehensive
runs are measured separately. See [audit and measurements](workflow-simplification.md).

Every new check must state in its PR its purpose/defect, trigger/dependencies, owner,
testing layer, expected cost, and why an existing check cannot cover it. The owner
is the module enforcing the invariant, not a new registry. Extend an existing suite;
do not add a project-wide stage for each ticket. Selection regression tests enforce
no FULL fallback, no content-triggered browser/regression suite, conditional
allocation work, missing-tool failure and blocking of unresolved PR claims. Keep
these tests alongside `validation/test_validation.py`. FULL stays explicit.
