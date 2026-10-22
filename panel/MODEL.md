# Cooling computation panel · model 2

Current scope: unconfined outdoor nozzles; people walk past. No seat. Max valve activation 30 s. Main outcome: air mass and volume at a chosen temperature drop. No minimum volume has been agreed. Default 0.1 m³ is an editable design target.

## Units and reference states

Internal units: kg, m, s, K, Pa, W, J/kg. Pressure is absolute internally. The interface labels gauge pressure as **barg**. Atmospheric pressure is 101325 Pa. Ideal air: R=287.05 J/kg/K, cp=1006 J/kg/K, cv=cp−R, gamma=cp/cv.

FAD is free-air volume. It is not actual compressed volume. The nominal design pair 19.4 g/s / 16.2 L/s gives 1.197530864 kg/m³. Its original reference state is unconfirmed. The density is editable. Dry ideal air at 20°C, 1.01325 bar is about 1.204 kg/m³. All supply/demand mass conversions use the same entered FAD density.

## Flow topology

```text
Compressor pressure/FAD pair → treatment pressure loss and purge
 → warm receiver → common warm main → N parallel warm branches
 → regulator headroom → motor inlet connection → expander
 → motor outlet connection → N parallel cold branches
 → M outlet faces → atmospheric jet
```

Connections are proxies for stock motor hose sizes: 10 mm inlet and 15 mm outlet. Default length 0.05 m and K=1 each are assumptions. Actual internal port area and collector losses are not established. Connection temperature loss is neglected. The model does not imply that a 50 mm downstream hose removes the small motor-port restriction.

Non-motor modes omit motor connectors. The branch count still sets parallel pipe flow. The number of outlets sets total open area. The perforated control has a fixed total open area of 0.1 m²; it is not multiplied by outlet count.

### Supply

Supply mass = FAD × entered reference density × (1−purge). Compressor pressure/FAD are paired catalogue points. No interpolation or variable-pressure performance map is invented.

- XAS38/48/58/68/78/88/98: 2/2.5/3/3.6/4.5/5/5.4 m³/min at 7 barg.
- XAHS38: 2 m³/min at 12 barg. XATS68: 3.6 m³/min at 10.3 barg.
- Kaneez: listing midpoint 1.1 m³/min at 8 barg. Listing range 1–1.2 m³/min and 8–10 bar. Exact FAD basis and supplier map unverified. The two limits are not asserted to be matched operating points.
- JUNIOR II: 100 L/min cylinder-filling rating. Direct continuous process supply remains blocked. Its hypothetical reference pressure is 200 barg; this is not approval to operate a process line.

Atlas engine ratings are retained as metadata. They are not used as actual compressor input, plant input or fuel power. Cooling/input ratio uses the full user-entered plant kW. Spare capacity is never prorated out of this denominator. Zero means unknown, not zero consumption.

### Motors and expansion

Loaded-motor demand = N×16.2 L/s FAD. Shaft power = N×840 W×load fraction. The pair is nominal and conditional. Changing the load fraction is a sensitivity at fixed flow, not a real motor control map. Net heat returned to the air is an independent input.

Steady first law:

`h2 = h1 − shaft_power/mass_flow + returned_heat/mass_flow`.

Isenthalpic valve: h2=h1. Ideal gas gives T2=T1. Real-air throttling uses the property table and can produce a Joule–Thomson temperature change. The valve has no shaft work.

Isentropic limit: s2s=s1. Ideal air gives T2s=T1(p2/p1)^(R/cp). Turbine: h2=h1−eta(h1−h2s). The turbine efficiency is assumed. No matched stock turbine is selected. Isentropic mode is a reversible upper bound.

Exhaust pressure is found from cold pipe/connection/nozzle losses, iterated with the exhaust temperature. Requested shaft work above the reversible limit blocks the result. Motor inlet above 7 barg or ambient above 40°C blocks the stock-motor result using the current supplier page limits. The working-pressure limit does not establish the performance test pressure. The imported assessment uses a 6.3 barg and 40°C comparison point.

Backpressure above 0.02 bar or a changed inlet/load triggers an off-design warning. **0.02 bar is a model proximity flag, not a supplier-approved tolerance.** The model does not validate the 840 W/flow pair under altered backpressure.

### Pipes, connections and nozzle

