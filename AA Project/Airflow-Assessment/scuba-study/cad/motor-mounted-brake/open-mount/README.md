# Open motor / brake mount · OPEN-01

Separate open variant. No walls, lid or enclosure. Enclosed R07 remains available one directory above.

Open `index.html`. Use **Mount only**, **Full assembly**, and **Exploded** to inspect the parts.

## Parts

| File | Size (mm) | Purpose |
|---|---|---|
| open-frame-FIT-ONLY.stl | 189 × 152 × 18 | Open ring, two brake-support arms, plate posts and IS adapter lands |
| motor-plate-FIT-ONLY.stl | 136 × 152 × 10 | Motor attachment plate |
| shaft-collar-REFERENCE.stl | See model | Shaft collar / disc hub reference only |

The two fit parts are separate, connected closed solids. Both fit the H2S bed. STLs have their flat rear faces at Z=0. PLA and a 0.4 mm nozzle may be used for non-powered fit checks; no print recipe or powered-load rating is established.

## Interfaces

Motor estimates: body Ø108 × 48 mm; boss Ø35 × 15 mm; shaft Ø12 × 25 mm exposed. Motor-hole centres are (0,+44) and (0,−39) mm. Holes are 7.5 mm clearance; actual threads remain unverified.

Five M5 reference bolts join the plate to the open support. Five 8 mm long metal sleeve references sit in the posts (OD8 / ID5.6 mm). Two IS adapter slots have a nominal 51 mm pitch and ±4 mm radial travel. Estimated M6 × 18 adapter bolts enter from the rear. The stock brake adapter and caliper remain metal hardware. Check actual thread engagement before choosing bolts.

The rotor plane remains 28 mm from the motor face. The collar occupies Z18–38 mm. It has a 12.4 mm plain bore and six plain disc holes on a 44 mm pitch circle. These holes have no working thread, clamp, key or axial retention. This is not a working torque coupling. A functional metal hub and disc fastening still need to be specified.

## Checked / unknown

`manifest.json` records 43 selected interference checks and 10 allowance checks. They pass for this nominal model. Brake-body/control allowances are 3 mm; the arm sweep is an assumed 0–30°. The brake is an image-based CMD23 estimate, not a measured production model. Actual fit is unverified.

This open support is not a rotor guard. Strength, heat, vibration, speed and brake duty are unverified. Use these prints for static fit checks only.

## Rebuild

Python dependencies: numpy, trimesh, manifold3d; Pillow for preview rendering.

Run `python build.py`, then `python render_preview.py`, then `python build.py` again to include previews in the ZIP. `reference-inputs.json` freezes the R07 assembly and parameters. `brake_reference.py` preserves the exact estimated brake solids for robust Boolean checks. The bundle is included for offline viewing. To change viewer source, bundle `viewer.js` with esbuild and Three.js 0.170.0, then rebuild.

Next: measure the actual caliper/adapter, confirm motor threads, and define the shaft hub before load testing.
