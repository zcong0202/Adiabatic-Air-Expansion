# Scuba tank → loaded air motor → one nozzle

Reference only: 12 L internal volume, 200 bar gauge, 30°C initial air, 20 bar
planning cutoff. Confirm the cylinder stamp and regulator before procurement.

Direct tank connection to the LZB46 is incompatible with its 7 bar gauge
maximum working pressure. The calculation assumes pressure reduction to
6.3 bar gauge at the running motor. A rated, cylinder-compatible industrial
pressure-reduction package must prove 972 L/min free-air delivery at the
minimum tank pressure, with downstream overpressure protection. No exact
regulator model or fitting is qualified here. An ordinary diving first stage
is not automatically adequate at this duty or output pressure.

The document's loaded motor point is 840 W at 1270 rpm, 16.2 L/s free air
(19.4 g/s conversion inherited from the DOCX). This needs a sustained
external shaft load of about 6.32 Nm. Return its heat outside the cold path.
Free spinning does not deliver the model's shaft-work cooling. Air-flow
reference conditions and the motor's cold operating envelope need supplier
confirmation. Tank pressure falls; regulator droop and icing can limit the
usable runtime before the inventory cutoff.

`calculate.py` uses CoolProp real-air inventory. Isothermal and adiabatic
rigid-tank blowdown are separate thermal scenarios. They are not a fitted
wall-heat-transfer transient or guaranteed operating runtimes. The adiabatic
scenario becomes extremely cold near depletion; motor/regulator operation
at those states is not established. Interrupted pulses may rewarm the tank;
no recharge schedule is inferred.

One motor gives nominal 19.4 g/s, 194 g per ten-second pulse. The inventory
supports about 105–123 s to 20 bar, or 10–12 complete ten-second pulses.
Four loaded motors can feed a common nozzle at 77.6 g/s, but consume the
same inventory in about 26–31 s and need four load stations and roughly
3888 L/min free-air regulator capacity. One motor is not rated to provide
77 g/s at the listed loaded point.

No extra cold-output receiver is selected. The scuba cylinder already
stores source air. A cold receiver adds warm wall mass and exhaust
backpressure, and cannot raise the cycle's total cooling-energy budget.

## CFD

New native OpenFOAM buoyantPimpleFoam runs use one 280 × 40 mm outlet,
19.4 g/s, gravity, still air and a ten-second ON pulse. Ambient is 30°C.
Nominal motor inlet is 30°C; motor heat pickup is zero and shaft work is
840 W. The earlier full four-motor-path UA=10.0737 W/K is conservatively
reused for this one path. It gives 4.313°C at the nozzle. It is not measured
or a vendor guarantee. A 40°C motor-inlet sensitivity gives 10.281°C supply.
These are distinct fixed boundary CFD runs, not rescaled saved fields.
The tank/regulator transient is calculated separately, not coupled to CFD.

Coarse spacing is 65 mm; fine spacing is 45 mm. The single nozzle uses the
existing CAD exit area. Internal nozzle flow, motor exhaust neck, mounting
and their backpressure are not resolved. Prototype STL inlet is an unfitted
100 mm hose interface, not a tank-pressure connector.

Cold-volume metrics use native cells ≥6 K below ambient. The target slab
is 20–50 cm downstream, x=−0.8..0.8 m, z=1.0..1.7 m. Sections at 20, 35
and 50 cm also report the best sampled 5 × 5 cm mean. This is a selected
local air patch, not full-body cooling or a comfort result. No post-shutoff
decay, moving person, wind, solar heat or moisture/icing CFD is included.
Two-grid sensitivity does not establish continuum accuracy.

## Reproduce

Use the existing CFD Python environment (numpy, scipy, matplotlib,
trimesh, CoolProp, lxml) and installed Docker OpenFOAM image.

- `python scripts/calculate.py`
- `python scripts/cfd.py scuba19_n1_wide`
- `python scripts/cfd.py scuba19_n1_wide_fine --h .045`
- `python scripts/cfd.py scuba19_n1_wide_warm --tin 40`
- `python scripts/report.py`

Native solver logs, reconstructed fields and mesh are retained in the LFS
ZIP archives, with field hashes and conservation screens. Calculations
are numerically checked; no new Lean proof or hardware validation.

## Executed result — 23 October 2026

All three new runs pass mesh, solver completion, field bounds, source mass,
mass/tracer/energy balance screens. The nominal grid pair has 37,955 and
103,572 cells. The fine case is the default.

| Case | Source °C | Best 5 cm drop at 20 cm / 50 cm | Target cold air at 10 s |
|---|---:|---:|---:|
| Nominal coarse | 4.313 | 19.97 / 15.42 K | 10.679 L / 13.021 g |
| Nominal fine | 4.313 | 19.93 / 15.40 K | 9.519 L / 11.638 g |
| Warm-inlet coarse | 10.281 | 15.56 / 12.76 K | 8.954 L / 10.831 g |

Target cold volume changes −10.86% with grid refinement; this is a sensitivity,
not an error bound. Fine-case best patch at 50 cm is centred near z=1.275 m,
below the 1.35 m outlet centre. Buoyancy changes the delivery height.

The 194 g injected over ten seconds is cumulative source mass. The 11.638 g
fine-case cold mass is resident mixed air in the target slab at t=10 s.
They are different quantities. Whole-domain cold air includes air beyond
that slab and is not the presentation's target-zone mass.

[Open calculations, 2D/3D playback and CAD links](results/index.html).
[Download native cooling animation](results/scuba19_n1_wide_fine-cooling.gif).

Ten numerical calculation checks and 44 browser checks each at desktop/mobile
pass. All 33 time frames are tied to native temperature/mesh hashes. The
inherited geometry/analysis suite also passes all 12 tests. No new Lean proof.
