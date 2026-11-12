# Motor-mounted brake · R04

12 Nov 2026. **Ribbed static fit prototype. Not released for powered operation.**

Open `index.html`. Orbit, select parts, hide the case or use the explode slider. Offline Three.js viewer; SVG fallback when WebGL is unavailable. Software rendering may show triangle depth-order artifacts.

## Changes

- 264 × 244 mm rounded rectangular cassette. Total forward depth74 mm, including lid ribs.
- 10 mm rear plate, 6 mm local ribs and reinforced motor-hole lands.
- Wide44 × 108 mm caliper saddle. 8 mm deck, locally recessed for caliper clearance. Two8 mm triangular webs and an outer spine replace the old narrow pedestal.
- Four M6 reference anchors attach the saddle to the plate. Wide metal washers; no printed threads.
- Eight M6 reference closure bolts and54 mm metal compression sleeves. Shell wall6 mm; lid6 mm with4 mm ribs.
- Stock Clarks metal IS adapter retained as the interface route. IS51 mm slots allow±4 mm radial adjustment. Exact radial/axial position and adapter envelope are still assumptions.

The brake reaction follows caliper → stock adapter → saddle → rear plate → motor mounting holes. The closure sleeves reduce shell compression under bolt preload. They do **not** create a qualified metal torque path. The case has no pneumatic pressure path and no fragment-containment rating.

## Printable files

Four updated files: `rear-FIT-ONLY.stl`, `carrier-FIT-ONLY.stl`, `shell-FIT-ONLY.stl`, `lid-FIT-ONLY.stl`. Each is a connected, watertight positive-volume solid in millimetres. Each is translated onto z=0 for printing. Viewer geometry retains assembly coordinates.

The R04 carrier replaces the superseded R03 56 mm carrier. IS51 is the frame-side interface for the stock adapter; it is **not** the caliper's native Post Mount74.17 interface. Do not use any older exported carrier.

Largest footprint264 × 244 mm fits the [H2S340 × 320 × 340 mm volume](https://us.store.bambulab.com/products/h2s). Start a **fit print** with0.4 mm nozzle,0.20 mm layers,8 wall loops,8 top/bottom layers,40% general infill and local solid regions around holes/webs. Rear, carrier and lid print flat underside down; shell stands on its end. Inspect bridging and supports at cable/vent openings in Bambu Studio. No sliced profile/G-code or print test is supplied.

PLA remains for **non-powered fit checks** here. [PLA material limits](https://help.prusa3d.com/article/pla_2062) include brittleness and low heat resistance. H2S supports engineering materials such as PC, but material choice alone does not qualify the brake. Actual layer adhesion, hot strength, creep and fastener clamp relaxation require tests.

## Motor fit retained

User estimates: bodyØ108 ×48; bossØ35 ×15; shaftØ12 ×25 exposed. Two approximatelyØ7 openings are vertically aligned.90 mm outer span minus7 gives83 mm centres.65 mm upper-hole-top to boss-bottom gives upper centre+44 mm and lower−39 mm relative to shaft centre. Printed motor clearanceØ7.5 is provisional; it establishes no thread size.

Motor front face is z0. Shaft z15–40. Hub envelope z18–38. Rotor centre plane z28. Motor front stack88 mm excludes rear accessories; manufacturer overall122 mm reference remains historical evidence. No shaft key, retention or functional hub is designed by this envelope.

Metal rotor, retained metal hub, caliper, stock adapter, spacers, sleeves, washers and bolts remain hardware. Their viewer envelopes are **not purchase drawings**. Rotor thickness1.8 and bolt circle44 mm remain unverified. Stock adapter geometry, washer stack, PM screws, cable sweep and motor ports are not fully modeled. Adapter-spacer length4 mm is provisional; it is not a thermal insulator.

## Calculations and verification

`load-screen.html` explains the conditional statics. `load-screen.json` stores inputs and results. Run `calculate_loads.py` to recompute the numeric record; the HTML report is the fixed R04 presentation.3 N·m reference torque gives42.9 N tangential pad force at assumed70 mm radius.9 N·m is a sensitivity input, not a measured peak or certified safety factor.400 W for10 s deposits4 kJ in the brake system. Separate motor torque/RPM maxima must not be multiplied into a claimed operating point.

`manifest.json` records closed meshes, single-solid print checks, printer envelope and selected interference checks. These checks establish geometry consistency only. They do not establish structural, thermal, fatigue, bearing, balancing, brake speed or guard performance. Bolt envelopes are illustrative; omitted stock hardware can still interfere.

`build.py` regenerates solids, assembly data, STLs, viewer and ZIP. Requires Python with numpy, trimesh and manifold3d. `parameters.json` holds main dimensions; structural topology and illustrative caliper shape are in the script. Viewer bundle uses Three.js0.170.0 and esbuild0.24.0. Rebuild bundle after viewer.js changes, then run build.py. Sources and license are packaged.

## Before powered operation

Confirm real brake offset/clearance and motor threads/engagement. Verify shaft bearing and case mounting loads. Use a retained metal hub with measured runout/balance. Establish actual motor torque-speed-flow conditions, stall/transient torque and brake speed/heat rating. Qualify a metal backup load path, suitable rotor guard and hot structural material. The current PLA casing is not an approved dynamometer.

Use a regulated, protected motor supply within its confirmed rating. Never connect the scuba cylinder directly to the motor. High flow does not imply high allowable motor pressure. No pneumatic components are redesigned here.

## Evidence

- `user-estimates.json`, `mount-pattern.svg`: user motor dimensions and tangent derivation.
- `brake-interface-audit.json`, `evidence/`: standard interface and Clarks source records. Earlier R03 references in these audit records are historical.
- [Selected Clarks CMD-23 kit](https://www.amazon.ae/dp/B08RPBLC55).
- [Clarks manufacturer](https://www.clarkscyclesystems.com/mechanical-disc-brake-sets-1/cmd-23).
- [Motor manufacturer](https://www.cosmostar.net/product/air-motor-and-agitator/255-am0701-0-9-hp-air-operated-vane-type-air-motor).
- [Load screen](load-screen.html) and [geometry manifest](manifest.json).
