#!/usr/bin/env python3
"""Build a portable offline app from source and a compiled Uno HEX."""
import argparse, base64, hashlib, json, shutil, zipfile
from pathlib import Path
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--hex',default='/tmp/aa-hold-build/aa_hold_controller.ino.hex');args=parser.parse_args()
hex_path=Path(args.hex)
if not hex_path.exists(): raise SystemExit('Compile firmware first. Pass --hex path/to/aa_hold_controller.ino.hex')
out=P/'dist/AA Controller Mac';out.mkdir(parents=True,exist_ok=True)
sources={f.name:f.read_text() for f in sorted((P/'firmware/aa_hold_controller').iterdir()) if f.is_file()}
tof=(P/'diagrams/ToF wiring.svg').read_text();valve=(P/'diagrams/Valve wiring.svg').read_text()
def literal(value):return json.dumps(value,ensure_ascii=True).replace('<','\\u003c')
data='const FW_HEX='+literal(hex_path.read_text())+';\nconst FW_SOURCES='+literal(sources)+';\nconst TOF_DIAGRAM='+literal(tof)+';\nconst VALVE_DIAGRAM='+literal(valve)+';'
for name,key in [('ToF wiring.png','TOF_PNG_BASE64'),('Valve wiring.png','VALVE_PNG_BASE64')]:
 data+='\nconst '+key+'='+literal(base64.b64encode((P/'diagrams'/name).read_bytes()).decode())+';'
html=(P/'src/index.html').read_text()
for token,value in {'__TOF_SVG__':tof,'__VALVE_SVG__':valve,'__FIRMWARE_DATA__':data,'__CORE__':(P/'src/core.js').read_text(),'__SERIAL__':(P/'src/serial.js').read_text(),'__APP__':(P/'src/app.js').read_text()}.items(): html=html.replace(token,value)
(out/'AA Controller.html').write_text(html)
for diagram in (P/'diagrams').iterdir():
 if diagram.suffix in ['.svg','.png']:shutil.copy2(diagram,out/diagram.name)
