# Adiabatic Air Expansion

Open **[the computation panel](index.html)**. It compares stock supply, expansion, receivers, pipes and nozzles for outdoor pass-by cooling.

Open **[the project overview](AA%20Project/project-overview.html)** for the full research record: design documents, Lean proofs, CFD, CAD and decisions.

## Use

Open `index.html` directly, or run `npm start` and visit `http://localhost:8080`. No build step. No runtime dependencies or external fonts.

- **System:** mass, enthalpy, pipe losses, motor work, receiver discharge, cold-storage budget and mixing limits.
- **Comparisons:** stock compressors, capacity-matched motor banks, nozzles, tank sizes, pipe lengths and expansion methods.
- **CFD evidence:** native-field cooled volume/mass for 16 executed outdoor cases. Time, region and temperature threshold controls. Animations and CAD.
- **Equations & limits:** first principles, supplier sources, numerical checks and conditional Lean coverage.

Inputs save locally. Export/import JSON scenarios, copy a scenario link, or export comparison CSV. The original calculator is preserved at [legacy.html](legacy.html). Its documented model disagreements remain; see [the audit](AA%20Project/Airflow-Assessment/pass-by-study/results/repo-model-audit.json) and [legacy documentation](LEGACY-CALCULATOR.md). The colleague’s [animated figures](figures/README.md) remain intact.

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
