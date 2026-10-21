# Adiabatic Air Expansion — Air-Cycle Bench

A single-page browser calculator for **outdoor seat cooling by expanding compressed air**. You build the gas path from left to right: a source, then coolers, dryers, tanks, regulators and an expander (turbine, vane air motor or vortex tube), then a hose and an outlet. The page shows the temperature, pressure and mass flow between each pair of stages, plus outlet temperature, cooling capacity, airflow and COP compared with air conditioning.

It was built to size the Nov 2026 Dubai demo (a rental compressor feeding 4 × LZB46 vane motors) and to show why a 200–330 bar supply doesn't help.

No build step and no dependencies: plain HTML, CSS and JavaScript.

## Run it

```bash
# open directly
open index.html            # macOS (or double-click it)

# or serve it locally (needed by some browsers for file:// scripts)
npm start                  # → http://localhost:8080
```

## Test it

```bash
npm test                   # Node 18+; runs tests/presets.test.js
```

The tests run every preset through the physics and check mass flow, outlet temperature, cooling and COP against the values recorded at handover. If you change the model on purpose, update `EXPECTED` in the test and explain why in the commit message.

## Files

| File | What's in it |
|---|---|
| `index.html` | Page markup: header controls, gas-path area, result cards, chart and tables |
| `styles.css` | All styles. Colours are CSS variables on `:root`, with dark-mode overrides |
| `physics.js` | **The model.** Constants, stage definitions (`STAGES`), sources, outlet, presets (`PRESETS`) and `compute(S)`, which walks the path and returns every number shown on the page. It has no DOM code, so it also loads in Node |
| `app.js` | UI only: renders the stage cards, gauges, charts and tables, plus drag-to-reorder, the preset picker and saving the last setup in the browser (`localStorage`) |
| `tests/presets.test.js` | Regression tests for the presets |
| `MODEL.md` | Equations, assumptions and known limits |

`physics.js` must load before `app.js` because both are classic scripts that share globals.

## Common changes

**Add a preset:** add an entry to `PRESETS` in `physics.js` with `mode`, `source`, `stages` (a list of `[type, params]`) and `outlet`, then add an `<option>` with the same key to the `#preset` select in `index.html`.

**Add a stage type:** add a definition to `STAGES`, where each parameter is `[label, unit, default, step]`. Set `exp: true` if it is an expander. Then add a `case` to the `switch` in `compute()` that updates `T`, `P` and `m`, and optionally writes `info` for the card footer in `stageStat()` in `app.js`.

**Change a physical assumption:** see `MODEL.md`. Everything is in `compute()`.

## Presets

| Key | Configuration | Outlet | Cooling | COP |
|---|---|---|---|---|
| `rental` | 4,000 L/min, 7.6 bar rental compressor → aftercooler → dryer → 500 L receiver → regulator at 6.3 bar → 4 × LZB46 → 12 % duct gain | 0.8 °C | 2.29 kW | 0.10 |
| `workshopVortex` | 2.2 kW workshop compressor → vortex tube | 19 °C | 0.04 kW | 0.02 |
| `workshopBurst` | Workshop compressor filling a 300 L receiver, 1 × LZB46 in bursts | 0.7 °C | 0.58 kW | 0.07 |
| `scuba` | 12 L, 200 bar scuba cylinder → two regulators → vortex tube | −7 °C | 0.12 kW | 0.03 |
| `junior` | Bauer Junior II (200 bar) → regulator at 9 bar → turbine at 75 % | −80 °C | 0.22 kW | 0.10 |

Ambient is 30 °C for all presets. A split air conditioner in Dubai runs at a COP of about 3.

## Status and caveats

These are engineering estimates from an ideal-gas model, **not measurements**. The vane-motor efficiency comes from the LZB46 datasheet (843 W shaft power at 16.2 L/s free air at 6.3 bar(g)), and the vortex-tube curve is a fit to typical vendor data. Validate against the bench test before relying on the numbers.
