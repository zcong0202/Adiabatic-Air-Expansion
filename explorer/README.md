# Ideal Air-Cycle COP Explorer (MIT Open Lab dashboard)

Four 16:9 pages for a big screen, showing the highest-COP adiabatic air expansion cooling cycle:

1. **Parameters and curve**: COP against supply pressure for the current setup, with the optimum pressure.
2. **Plant and flow**: the plant drawn to scale, with state points and an energy table.
3. **Recovery shares and COP**: how turbine-work recovery and compression-heat recovery move the COP.
4. **Why the COP stays low**: where the electricity goes, and COP against machine efficiency.

Chinese and English, switchable in the header. No build step: plain HTML and JavaScript.

## Run it

The plant drawing loads ES modules and a Web Worker, so serve the folder rather than opening the file directly:

```bash
npx --yes serve -l 8080 .   # from the repo root, then open http://localhost:8080/explorer/
```

## Files

| Path | What's in it |
|---|---|
| `index.html` | Page markup and styles |
| `app.js` | UI: controls, charts, tables, language switch |
| `params.js` | Every parameter with its default, range and source |
| `model/` | The physics: compression, expansion, work and heat recovery, whole system, sweep, ledger |
| `plant/`, `kit/` | The isometric plant drawing (rendered in a worker) |
