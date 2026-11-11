# Motor and brake static fit layout

This is a geometry study. It is not the powered, fully printed assembly requested.

The AM0701 manufacturer publishes a 1–7 bar operating range. The reference scuba source is about 200 bar. Do not bypass pressure regulation. A restriction or partly opened valve does not limit downstream static pressure. Use a correctly pressure-rated and flow-qualified pressure-reduction/protection package.

## What is supplied

- Four closed-mesh STL layout parts, in millimetres: base, example cradle, blank bearing support and blank brake adapter.
- `layout.scad`: editable geometry. All hardware dimensions are examples, not actual fit dimensions.
- `layout-preview.png`: static assembly with translucent hardware envelopes.
- `manifest.json`: missing measurements, assumptions and mesh checks.
- `static-fit-layout.zip`: bundle.

Cradle quantity: 2. Bearing-blank quantity: 2. No bearing seats or brake mounting pattern are cut. No fitted or torque-transmitting coupler STL is supplied. The blue object is a solid spacing envelope, not a coupling.

## Why powered use is not established

Actual shaft diameter, protrusion, retention and key/flat/thread are unknown. The previous “4 cm” estimate does not identify these dimensions. Motor body/mount geometry and brake selection are also unknown.

PLA brake supports/couplers need strength, temperature, creep, fatigue, retention, alignment and speed evaluation. Mesh closure is not this evaluation. The earlier 400 W cooling budget is not an operating rating for these parts. No rotating containment is supplied.

The exported 80 mm-body cradle is a labelled example, not an AM0701 fitting. Do not attach the motor and power this layout. Printed guides/accessories are useful, but the hot brake and rotating load path still require a qualified design.

## Next inputs

1. Workshop measurements: body, shaft and mount interfaces.
2. Selected brake and separate shaft/bearing geometry.
3. Confirmed regulated pressure/flow point within nameplate limits.
4. Material, print process and mechanical/thermal qualification for any proposed printed torque or brake support part.

For high-pressure work recovery directly from the cylinder, select an expander designed for the cylinder pressure. It is not an operating mode of this AM0701.
