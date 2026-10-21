---
name: execute-ticket
description: Execute a Briarwake implementation ticket only after the separate Unreal Engine 5 C++ game repository and prerequisites have been verified.
---

# Execute a ticket

1. Read the supplied ticket, its parent epic, linked data contracts, prerequisites, and acceptance criteria from this documentation repository. Follow its canonical source and generator instructions.
2. **Preflight gate:** This repository contains documentation only; the separate implementation is https://github.com/evanmcpheron/BriarwakeUnreal. Verify the actual game checkout, its instructions, current engine/toolchain and relevant plugin inventory before execution. Retained evidence applies to its recorded revision and environment; it does not prove current runtime capabilities. If prerequisites are unavailable, limit work to independent documentation planning and identify what remains unverified.
3. Once a valid game repository exists, inspect its real C++ project and build/test setup. Implement only the scoped behavior using native C++ gameplay ownership, server-authoritative outcomes and Blueprint assets only where they are appropriate. Evaluate built-in Unreal networking and verified replication plugins before adding new infrastructure.
4. Include the smallest fixtures or test level needed to execute every manual acceptance check. Record project-specific build targets, setup, client/server launch steps, expected observations and cleanup only after they have been verified against the actual repository.
5. Run the available checks and report separately which are executed, failed, blocked or unverified. Never present a planned test, a design fixture, a documentation test or a plugin claim as game runtime evidence.
6. Update `sources/development-roadmap.json` only with truthful implementation status and revision-specific acceptance evidence. `Complete` requires passing evidence for every criterion and all hard dependencies. Follow `AGENTS.md` and `README.txt`: regenerate affected documentation, use FAST while correcting changes and require FULL for final PR verification. Report the implementation commit, executed checks and remaining decisions; FAST never replaces acceptance evidence.
