# Briarwake Unreal

Native C++ implementation, created for BW-001 on 2026-10-21. The older Godot
project and the AI-guidance repository remain separate. This project currently
contains startup configuration checks and editor automation, with no gameplay.

## Build and check

Use native macOS arm64, Xcode 27.0 build 27A266a and Unreal Engine 5.8.3.
The Launcher build is changelist 58210709. The source engine is
Epic's `5.8.3-release` tag, commit
`396c9f059903aed5fec78ecd3d437a40c6415368`. Exact identities are checked by
[tools/toolchain.lock.json](tools/toolchain.lock.json); changing a pin requires
new build and runtime evidence.

Install Xcode from Apple and the matching engine from Epic. Verify the active
Xcode with `xcodebuild -version`. Clone this private repository, then run these
commands from the directory containing `Briarwake.uproject`:

```sh
python3 tools/check_baseline.py toolchain
python3 tools/prepare_build_tool.py
python3 tools/check_baseline.py build
python3 tools/check_baseline.py test
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/check_baseline.py build --target Briarwake
python3 tools/check_baseline.py package
```

The default engine directory is `/Users/Shared/Epic Games/UE_5.8`. Override it
with `--engine /absolute/engine/path` or `UE_ENGINE_ROOT`. Every invocation
creates a fresh `artifacts/<UTC>-<stage>-<identity>/` directory containing its
command, process status, source hashes, toolchain identity and logs. Existing
output directories are rejected. Build identities are explicit UBT dependencies;
the test stage rejects a native module built from different inputs.

The two `Briarwake.Baseline` automation tests evaluate the committed configuration
and an execution control. Run `python3 tools/check_baseline.py test --control
assertion-failure` to execute a deliberate failing assertion; it must return
nonzero. Rerun the ordinary test command for independent clean recovery.
`--timeout SECONDS` bounds each child process and stops its process group on timeout.
Test results are read from Unreal's actual report, including its UTF-8 BOM;
process exit alone does not establish an executed test.

## Dedicated-server prerequisite

