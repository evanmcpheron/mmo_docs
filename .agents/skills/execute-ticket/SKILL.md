---
name: execute-ticket
description: Execute a Briarwake ticket URL through implementation, scene setup and verification, fixing small blockers or asking the user for guidance.
---

# Execute a ticket

1. Read the supplied ticket URL, parent epic, linked contracts and dependencies. Use local sources when available. Inspect the actual implementation and follow the applicable repository instructions. This repository holds documentation; Godot code belongs in `../briarwake`.
2. Implement the ticket's scope and acceptance criteria. Add any scene objects, fixtures, test data or controls needed for its manual tests. Reuse an existing test scene or create a minimal one when needed, and record the exact launch/setup steps and expected results.
3. Keep working through blockers. Fix small, clear, reversible prerequisite issues within the ticket's scope and record the fix. If a decision, missing access or larger prerequisite needs user guidance, ask a specific question with a recommended next step. Continue independent work while waiting; when everything remaining needs the answer, wait for the reply instead of ending with a blocked report. Resume when the answer arrives.
4. Run the relevant checks and verify the acceptance criteria. Record what passed, failed or remains unverified; instructions for a manual test are not evidence that it ran. Fix failures caused by the change and retry the affected checks.
5. Update the ticket's status, blockers, evidence and manual testing instructions in `sources/development-roadmap.json`. Mark it `Complete` only when its criteria are verified. Preserve the parent epic's completion requirements. Rebuild and validate the documentation using `README.txt`, then report the changes, test results and anything still needing the user's verification.