Darcy loss: `(f L/D + K) rho v²/2`. Reynolds number uses Sutherland viscosity. Laminar f=64/Re; turbulent f uses Swamee–Jain. Re=2300–4000 is blended. Mean-pressure density is iterated to obtain required inlet pressure. The ideal-gas solve reproduces the squared-pressure Darcy relation at fixed temperature.

Warm pressure floor is built backward from the motor inlet through the inlet connection, headroom, branch and common main. Warm-path heat is propagated forward. A regulator preserves enthalpy between the warm branch and regulated motor inlet. Warm main losses use mean density near the required floor; these are not a full compressible pipe solution at every receiver state.

Cold nozzle pressure requirement: `dp = rho*v_exit²/(2*Cd²)`. This is a low-speed lumped loss model. Exit kinetic energy is subtracted from total enthalpy to obtain static exit temperature. Useful cooling retains kinetic energy in delivered total enthalpy. Mach >0.3 in any pipe, connector or exit blocks the low-speed screen.

Cold heat leakage has two modes:

1. Reference UA: **2.518430164825 W/K per metre per branch**, default. Four 1 m branches give total UA=10.0737206593 W/K. This reproduces the assumed 4 K source-path warming from the imported CFD study. It is not a measured hose conductance.
2. Cylindrical wall and insulation resistance, including outside convection. Internal thermal resistance is omitted. Within this steady model, that increases predicted heat leakage.

`hout = hAmbient + (hin−hAmbient)*exp(−UA/(mass_flow*cp_local))`.

For ideal gas and unchanged pressure, this reduces to the usual temperature relaxation. Real-air mode applies the same approximate heat-exchanger effectiveness to enthalpy. This is not a rigorous distributed real-gas heat-exchanger model.

Warm UA is entered per metre of each pipe. Parallel branch UA is summed. The warm UA default is zero, preserving the reference motor inlet temperature. It is an explicit assumption, not an assertion that a real hose is adiabatic. Cold reference UA scales with length and branch count. Ambient wall temperature is fixed. Startup line cooldown, wall thermal mass, solar heating, condensation, heat from the motor casing and distributed compressibility remain unresolved.

## Warm receiver before expansion

Fixed volume, mixed ideal gas:

`dm/dt = min − mout`

`d(m cv T)/dt = min cp Tin − mout cp T + UA(Tambient−T)`

`pV = mRT`.

Initial tank air is at the aftercooler temperature and compressor pressure minus treatment loss. Initial pressure is assumed precharged. Supply ramps linearly from zero to available listed mass flow over the entered response time. A pressure controller caps incoming mass or enthalpy so the next state does not exceed initial pressure. This is a declared controller hypothesis, not a manufacturer response curve.

Forward integration step ≤0.025 s. First pressure-floor crossing is interpolated within the step. Discharge stops at this first failure; no restart credit. The fixed-temperature mode supplies whatever wall heat is needed to hold temperature and is a comparison bound. The energy mode uses fixed ambient wall temperature and entered UA; vessel wall thermal mass is absent.

The displayed fixed-T inventory size covers a constant flow deficit, ignoring response ramp:

`V = max(0,mout−min) * activation * R*Tinitial / (pstart−pstop)`.

The mass+energy size uses bisection and the selected ramp/thermal model. Search cap 100000 L. Results are screening sizes, not vessel selections. A sustained average deficit cannot be solved by a finite tank. Refill time assumes valve closed and full available supply.

The cold energy budget samples the steady flow model along the saved tank history, about every 0.5 s, and integrates delivered cooling with the trapezoid rule. Tank pressure and temperature feed that calculation. Motor flow and shaft work remain fixed hypotheses. The pressure-floor solve uses the initial temperature. No measured off-design motor map or dynamic pipe thermal model is available. Do not interpret this energy history as measured transient cooling. Near a target-temperature crossing, cumulative mixed mass uses endpoint threshold classification; refine before using a marginal threshold result.

## Cold storage before release

Separate sealed tank, initially at atmospheric pressure and entered cold temperature. It is **not inserted into the main flow network**.

`m = patm V/(R Tinitial)`

`T(t)=Tambient+(Tinitial−Tambient)exp(−UA*t/(m cv))`.

