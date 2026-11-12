# One-piece motor / brake mount · OPEN-02

Motor plate and brake support are one connected printed solid. No walls or cover. Five integral solid posts replace the previous joint bolts, nuts and sleeves. Motor and brake attachment bolts remain.

- Mount: **189 × 152 × 28 mm**. File: `single-piece-mount-FIT-ONLY.stl`.
- Collar: separate `shaft-collar-REFERENCE.stl`. It rotates with the shaft and must not be joined to the stationary mount.
- Viewer: `index.html`. Mount only / full assembly / exploded views.

## Print and fit

The mount STL is oriented with the motor plate front face on the bed, at Z=0. It fits the H2S bed. Local supports are needed under the offset brake-support arms/ring. It is not a support-free flat plate. PLA with a 0.4 mm nozzle is for static fit checks only; strength and thermal duty are unverified.

Motor estimates remain Ø108 × 48 mm body, Ø35 × 15 mm boss and Ø12 × 25 mm exposed shaft. Motor holes remain at (0,+44) and (0,−39) mm, with 7.5 mm printed clearance. Brake adapter slots retain 51 mm pitch and ±4 mm radial adjustment. Rotor plane remains 28 mm from the motor face. The brake adapter is separate metal hardware. Actual threads, adapter offsets and motor ports remain unverified.

## Evidence and limits

`manifest.json` records the connected-solid check, bed envelope, selected non-interference checks and 3 mm local brake/control allowances. These apply to the estimated CMD23 model. Actual brake fit remains unverified. No structural or thermal qualification is claimed.

The collar has a plain 12.4 mm bore and six plain disc holes on a 44 mm pitch circle. It has no working shaft clamp, key, thread or axial retention. It remains a reference, not a powered coupling. The open mount provides no rotor guard.

Next: check actual hardware fit, specify a functional shaft hub, then validate strength and hot duty before powered use.

## Rebuild

Python: numpy, trimesh, manifold3d; Pillow for previews. Run `python build.py`, `python render_preview.py`, then `python build.py` to pack images. Frozen `reference-inputs.json` and `brake_reference.py` preserve source geometry. Viewer uses the included offline Three.js bundle (0.170.0).

Previous two-piece variant: `../open-mount/index.html`. Enclosed variant: `../index.html`.
