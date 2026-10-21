# Figures

Two interactive isometric figures for explaining the system, made for the MIT Open Lab show on Nov 16 and for the 200 bar discussion. Each one is a single self-contained HTML file: open it in a browser, with no install and no network needed. They follow the system's light or dark setting.

| File | What it shows | Interaction |
|---|---|---|
| `fig1-air-cycle-seat.html` | **Fig 1 · Air-cycle seat:** the demo rig. A rental compressor feeds an aftercooler, then a tank and a regulator at 6.3 bar(g). Four LZB46 vane motors drive generators, a load bank burns off the power, and an insulated duct carries the cold air to a diffuser over a chair, with a thermometer beside it | Move the pointer left and right to set the generator load (0–100 %). Toggle **7.6 bar ↔ 200 bar** supply to compare. Live values on the drawing |
| `fig2-ideal-air-cycle.html` | **Fig 2 · Ideal air cycle:** the theoretical limit. One motor and crankshaft drive a 3-stage intercooled piston compressor and an expansion turbine on the same shaft, so turbine work goes straight back into the compressor. Exhaust runs to the seat | Move the pointer left and right to set the pressure ratio (1.5–9.5). Toggle **ideal ↔ realistic** machines. A COP-versus-pressure-ratio chart shows the split-AC band |

Arrow keys also work once the figure has focus. The animation stops when the system asks for reduced motion.

## Key numbers (30 °C ambient, 78 g/s)

| Case | Outlet | Cooling | COP |
|---|---|---|---|
| Fig 1, 7.6 bar supply, full load | 0.8 °C | 2.29 kW | 0.10 |
| Fig 1, 200 bar supply, full load | −25.9 °C | 4.38 kW | 0.05 |
| Fig 2, ideal, pressure ratio 7.3 | −96 °C | 9.9 kW | 3.4 |
| Fig 2, realistic (80 % efficiencies), pressure ratio 7.3 | −57 °C | 6.8 kW | 0.62 |

Both figures use the same ideal-gas model as the calculator (see `../MODEL.md`). Fig 2's model is in `src/ideal-cycle/live.js` (`model()`). The values are calculated, not measured.

## Editing the figures

The HTML files are **build output**. Small text or number changes can be made directly in them, since the model code is near the end of each file. For changes to the drawing, edit the sources in `src/` and rebuild with the [anatomy](https://github.com/wheresryan22/anatomy) isometric kit (MIT, see `src/ANATOMY-LICENSE`):

```bash
git clone https://github.com/wheresryan22/anatomy
cp -r src/air-cycle src/ideal-cycle anatomy/src/figures/
cd anatomy/src
node figures/air-cycle/build.mjs --audit          # writes figures/air-cycle/air-cycle.html (dark)
node figures/air-cycle/build.mjs --light --audit  # light version
node figures/ideal-cycle/build.mjs --audit
```

`--audit` checks the geometry (overlaps, floating pipe ends, depth order) and fails the build if anything is wrong. `ideal-cycle` reuses `air-cycle/air-cycle.css`, so keep both folders together.

| Source file | Role |
|---|---|
| `build.mjs` | Geometry: every part's position and size, the pipe routes, callout anchors and caption text |
| `live.js` | Runtime: the thermodynamic model, value chips, controls, animation and chart. `__DATA__` is filled in by the build |
| `*.css` | Chip, control and chart styles |

To ship a rebuilt figure that follows the system light or dark setting, add this just before `</body>`, as the committed files already do:

```html
<script>(function(){var d=matchMedia("(prefers-color-scheme: dark)").matches;document.body.setAttribute("data-theme",d?"dark":"light");document.documentElement.style.colorScheme=d?"dark":"light";})();</script>
```
