# Pressure, mass flow and cooling duration

Current interface: `index.html`, `lab/app.js`. Source/network model: `panel/model.js`. New transient model: `panel/dynamics.js`. Inputs use SI internally. Display flow is g/s. All UI pressure is gauge pressure.

These are conditional budgets. No hardware measurements, new CFD runs or new Lean proofs were added. Existing saved CFD is unchanged. Its post-shutoff decay was never simulated.

## 1. Flow and pressure are separate constraints

`m_available = source_FAD / 60 × rho_FAD × (1 − purge)` with FAD in m³/min.

For LZB46 motors: `m_demand = N × 0.0162 × rho_FAD` kg/s. Nominal shaft power is `N × 840 W`, conditional on matched load and supplier operating state. No off-design flow/pressure/load map exists in this project. We do not multiply flow by pressure or invent fractional motor operation when supply is insufficient.

Source pressure and flow use the listed paired rating. `chargeBar=0` means use that pressure. A lower positive charge pressure represents a downstream regulator before treatment and the receiver. The source retains its listed FAD as a supply bound. Enter temperature after that regulation. This is not a compressor performance curve. The receiver starts at this supply pressure minus the entered treatment pressure loss. A supply setting above the source rating is rejected.

The warm receiver equation and network pressure floor are specified in [MODEL.md](MODEL.md). Pressure, volume, source ramp and mass deficit determine the supported interval. Output stays at rated demand until cutoff, then goes to zero. No restart credit. When supply exceeds demand and response is immediate, this model needs no receiver. That does not establish real compressor or valve startup performance.

The component dot chart offers two comparisons:

- Largest integer motor bank that fits each compressor's net listed flow, capped at 16, one outlet per motor. This is a flow screen, not a motor-map match.
- The current bank and outlet count for all compressors.

Every candidate uses its own listed pressure. Other settings stay current. The dot shows requested flow; a filled dot has a supported interval under the model. A hollow dot is unsupported. Tables give supported output, initial source cooling, support duration and delivered mass. More available compressor flow does not create more motor output unless the bank or process changes. BAUER direct process supply stays blocked. Kaneez remains listing-only data.

## 2. Target air volume: first-law budget

Let `Delta = T_ambient − T_target`, `Delta_source(t) = T_ambient − T_source,total(t)`.

Assume a well-mixed isobaric target inventory with fixed ambient density:

```
M = p_ambient V / (R T_ambient)
m_captured = capture × m_output
M dDelta/dt = m_captured(Delta_source − Delta)
             − m_ambient_exchange Delta − heat_W/cp
```

Each entering mass flow displaces equal mixed mass. Ambient exchange is additional warm inflow. Positive `heat_W` adds heat. Capture includes geometric delivery losses; it is not computed from nozzle area, distance or wind here. Constant density is a screening approximation. Actual mass changes with temperature are neglected. Real outdoor entrainment, buoyancy, diffusion and person wakes require CFD or measurement.

For one constant step, define `k = (m_captured + m_exchange)/M` and `F = (m_captured Delta_source − heat_W/cp)/M`. The exact update is:

```
Delta_next = Delta exp(−k dt) + (F/k)(1 − exp(−k dt))
```

For `k=0`, use `Delta_next = Delta + F dt`. Source changes are sampled at the step midpoint. Default time step is 0.05 s; the step splits at source cutoff. A receiver's recorded source-temperature history drives delivery. Warm receiver temperature drift still assumes fixed motor work; the missing off-design map remains material.

The steady limit for constant source conditions is:

```
Delta_infinity = (capture m_output Delta_source − heat_W/cp)
                 / (capture m_output + m_exchange)
```

For `Delta_source > Delta_required`, the minimum steady capture is:

```
capture_min = (m_exchange Delta_required + heat_W/cp)
              / [m_output(Delta_source − Delta_required)]
```

A required capture above 1 is impossible under those inputs. Smaller volume speeds the response; it does not change the steady limit. Greater captured cold flow raises that limit. Greater ambient exchange lowers it.

After shutoff, with no other heat and positive ambient exchange, `Delta` decays as `exp(−m_exchange t/M)`. There is no fixed 0.5 s reheating law. Zero exchange and zero heat produce no recovery in this ideal budget. A real outdoor zone will exchange air.

