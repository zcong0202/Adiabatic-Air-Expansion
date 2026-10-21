AA standalone LED presence firmware — 8 Oct 2026

Open aa_presence_led_deploy.ino in Arduino IDE. Select Arduino Uno.
All sensor driver sources are included. No separate library installation.

Wiring:
ToF VCC -> Uno 3.3V; GND -> GND; SDA -> A4; SCL -> A5.
Leave INT/SHUT unconnected. PIR disconnected.
Keep D8 -> D7 and A0 jumper. Feedback inputs must remain connected.
Onboard LED D13 mirrors D8.

Starts ToF presence control automatically when powered or reset.
Entry: valid object within 1.5m, stable 150ms after median-of-three filter.
Hold: within 1.6m. Departure dwell 200ms. No software near cutoff.
LED version has no 60-second ON cap.
Invalid/stale data closes output. Feedback fault latches output OFF.
Restart power or reset board to clear a latched fault.

Can run from USB power without the computer or live viewer.
ToF detects objects; human identity and outdoor performance need tests.
This firmware is for the LED prototype. The separate bench firmware keeps
its complete-stop controls and 60-second test cap.