The Launcher distribution rejects Server targets. Use a source engine for
`BriarwakeServer`, following Epic's [source build instructions](https://dev.epicgames.com/documentation/en-us/unreal-engine/building-unreal-engine-from-source)
and [dedicated-server instructions](https://dev.epicgames.com/documentation/en-us/unreal-engine/setting-up-dedicated-servers-in-unreal-engine).
The source engine is a separate installation; do not modify the Launcher engine.
The initial source checkout and dependency installation are:

```sh
git clone --depth 1 --branch 5.8.3-release --single-branch git@github.com:EpicGames/UnrealEngine.git /Users/Shared/UnrealEngine-5.8.3-source
cd /Users/Shared/UnrealEngine-5.8.3-source
./Setup.sh --exclude=Win64 --exclude=Win32 --exclude=Linux --exclude=LinuxArm64 --exclude=Android --exclude=IOS --exclude=TVOS --exclude=VisionOS --exclude=HoloLens --threads=4 --no-cache
git apply "/absolute/path/to/BriarwakeUnreal/tools/patches/ue-5.8.3-macos-xcode-stdin.patch"
```

From this game repository, the source-engine build command is:

```sh
python3 tools/check_baseline.py build --target BriarwakeServer --engine /Users/Shared/UnrealEngine-5.8.3-source --timeout 7200
```

The verification environment already contained this local engine patch. This task
used it without changing engine source. The patch and exact patched-file hash
are versioned here; the engine base commit stays pinned. The verifier rejects
other tracked engine source changes. The patch gives
Xcode a valid input stream when Unreal's build accelerator has closed inherited
descriptors. It changes the build tool, with no runtime or security-setting change.

The Server target is a console application. After building Editor and Server,
package and execute it from the game repository:

```sh
python3 tools/check_baseline.py package --target BriarwakeServer --engine /Users/Shared/UnrealEngine-5.8.3-source --output artifacts/server-package --timeout 1200
python3 tools/smoke_server.py --executable artifacts/server-package/package/MacServer/BriarwakeServer.sh --case pass --output artifacts/server-pass
python3 tools/smoke_server.py --executable artifacts/server-package/package/MacServer/BriarwakeServer.sh --case missing-config --output artifacts/server-missing
python3 tools/smoke_server.py --executable artifacts/server-package/package/MacServer/BriarwakeServer.sh --case invalid-config --output artifacts/server-invalid
python3 tools/smoke_server.py --executable artifacts/server-package/package/MacServer/BriarwakeServer.sh --case timeout --timeout 3 --output artifacts/server-timeout
```

Missing/invalid configuration and timeout deliberately return nonzero. The pass
case checks three dedicated world ticks, disabled rendering and zero local
players, controllers and pawns, then exits. A later pass uses a new output path.
The wrapper starts outside the source tree and binds only loopback port 17777.

Packaging uses the matching Launcher AutomationTool and cooker by default;
`--cook-engine` overrides that installation. Source AutomationTool could not build
an unrelated IOS automation assembly after the documented platform exclusions.
The matching installed tools avoid changing engine files. Mac UAT does not archive
a console Server executable correctly, so the wrapper assembles the staged Pak,
verified native executable, relocatable launcher and runtime libraries explicitly.
It validates library dependency closure and hashes the resulting package. A
zero process exit with an empty package is rejected. No engine installation or
source directory is needed to launch the resulting Server package on the tested
macOS host.

The Game build uses a side-by-side UBT prepared by `tools/prepare_build_tool.py`
from the pinned patched source. Existing Launcher build-tool files are preserved.
The preparation command verifies an existing copy or publishes a separate copy;
it requires the source-engine checkout described above.

## Configuration boundary

`FServerConfiguration` implements the canonical
[ServerConfiguration](https://evanmcpheron.github.io/mmo_docs/guide/data-inventory.html#server-configuration)
startup shape. It requires every field, rejects extra fields and wrong JSON
types, and accepts only nonempty revision identities, finite positive rates and
finite nonnegative durations. Loading is bounded to 64 KiB and rejection leaves
the prior value intact. This code validates configuration; it does not implement
a simulation, snapshots, disconnect handling or logout behavior.

Dedicated startup requires `-BriarwakeServerConfig=<absolute JSON path>`.
`fixtures/config/server.valid.json` is an explicit test configuration, including
test revision names and a test logout duration; it is not production balance.
Keep deployment configuration outside the distributed client. Fixture files
are outside `Content/`, and native tests are guarded by editor and development
automation flags.

All targets use the existing engine map `/Engine/Maps/Entry`. No authored maps,
credentials or configured network provider are required. Reset by
allowing bounded test processes to finish and invoking the command into a new
output directory. Keep earlier evidence; do not delete user assets or engine
files to recover a failed build.


## Client inspection and clean execution controls

The normal client package is `artifacts/<package-run>/package/Mac/Briarwake.app`.
Launch its exact `Contents/MacOS/Briarwake` executable from outside the checkout,
capture stdout, inspect its reported source identity, then close the window.
The baseline window is empty; it is not a playable gameplay scene.

```sh
python3 tools/inspect_client.py --bundle artifacts/client-package/package/Mac/Briarwake.app --report artifacts/client-inspection.json --self-test
python3 tools/verify_baseline.py --case pass --output artifacts/clean-pass
python3 tools/verify_baseline.py --case build-failure --output artifacts/clean-build-failure
python3 tools/verify_baseline.py --case assertion-failure --output artifacts/clean-assertion-failure
python3 tools/verify_baseline.py --case timeout --output artifacts/clean-timeout
python3 tools/verify_baseline.py --case pass --output artifacts/clean-recovery
```

Use `--output artifacts/client-package` on the client package command when using
the example inspection path. Inspection hashes loose files, lists and extracts
every Pak member, and rejects private paths and synthetic private content.
Its controls verify detection in loose files and in a compressed Pak whose raw
bytes do not contain the synthetic marker. Unknown containers fail inspection.
This is an inspection of the recorded baseline inputs, not a general secret
classification guarantee for arbitrary future assets.

Clean controls copy versioned inputs into disposable source snapshots without
Binaries/Intermediate/Saved caches, build native C++ and read actual Unreal test
reports. Build failure leaves runtime Not Executed; assertion failure remains
Executed/Failed; timeout never becomes an assertion pass. Only owned snapshots
and contamination fixtures are removed. Logs and reports remain in artifacts.

## Verified scope

BW-001 evidence is retained in the companion [mmo_docs PR](https://github.com/evanmcpheron/mmo_docs/pull/29).
The supported baseline is macOS ARM64 Development with the pinned UE/Xcode
versions. Editor automation, Game/client packaging and visible launch, source
Server packaging/headless execution, configuration rejection, decoded-Pak
inspection and clean failure/recovery controls are checked separately.
The Python wrapper suite has ten regression tests.

The supplied engineering docs and `Plugins/MultiplayerSessions` source, descriptor,
icon and `WBP_MenuWidget` asset are included. The plugin compiles and its widget
was compiled by Unreal. Connected Steam sessions, real accounts, provider setup,
multiplayer gameplay, persistence, capacity, other platforms, Shipping and the
separate Client-only target have not been tested. Steam session code is the
owner's imported work and is not a server-authority implementation.
