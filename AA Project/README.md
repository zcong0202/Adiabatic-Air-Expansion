# AA engineering project

Start with [the interactive project overview](project-overview.html). Open it in a browser. All engineering work imported on 21 October 2026 lives here. The root browser calculator remains a separate, pre-existing model.

## Current scope

Open outdoor nozzles cool a local air mass while people pass. Commercial components provide the compressed air and expansion; nozzle geometry may be custom. The working study range is 20–50 cm from outlet to target. Valve opening is at most 30 seconds. A person's exposure is shorter.

The immediate output needed is the mass and volume of air below a specified temperature, its location and persistence. Current outdoor CFD mainly evaluates moving 5 × 5 cm air patches. Total cooled volume and mass remain unreported. Earlier seated-enclosure results do not validate this use.

## Evidence map

| Material | Location |
|---|---|
| Current outdoor results, source assumptions, animations and nozzle CAD | `Airflow-Assessment/pass-by-study/` |
| Source equations | `Airflow-Assessment/pass-by-study/FIRST-PRINCIPLES.txt` |
| Compressor, receiver and hose calculations | `Airflow-Assessment/pass-by-study/scripts/system_sizing.py` and `results/system-sizing.json` |
| Conditional Lean proofs and build evidence | `Airflow-Assessment/formal-model/` |
| Historical seat CFD and source assessment | `Airflow-Assessment/motor-seat-study/` |
| Earlier vortex/nozzle and stock-system studies | `Airflow-Assessment/optimization/`, `system-study/`, `designs/`, `results/` |
| Supplied documents and presentations | `Project-Documents/` and `1008.pptx` |
| Activation test and controller work | `Activation-Test/` and `Controller-App/` |
| Full native solver output | [Git LFS archive instructions](CFD-Archives/README.md) |
| Import inventory, source hashes and archive hashes | `import-manifest.json` |
| Import checks | `import-verification.json` |

## Limits

- About 77.6 g/s at approximately 1°C is a conditional source model, not measured motor exhaust performance.
- It requires the assumed loaded motor operating point, external shaft heat rejection, air treatment and low heat pickup.
- Lean checks algebra under hypotheses. It does not validate turbulence, source performance or hardware.
- Outdoor CFD uses prescribed outlet conditions. It does not solve the complete compressor, motor, valve and hose transient.
- Nozzle prototypes share the simulated outlet dimensions. Full internal losses and stock connections remain unvalidated.
- Existing calculator presets and imported studies use different assumptions. They were not silently reconciled during import.

## Reproduce

The root calculator runs with `npm test`. The sizing calculation uses Python standard-library modules:

```bash
python3 'AA Project/Airflow-Assessment/pass-by-study/scripts/system_sizing.py'
```

Each study retains its source scripts, dependency declarations, evidence and original deliverable bundles. Restore native CFD output only when needed. Local runtime caches are not versioned.
