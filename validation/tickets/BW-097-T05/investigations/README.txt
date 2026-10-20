Exploratory source-only rendering investigations, 2026-10-20.
These logs are historical diagnostics, not current ticket acceptance.

The initial full run exposed reversed winding in one synthetic fold and a
real convex side rim in the grazing-box fixture. The winding was repaired;
the grazing fixture now isolates a sloped plane rather than a box rim.

Final palette quantization at 32/16 linear RGB levels was investigated
because it reduced the number of varying stationary pixels. It amplified
small residual color changes and was rejected. The current candidate retains
source albedo colors and uses three diffuse lighting bands. The temporary
focused runner is the last exploratory version, not an immutable reconstruction
of every earlier experiment; exact per-run settings/source hashes and original
engine output remain in the corresponding retained launcher records. Some
exploratory runs were stopped or their source settings changed while they ran;
they are retained as failures and confer no current pass.

A hard-shadow-band experiment increased visible changes and was rejected.
Disabling the toon material specular term and adding a 16-render-frame warmup
were examined without changing the approved T02/T04 owners. Strict stationary
color identity remains the current gate until an explicit T05 review decides
otherwise. No T04 deviation is inherited.
