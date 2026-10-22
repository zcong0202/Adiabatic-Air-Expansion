# Adiabatic Air Expansion

Open **[the visual designer](index.html)**. Select a component in the isometric drawing. Change its settings. See live source results. The style follows the air-cycle seat figure; the system uses outdoor nozzles and a walking path.

Open **[the full computation panel](engineering.html)** for all inputs, calculations, comparison tables, Lean references and exports. Both views use the same model and share input state.

Open **[the project overview](AA%20Project/project-overview.html)** for the full research record: design documents, Lean proofs, CFD, CAD and decisions.

## Use

Open `index.html` directly, or run `npm start` and visit `http://localhost:8080`. No build step. No runtime dependencies or external fonts.

- **Visual designer:** click-to-edit source, receiver, pipes, expansion and nozzles. Four live results. Light/dark themes.
- **Full system panel:** mass, enthalpy, pipe losses, motor work, receiver discharge, cold-storage budget and mixing limits.
- **Comparisons:** stock compressors, capacity-matched motor banks, nozzles, tank sizes, pipe lengths and expansion methods.
- **CFD evidence:** native-field cooled volume/mass for 16 executed outdoor cases. Time, region and temperature threshold controls. Animations and CAD.
- **Equations & limits:** first principles, supplier sources, numerical checks and conditional Lean coverage.

Inputs save locally and carry between the two views. Save a scenario in the designer. Import/export JSON, copy scenario links and export comparison CSV in the engineering view. The original calculator is preserved at [legacy.html](legacy.html). Its documented model disagreements remain; see [the audit](AA%20Project/Airflow-Assessment/pass-by-study/results/repo-model-audit.json) and [legacy documentation](LEGACY-CALCULATOR.md). The colleague’s [animated figures](figures/README.md) remain intact.

## Evidence limits

Calculated source temperatures assume a loaded motor catalogue pair, dry air and specified heat leakage. They are not measured hardware results. Changed inputs do not run or rescale CFD. CFD uses a prescribed source and excludes people, humidity, solar load and valve shutoff. Cold storage has a separate finite-energy budget; pressurised charging/discharge is not established.

See [panel/MODEL.md](panel/MODEL.md) for equations, units, pressure topology and limitations. Existing Lean proofs establish conditional algebra, not the new numerical integration or hardware performance.

## Validate and reproduce

`npm test` runs independent physics checks plus the six original regression tests. `node tools/validate_panel.cjs` saves a numerical validation record.

Python data generation needs NumPy and CoolProp. Native fields are in the archived CFD data or the original raw-data checkout:

```bash
python tools/build_air_table.py
python tools/build_cfd_panel.py /path/to/pass-by-study/cfd/cases
python tools/build_validation.py --native /path/to/pass-by-study/cfd/cases
node tools/validate_panel.cjs
```

[Native archive instructions](AA%20Project/CFD-Archives/README.md). Do not treat a passed numerical screen as hardware validation.

## Visual interface sources

`studio/app.js` controls the designer. `studio/style.css` defines its layout. `studio/artwork.js` and `studio/diagram.css` adapt the existing air-cycle artwork. The seat and enclosure are removed. Illustration is not CFD. Attribution: [ANATOMY-LICENSE](studio/ANATOMY-LICENSE). Rebuild with `python studio/build-artwork.py` from the repo root. Numerical equations remain in `panel/model.js`.
