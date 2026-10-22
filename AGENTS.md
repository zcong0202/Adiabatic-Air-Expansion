# Project instructions

- Use short sentences, active voice and consistent terms. Keep messages concise.
- Maintain `AA Project/project-overview.html` as the single project overview.
- Keep goals, scope, progress, decisions, open questions and next steps current.
- Distinguish measured evidence, numerical checks, conditional calculations and assumptions.
- Link claims to source documents, scripts, proofs, CAD and CFD evidence.
- Current use: open outdoor nozzles; people walk past; no seat or enclosure.
- Current priority: cooled air mass, volume, temperature deficit and persistence.
- Earlier seat/enclosure studies are historical. Do not use them as outdoor validation.
- Use diagrams when they clarify the system. End plans with unresolved questions, if any.
- Use gstack `/browse` for web browsing. Do not use Claude-in-Chrome tools.
- `/graphify` is an explicit trigger for the graphify skill.
- Preserve the original browser calculator at legacy.html with physics.js/app.js/styles.css.
- index.html is the focused numerical lab (lab/). engineering.html retains the full computation panel. Isometric studio sources are retained but not loaded.
- Both views use panel/model.js and shared aa-panel-v2 input state. panel/dynamics.js provides conditional mixing and precharged-tank transients. Preserve the original figures.
- Illustration is not CFD. Keep saved-case source, time, region and hardware limits explicit.
- Never rescale saved CFD when inputs change. Distinguish budgets, CFD, conditional Lean algebra and hardware validation.
- New panel receiver/EOS calculations are numerically tested, not Lean-verified.
- Large artifacts use Git LFS. Native solver output is stored in the split archives described in `AA Project/CFD-Archives/README.md`.
