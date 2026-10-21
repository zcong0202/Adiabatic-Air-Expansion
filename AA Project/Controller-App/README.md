# AA Controller

Ready-to-run native app for an Apple Silicon Mac (macOS 11+). Release: [AA Controller App.zip](AA%20Controller%20App.zip). Unzip and double-click AA Controller.app. No recipient build or runtime installation. Connect, choose seconds, Save. First Save installs firmware automatically if needed. The app is ad-hoc signed, not Apple-notarized; first launch may need Open Anyway. Native source and developer build/package scripts are in `native/`. The original Chrome app remains a fallback in [AA Controller Mac.zip](AA%20Controller%20Mac.zip). Maintained project record: [project overview](../project-overview.html).

Firmware source updated 14 October 2026; not flashed or bundled into the existing Mac app ZIP. Each activation closes at the earlier of 30 seconds from its first detection or 3 seconds from its last detection. Repeated presence readings refresh only the departure delay. After the 30-second limit, output stays OFF until 3 seconds of valid empty-zone readings. Invalid/stale readings cannot re-arm it. Default relay polarity is LOW-trigger, matching the lab system. D13 mirrors logical activation; D7/A0 measure physical D8.

`SET milliseconds activeLow` now adjusts only the departure delay, from 100 to 3000 ms. The 30-second cap cannot be increased through saved settings. A new profile generation discards the previous 10-second EEPROM setting on installation. Existing app packages retain the earlier unlimited timer; do not use their installer to deploy this revision. Compiled pending firmware: `evidence/bounded-30s-3s.hex`. Hardware checks await attachment and an explicit flash request.

The offline HTML embeds the compiled firmware and complete source. Exports patch a unique packed PROGMEM profile and recompute its check word. Each export gets a fresh generation token. Firmware loads EEPROM only when it matches that token. Browser exports are checked against a fresh Arduino compilation of the exported source.

`Apply & save` sends `SET hold_ms activeLow`; UI claims success only after matching Arduino ACK. Flashing uses Uno STK500v1, verifies ATmega328P signature and reads back every 128-byte page. Browser tests use simulated streams and a bootloader emulator. Physical USB and valve tests remain pending.

Build with Arduino CLI and Python (developer tools only):

```sh
arduino-cli compile --fqbn arduino:avr:uno --build-path /tmp/aa-hold-build firmware/aa_hold_controller
python3 build.py --hex /tmp/aa-hold-build/aa_hold_controller.ino.hex
node tests/core.test.js
node tests/bootloader.test.js
node tests/serial-transport.test.js
c++ -std=c++11 tests/timer.test.cpp -o /tmp/aa-timer-test
/tmp/aa-timer-test
```

`tests/browser-flow.js` runs through gstack browse `eval` on the built HTML. It injects mock USB streams only into the test page. Reload to remove them. Save `window.__exportZip` through browse `js --out`, extract to `/tmp/aa-custom-firmware`, compile to `/tmp/aa-custom-build`, then run `node tests/export-compare.js`. Production HTML has no mock USB source.

Current wiring: supplied BoM relay driver, not direct valve-to-Uno wiring. ToF supply is 3.3 V with included software I²C. Keep short leads and D8→D7/A0 feedback. Included lab instructions distinguish software verification from hardware acceptance.

Native verification: `evidence/native-verification.json`, `native-smoke.json`, `native-guided-flow.json` and `native-serial.txt`. Native serial is tested on a real macOS PTY; guided flashing uses an emulated bootloader. Physical Uno upload/DTR and valve checks remain pending.
