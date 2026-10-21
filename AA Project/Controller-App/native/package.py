#!/usr/bin/env python3
from pathlib import Path
import shutil,subprocess,json,hashlib,zipfile
P=Path(__file__).resolve().parent.parent
stage=P/'dist-native/AA Controller';stage.mkdir(parents=True,exist_ok=True)
app=stage/'AA Controller.app'
if app.exists():shutil.rmtree(app) # Generated staging copy only; never edits installed apps.
shutil.copytree(P/'dist-native/AA Controller.app',app)
(stage/'START HERE.txt').write_text('''AA CONTROLLER — READY-TO-RUN MAC APP
Apple Silicon Mac. macOS 11 or newer.

1. Unzip the attachment. Double-click AA Controller.app.
2. Plug in the Uno with the USB data cable. Click Connect Arduino.
3. Choose seconds, then click Save time to Arduino.

First setup installs the firmware automatically. Turn OFF the valve 12 V switch
and tick the app's box before first setup. Keep USB connected until setup ends.
Later time changes save directly. Each detection restarts the full interval.
Arduino keeps the saved time when the app closes and the board remains powered.

No browser, Arduino IDE, Python, Terminal, build or Internet needed.
PNG wiring diagrams are inside the app. Use their Download PNG buttons to save copies.
Save files / advanced → Save firmware file creates a complete shareable firmware ZIP.

FIRST MAC LAUNCH
This privately built app is not Apple-notarized. If macOS blocks it:
After trying to open it, go to System Settings → Privacy & Security → Open Anyway.
Confirm Open. Future launches are normal double-clicks. No Terminal commands needed.
Only approve the exact AA Controller app shared by Ege; do not disable Gatekeeper.
Apple's guide: https://support.apple.com/en-us/102445
If the Mac is managed and blocks this exception, ask its administrator.

LAB CHECKS
Standalone power: UPS regulated 12 V → Uno barrel jack, centre positive.
Keep ToF at 3.3 V and retain D8 → D7/A0 loopback.
Connect the valve through the BoM relay, fused 12 V supply and striped-positive flyback diode.
Check the relay's HIGH/LOW trigger setting and OFF-at-reset behavior with 12 V isolated.
Start valve tests without pressure. Verify valve rating / continuous duty before air tests.
Software tests pass. Physical Uno upload, relay switching and valve tests still need lab checks.
''')
archive=P/'AA Controller App.zip'
subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(stage),str(archive)],check=True)
# Mac-specific bundle and executable permissions preserved by ditto.
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report={'version':'1.1','platform':'arm64 macOS 11+','package_bytes':archive.stat().st_size,'package_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'notarized':False,'developer_identity_available':False,'verified':['Native app compiled, launched and observed with macOS accessibility/screenshot','Actual WKWebView document-start bridge and Swift reply round-trip','macOS termios USB transport reads/writes tested on a PTY','Guided first Save installs full firmware with bootloader page readback in emulator','Subsequent Save updates duration without reflashing; matching board acknowledgement','Isolation acknowledgement enforced for first setup/polarity changes','Native file-save bridge success / cancellation in emulator','Firmware source / HEX / PNG diagrams included; no recipient build steps','Ad-hoc bundle signature verified before and after ZIP extraction'],'pending':['Physical Uno USB/DTR reset and upload','Relay trigger and OFF-at-reset','Valve actuation / pressure / duty checks','First launch on recipient Mac; Gatekeeper exception may be required']}
(P/'evidence/native-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Packaged {archive}: {archive.stat().st_size:,} bytes')
