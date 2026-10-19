from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify BW-003-T02 launch isolation against existing exports.")
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.game_root.resolve()
    bundle = arguments.artifact_dir.resolve()
    output = arguments.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / "tools"))
    from check_client_artifact import engine_command
    from run_baseline import artifact_command, source_build_revision
    engine = engine_command(None) + ["--path", str(root)]
    manifest = json.loads((bundle / "manifest.json").read_text())
    launches = [("native-client", engine + ["--", "--role", "client"]),
                ("native-server", engine + ["--", "--role", "server"])]
    for role in ("client", "server"):
        launches.append(("exported-" + role, artifact_command(bundle, role) + ["--headless", "--"]))
    results = []
    for label, launch in launches:
        for option in ("--seed", "--clock", "--owner-epoch", "--test-control"):
            command = launch + [option, "forged"]
            process = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=10)
            captured = process.stdout + process.stderr
            log_name = label + option + ".log"
            (output / log_name).write_text(captured)
            passed = (process.returncode == 2 and "Unknown baseline option." in captured
                      and "context-started" not in captured and "server-ready" not in captured)
            results.append({"label": label, "option": option, "command": command, "cwd": str(root),
                            "exit_status": process.returncode, "passed": passed, "log": log_name})
    report = {"result": "Passed" if all(case["passed"] for case in results) else "Failed",
              "source_build_revision": source_build_revision(),
              "export_build_revision": manifest["build_revision"],
              "export_source_manifest_sha256": manifest["source_manifest_sha256"], "cases": results}
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], len(results), output)
    return 0 if report["result"] == "Passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
