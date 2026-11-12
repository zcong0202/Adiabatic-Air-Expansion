# R06 · Source-based brake fit review

The CMD-23 placeholder is replaced by an image-based estimate. See `brake-estimate/index.html`, `brake-estimate/estimate-report.html` and `brake_estimate.py`.

Nominal body + controls envelope: approximately55 ×110 ×60 mm (radial, tangential, axial). These are inferred dimensions, not manufacturer measurements. Planning ranges and provenance are in `brake-estimate/estimate-sources.json`.

The estimate conflicts with the retained R05 housing and lid. The source-case geometry is unchanged. R05 printed-body downloads are withheld from the current pack. Older STL files may remain locally; do not treat them as fitted parts. The pack now contains reference brake meshes only. No operating brake or hub is supplied.

Build order: `brake_estimate.py`, then `build.py`. Manifest collision volumes are findings, not passed checks. Some assumed brake controls collide with the old case; this is deliberately retained for review. See the report before changing dimensions.

# Historical R05 housing notes

**Gearbox-style fit prototype. No powered-use rating.**

Open `index.html`. The viewer starts with a closed case. Use **Open cover**, **Exploded**, orbit and part selection to inspect the arrangement.

## Form and integration

Two printed parts replace the R04 four-part cassette:

- `housing-FIT-ONLY.stl`: one cup with rounded circular body, smooth caliper bulge, internal adapter lands, internal gussets, rear motor plate and recessed rear nut pockets.
- `lid-FIT-ONLY.stl`: matching chamfered cover with recessed screw heads, a shallow circular face detail and five small caliper-side vents.

The housing follows the rotor and caliper envelope, like a gearbox cover. There is no separate printed caliper saddle or external bracket. The real brake stays inside. Eight metal through-bolts and metal compression sleeves close the assembly. The commercial caliper and correct Clarks IS adapter attach to lands inside the cup. These lands carry reaction into the rear plate and two motor mounting holes.

Envelope238 ×200 ×58 mm, versus R04's264 ×244 ×74 mm. Rear plate10 mm, wall8 mm, lid10 mm with recessed head seats. These are geometry changes, not proven strength increases. Brake and motor interfaces remain estimate-based.

## Printing

Both STLs are single connected, watertight solids in millimetres, with minimum z=0. Each fits the Bambu H2S340 ×320 ×340 mm bed. Print the cup with the motor mounting face on the bed, opening upward. Print the lid flat underside down. Inspect supports/bridges at the radial cable opening and cover slots in Bambu Studio.

For a static PLA fit print:0.4 mm nozzle,0.20 mm layers,8 wall loops,8 top/bottom layers,40% general infill and solid modifiers around motor holes, adapter lands and bolt bosses. Use the actual filament profile. No G-code or physical print validation is supplied.

Older R04 `rear`, `carrier` and `shell` STL files may remain locally for history. They are excluded from the R05 pack and viewer. Do not combine them with the R05 cover. Current pack contains **two STLs only**.

## Fit assumptions

User estimates remain: motor bodyØ108 ×48 mm, bossØ35 ×15, shaftØ12 ×25 exposed. Hole openings≈Ø7, centre pitch83, centres(0,+44) and(0,−39). Motor plate clearanceØ7.5 does not establish thread size.

Motor front face z0; shaft z15–40; hub envelope z18–38; rotor centre plane z28. Stock adapter IS51 slots allow±4 mm radial adjustment. Spacer4 mm, adapter shape and rotor-plane alignment are provisional. Exact PM hardware, washer stack, motor ports and cable sweep are not fully modeled. Confirm actual cable exit before final printing.

RotorØ160 is the selected size. Thickness1.8 and bolt circle44 mm are unverified. The hub envelope does not specify keying, clamping or axial retention. Rotor, retained hub, caliper, stock adapter and fasteners remain metal. No functional printed rotating parts are supplied.

## Evidence and limits

`manifest.json`: closed meshes, connected print solids, H2S envelope and selected non-interference pairs. This is geometry screening only, not full tolerance analysis, FEA or a hardware rating.

`load-screen.html` and `load-screen.json`: conditional torque and heat budgets.3 N·m at assumed70 mm pad radius gives42.9 N tangential force.9 N·m is a sensitivity input, not a certified safety factor.400 W for10 seconds gives4 kJ brake heat. A smoother enclosed case does not establish adequate cooling.

PLA remains for non-powered fit checks. Hot material strength, creep, preload, shaft/bearing loads, brake speed/heat duty, balance and fragment containment remain unqualified. A powered version needs a suitable material, verified hardware, metal backup load path and a suitable rotor guard. The case is not a pressure vessel. Keep the scuba supply regulated within the confirmed motor rating.

## Rebuild

Run `build.py` with numpy, trimesh and manifold3d. Main dimensions are in `parameters.json`; the R05 outline and integrated land topology are in the script. Run `calculate_loads.py` to refresh numeric load records. The HTML report is a fixed revision presentation.

Viewer uses Three.js0.170.0 and esbuild0.24.0. Rebundle `viewer.js` after edits, then rebuild to update the ZIP. The fallback software view may show triangle ordering artifacts; the saved CPU-rendered preview uses a depth buffer. Source mesh geometry is the same.

## Sources

- `user-estimates.json`, `mount-pattern.svg`: motor dimension derivation.
- `brake-interface-audit.json`, `evidence/`: Clarks and standard-interface evidence; older revision references are historical.
- [Clarks kit](https://www.amazon.ae/dp/B08RPBLC55).
- [H2S specifications](https://us.store.bambulab.com/products/h2s).
- [PLA material limits](https://help.prusa3d.com/article/pla_2062).
