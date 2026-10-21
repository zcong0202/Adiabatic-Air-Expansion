SCOPE CORRECTION / 21 OCTOBER 2026
This study is a historical seated-enclosure computation. The user clarified
that people WALK PAST triggered OUTDOOR nozzles. No seat or enclosure is
part of the current assumed design. The reported temperatures do not
validate pass-by performance. CAD is an unselected prototype.
Current scope: ../current-design-scope.json and the single project overview.
Existing reports and ZIP remain historical records. Pass-by CFD is not run.

AA / MOTOR-SEAT CFD-CAD-LEAN LOOP / 19 OCTOBER 2026

Current report: output/pdf/AA-seat-CFD-CAD-Lean-iteration.pdf.
Current results: results/cfd-cad-loop.json.
Current overview: ../../project-overview.html in the original workspace.
The single overview includes the animation, CAD links, case table and limits.
Phase1 report: output/pdf/AA-motor-seat-viability.pdf (before seat CFD).
Full editable equations: FIRST-PRINCIPLES.txt.

WHAT WAS DONE
Loaded-motor first law -> Lean -> transient3D CFD -> custom outlet CAD ->
internal-nozzle CFD -> actual exit-profile transfer -> seat CFD repeat.
A3-active mode was tested within a4-installed architecture. Its longer run
misses20C at the neck. Four-active mode is the thermal candidate.
Numerical/geometry validation is separate from real hardware validation.
Some local peak speeds and unsteady temperatures remain material limits.
There is no global optimum or human-comfort claim.

GEOMETRY AND SOURCE
User accepted a0.9x0.85x1.8m reference seat enclosure with open front.
Side outlets:4x140x80mm, at x0.49m,y+/-0.45m,z0.84/1.24m.
Final custom outlet:100mm nominal hose spigot,95.2mm clear inlet,
205mm total length,2.4mm nominal wall. STL units:mm. STEP units:m.
The100mm inlet replaces the rejected50mm inlet after internal CFD.
Print PLA/0.4mm: start0.2mm layers,4-6 walls; inspect supports/overhangs.
Fit coupons are supplied. No physical fit, pressure rating or mount is proven.
Only the near-atmospheric outlet is custom. Commercial supply/load/collector/
insulated branches and interfaces are not a complete selected installation.

CASE PHYSICS
Perfect-gas variable-density buoyant URANS, k-epsilon,100W body heat input.
Adiabatic panels except C23's prescribed500W panel-to-air heat sensitivity.
This is not solar ray tracing, conjugate walls, a moisture/icing simulation,
or a fixed34C skin model. Do not infer human heat removal from air cooling.
Wind cases are short startups; check their time ranges before making claims.
Final hydrostatic pressure BCs passed the rest test. Earlier approximate
pressure runs remain labelled preliminary; failed pilots are not designs.

TOOLS AND REPRODUCTION
Python3.13; numpy2.5.4; scipy1.18.1; matplotlib3.11.2; CoolProp8.0.0;
gmsh4.15.2; trimesh5.1.1. Report generation: ReportLab4.4.9.
Solver: OpenFOAM v2506 in pinned Linux arm64 Docker image:
microfluidica/openfoam:2506@sha256:9ab54b92553d58a2e21adaf4ef98a8d0c118a09a1b388bd95480720ed7809b37
Commands run from this folder using the project's Python environment.

Re-evaluate first-law/psychrometric screens:
  python assess.py
Rebuild all case audits and plots from LOCAL native fields:
  python cfd/scripts/summarize_campaign.py
Generate exact nozzle/assembly CAD:
  python cfd/scripts/make_cad.py 100
Animate the selected case; use its ID from results/cfd-cad-loop.json:
  python cfd/scripts/animate.py CASE_ID
Replay a saved thermal case from exact mesh, BCs and initial fields:
  python cfd/scripts/reproduce_case.py CASE_ID NEW_UNIQUE_CASE_ID
Rebuild PDF/overview after new result summaries:
  python cfd/scripts/make_iteration_note.py
  python cfd/scripts/update_loop_overview.py

Lean/mathlib4.31.0, git pins in ../formal-model/lake-manifest.json:
  cd ../formal-model
  lake build > build.log 2>&1
Use the pinned toolchain, not a newer default Lean. A fresh install needs
its declared mathlib dependencies/cache. .lake symlinks are not packaged.
50 printed axiom checks pass;9 new CFD/design theorems. Physics equations,
source state and error bounds remain hypotheses. No sorry or new physics axioms.

PACKAGE SCOPE
The package includes native selected-case fields and internal exit-profile
fields, CAD, animations, scripts, all reported case meshes/initial fields/
dictionaries/logs/audits, proof source/build hashes, and field hashes for other
cases. Their full native volume fields remain in the original local workspace.
The package does not include Docker itself or Lean's dependency cache.
The original source DOCX is included with a source extract and manufacturer
snapshots. New source evidence is not fabricated or substituted by EXAIR data.

NEXT CHECKS
Longer wind statistics; profile-case mesh study; larger atmospheric domain;
turbulence/source/heat-pickup/branch-imbalance sensitivity; true solar/radiation;
moist surfaces/icing; person heat transfer and comfort; matched commercial
motor-load/air-treatment source; actual stock interfaces. These are unresolved,
not approvals to purchase or build a pressure system.
