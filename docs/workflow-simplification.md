# Documentation workflow audit and measurements — 2026-10-22

Task base / rechecked main: `47b1dea02682875f3be3b95d80577280e1c2a206`.
The companion game started at `c47f367c37950cbb6b992e307eae907ebc19e60e`.
[Validation policy](validation.md) is the single maintained command/ownership entry
point. Both PRs are cross-linked in their descriptions; merge the documentation
workflow before adopting the updated game ticket skills. Neither PR was merged.

Previously, a roadmap edit ran whole-site Prettier, the data/links/roadmap/inventory
aggregate, validator regression modules and Chrome; FULL was still required for
final delivery and every CI PR. Unknown files or failed Git scope silently selected
FULL. This is replaced by QUICK content checks, an affected generated-output PR
gate, conditional browser integration, and explicit/weekly FULL.

| Owner/check | New trigger and decision | What remains / coverage difference |
| --- | --- | --- |
| Roadmap validator | Current graph/evidence/IDs/AC references for planning QUICK | Required evidence, hard dependencies and completion rules unchanged |
| Model/inventory validator | Relevant contract/data edits | Canonical schema, reviewed source coverage, authority and compatibility unchanged |
| Validator/generator regressions | Python implementation imports/dependents change; FULL | No malformed-graph tests for ordinary ticket text |
| Data arithmetic/recipes | Affected shipped data at PR gate; FULL | No unrelated data calculations for planning |
| Every-level allocation/capstone searches | Catalog/talent/class/specialization/allocation inputs; FULL | No 2,940 cases for ticket edits; all cases retained |
| Two generators' freshness | Once after actual generation/review, at relevant PR gate | Formatted HTML/schema/search/navigation/manifest remain current; writes only changed bytes |
| Static links/search | Changed rendered HTML/search, relevant PR gate, FULL | All destinations/anchors/canonical epic/AC structure remain checked |
| Chrome | UI/template/CSS/JS/browser implementation changes, explicit integration/FULL | First/last/largest epic samples replace every-epic desktop/mobile visits; actual search/navigation/print/no-JS remain |
| Whole-site formatting | FULL; changed HTML formatted directly | Removed routine duplicate formatting pass; generated freshness still compares formatted bytes |
| Engine-artifact audit | Changed legacy engine inputs; FULL | Docs cannot silently acquire legacy implementation |
| Evidence output | Explicit report destination; ignored local paths / CI artifacts | Standalone aggregate/browser scripts no longer rewrite tracked evidence by default |
| CI | Focused PR gate; weekly/manual FULL | Real browser on relevant inputs; no Unreal certification |

On macOS 27 ARM64 / M2 Max / 32 GiB / Python 3.14.0, with existing Node 24.22.1 / Prettier 3.8.3 and
Chrome 155.0.8059.86, the original main roadmap FAST chain took **92.399s**: 59.816s validator
regressions, 16.443s aggregate, 9.345s browser, 6.609s whole-site formatting.
The reported 181.7s old CI FULL remains historical, not a matched local benchmark.

| Representative edit / scope | New wall time | Reduction from measured roadmap FAST |
| --- | ---: | ---: |
| Documentation wording QUICK | 0.995s | No matched wording baseline |
| Ticket scope wording QUICK | 1.004s | 91.395s / 98.9% |
| Ticket PR source/freshness/static gate | 17.111s | 75.288s / 81.5% |
| Contract metadata QUICK | 3.251s | No matched contract baseline |
| Contract PR source/freshness gate | 16.132s | No matched contract baseline |

QUICK defers freshness and rendered-site checking until delivery; the PR gate
retains applicable structural/source/generated correctness, while omitting unchanged
validator regressions, unrelated data arithmetic and browser behavior. This is a
coverage policy change, not an assertion of identical execution. Every figure
includes interpreter startup, selection, identity hashing and subprocesses. Exact
source bytes were restored after reversible wording/metadata probes. Scope was
supplied explicitly to isolate representative work from the infrastructure branch;
actual delivery/CI scope includes the whole task. No gameplay contract semantics,
status, ACs or evidence were changed to fabricate a benchmark.

Common QUICK meets <5s; small PR verification meets 15–20s locally with prerequisites
already installed. Freshness rendering/formatting is now the PR bottleneck; no cache
framework was added. Current-input identity omits unchanged historical detail
archives, while explicitly changed archives remain identified. No historical
passing artifact is treated as current game execution.

FULL passed **243 aggregate checks, 2,940 allocation cases, 98 capstone routes,
99 Python regressions, four Node cleanup tests and 110 browser assertions** in
**109.974s**. The old exhaustive browser record had 296 assertions; static canonical
page/AC/link checks replace repetitive browser structure checks. Final selector/
identity refinements then passed **14 focused regressions**, including failed Git,
unknown PR scope, malformed JSON, missing links/anchors, stale input identity,
conditional allocation/browser work and archive hashing. Earlier full regression
coverage retains invalid dependency/AC/evidence and stale generated output controls.
The passing unchanged model/generator/browser stages were reused after selection
refinements; no comprehensive rerun was required for evidence prose.

An edited fragment initially failed formatting; that file alone was formatted,
affected output regenerated and the failing check corrected before passing FULL.
Only successful workloads enter timing comparisons. Missing executables, missing
prerequisites and unresolved PR impact return nonzero rather than claiming success.
The source fingerprint update in `sources/data-inventory.json` reviews the changed
maintenance instructions; it changes no canonical gameplay contract.

Artifact audit: 1,738 tracked files / 64,754,950 bytes under existing epic/ticket
execution evidence, plus other performance/report history. All referenced history
was preserved. New reports live under `.git` or ignored artifacts; Actions retains
details for 14 days. A compact durable summary accompanies acceptance evidence;
expiring artifact links cannot replace required long-term records. No raw execution
log, screenshot set, package, or source snapshot is added by this task.

[Compact evidence](workflow-simplification.json) contains measured scope, source and
environment identities, stage timings and outcomes. The complete per-stage audit
is in the companion game's `docs/workflow-simplification.md`. Local raw logs remain
under workspace `artifacts/workflow-simplification`; they are not claimed uploaded.
Native game FULL was attempted but blocked by the preserved local plugin setup
(DarkerNodes cook errors; ElectronicNodes absent in source engine). Docs success
never certifies that packaging, Server build, real peers, persistence or visual
acceptance. The manual browser procedure is documented; no human observation is
fabricated. New checks require purpose, trigger, owner, layer, measured cost and
nonduplication justification; selector regressions enforce bounded routine work.
