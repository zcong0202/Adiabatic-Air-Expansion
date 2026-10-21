#!/usr/bin/env python3
"""Developer build. Recipient receives only a ready-to-run .app."""
from pathlib import Path
import plistlib, shutil, subprocess, re
P=Path(__file__).resolve().parent.parent
native=P/'native';app=P/'dist-native/AA Controller.app';contents=app/'Contents';resources=contents/'Resources';exe=contents/'MacOS'
resources.mkdir(parents=True,exist_ok=True);exe.mkdir(exist_ok=True)
# Build browser source first; native app embeds same tested firmware and diagrams.
subprocess.run(['python3',str(P/'build.py'),'--hex',str(P/'evidence/template.hex')],check=True)
html=(P/'dist/AA Controller Mac/AA Controller.html').read_text()
html=html.replace('AA · Presence timer','AA Controller').replace('AA PROJECT / LOCAL USB CONTROL','AA PROJECT / MAC APP').replace('Presence timer</h1>','Cooling timer</h1>')
html=html.replace('Every detection refills the timer. The signal stays HIGH until the last detection + your chosen time.','Connect Arduino. Choose seconds. Save. Each detection restarts the full timer.')
html=html.replace('1. Set the hold time','Set the time').replace('HIGH duration after the latest detection','How long should cooling stay on after the latest detection?').replace('2. Live signal','Live signal')
html=html.replace('Connect the Uno with a USB data cable. Close Arduino IDE Serial Monitor first.','<span id="connectHelp">Plug the Uno into this Mac with the USB data cable.</span>')
# Put relay configuration under an explicit optional setup disclosure.
start=html.index('<label for="polarity">');end=html.index('<div class="row actions">',start)
html=html[:start]+'<details><summary>Valve setup · relay type</summary>'+html[start:end]+'</details>'+html[end:]
html=html.replace('<div id="configuration"', '<div id="setupSafety" class="subtle hint"><label style="margin:0;color:var(--ink)"><input id="valveIsolated" type="checkbox">The valve’s 12 V switch is OFF. (First setup / relay changes only.)</label></div><div id="configuration"',1)
html=html.replace('D8 / D7 wire feedback','Wire check').replace('Wire voltage estimate','Signal voltage').replace('ACTIVATION COMMAND','COOLING SIGNAL').replace('HOLD REMAINING','TIME LEFT')
html=html.replace('Apply &amp; save to Arduino','Save time to Arduino')
html=re.sub(r'<section id="handover".*?</section>',(native/'handover.html').read_text(),html,flags=re.S)
html=re.sub(r'<div class="footer">.*?</div>', '<div class="footer">AA Controller 1.1 · Apple Silicon Mac · Runs offline. Saved settings stay on Arduino. Closing this app does not stop the powered controller.</div>',html,flags=re.S)
html=html.replace('Open this file in Google Chrome. The app stays on this Mac and uses no server or cloud.','Plug in Arduino, click Connect Arduino, choose seconds, then Save time.')
# Keep export below the main task; less jargon in the daily workflow.
html=html.replace('<button id="download" class="download">Download firmware</button>','')
html=html.replace('<details><summary>Valve setup · relay type</summary>','<details><summary>Valve setup · relay type</summary><p class="hint">Use only after checking the relay label. Keep 12 V OFF while changing this setting.</p>')
html=html.replace('<div id="uploadProgress"', '<details><summary>Save files / advanced</summary><button id="download">Save firmware file</button></details><div id="uploadProgress"')
html=html.replace('</script></body>', '\n'+(native/'interface.js').read_text()+'\n</script></body>')
(resources/'index.html').write_text(html)
shutil.copy2(native/'bridge.js',resources/'bridge.js')
for f in (P/'diagrams').iterdir():
 if f.suffix in ('.png','.svg'):shutil.copy2(f,resources/f.name)
shutil.copy2(P/'dist/AA Controller Mac/BoM - Procurement List.pdf',resources/'BoM.pdf')
info={'CFBundleName':'AA Controller','CFBundleDisplayName':'AA Controller','CFBundleIdentifier':'org.aa.controller','CFBundleExecutable':'AAController','CFBundlePackageType':'APPL','CFBundleShortVersionString':'1.1','CFBundleVersion':'2','LSMinimumSystemVersion':'11.0','NSHighResolutionCapable':True,'NSPrincipalClass':'NSApplication','CFBundleIconFile':'AppIcon','LSApplicationCategoryType':'public.app-category.utilities'}
(contents/'Info.plist').write_bytes(plistlib.dumps(info))
subprocess.run(['swiftc','-O','-target','arm64-apple-macosx11.0',str(native/'main.swift'),'-o',str(exe/'AAController'),'-framework','AppKit','-framework','WebKit'],check=True)
iconset=native/'AppIcon.iconset'
subprocess.run(['swift',str(native/'icon.swift'),str(iconset)],check=True)
subprocess.run(['iconutil','-c','icns',str(iconset),'-o',str(resources/'AppIcon.icns')],check=True)
subprocess.run(['codesign','--force','--sign','-','--timestamp=none',str(app)],check=True)
print(app)
