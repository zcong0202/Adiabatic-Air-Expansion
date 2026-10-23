# Adiabatic Air Expansion

Open **[the cooling computation lab](index.html)**. Set pressure and demand. Check output in g/s, receiver need and duration. Compare stock compressors in the dot chart. Simulate a target air volume over time.

Open **[the full computation panel](engineering.html)** for all source/network inputs, saved CFD, CAD, Lean references and exports. Both views share source inputs. The lab has a separate, explicit transient budget.

Open **[the project overview](AA%20Project/project-overview.html)** for the full research record: design documents, Lean proofs, CFD, CAD and decisions.

Open **[the new 2–77 g/s CFD sweep](AA%20Project/Airflow-Assessment/mass-flow-study/results/index.html)** for native 2D sections, rotatable 3D cold-air volumes, 1/2/4-nozzle comparisons, mesh/model checks, CAD and source budgets. This is a separate prescribed-source study. It does not rescale the panel’s earlier CFD.

## Use

Open `index.html` directly, or run `npm start` and visit `http://localhost:8080`. No build step. No runtime dependencies or external fonts.

- **Focused lab:** pressure support, warm receiver sizing, component mass-flow dot chart and cooling/recovery time series. No isometric drawing.
- **Delivery modes:** direct system output or an isolated precharged cold-tank what-if. Cold-tank charging is not established.
- **Full system panel:** mass, enthalpy, pipe losses, motor work, receiver discharge, cold-storage budget and mixing limits.
- **Comparisons:** stock compressors, capacity-matched motor banks, nozzles, tank sizes, pipe lengths and expansion methods.
- **CFD evidence:** native-field cooled volume/mass for 16 executed outdoor cases. Time, region and temperature threshold controls. Animations and CAD.
- **Equations & limits:** first principles, supplier sources, numerical checks and conditional Lean coverage.

Inputs save locally and carry between the two views. Export source and transient settings from the lab. Import/export JSON, copy scenario links and export comparison CSV in the engineering view. The original calculator is preserved at [legacy.html](legacy.html). Its documented model disagreements remain; see [the audit](AA%20Project/Airflow-Assessment/pass-by-study/results/repo-model-audit.json) and [legacy documentation](LEGACY-CALCULATOR.md). The colleague’s [animated figures](figures/README.md) remain intact.

## Evidence limits

Calculated source temperatures assume a loaded motor catalogue pair, dry air and specified heat leakage. They are not measured hardware results. Changed inputs do not run or rescale CFD. CFD uses a prescribed source and excludes people, humidity, solar load and valve shutoff. The lab models an isolated precharged cold-tank discharge as a what-if. It does not establish stock-system charging. A charge above the calculated motor exhaust pressure is flagged. The original full panel retains its sealed cold-storage hold budget.

See [panel/MODEL.md](panel/MODEL.md) for equations, units, pressure topology and limitations. Existing Lean proofs establish conditional algebra, not the new numerical integration or hardware performance.

## Validate and reproduce

`npm test` runs 45 numerical checks, including six original regression tests. Browser evidence: [26 interaction checks](lab/evidence/browser-checks.json) and [scenario round trip](lab/evidence/roundtrip.json). `node tools/validate_panel.cjs` saves a numerical validation record.

Python data generation needs NumPy and CoolProp. Native fields are in the archived CFD data or the original raw-data checkout:

```bash
python tools/build_air_table.py
python tools/build_cfd_panel.py /path/to/pass-by-study/cfd/cases
python tools/build_validation.py --native /path/to/pass-by-study/cfd/cases
node tools/validate_panel.cjs
```

[Native archive instructions](AA%20Project/CFD-Archives/README.md). Do not treat a passed numerical screen as hardware validation.

## Interface sources

`lab/app.js` controls the focused numerical UI. `lab/style.css` defines its layout. Source/network equations remain in `panel/model.js`. `panel/dynamics.js` holds transient budgets. See [the transient specification](panel/TRANSIENT.md).

The previous isometric interface sources remain in `studio/` for reference. They are not loaded by the active page. Original artwork attribution remains in [ANATOMY-LICENSE](studio/ANATOMY-LICENSE).