Pressure rises in proportion to absolute temperature. Reported sensible cold budget is m cp(Tambient−T). This is a mass/energy retention calculation. Initial charge energy, wall cooldown and driven discharge are absent. There is no claim that an atmospheric tank can deliver a fast directed nozzle burst. A pressurised cold tank changes motor backpressure and expansion; that architecture needs a coupled charge/discharge model and approved stock hardware before it can be promoted to a system prediction.

## Mixing and spatial outcomes

Constant-cp, adiabatic mixing at atmospheric pressure:

`drop = cold_mass_flow*(Tambient−Tcold)/(cold_mass_flow+added_warm_flow)`.

Minimum cold fraction = target_drop/(Tambient−Tcold). Maximum added warm flow follows from the same balance. If source air is warmer than the requested final temperature, no mixing with ambient air can meet that target.

Cumulative mixed mass is an ideal throughput budget from delivered sensible energy divided by cp×target_drop, only while the source is cold enough. It is not resident mass. Required target volume is converted to mass at its cooled temperature and ambient pressure. Wind, nozzle reach and a persistent cold volume are not inferred from this budget. No universal parcel reheating time is asserted.

## Actual CFD evidence

16 executed pass-by-study cases, 236 saved snapshots. Dry ideal-gas 3D buoyant URANS k-epsilon, prescribed sources. No live solver call from the dashboard. The selected system boundary is compared with saved source mass, temperature, ambient, geometry, layout, distance, pitch and wind. A compatible boundary is not hardware validation. Changes never rescale or recompute the field.

Field extraction uses ASCII OpenFOAM T, p and origin. rho=p/(R*T), using the solver molecular weight. Exact rectilinear cell/region overlap volumes. Cell-constant T classifies thresholds every 0.5 K from 0.5 to 30 K. No reconstruction of subcell isotherms. Source mass is rho×origin×cell volume, without clamping tracer excursions. The original audit T hashes are checked independently. Extracted T/p/origin and mesh hashes are retained.

Regions:

- Whole simulated fluid domain: x[−1.25,1.25], y[−1.1,1.1], z[0,2.7] m, minus solid nozzle blocks.
- New analysis corridor: x[−0.8,0.8], y[−0.2,0.2], z[1,1.7] m. Nominal 0.448 m³. This region is an analysis choice, not an agreed requirement.

`Vdelta = sum(overlapVolume * [T<=Ta−delta])`

`Mdelta = sum(rho * overlapVolume * [T<=Ta−delta])`.

At 10 s and ≥6 K drop, the finer standard slot gives 0.44629171 m³ / 0.53841107 kg over the whole domain. The finer wide slot gives 0.49777557 m³ / 0.59968438 kg. These include entrained ambient air, not only injected air. They are conditional numerical results without a continuum error bound.

Threshold volumes may include disconnected cold regions. No connected cooling pocket is established. No human, wake, solar load, humidity, motor coupling, internal nozzle profile, real valve transient or post-shutoff decay. Volume-time changes are Eulerian, not parcel lifetimes. Grid/turbulence/domain sensitivity remains necessary. Animation case IDs are explicit; the coarse wide animation is not the finer case.

## Real-air property table

CoolProp 8.0.0 HEOS Air. 180 pressure ×171 temperature nodes. 1.01325–331.1 bar absolute, 160–500 K. Bilinear p,T interpolation; monotone inversion for h or s. Out-of-range states stop; no extrapolation. Extreme isentropic expansion can leave this range. Throttling can remain in range even when the isentropic comparison does not.

Seven independent CoolProp reference states check enthalpy, entropy, density and inverse temperatures. Tolerances in the tests apply to these points, **not** a certified maximum error over the table. No humidity or phase-change/icing prediction. Receiver ODE remains ideal gas in real-air mode.

## Formal and numerical verification

Existing Lean proofs cover conditional algebraic mixing, energy, pipe retention and pass-by bounds. They do not prove source hypotheses or turbulence. The new JS/EOS table/receiver ODE are numerically tested, not Lean-verified. `tests/panel.test.js` checks first-law closure, mixing inequalities, analytic Darcy and tank limits, ODE step refinement, no-overcharge, pressure floors, source capacity, energy retention, EOS references and CFD integration invariants. Six original tests are retained as historical regressions; their assumptions are not adopted.

Rebuild commands are in the root README. `panel/data/validation.json` records numerical checks and source hashes. No hardware performance is validated by these checks.