Report: target inventory, minimum mean temperature, first threshold crossing, intervals at or above the required drop, delivered source mass and captured mass. Threshold crossings are linearly interpolated between integration outputs. Source delivery continues up to the valve limit, even if the observation horizon is shorter. A `+` duration means the observation horizon ended while the threshold was still met. The result concerns the entire assumed mixed volume, not a spatially resolved pocket. It does not give comfort or passing-person exposure.

## 3. A cold output buffer is a separate question

The original full panel models a sealed atmospheric tank during a hold. The lab adds an **isolated precharged tank burst**, not an automatically coupled downstream accumulator.

Inputs: initial cold air temperature, initial gauge pressure, tank volume, hold time, UA, valve flow cap, selected total nozzle area/Cd, and minimum pressure head. The cold tank supplies direct outlet orifices. There is no downstream hose, regulator thermal inertia, inflow during release, charge process or recharge model.

Initialization and hold:

```
m0 = p0 V / (R T0)
T_hold = Ta + (T0 − Ta) exp(−UA hold/(m0 cv))
p_hold = m0 R T_hold / V
```

Pressure rises during a sealed warming hold. This is not free cooling or an assumed compressor charging process.

For upstream stagnation pressure `p`, temperature `T`, and downstream ambient pressure `pa`, let `q=pa/p`, `g=gamma` and `qcrit=(2/(g+1))^(g/(g−1))`.

Using mass conservation, ideal-gas isentropic pressure/density relations and the nozzle energy equation gives the ideal orifice capacity:

```
m_orifice = Cd A p / sqrt(R T) × sqrt[2g/(g−1) × (q^(2/g) − q^((g+1)/g))]
```

For `q <= qcrit`, replace the bracket factor with the choked factor `sqrt(g) × (2/(g+1))^((g+1)/(2(g−1)))`. For `p<=pa`, flow is zero. Actual tank outflow is `min(valve_cap, m_orifice)`. Cd is assumed. A mass-flow cap presumes an ideal regulating valve; a matched commercial valve is not selected.

For each removal step, use the exact ideal adiabatic blowdown relation:

```
m_next = m − m_out dt
T_adiabatic = T (m_next/m)^(g−1)
U_removed = m cv T − m_next cv T_adiabatic
T_out,mean = U_removed / (dm cp)
```

Then apply an exact fixed-mass heat relaxation over that step. The two operations are split numerically. Default step is 0.005 s. If pressure crosses the cutoff, bisection locates the first crossing. The valve stays closed afterward, even if later heat raises pressure. The same 30 s maximum valve opening applies. No restart. Mass and energy residuals are recorded.

Cooling simulation uses these piecewise discharge intervals with <=0.005 s steps. A cold tank with substantial stored mass but little gauge pressure can exhaust its usable pressure head quickly. At atmospheric pressure and no hold, there is no initial pressure-driven flow. An external fan or piston would be a different architecture.

A requested initial cold pressure above the source model's exhaust pressure is flagged as outside that motor-point charging screen. A lower pressure is **not proof of chargeability**. Accumulation changes motor backpressure and cooling. Supplier maps and a coupled charge/discharge network are required before this becomes a stock-system design prediction. Dry ideal gas also neglects moisture, condensation and icing.

## 4. What the controls can and cannot establish

| Change | Calculated effect | Remaining evidence needed |
|---|---|---|
| Pressure / warm receiver | Pressure margin and rated-flow support interval | Source controller, motor map, real startup |
| Motor count / load | Conditional g/s and extracted work | Loaded operating map and exhaust state |
| Hose length / bore | Heat gain, pressure loss, backpressure | Actual UA, port dimensions and wall cooldown |
| Nozzle area | Speed and pressure requirement | Internal flow and outdoor capture/entrainment |
| Cold tank volume / burst cap | Precharged burst flow and usable mass | How that cold state is charged with stock components |
| Target volume / capture / exchange | Mean cooling and recovery time | Outdoor spatial CFD and validation |

No spatial cooled volume is inferred by rescaling a saved CFD run. Existing Lean algebra, numerical tests, saved CFD and hardware evidence remain separate.
