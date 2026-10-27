# Storyboard shots 11–13

Editor handover · 27 October 2026.

- `index.html`: preview, downloads and source links.
- `exports/`: 1920 × 1080 PNG stills, editable SVG labels/geometry, silent H.264 MP4 clips.
- `11/12/13-narration.txt`: proposed voice copy. No voice recording included.
- `11/12/13-caption.srt`: optional short captions.
- `data/`: simulated patch values and configuration comparison CSVs.
- `manifest.json`: case IDs, native field/mesh verification and export hashes.
- `validation.json`: video duration/frame/resolution checks and local links.
- `scripts/build.py`: reproducible native-field rendering; run `--movies` for clips.
- `scripts/package.py`: validation, gallery, narration and ZIP.

## Evidence and scope

Shot 11: `scuba19_n1_wide_fine`, 103,572 cells, one 280 × 40 mm outlet,
19.4 g/s, prescribed 4.313°C source, 30°C ambient. Side slice is taken from the
native cell containing x=0. Patch values use best sampled 5 × 5 cm air patches
on the full 20/50 cm cross-sections. They are not probes on the side slice.

Shot 12: five saved 77 g/s configurations, prescribed 0.959°C source,
30°C ambient, native fields at 10 s. All have the same 2.250 kW supply deficit.
Displayed cold volume uses the same whole domain. It is not heat removed from a person.
Nozzle boxes show CFD outlet boundary geometry, not internally resolved printable CAD.

Shot 13: `m77_n4_wide_opposed_fine`, 114,408 cells, four opposed outlets,
77 g/s total, 0.959°C prescribed source, 30°C ambient. Blue geometry is the
boundary of native cells at T≤24°C, not a smooth continuum isosurface.
The 1.6 m slice uses the native cell containing that plane. Domain: 2.5 × 2.2 × 2.7 m.

Still air and gravity in all cases. No people, solar heating or wind. None is
hardware validated. No measured points have been invented. No new CFD was run.

## Changes to storyboard wording

- “Measured points” becomes “simulated patch temperatures”. The cited 14 October
  measurement deck was not matched to this source or geometry.
- “Warms within half a metre” becomes “mixes, sinks and warms with distance”.
  This single-nozzle case retains cooling at 50 cm.
- “Room-scale cooling around people” becomes “a localized simulated cold volume”.
  No occupied-room or passing-person result exists in the selected fields.
- “Air mass times temperature drop” becomes “mass flow × specific heat × temperature drop”
  when discussing cooling power.

## Timing

Clip lengths: 14 / 14 / 16 seconds. CFD time: 0–10 s while the source stays ON.
Native integer-second fields are held; no field interpolation, post-shutoff
decay or particle trajectories are added. Shot 13 changes only the camera
between saved fields. These are data renders, not new physical simulations.
