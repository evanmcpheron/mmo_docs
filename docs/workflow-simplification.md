# Workflow reduction — 2026-10-23

This PR implements [the lean workflow policy](validation.md), rather than adding
another validation layer. The companion game's `docs/workflow-simplification.md`
contains the BW-097-T02 audit and native decisions. The historical camera record
at [review.json](../validation/tickets/BW-097-T02/review.json) remains unchanged.

The 113.636s native run (49.810s build, 58.995s engine tests) cannot explain the
reported approximately 80-minute task. Rendered cases, 240 frame observations,
GIF/capture work and save/restart checks are documented but not fully timed.
Original T02 criteria require quantitative continuity, variations and UI save/reload;
we preserve those requirements/history. Their particular artifact count, formatting,
restarts and repeated reconciliation must not become ordinary ticket requirements.
No estimate of total editor, reasoning, CI or evidence-preparation time is asserted.

Implemented changes:

- Remove 160 generated roadmap review/fingerprint records from the inventory;
  generated HTML remains checked against authoritative roadmap JSON. Feature and
  canonical contract reviews stay intact; all 501 contract definitions are unchanged.
- Roadmap generation now owns its search records/counts. Routine status changes
  run one generator and scoped source/freshness/link checks; no inventory builder,
  unrelated allocation cases, validator regressions or browser execution.
- Replace Python import-graph selection with adjacent tests and deliberate caller
  test selection. Hash selected changed inputs, not every tracked output/archive.
- Admit explicit Not Run evidence; it blocks Complete even if an older pass exists.
  Keep IDs, exact AC/parent/dependency checks and truthful acceptance. Existing
  tickets/epics, ACs, completion statuses and accepted evidence are unchanged.
- Skills forward to the single workspace procedure. Update only necessary records
  once; no parent/phase/dashboard audit, source-manifest tree or repeated game run.
- Remove weekly exhaustive CI and automatic evidence uploads. Existing logs remain;
  full/browser diagnostics are explicit. Ignore new routine capture/log archives.

Warm macOS ARM64/Python 3.14 measurements, one sample each:

| Workload | Before | After |
| --- | ---: | ---: |
| Roadmap source/freshness/static-site gate | 15.968s | 6.667s |
| Roadmap generation freshness | 2.618s | 2.785s |
| Additional inventory generation freshness | 10.300s | Removed |
| Combined generation checks + roadmap gate | 28.886s | 9.452s |

Before source: docs `3b57bcc0957323fb18e104d5559ce709b5a905b9`; after: workflow
source on this PR branch. The combined comparable path is about 67% shorter;
this does not measure total ticket implementation. Isolated mocked wording selection
measured 0.269s. The actual overhaul gate passed 63 affected regressions (49.334s)
and all selected stages (63.777s); ordinary content edits select none of those
validator/generator regression modules. Necessary formatting/startup remains the
main documentation cost. Local logs are bounded under workspace `artifacts/`.

Regression coverage includes documentation/status/AC/contract selection, malformed
JSON, invalid definitions/dependencies, missing evidence, pending human QA, static
anchors and output freshness; no native build can be selected by docs. The game
companion tests ordinary/new C++, camera, tooling, config/plugin and failed native
result selection. No full historical matrix or new evidence archive was generated.

Not run at this local checkpoint: browser/visual QA, native/game integration and
hosted CI. This change preserves UI output except the removed duplicate inventory
review list and the revised maintenance policy text; no visual design changed.
Routine manual QA may be handed off as Not Run. Neither delivered PRs nor passing
documentation checks can make unfinished gameplay acceptance Complete.
