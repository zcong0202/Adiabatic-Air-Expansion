# Fixed-source mass-flow and outlet sweep

23 October 2026. Current use: outdoor air release for people walking past. No seat or enclosure.

Open [the executed CFD results](results/index.html). The single project overview remains [project-overview.html](../../project-overview.html#mass-flow-sweep).

## Boundary conditions

- Total flow: **2, 27, 52, 77 g/s**, inclusive, 25 g/s steps.
- Total flow is split equally over **1, 2 or 4 outlets**. Four at 77 g/s means **19.25 g/s each**.
- Fixed nozzle-face temperature: **0.959275°C**, from the preceding source hypothesis. Ambient **30°C**.
- Still air. Exact hydrostatic initial pressure. Gravity **(0, 0, −9.81) m/s²**.
- Ideal constant spray from **0 to 10 s**. Simulation ends at 10 s. No startup delay, line cooldown or post-shutoff decay.
- Sample planes at **20, 35, 50 cm** downstream, within the same 3D field.

The producer remains the preceding four-motor source hypothesis (77.6 g/s nominal capacity). The requested sweep stops at 77 g/s. The sweep varies total flow admitted to the modelled outlets. Holding the producer operating point would require unused flow to be diverted outside this domain; throttling the producer itself could change temperature. That commercial routing is not resolved.

Flow is a prescribed boundary, not a prediction that the stock motors can deliver the same cold temperature at every selected flow. A change in outlet count is a distribution change, not a change in motor count. Upstream manifold, motor/vortex operating point and internal nozzle flow are absent.

## Design loop

1. Calculate source energy, outlet area, velocity and Reynolds number for every flow split.
2. Execute the original 140×80 and 280×40 mm equal-area slots with one, two and four outlets.
3. Compare four-outlet same-side, opposed and overhead arrangements using the wide slot.
4. Add compact 2:1 exits sized for **1.5 m/s** at each total flow and outlet count. This is an explicit reach/coverage hypothesis, not a universal optimum.
5. Compare laminar and URANS closures around transitional Reynolds numbers. Reynolds cutoffs are a screening index. Free-jet transition also depends on nozzle history and disturbances.
6. Refine selected meshes and compare the same region and sampling metrics.
7. Generate CAD with the exact corresponding exit dimensions. Verify watertight STL, consistent normals, one component, STEP units and independent STEP reimport dimensions.

The CFD resolves external jets and short nozzle blocks. It does not resolve the CAD loft interior. CAD is an unfitted near-atmospheric outlet prototype, not a pressure-rated component or validated stock connection.

## Geometry and measurement

Domain: x=−1.25…1.25, y=−1.1…1.1, z=0…2.7 m. Ground is an adiabatic no-slip wall. Far fields permit ambient inflow/outflow. No body, heat load, roof or side enclosure.

Same-side nozzles point +y from y=−0.55 m. One outlet is at x=0,z=1.35 m. Two are at x=±0.2,z=1.35 m. Four form a 2×2 bank at x=±0.2,z=1.15/1.55 m.

Opposed banks are at y=±0.55 m, z=1.15/1.55 m. Sampling is measured from the negative-y bank; opposite jets can influence those planes. Overhead outlets point down from z=2.1 m, at x=±0.2,y=±0.08 m. Their section orientation differs from the side layouts.

**Common walking corridor:** x=−0.8…0.8, y=−0.2…0.2, z=1…1.7 m. Nominal 0.448 m³. This is an analysis assumption, not a defined person or agreed minimum useful volume. Cold air can be disconnected. The full-domain result can include a cold layer near the ground.

Vertical sampling bounds: x=−0.8…0.8,z=1…1.7 m. Overhead horizontal sampling bounds: x=−0.8…0.8,y=−0.2…0.2 m. Areas from these orientations are not equivalent body coverage.

Thresholds: drops of ≥2, ≥6 and ≥10°C. Reported 3D surface uses ≥6°C (T≤24°C). Air mass includes entrained ambient air. Source-origin mass is stored separately.

For a native cell and region intersection:

```
V_cold = Σ V_overlap × [T ≤ T_ambient − threshold]
m_cold = Σ p/(R T) × V_overlap × [T ≤ T_ambient − threshold]
```

Volume overlap is exact for the rectilinear cells. Temperature is classified cellwise, without subcell isotherm reconstruction. The 3D mesh is the boundary of those cold cells. Its closed volume is independently checked against the cell-volume sum. Sections use the native cell containing each plane. Mesh refinement is needed to assess the resulting discretisation sensitivity.

## Calculations

At the fixed source temperature:

```
Q_sensible = m_total cp (T_ambient − T_source)
m_per_outlet = m_total / outlet_count
A_exit = m_per_outlet / (rho_source × target_speed)
Re = m_per_outlet Dh / (A_exit mu)
```

cp=1006 J/(kg K), mu=1.8e−5 Pa s, matching the CFD. Ideal-gas density uses the solver molecular weight. Source budgets exclude kinetic energy; native conservation audits include it and gravity. The largest standard-slot speed produces less than 0.02 K total/static temperature difference. Changing mass flow does not supply a validated new motor work/efficiency point.

## Solver and numerical screens

Pinned arm64 Docker image:

`microfluidica/openfoam:2506@sha256:9ab54b92553d58a2e21adaf4ef98a8d0c118a09a1b388bd95480720ed7809b37`

OpenFOAM buoyantPimpleFoam, dry perfect gas, variable density, transient Euler, limited convection, laminar or k-epsilon URANS. Molecular and turbulent diffusion transport a source-origin scalar. Adaptive timestep with maximum Courant number 0.7. Coarse maximum bulk spacing 65 mm; exact outlet boundaries and at least two cells across compact exit dimensions. Selected fine meshes refine the bulk and exit dimensions.

Screens: checkMesh; solver end at exactly 10 s; finite fields; temperature and tracer bounds; source mass within 0.5%; native mass, tracer and energy closure. Original closure gates are 3%, 5%, 8%, respectively, evaluated over the last five seconds with 1 s saved fields. These are numerical screens, not a continuum-error or physical uncertainty bound.

URANS inlet intensity is 5%, with the inherited 5.6 mm dissipation length hypothesis held across designs. These inlet disturbances are not measured. Laminar closure does not establish that a real fed nozzle is laminar. URANS does not resolve individual turbulent eddies. Thermal comfort, solar heat, humidity, condensation, people and their wakes are not modelled.

## Reproduce and inspect

Use the existing project `.venv-cfd` with NumPy, SciPy, Matplotlib, Gmsh and trimesh. No internet data is fetched by the solver.

```
python scripts/campaign.py
python scripts/refine.py
python scripts/cad.py
python scripts/finish.py
python scripts/test_math.py
```

`results/campaign-plan.json` and `results/campaign-status.json` record planned and executed work. `results/comparison.csv` is the result table. Each case JSON includes exact inputs, numerical gates, conservation, all saved volume metrics and field hashes. JS mesh/section files render locally without network libraries. GLB files contain the actual cold-cell mesh in metres.

New native fields are compressed into `archives/CASE.zip`. Every T/p/U/origin field hash is checked after compression, before redundant expanded time directories and processor copies are removed. Archives retain reconstructed native fields, initial fields, mesh, dictionaries, logs and audit. Unzip into `cfd/cases/` to restore a case. Existing studies and archives are untouched.

[First-principles budgets and buoyancy diagnostics](results/calculations.json). [Per-design calculation CSV](results/calculation-screen.csv). Densimetric Froude is a scale diagnostic, not a substitute for the gravity-inclusive CFD. The 10 s ideal mixing bounds are throughput/enthalpy limits; they do not predict the resident cooled volume.

## Local 5×5 cm reach metric

Final native section values also support exact cell/patch area averages. A 5×5 cm patch scans each target plane with 10 mm centre increments. The report gives the best sampled mean temperature drop. This avoids treating a single cold cell as a cooled 5 cm target. It is not the continuous-position optimum or a passing-person exposure. Section metrics concern the saved 10 s field.

## Requested 20–50 cm target-band volume

This metric excludes colder air beyond the requested range. For side layouts, use x=−0.8…0.8 m, y=−0.35…−0.05 m, z=1…1.7 m (0.336 m³). Opposed layouts use the disjoint union of both side bands (0.672 m³). Overhead uses x=−0.8…0.8, y=−0.2…0.2, z=1.6…1.9 m (0.192 m³). **Sample volumes differ by layout.** Absolute cold volume, cold mass and fluid-volume denominator are retained; they are not equivalent human coverage scores.

Native cells intersecting these boundaries are clipped geometrically. The resulting range mesh has flat analysis cuts. Its closed volume is checked against exact cell/band overlap. No CFD field is rescaled. The refinement selects the largest >=6 K cold air mass within this declared target band. This is a numerical design objective, not an agreed minimum cooled volume or proof of a global optimum. The earlier fixed walking corridor and whole domain remain separate measures.

The calculation CSV also compares native cold-region enthalpy deficit with `source-origin mass × cp × source temperature deficit`. This checks consistency of thermal and tracer transport with the ideal mixing equation. It is a numerical cross-check, not independent physical validation.

## Execution details and limits

The campaign has 48 first-pass cases and seven additional model/grid checks. A two-grid comparison is sensitivity evidence, not demonstrated grid convergence. Fine bulk spacing is 45 mm, with at least three cells across compact exits. Small compact exits use additional far-field resolution to pass every mesh quality check. Two rejected first-pass meshes are retained as ZIP evidence; their repaired runs replace them in the comparison.

For serial runs, launch the solver directly. For parallel runs, use `mpirun --bind-to none`; independent containers must not all bind to the same two host cores. The runner records ranks and the pinned image.

This campaign adds numerical and geometric consistency checks. It does not add a Lean proof of the Navier–Stokes solution or certify the source hardware. Existing Lean algebra remains supporting first-principles evidence. The simulated air volume is resident air below a temperature threshold at each saved time; it is not the cumulative delivered volume.

[Execution repairs and retained attempt logs](results/execution-notes.json). Failed launches and rejected meshes are separate from accepted CFD fields.

## CFD dashboard

The same result page now has a flow slider, nozzle/count/layout selectors, camera controls and native time playback. Flow snaps to 2, 27, 52 and 77 g/s. The chosen geometry family and layout stay fixed as flow changes. Compact exits use different CAD dimensions at each flow/count to hold 1.5 m/s; this is explicit in the controls. Main controls prefer a finer run when one exists. Exact model/grid alternatives remain available.

`python scripts/timeline.py` extracts temperature fields at 0–10 s from every native archive. It verifies every temperature hash and mesh hash. All 1,210 whole/band mesh volumes are checked against native metrics. The 605 frames contain their own 20/35/50 cm sections and patch means. Playback has one saved frame per second, with no temporal interpolation or new CFD. It ends at 10 s; valve-off persistence is absent. Frame bundles use Git LFS.

[Supply-temperature provenance](results/source-provenance.json) traces the fixed 0.959275°C boundary to the original 1°C document assumption, four loaded motors, 40°C inlet, 3.36 kW shaft work, 77.6 g/s and 4 K nominal cold-path warming. It is an assumed source state, separate from the earlier 5°C vortex-tube test.

### Full nozzle catalogue

Dashboard `results/index.html#nozzle-catalogue` contains all 23 flow designs:
14 current slots, four early concepts and five conical designs. Repeated
seat/pass-by bodies and thread tolerances are grouped with their flow design.
The rejected 50 mm inlet is linked as history. Download individual STL (mm),
STEP (metres), or the all-CAD ZIP. The C24 3° card also has the actual threaded
STL/3MF, three thread tolerances, fit coupons and guide. Smooth STEP files
have no thread. No printed attachment fit or pressure rating is verified.
Only the commercial Milton reference tip fit was user-confirmed. The slots
have an unfitted 100 mm hose spigot. Other connectors remain unspecified.

Each current slot maps to its exact exit-size runs. Tables show the best
sampled 5 × 5 cm area mean drop at 20/50 cm, at 10 s. Open either distance
in the native 3D/2D viewer. This does not solve the internal CAD passage.

Five earlier accepted steady fields were sampled at 20 and 50 cm using
OpenFOAM `cellPoint` sets. These fixed centred patches, source conditions
and gravity-free axisymmetric models differ from the current sweep. C16
uses a prescribed 16 mm uniform exit, without its internal 5° cone. Four
early D0–D3 solves never converged; their values are withheld. These gaps
need new named solves, not interpolation or transplantation of slot results.

Rebuild the catalogue via `python scripts/report.py`. Native sampling is
separate: `python scripts/legacy_ranges.py --native-root PATH`, where PATH
contains the original `optimization/cases` fields. Replay ZIPs preserve each
sampled case, fields, mesh, dictionary, log and acceptance audit under
`archives/catalogue-*.zip`. `results/nozzle-catalogue/legacy-ranges.json`
records hashes and checks the new 20 cm extraction against the older target.
No flow solve or source change occurs in this postprocessing.