launcher=out/'Open on Mac.command'
launcher.write_text('''#!/bin/bash
# Opens the local offline app; no server or runtime required.
aa_app_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
if [ -d "/Applications/Google Chrome.app" ] || [ -d "$HOME/Applications/Google Chrome.app" ]; then
  open -a "Google Chrome" "$aa_app_dir/AA Controller.html"
elif [ -d "/Applications/Microsoft Edge.app" ]; then
  open -a "Microsoft Edge" "$aa_app_dir/AA Controller.html"
else
  osascript -e 'display dialog "Install Google Chrome, then open AA Controller.html with Chrome. Safari cannot connect to the Arduino." buttons {"OK"} default button "OK"'
fi
''');launcher.chmod(0o755)
readme='''AA Controller 1.0 — Mac handover — 11 October 2026

START
Unzip AA Controller Mac.zip. Right-click AA Controller.html → Open With → Google Chrome.
Open on Mac.command is an optional shortcut. If macOS blocks it, open the HTML directly.
Chrome or Edge required for USB. No Python, server, account or Internet needed after browser installation.
This portable app runs on Apple Silicon. Send the ZIP as a WhatsApp document or email attachment.

TIMER
Choose 0.1–3600 seconds. Every new valid target reading refills the full interval.
Output turns off X seconds after the last detection. Repeated detections can keep it on indefinitely.
A bad/absent sensor reading does not cancel a running timer; it stops refilling it.
A feedback wiring fault forces logical activation off and latches until reset.
Detection zone starts at 1.5 m; retention edge 1.6 m. No 40 cm lower cutoff.
ToF sees objects, not people specifically. Test the mounting direction and background at the lab.

USB / FIRMWARE
Keep valve 12 V OFF. Close Arduino IDE Serial Monitor. Connect Uno with a USB data cable.
Click Connect Arduino; select Uno. Choose hold time and trigger polarity.
Click Install / update firmware on Uno. This programs and verifies the ATmega328P.
The browser installer has only simulator tests here; physical USB upload needs a lab check.
If it fails: Download firmware, unzip, open aa_hold_controller/aa_hold_controller.ino
in Arduino IDE, select Arduino Uno and USB port, and upload. All sensor driver files included.
Live HIGH/LOW comes from actual firmware telemetry. Offline Timer preview is clearly simulated.
Apply & save requires an Arduino acknowledgement, and stores settings in EEPROM.
Download firmware is one click. ZIP includes customized compiled HEX, Arduino source,
settings and both wiring diagrams. A new exported profile takes priority over old EEPROM settings.
Do not open HEX as an Arduino IDE sketch; use the included .ino for IDE uploads.
Disconnect USB does not stop the standalone controller. It runs whenever Uno is powered.
No output Stop control is included.

WIRING
See ToF wiring.png and Valve wiring.png. SVG copies are also included.
Both PNGs are available from the app and in every firmware download.
ToF: Uno 3.3V → VCC, GND → GND, A4 → SDA, A5 → SCL. INT/SHUT unused. PIR disconnected.
Keep leads short. Tested Walfront VL53L1X module only. Software I²C uses module pull-ups;
A4/A5 are only driven LOW or released, with no 5 V internal pull-ups. No loose resistors needed.
Use only this firmware for this direct Uno wiring. The BoM's older ToF 5 V note is superseded.
D8 → D7 and A0 remains connected. D13 built-in L LED shows logical activation.
Add D8 → relay IN, Uno 5V → relay VCC, Uno GND → relay GND. Match printed labels.
Use relay H/L trigger mode or app LOW/HIGH selection that matches the delivered module.
HIGH on the app means activation. A LOW-trigger relay uses physical D8 LOW to activate.
Test relay COM/NO continuity with 12 V OFF. Ensure relay OFF at startup/reset.

VALVE
BoM: U.S. Solid USS-PSV00041, 12 V DC normally closed, max 0.8 MPa / 8 bar.
Confirm delivered valve label and continuous-duty rating before sustained operation.
UPS DC output set to 12 V: positive → 1 A fuse near UPS → isolation switch → relay COM.
Relay NO → valve positive. Valve negative → UPS 12 V negative. Relay NC unused.
1N4007 across valve coil, close to coil: striped cathode → positive, plain anode → negative.
Use WAGO nodes. Coil current stays off the Uno/breadboard. Never replace D8 LED logic with a coil.
The relay module supplies the driver components; a bare relay/diode cannot substitute for it.
PC USB powers Uno during setup. For standalone use UPS regulated 12 V output → Uno barrel jack (5.5 × 2.1 mm, centre positive).
Never connect 12 V to the 5V pin.
Check barrel polarity with multimeter. Keep 12 V isolated while moving wires, uploading or changing polarity.
D7/A0 verify the logic wire, not actual valve position or airflow. The BoM 10 m cable is for PIR, not ToF I²C.

LAB ACCEPTANCE
1. ToF runs with LED and D8→D7/A0 loopback; feedback matches, no fault.
2. Single pass gives full selected hold. Another pass before expiry refills without a LOW gap.
3. Staying in front keeps activation on beyond 60 seconds. Leaving allows full hold, then off.
4. Saved duration survives power cycle. Exported firmware adopts its chosen defaults on reinstall.
5. Relay NO closes only for logical HIGH; check LOW/HIGH trigger and reset behavior with 12 V OFF.
6. Verify valve/power ratings and diode polarity, then bench-test valve without pressure first.
Hardware, relay, valve and actual occupancy performance are not verified in this software release.

SOURCE
Supplied procurement PDF included for component labels. Current app wiring overrides its ToF 5 V note.
Web Serial: https://developer.chrome.com/docs/capabilities/serial
'''
(out/'READ ME.txt').write_text(readme)
bom=Path('/Users/egedoganay/Downloads/PIR _ ToF-Controlled Solenoid — Bench-Test Procurement List.pdf')
if bom.exists():shutil.copy2(bom,out/'BoM - Procurement List.pdf')
manifest={'version':'1.0','built':'2026-10-11','files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='SHA256.json'}}
(out/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=P/'AA Controller Mac.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.iterdir()):z.write(f,'AA Controller Mac/'+f.name)
(P/'evidence/template.hex').write_text(hex_path.read_text())
print(f'Built {archive}: {archive.stat().st_size:,} bytes')
