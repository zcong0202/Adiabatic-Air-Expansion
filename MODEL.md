> Historical calculator specification, retained for comparison. Current equations: [panel/MODEL.md](panel/MODEL.md). Known disagreements: [model audit](AA%20Project/Airflow-Assessment/pass-by-study/results/repo-model-audit.json).

# Model

All of this lives in `compute(S)` in `physics.js`. Air is treated as an ideal gas with cp = 1005 J/kg·K, γ = 1.4 and R = 287.05 J/kg·K. Atmospheric pressure is 1.01325 bar. Free-air delivery (FAD) is converted to mass flow at ρ = 1.204 kg/m³ (20 °C, 1.013 bar).

The path is walked stage by stage, carrying temperature `T` (°C), absolute pressure `P` (bar) and mass flow `m` (kg/s).

## Source

- **Compressor:** P = discharge pressure + atmospheric, T = discharge temperature, supply = FAD × ρ.
- **Storage tank:** usable mass = (p_fill − p_min) · V / (R · T). Flow is the release rate or the expander's demand.

**Mass flow.** If the first expander has a rated air use, it sets the demand. In continuous mode the flow is min(supply, demand), with a warning when demand exceeds supply. In burst mode it draws at full demand from a receiver, and the page reports the on time (usable mass ÷ net draw) and the refill time.

## Stages

| Stage | Temperature | Pressure |
|---|---|---|
| Aftercooler | T → min(T, T_amb + approach). Heat rejected = m·cp·ΔT | −Δp |
| Dryer + filters | unchanged | −Δp |
| Receiver | unchanged; holds usable mass for burst mode | unchanged |
| Regulator | Joule–Thomson drop, integrated: μ(p) = max(0.02, 0.22 − 0.0006·p) K/bar | → set point |
| Hose / duct | T → T + (T_amb − T) × loss % | −Δp |
| Turbine (loaded) | ΔT = η · T₁ · (1 − (P₂/P₁)^((γ−1)/γ)). Shaft work = m·cp·ΔT | → outlet |
| Vane motor (loaded) | ΔT = W_shaft / (m·cp), capped at the isentropic ΔT. W_shaft = count × rated power × load × (p / p_rated), with load = m / demand | → atmospheric |
| Vortex tube | ΔT_cold = ΔT_ref · √((1 − f)/0.2) · ln(P/Pa) / ln(7.9/1.013). Mass flow × cold fraction f | → atmospheric |

An unloaded turbine or vane motor (shaft spinning freely) only throttles, so it applies a Joule–Thomson drop and almost no cooling.

## Outlet

- **Cooling:** m·cp·(T_amb − T_out).
- **Velocity:** volumetric flow at the outlet ÷ open area. Nozzles use n · πd²/4; a diffuser uses face area × open %.
- **Reynolds number:** ρvD/μ, with μ = 1.8e‑5.
- **Archimedes number:** g·(ΔT/T_amb)·D / v². Much greater than 1 means the cold air sinks as a plume; much less than 0.1 means it behaves as a jet.
- **"Holds −10 K in a cross-breeze up to":** cooling ÷ (ρ_amb · cp · 10 K · seat-zone area).

## COP

- **COP** = cooling ÷ (mass drawn from the source × specific compression energy).
  - For a compressor, the specific energy = power input ÷ supplied mass flow.
  - For a tank, it is the "energy used to fill" field (1,100 kJ/kg for a 200 bar fill).
  - For a vortex tube, the hot fraction is still charged.
- **Recovered COP** (when "Shaft work recovered" > 0): cooling ÷ (input − recovered % × shaft work).
- **Ideal limit:** Carnot COP for cooling a stream from T_out up to T_amb: (Ta − To) / (Ta·ln(Ta/To) − (Ta − To)).

## Known limits

- The Joule–Thomson coefficient is a linear fit for air from 0 to about 300 bar near room temperature. It is less accurate when the gas is very cold.
- Only dry air is modelled. Moisture, icing and latent load are flagged with warnings, not calculated.
- Duct heat gain is a fixed fraction, not a heat-transfer calculation.
- Vane-motor shaft power scales linearly with pressure around the rated point, which is a rough approximation away from 6.3 bar(g).
- Stages have no transient or thermal-mass behaviour. Burst-mode times are mass balances only.
- Typical COP values for air conditioning are hard-coded in `app.js` (`renderCop`).

## Reference results (30 °C ambient)

| Case | Outlet | Cooling | COP |
|---|---|---|---|
| Rental 7.6 bar + 4 × LZB46 (78 g/s) | 0.8 °C | 2.29 kW | 0.10 |
| Same, supplied at 200 bar (extra ~30 K of Joule–Thomson cooling in the regulator) | −25.9 °C | 4.38 kW | 0.05 |
| Ideal air cycle at pressure ratio 7.3: isothermal compression, isentropic turbine, all shaft work recovered | −96 °C | 9.9 kW | 3.4 |
| Same cycle with 80 % stage efficiencies and 95 % recovery | −57 °C | 6.8 kW | 0.62 |
