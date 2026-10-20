# Repository instructions

## Mandatory workspace Git and pull request workflow

For every task that changes `mmo_docs`, create a new task branch and open a pull request in this repository. The documentation baseline designates no game implementation repository. Documentation, tests, tooling, generated files and retained evidence count as changes. Read-only inspection does not require a branch or PR.

This is standing user authorization to create task branches, commit task-scoped changes, push those branches and open PRs. Do not request separate confirmation for these steps. This authorization takes precedence over guidance requiring fresh per-task approval for those Git actions. Explicit user instructions for the current task take precedence; repository scope restrictions and safeguards for unrelated work still apply.

Branch names must use `<type>/<ticket-or-topic>` with a conventional lowercase prefix: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `style` or `revert`. Use lowercase kebab-case for the ticket/topic and choose the type that matches the work. Do not use agent or vendor prefixes such as `codex/`.

1. **Start from the latest main.** Before editing each repository, inspect its status, branch, remotes and any active Git operation. Fetch `main` from its authoritative remote and record the fetched commit SHA. Create a new, descriptively named task branch directly from that exact remote `main` HEAD. Do not base it on stale local `main`, an existing feature branch or unrelated unmerged commits. Use a separate worktree when needed to preserve the current checkout and user edits.
2. **Keep each repository scoped.** Use one new branch per changed repository for the task; continue on that branch for follow-up work on the same task. If task changes already exist, transfer only those changes onto the new branch while preserving unrelated work. Never reset, clean, force-checkout, automatically stash, or overwrite user changes to obtain a clean base.
3. **Recheck main before delivery.** Fetch remote `main` again before opening the PR. If it advanced, integrate its latest HEAD into the task branch without rewriting shared history or force-pushing, resolve conflicts within scope and rerun affected checks. Record the updated main SHA and tested revision in the delivery evidence.
4. **Publish a PR for every changed repository.** Review and commit only task-scoped changes, push each task branch and open its PR targeting `main`. Describe the resulting behavior, validation and remaining limitations; link related PRs when a task spans repositories. Do not merge PRs, tag releases or deploy without an explicit user request.
5. **Verify delivery.** Confirm that every changed repository has its pushed branch and open PR, then include every PR URL in the final report. Do not call delivery complete while any required PR is missing. If fetching current `main`, preserving existing work, pushing or opening a PR is blocked, report the exact blocker and finish independent safe work; never silently substitute an older base or omit a repository.

## Documentation scope and technical baseline

This repository is the independently usable Briarwake design reference. The game is a new Unreal Engine 5 native C++ MMORPG with server-authoritative dedicated servers and zero credited implementation. No implementation repository location is designated; do not infer, link or require one, create a game project here, or use workspace-relative game/skill paths. Repository-local workflows are in `.agents/skills/`; technical standards are in `guide/unreal-cpp.html`.

Preserve gameplay rules, canonical identifiers, encodings, schemas and catalog relationships. Roadmap/progress ownership is `sources/development-roadmap.json`; inventory ownership is `sources/data-inventory.json`. Inspect generators before running them. Follow `README.txt` for deterministic documentation generation and validation. Documentation evidence is separate from game execution. Supplied replication plugins are already acquired and await capability, compatibility and integration verification. Never invent plugin details or capabilities.

Comments exist only when they reduce the effort required to understand code; prefer clear names and structure. Add no speculative frameworks or placeholder C++ classes. Retain useful comments and legitimate verification gates. Keep changes scoped and report actual checks separately from not-run Unreal or browser checks.
