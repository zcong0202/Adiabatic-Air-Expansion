# Motor-mounted brake housing · R07

**Estimate-based static fit prototype. No powered-use qualification.**

R07 replaces the R05 case that conflicted with the R06 image-based CMD-23 model. The brake estimate remains unchanged. Open `index.html`; use Open cover, Rear, Exploded, Assumed arm envelope and part selection.

## Arrangement

Three flat-print pieces: recessed case, D-shaped motor adapter plate and smooth cover. The case supports the stock brake adapter on two short internal lands. Five M5 reference bolts attach the case to the motor plate. Two motor mounting holes attach the plate to the motor. No external base, second shaft or shaft extension is added.

The motor face remains z0, rotor plane z28, shaft z15–40 and hub envelope z18–38. To make room behind the rotor, the case back moves to z−18; its floor inner face is z−8. The cover inner face is z75 and outer front z85. The case envelope is279 ×210 ×103 mm, excluding motor, cable and fastener protrusions.

The central rear opening isØ124 around the estimatedØ108 motor. This leaves8 mm radial space in that section; motor inlet/exhaust fittings remain unmodeled. Confirm their clearance. The separate plate lets all three printed parts sit flat on the H2S bed. It also keeps the motor mounting face at its previous datum.

## Printable parts

- `housing-FIT-ONLY.stl`:279 ×210 ×93 mm cup. Flat outer rear face on bed, open face upward.
- `motor-plate-FIT-ONLY.stl`: D-shaped plate, clipped at x60;10 mm thick. Flat underside on bed.
- `lid-FIT-ONLY.stl`:279 ×210 ×10 mm. Flat inner face on bed.

Each STL has minimum z0 and one connected closed solid. The viewer uses assembly coordinates. All fit the H2S340 ×320 ×340 mm build volume.

For a non-powered fit print:0.4 mm nozzle,0.20 mm layers,8 wall loops,8 top/bottom layers,40% general infill and solid modifiers around mounting lands, posts and holes. Inspect support needs at the cable tunnel and nut-pocket roofs in Bambu Studio. Do not fill the sleeve bores with supports that cannot be removed. Use the actual filament profile. No G-code, print test or material strength validation is supplied.

PLA remains for static fit checks. Closed geometry, thicker walls and metal sleeves do not establish hot strength or fragment containment.

## Clearance changes

- Wider smooth caliper bulge;8 mm nominal wall.
- Rear brake pocket clears the pad adjuster and the assumed stepped IS adapter.
- Two IS51 lands at z−1 follow the estimated adapter rear face. Slots allow±4 mm radial travel.
- Cable entry follows the estimated negative-y cable direction. It does not specify a safe cable bend radius.
- Ø14 rear service opening gives straight access to the rear pad adjuster, without removing the case. Tool shape and actual screw orientation still need checking.
- Cover removes for caliper/rotor service. No separate printed caliper saddle.

`manifest.json` records72 selected interference pairs and18 allowance/access checks. All must pass for the build to finish. The0–30° arm sweep is an assumption. Conservative convex envelopes add3 mm in each axis to the body, controls and sampled sweep. This is a local layout allowance, not a measured tolerance or a guarantee that the full uncertainty ranges of the image model fit.

## Reference hardware

Eight M6 cover bolts/nuts, eight83 mm metal compression sleeves (OD10/ID6.6); five M5 motor-plate bolts/nuts, five8 mm sleeves (OD8/ID5.6); two M6×18 IS screw references inserted from the rear into the metal adapter. Motor mounting screw threads and safe engagement remain unknown. Viewer screw heads, washers and lengths are illustrative; match the actual selected hardware before a final print.

The disc, caliper, adapter and shaft hub stay metal. The existing hub is **still an envelope**: shaft clamping/keying/retention and disc-bolt thread engagement are not resolved. No functional printed hub or rotor is provided. The housing redesign does not complete the shaft coupling.

## Qualification still required

Actual brake/adapter dimensions and cable travel; motor threads, ports and bearing loads; retained metal hub, balance and disc runout; brake speed/heat duty; hot printed strength, creep and preload; suitable metal load path/guard for powered use. At400 W for10 s, the brake absorbs4 kJ. Vent slots are not a validated cooling system. Regulated, protected motor supply remains required; this enclosure is not a pressure vessel.

## Rebuild and evidence

1. `brake_estimate.py` regenerates reference brake meshes.
2. `build.py` creates case geometry, performs checks and writes the main viewer.
3. `build_brake_viewer.py` refreshes the brake-only viewer.
4. `render_preview.py` renders current assembly previews from the exact triangles.
5. Re-run `build.py` after documentation/preview updates to refresh the ZIP.

Python requires numpy, trimesh, manifold3d and Pillow for previews. Three.js/esbuild versions remain in the project. Rebundle viewer.js after changes. Primary dimensions are in parameters.json; topology is in build.py.

`redesign-report.html` gives R07 changes and limits. `brake-estimate/estimate-report.html` retains the R06 image-source record. Its R05 collision findings are historical. `load-screen.html` retains conditional torque/heat budgets, not structural approval. Old rear/carrier/shell STL files are excluded from the current pack; do not combine them with R07.
