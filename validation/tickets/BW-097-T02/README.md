# BW-097-T02 execution evidence

Implemented game revision: `4339aeeae46b49d4bc8fbf2d3ff7ee6cb423b5f3`.
The ticket is Complete; BW-097 remains In Progress for T03–T06 and final UI/readability gates.
[Reviewed results and identities](review.json), [frame observations](observations.json),
[per-frame coordinates](frames.csv), and [editor configuration recovery](configuration-review.json)
are the durable acceptance record.

- **Purpose:** verify genuine orthographic/perspective endpoints, reversible visible zoom,
  following, unchanged route/aim, and validated tuning through the existing Unreal Data Asset.
- **Prerequisites:** UE 5.8.3 CL 58210709, Xcode 27.0 build 27A266a, macOS ARM64,
  the versioned reference map and configuration, and a passing Editor build. Tests used
  the M2 Max/32 GiB host. The original editor and staged project-plugin preferences were preserved.
- **Setup:** run from GAME_ROOT, the workspace containing `Briarwake.uproject`.
  Use `python3 tools/validate.py --mode native --suite camera`. Launch the reference level
  as documented in the game's `docs/camera-reference.md`, then Play in standalone PIE.
- **Execution:** run stationary, axial and diagonal routes with endpoint requests and rapid
  reversals. Actual rendered viewports were 1280×720, 1920×1080 and 1280×960. Native tests
  check 30/60/120 FPS interpolation. Captured median rates were 29.98/15.80/28.40 FPS;
  screenshot overhead and background editor work prevent a 60/120 FPS performance claim.
  Typed wheel commands and native possessed-pawn input-binding callbacks use the same rig.
- **Expected results:** the controlled foot/head remain within 5% viewport margins, reference
  floor Z and continuous aim stay unchanged, and zoom reaches exact endpoints. Native tests
  assert 45 handoff landmark/window/route comparisons below 0.5 pixels. Actual held samples
  measured at most 0.06626 pixels forward/reverse and 0.000206 pixels on overview round-trip.
  Some zoomed landmark projections are outside the viewport; visible body framing is checked separately.
- **Negative cases:** nonfinite/range/policy/sample rejection, bounded input, rapid reversal,
  ended-rig rejection/reset, arbitrary possessed controller aim and serialization run natively.
  A real editor handoff-FOV edit of 0 was rejected atomically. The authored preset saved and
  recovered every field after restart; live close properties matched FOV75/distance360/
  pitch−20/focus(10,15,125). Defaults were restored and recovered on another restart.
- **Cleanup:** owned PIE/editor instances stopped; original play-window settings and camera
  defaults restored. Original map/configuration bytes and the user's staged descriptor blob
  remain unchanged. No worktrees, project copies, unrelated resaves or cache cleanup were used.
- **Evidence:** [endpoints](endpoints.png), full-resolution [orthographic handoff](hold-ortho.png)
  and [perspective handoff](hold-perspective.png), sampled motion for
  [stationary](stationary-1280x720-30-final.gif), [axial](axial-1920x1080-60-final.gif) and
  [diagonal](diagonal-1280x960-120-final.gif) routes. GIFs use real in-engine screenshots,
  reduced to 480px width, with timing derived from recorded world time.
- **Limitations:** physical OS wheel-device/focus/capture routing was not certified by the
  available UI surface. Orbit/pointer capture, production picking/privacy/occlusion, art and
  accessibility, cooked camera scene and performance remain T03–T06. The finite narrow-FOV
  approximation places the default handoff about 62 km from focus; long collision sweeps and
  renderer behavior need those later checks. No production movement/aim or protocol was added.

The original [70-degree native handoff failed](failed-native-70-degree-handoff.png);
[geometric measurements](native-handoff-measurement.json) retain that diagnostic.
An earlier rendered run also exposed Unreal's camera-derived human-player base aim.
The reference pawn now reads its existing controller rotation; current native and rendered
checks pass. These historical failures are distinguished from current evidence in the review.

For repeatable observation, [capture.py](capture.py) is the bounded editor-side observer used
for the rendered procedures. Enable `PythonScriptPlugin` for that launch and pass
`-ExecutePythonScript="$PWD/mmo_docs/validation/tickets/BW-097-T02/capture.py"` to the Editor
command from the game documentation. It keeps that owned editor alive, waits for PIE, and
reads `artifacts/bw-097-t02/rendered/command.json`. Use fresh unique command IDs when repeating:

```json
{"id":"new-unique-stationary-run","action":"run","route":"STATIONARY","cap":30}
```

The observer writes six endpoint requests, including rapid reversals, projected coordinates and sampled
screenshots under that GAME_ROOT artifact folder. `AXIAL` and `DIAGONAL` select other routes.
On this Retina host, floating-window height settings 700/1060/940 yielded physical viewport
heights 720/1080/960; always inspect the recorded `width_height` rather than infer content size
from the outer window. Restore original play-window preferences afterward.

For exact held samples, start a fresh stationary overview. A `wheel` action with `detents:5`
reaches zoom 0.5; wait at least 1.25 seconds, then use a `snapshot` action with a fresh ID.
Next request `detents:0.00002`, wait and snapshot; reverse that increment and repeat.
Use +5 and −10 detents for close and overview. These call the same `AddWheelInput` API as
native wheel bindings. Close only the owned editor after stopping PIE.

The retained observer omits an unused prototype quit action. Its executed camera commands,
recording and timing behavior are unchanged. Native source reuse is also explicit: the three
motion cases preceded only the addition of BlueprintCallable metadata to existing rig input
methods; final held samples used the rebuilt final module. All presentation bodies match.
