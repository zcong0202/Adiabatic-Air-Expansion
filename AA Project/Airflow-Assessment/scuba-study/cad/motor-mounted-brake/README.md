# Motor-mounted brake · R01

12 Nov 2026. **Static fit prototype only. Not fitted to the user's hardware.**

Open `index.html` in a browser. No server or internet required. Drag to orbit; scroll to zoom. Use the explode slider, select parts, hide the casing, isolate parts or export a PNG. When WebGL is unavailable, the viewer uses a software SVG renderer and exports SVG. The software renderer can show depth-order artifacts on thin faces; these are not CAD cuts.

## Arrangement

Motor mounting holes → adapter plate → caliper carrier and chamber → bolted lid.

The rotor sits on a hub directly on the motor shaft. There is no second shaft, coupling or external base. The motor supports the casing through its mounting holes. This assumes the real mounting holes can carry that load and accept this orientation; neither is verified.

## Files

- `rear-FIT-ONLY.stl`: motor adapter, example mounting pattern.
- `carrier-FIT-ONLY.stl`: caliper carrier, example mounting pattern.
- `shell-FIT-ONLY.stl`: brake chamber with cable access.
- `lid-FIT-ONLY.stl`: vented cover.
- `parameters.json`: editable dimensions, all in mm.
- `build.py`: parametric solid construction with trimesh/manifold, mesh export and interference checks.
- `manifest.json`: checks, dimensions and unresolved interfaces.
- `viewer.js`, `viewer.template.html`, `viewer.bundle.js`: editable and bundled viewer.

The four STL meshes are flat-faced print candidates for a **non-powered fit check**. Orient the rear, carrier and lid with their broad rear faces on the bed. Stand the chamber on its end face; inspect support needs at the cable opening in the slicer. No printer profile or physical fit is validated. Metal bolts/nuts are required for assembly; printed threads are not provided.

Disc, hub, motor, caliper, pads and metal screws are reference geometry in the viewer. They are not production CAD or printable operating parts. No functional rotor/hub STL is released. The assembly is therefore **not an all-printed operating brake**.

## Example dimensions

Case Ø248 × 51 mm. Rear 6 mm; chamber 40 mm; lid 5 mm.
Selected Clarks disc diameter 160 mm. Disc thickness 1.8 mm and six-hole 44 mm pitch circle are assumptions, not checked Clarks dimensions.
Motor envelope Ø80 × 90 mm. Shaft Ø12 × 32 mm is an example, not a measurement. The user's earlier “4 cm” does not establish a shaft diameter.
Example motor holes: (±24, ±24), Ø6.5 mm clearance. No motor thread is specified.
Example caliper holes: (94, ±28), Ø6.5 mm. The actual Clarks tabs may require a different carrier and orientation.

`parameters.json` controls case, motor-hole and shaft/rotor dimensions. The caliper envelope and carrier base are illustrative fixed geometry in `build.py`; a real caliper drawing requires revising those solids. Parameter edits require rebuilding; the viewer does not silently alter the download meshes.

## Before any powered version

Measure the motor mounting face, hole coordinates, thread/engagement, shaft diameter, usable length, key/flat and axial retention. Measure the caliper and rotor interfaces. A plain bore envelope in this model does not define torque transmission or hub retention.

Verify the motor shaft/bearings can carry the overhung rotor and hub, and that the mounting holes can carry the case/caliper. Check dynamic balance, disc runout, rotor/hub RPM limits and braking duty. Add an engineered metal load path, retained metal hub, metal rotor and suitable guard for powered tests. PLA carrier/case strength, creep and heat resistance are unqualified. This shell is not a fragment-containment guard. Vent slots and air gaps do not establish thermal safety.

At 400 W for 10 seconds, the brake receives 4 kJ. The selected bicycle brake has no verified rating for this duty or the motor's speed. These parts must not be treated as an approved 3000 RPM dynamometer.

The brake can react torque into the motor body in this arrangement. Steady reaction torque can close internally, but start/stop loads, imbalance, hose loads and the complete assembly still need controlled support and handling. Rigidly mounting a caliper does not measure torque. Cooling power needs an independent torque measurement or a validated motor map, plus RPM and airflow.

This casing contains no pneumatic path. Keep motor inlet and exhaust accessible; port locations are not known and not modeled. Use a regulated, protected supply within the confirmed motor rating. Never connect the scuba cylinder directly to the motor.

## Validation and rebuild

Generated meshes have closed positive volume. Ten selected pairs have no positive-volume interference in the example assembly. This is geometry screening only, not a complete interference, tolerance, strength, heat, speed or hardware qualification.

Run `build.py` with Python containing numpy, trimesh and manifold3d. Viewer bundle uses Three.js 0.170.0 and esbuild 0.24.0. Bundle with `esbuild viewer.js --bundle --format=iife --minify --outfile=viewer.bundle.js` using those dependencies. Re-run `build.py` after bundling to refresh the ZIP. Three.js license included.

References: [AM0701 manufacturer](https://www.cosmostar.net/product/air-motor-and-agitator/255-am0701-0-9-hp-air-operated-vane-type-air-motor), [selected Clarks kit](https://www.amazon.ae/dp/B08RPBLC55), [prior load calculations](../../results/friction-fan-load.html), [prior brake plan](../../results/diy-brake-plan.html).
