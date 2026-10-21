AA / OUTDOOR PASS-BY / FIRST COMPUTATIONAL ITERATION / 21 OCTOBER 2026

CONFIRMED USE
People walk past outdoor nozzles. No seat, roof or enclosure.
Study nominal nearest-target distances 0.2, 0.35 and 0.5 m.
Valve activation is at most 30 s; personal exposure is much shorter.
Walking speed 1.2 m/s is an assumption; 0.6/1.8 m/s are sensitivities.

WHAT THESE RESULTS MEAN
Unconfined dry buoyant URANS with virtual moving 5 x 5 cm air patches.
NO human body, blockage, wake, skin heat transfer or comfort prediction.
An air-temperature deficit is a necessary delivery test, not person cooling.
Read results/cfd-summary.json for actual completed case counts and values.
All full native fields remain locally in cfd/cases/.
The previous seated-enclosure temperatures are not used as pass-by evidence.

DESIGN ITERATION
Nine controls: one side, two sides, overhead, each at 20/35/50 cm.
Four outlets and the same nominal source/total area in every control.
Follow-ups compare a 280x40 mm slot against 140x80 mm, two grid sizes,
0.5 m/s opposing wind, a four-position one-height row, an 8 C heat-pickup
source state and an 8 degree upward prescribed-velocity aim test.
The aim test follows a native-field diagnosis of cold-core downward shift.
It uses oblique flow on vertical slot patches, not fully tilted CAD faces.
No global optimizer or optimal physical design is claimed.

TIMING
Controls run 10 s; selected early controls run 30 s. Compare their common
5 s centre-crossing passage. Later arrivals are retained in individual
case audits. Ideal full cold flow starts at the nozzle at t=0. Upstream
valve response, motor spin-up, line cooldown and valve shutdown are absent.

SOURCE AND FORMAL MATH
source-input.json records the paired four-motor first-law hypothesis.
Nominal 77.6 g/s; 0.959 C supply; 30 C ambient; 2.267 kW cold-air power.
3.888 m3/min free-air demand; ideal 30 s event = 2.328 kg / 1.944 m3 free air.
Source state is calculated directly from this input, not old seat CFD.
The actual motor/load thermal state and commercial flow network are unknown.
Changing source inputs requires a new campaign; do not mix them with old audits.
FIRST-PRINCIPLES.txt explains timing, mixing, source methods and limits.
../formal-model/AAThermo/PassBy.lean adds seven conditional theorems.
Lean/mathlib 4.31.0: 57 printed axiom checks pass. No new physics axioms.
Lean proves mathematical implications, not CFD accuracy or hardware.

CAD
cad/: 140x80 and 280x40 mm exit prototypes. STL units mm; STEP units m.
100 mm nominal spigot; 95.2 mm clear inlet; 205 mm long; 2.4 mm wall.
Watertight, consistent normals, one component; STEP reimport/remesh unit check.
Fit coupons: nominal OD 99.4/100/100.6 mm. Actual fit is not verified.
Bambu H2S / PLA / 0.4 mm: start 0.2 mm layers, 4-6 walls; inspect supports.
No G-code, fitted stand, stock motor connector or pressure certification.
External CFD shares outlet dimensions, not the actual internal loft mesh.

REPRODUCE
Python environment: ../.venv-cfd/bin/python. numpy/scipy/matplotlib/gmsh/
trimesh/Pillow; ffmpeg for movies; ReportLab for PDF. Lean uses its pinned
4.31.0 toolchain and declared mathlib dependency; .lake cache is excluded.

  python scripts/screen.py
  python scripts/open_flow.py NEW_CASE --layout one-side --distance .35 --end 10 --run
  python scripts/analyse.py NEW_CASE
  python scripts/replay.py SAVED_CASE NEW_UNIQUE_CASE
  python scripts/summarize.py
  python scripts/core_diagnostic.py
  python scripts/make_cad.py --width .28 --height .04
  python scripts/animate.py R00_wide_d35
  python scripts/update_overview.py

Pinned arm64 Docker solver:
microfluidica/openfoam:2506@sha256:9ab54b92553d58a2e21adaf4ef98a8d0c118a09a1b388bd95480720ed7809b37
The mesh/source writer and native parsers reuse existing tested project
library files. Seat geometry and seat temperature fields are not imported.

EVIDENCE AND PACKAGE
Individual checkMesh, solver/reconstruction logs, audits and moving traces.
Failed original overhead-50cm mesh is retained in cfd/rejected. It failed
before solving; the fine/coarse grid transition was repaired and rerun.
Numerical screens cover finite fields, completion, mass/origin/energy closure.
They are not a rigorous continuum-error or physical uncertainty bound.

Package: selected full native fields/probes, all case exact initial/mesh/
dictionary inputs, audits/traces/logs and hashes for other native fields;
source, CAD, animations, report and formal proofs. Dependency caches excluded.
Single living overview: ../../project-overview.html#pass-by-results.

NEXT MODEL
Moving upright body and wake, then heat transfer versus ambient baseline;
actual source/valve/line startup; domain/turbulence/wind/source sensitivities;
commercial branch balance and interfaces; minimum useful exposure per person.
