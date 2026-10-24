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

## Shaft load and 22°C sensitivity

[Configuration sketch](results/shaft-load-configuration.png) separates the
regulated air path from the mechanical shaft coupling. A brake or a generator
and controlled load bank absorbs shaft power. No air passes through that load.
Its heat is rejected away from the cold air.

The 19.4 g/s point already assumes 840 W external shaft load at 1270 rpm.
Published free speed is 2400 rpm. Adding load changes speed and air consumption;
there is no free-speed mass-flow value in the data used here. Extra load may
stall the rotor; torque alone is not power. Wshaft=torque×angular speed.
Free-running external shaft work tends to zero after spin-up. Regulator cooling,
internal losses and housing heat transfer can still affect the exhaust, so no
exact unloaded temperature is claimed. The manual notes high no-load housing
hotspots; this is not an exhaust-temperature measurement.

If measured motor inlet temperature is 22°C, the fixed 840 W / 19.4 g/s first
law gives a 43.04 K bulk temperature reduction: −21.04°C motor exhaust.
Inherited cold-path UA=10.0737 W/K and 30°C ambient give −0.46°C at the nozzle.
These are conditional calculations, not hardware ratings or new CFD. A fast
exhaust port's local static temperature can differ from stagnation temperature.

If only the tank is known to be 22°C, motor inlet temperature is not fixed.
CoolProp's initial heat-free, isenthalpic 200→6.3 bar gauge calculation gives
−11.81°C after reduction. This ignores regulator/hose wall heat and blowdown.
Do not extrapolate the fixed motor power/flow pair to that cold inlet without
a supplier map/test. See [calculations](results/load22-calculations.json) and
[eight algebra/EOS checks](results/load22-validation.json).

The product page lists 7 bar maximum working pressure; the product manual says
6.3 bar or the nameplate. Keep the 6.3 bar running target and confirm the actual
nameplate and pressure-reduction package. No cylinder-pressure parts are printed.

## Alternative motor shortlist — 24 October 2026

[Open alternatives and bench POC plan](results/index.html#motor-options).
Three standard Gast models are compared with LZB46. Manufacturer PDFs and
observed supplier pages are retained in `evidence/motor-options/`.

- 1AM-NRV-39A: about 270 W / 7.4 L/s free air at 6.3 bar / 8000 rpm.
- 2AM-NCC-16: about 600 W / 13 L/s at 6.3 bar / 3000 rpm.
- 2AM-NCC-16 low duty: about 200 W / 7 L/s at 5.6 bar / 1000 rpm.
- 4AM-NRV-50C: about 1100 W / 30.5 L/s at 6.3 bar / 3000 rpm.

These are paired approximate manufacturer-curve reads. The 6.3 bar estimates
interpolate between 7 and 5.6 bar curves at the same rpm. They are not power
ratings arbitrarily paired with no-load flow. Free-air conversion uses an
assumed 1.2 kg/m³. Script: `scripts/motor_options.py`; JSON/CSV include sources,
30 numerical balance checks, assumptions and sensitivities. No new CFD or
Lean proof was generated. Existing saved source-specific CFD stays unchanged.

All thermal comparisons assume 22°C measured motor inlet and 30°C ambient.
A 22°C cylinder does not establish 22°C motor inlet. Heat pickup in the motor
is zero in the nominal calculation. Old-path UA=10.0737 W/K and short-path
UA=1 W/K are comparison assumptions, not measured conductance. Separate
scenarios return 25% of shaft work as heat and vary power/flow by ±10%.
Inventory runtimes use a 12 L / 200 bar / 22°C tank to a 20 bar cutoff and
exclude conditioning, leakage, regulator dropout and temperature limits.

Gast's standard models require lubrication. They are candidates for a
contained, instrumented bench POC, not direct person-facing exhaust.
LL/NLP model families have different <=5.5 bar limits and require their own
curves. Zoro marks its 4AM-NRV-50CLL listing discontinued; this does not mean
Gast has globally discontinued the model. 2AM-NCC-96 retailer power fields
conflict, so it is excluded from the calculation.

Procurement status: exact-model Zoro US listings/prices observed. Physical
stock, ship-from warehouse and delivery to San Francisco remain unconfirmed.
Gast's locator identifies TAHAS Istanbul; its contact page confirms the
phone/address, but no Ankara stock or dispatch date is published. UAE RS
Delivers was unavailable during research, and no Dubai ready-stock unit was
verified. No alternative is confirmed faster than the reported four-week
LZB46 lead. A public listing named 'Stock 40/Skid' is not an inventory count.
No supplier inquiry, message, purchase or order was sent. The stock enquiry
brief is a downloadable draft only.

For the POC, first compare a rated regulator-only bypass with a loaded motor
at comparable measured flow and motor-inlet conditions. Use calibrated bulk
inlet/exhaust temperatures, pressures, mass flow, shaft torque and rpm.
Cold housing, free-jet sensation or an IR image alone does not establish air
cooling. Precondition to repeatable source conditions before the up-to-ten-
second demonstration interval. Warm motor/nozzle metal may absorb the first
pulse's budget; no fixed warmup duration is predicted. Report whether the
measurement proves throttling, incremental motor expansion, or outdoor
20–50 cm cooling. These are different claims.

### Local suppliers and steady cooling budget · 24 October

Goodwin Dubai explicitly offers Gast motors. Mechatronics Dubai lists GLOBE
V1/V2/V4. These are local supply leads; exact stock and dispatch remain
unconfirmed. The V1 listing gives 520 W maximum power but no paired airflow.
Do not derive a V1 temperature prediction from that rating alone.

`scripts/cooling_budget.py` runs with the report generator. It writes
`results/cooling-budget.json` and 20 energy/mixing balance checks. The model is:

```
Tmotor = Tin - (Pshaft - Qinto)/(mdot cp)
Tnozzle = Tamb + (Tmotor - Tamb) exp(-UA/(mdot cp))
Qcold = mdot cp (Tamb - Tnozzle)
mdot_mixed,max = Qcold/(cp * 6 K)
```

At 22 C motor inlet, 30 C ambient, UA=1 W/K and zero motor heat pickup,
the 600 W / 15.6 g/s 2AM point gives -13.38 C at the nozzle and 680.8 W
of sensible cooling relative to ambient. The latter includes the inlet's
existing 8 K deficit. The 112.8 g/s total mixed-flow ceiling includes entrained
ambient air. It is not a spatial CFD prediction or achieved cold air mass.
With 150 W motor heat pickup and inherited UA=10.0737 W/K, nozzle temperature
is +10.70 C. Neither UA nor the 25% heat-return scenario is measured.

These steady budgets support conditional bench POC potential. They do not
establish startup performance, approved subzero operation, or a >6 K area
average at 20–50 cm. Existing CFD retains its original source and motor.
