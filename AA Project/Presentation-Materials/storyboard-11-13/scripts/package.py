"""Verify editor assets and build the local handover page."""
from pathlib import Path
import hashlib, json, subprocess, zipfile
from html import escape
from urllib.parse import unquote,urlsplit
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports'
PROJECT=ROOT.parents[1]
SHOTS=[dict(number=11,title='Cold dispersion',duration=14,video='11-cold-dispersion-14s.mp4',poster='11-cold-dispersion.png',
    voice='Cold air leaves the nozzle, mixes with warm air and sinks. The simulation shows how much cooling remains at twenty and fifty centimetres. These are simulated air temperatures, not measurements.',
    caption='One outlet. The cold jet mixes and sinks.',source='scuba19_n1_wide_fine · 19.4 g/s · 4.31°C assumed source'),
    dict(number=12,title='Nozzle setup',duration=14,video='12-nozzle-setup-14s.mp4',poster='12-05-m77_n4_wide_opposed.png',
    voice='Cooling power depends on air mass flow and temperature drop. With the same supply, changing nozzle number, size and spacing changes where the colder air goes and how much remains cold.',
    caption='Same supply. Different number, size and spacing.',source='Five saved cases · 77 g/s total · 0.96°C assumed source'),
    dict(number=13,title='A localized cold volume',duration=16,video='13-localized-cold-volume-16s.mp4',poster='13-localized-cold-volume.png',
    voice='The simulation maps the air that remains at least six degrees below ambient. Four opposed outlets create a localized cold volume. This result does not yet establish cooling or comfort for passing pedestrians.',
    caption='The simulation maps a localized cold volume.',source='m77_n4_wide_opposed_fine · 77 g/s · 0.96°C assumed source')]

def build():
    validation=[]
    for shot in SHOTS:
        path=OUT/shot['video']
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames',
            '-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames:format=duration','-of','json',str(path)]))
        stream=probe['streams'][0]
        assert (stream['width'],stream['height'])==(1920,1080)
        assert stream['codec_name']=='h264' and stream['avg_frame_rate']=='30/1'
        assert int(stream['nb_read_frames'])==shot['duration']*30
        assert abs(float(probe['format']['duration'])-shot['duration'])<.05
        assert Image.open(OUT/shot['poster']).size==(1920,1080)
        validation.append(dict(shot=shot['number'],file=shot['video'],probe=probe,status='passed'))
        (ROOT/f'{shot["number"]}-narration.txt').write_text(shot['voice']+'\n')
        (ROOT/f'{shot["number"]}-caption.srt').write_text(f'1\n00:00:00,000 --> 00:00:{shot["duration"]:02d},000\n{shot["caption"]}\n')
    (ROOT/'narration-and-edit-notes.txt').write_text('\n\n'.join(
        f'{s["number"]}. {s["title"]} / {s["duration"]} seconds\nVOICE: {s["voice"]}\nSOURCE: {s["source"]}' for s in SHOTS)+'''

EDITOR NOTES
No voice recording is included. Text is ready for recording.
Movies are silent H.264 / 1920 x 1080 / 30 fps. All source fields stop at 10 s.
Shots 11 and 13 hold native saved fields between times; no temperature interpolation.
Shot 12 cuts between five separate 10 s configurations at 2.8 s each.
Shot 13 rotates the camera; no synthetic particle trajectories are shown.
Shot 11 uses the current scuba reference. Shots 12–13 use the historical 77 g/s study.
Do not cut away the source-temperature labels and imply that all three clips describe one motor.
Original wording “warms within half a metre” is too strong: cold air remains at 50 cm in this case.
No verified measurements from the cited 14 October deck were matched. Values shown are simulated.
Cooling power is mass flow times specific heat times temperature difference, not mass alone.
The whole-domain cold volume is used for the controlled nozzle comparison. Range-band volumes
are also provided in CSV; side and opposed range bands have different sampling volumes.
The saved domain has no people, solar load or wind. Do not claim an occupied room is cooled.
Use shot 13 as a local CFD demonstration, not a pedestrian-comfort or room-scale result.
No new CFD, CAD-to-flow coupling, motor-source validation or valve-off decay was performed.
''')
    readme='''# Storyboard shots 11–13

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
'''
    (ROOT/'README.md').write_text(readme)
    cards=[]
    for s in SHOTS:
        svg=Path(s['poster']).with_suffix('.svg').name
        cards.append(f'''<section id="shot-{s['number']}"><div class="row"><h2>{s['number']} / {escape(s['title'])}</h2><span>{s['duration']} s</span></div><video controls preload="metadata" poster="exports/{s['poster']}" src="exports/{s['video']}"></video><p class="source">{escape(s['source'])}</p><div class="links"><a download href="exports/{s['video']}">MP4</a><a download href="exports/{s['poster']}">PNG</a><a download href="exports/{svg}">SVG</a><a href="{s['number']}-narration.txt">Narration</a><a download href="{s['number']}-caption.srt">Caption</a></div><details><summary>Voice copy</summary><p>{escape(s['voice'])}</p></details></section>''')
    configs=[]
    for i,(name,label) in enumerate([('m77_n1_wide','1 wide'),('m77_n2_wide','2 wide'),('m77_n4_base','4 compact'),('m77_n4_adaptive','4 adaptive'),('m77_n4_wide_opposed','4 opposed')]):
        configs.append(f'<button type="button" data-png="exports/12-{i+1:02d}-{name}.png">{label}</button>')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Storyboard / 11–13</title><style>
    *{box-sizing:border-box}body{margin:0;background:#fff;color:#171b20;font:16px/1.5 Arial,sans-serif}main{max-width:1100px;margin:auto;padding:42px 24px}h1{font-size:32px;margin:0 0 10px}h2{font-size:21px;margin:0}p{max-width:900px}a{color:inherit;text-underline-offset:4px}.muted,.source{color:#64717b;font-size:14px}.row{display:flex;align-items:center;justify-content:space-between;margin:0 0 16px}.row span{color:#64717b}section{padding:32px 0;border-top:1px solid #dce1e5}video,img{display:block;width:100%;height:auto;background:#10151c}.links{display:flex;gap:22px;flex-wrap:wrap;margin:16px 0}details{margin-top:14px}summary{cursor:pointer;color:#53616c}button{padding:10px 16px;background:white;border:1px solid #bdc7cf;font:inherit;cursor:pointer}button[aria-pressed=true]{background:#171b20;color:white}.buttons{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}header{margin-bottom:30px}footer{padding:24px 0;color:#64717b;font-size:13px}@media(max-width:600px){main{padding:24px 15px}h1{font-size:27px}.links{gap:16px}}
    </style><main><header><h1>Storyboard / 11–13</h1><p>Full HD stills and silent clips. 14 / 14 / 16 seconds.</p><p class="muted">Shot 11: current 19.4 g/s reference. Shots 12–13: historical 77 g/s study. Simulations with assumed sources; no measured probes or pedestrian-comfort result.</p><div class="links"><a download href="storyboard-11-13-editor-pack.zip">Download editor pack</a><a href="narration-and-edit-notes.txt">Edit notes</a><a href="manifest.json">Source record</a></div></header>'''+''.join(cards)+'''
    <section><h2>Nozzle stills</h2><div class="buttons">'''+''.join(configs)+'''</div><img id="configuration" src="exports/12-01-m77_n1_wide.png" alt="Saved CFD nozzle configuration"><div class="links"><a id="configuration-download" href="exports/12-01-m77_n1_wide.png" download>Download selected PNG</a><a href="data/12-configurations.csv">Comparison CSV</a><a href="data/11-simulated-patches.csv">20/50 cm values</a></div></section>
    <section><h2>Evidence</h2><p>Blue 3D volumes contain simulated air at least 6°C below 30°C ambient. Native cells remain visible. Ten seconds of source-ON data; no cooling-duration claim after shutdown.</p><div class="links"><a href="../../Airflow-Assessment/scuba-study/results/index.html">Current source / CFD</a><a href="../../Airflow-Assessment/mass-flow-study/results/index.html">Historical nozzle sweep</a><a href="README.md">Methods / limits</a><a href="validation.json">Export checks</a></div></section><footer>27 October 2026 · Existing CFD re-rendered. No new solver run.</footer></main>
    <script>document.querySelectorAll('[data-png]').forEach((b,i)=>{b.setAttribute('aria-pressed',i===0);b.onclick=()=>{document.getElementById('configuration').src=b.dataset.png;document.getElementById('configuration-download').href=b.dataset.png;document.querySelectorAll('[data-png]').forEach(x=>x.setAttribute('aria-pressed',x===b));};});</script></html>'''
    (ROOT/'index.html').write_text(html)
    # Overview remains the only project overview. This page is an editor asset gallery.
    overview=PROJECT/'project-overview.html';text=overview.read_text();start='<!-- storyboard-materials-start -->';end='<!-- storyboard-materials-end -->'
    block='''<!-- storyboard-materials-start -->
<section id="storyboard-materials"><div class="eyebrow">Editor materials · 27 Oct 2026</div><h2>Storyboard shots 11–13</h2><p><a href="Presentation-Materials/storyboard-11-13/index.html"><strong>Open stills, 14/14/16 s clips and editor pack →</strong></a></p><p>Completed: side-view cold dispersion, five nozzle configurations, and native 3D cold-volume growth with camera orbit. Full HD PNG/MP4, editable SVG, narration, captions, calculation CSVs and source hashes. Existing CFD only; no new solver run.</p><p class="sub">Verified: native archive/temperature/mesh hashes for the two transient shots, saved geometry volumes, 30 fps video dimensions and durations. Assumed: prescribed cold-air sources. Shot 11 uses 19.4 g/s / 4.31°C; shots 12–13 use historical 77 g/s / 0.96°C. No measured probe overlay or room-scale pedestrian claim. Next: editor reviews revised voice copy; matching physical measurements remain open.</p></section>
<!-- storyboard-materials-end -->'''
    if start in text:
        before,tail=text.split(start,1);_,after=tail.split(end,1);text=before+block+after
    else: text=text.replace('</nav>','</nav>\n'+block,1)
    if 'href="#storyboard-materials"' not in text:text=text.replace('<nav aria-label="Sections">','<nav aria-label="Sections"><a href="#storyboard-materials">Storyboard assets</a>',1)
    overview.write_text(text)
    # Offline link inventory, including links the ZIP will satisfy below.
    targets=references(html)
    for target in targets:
        if target in ['storyboard-11-13-editor-pack.zip','validation.json']:continue
        assert (ROOT/target).exists(),target
    manifest=json.loads((ROOT/'manifest.json').read_text())
    for item in manifest['exports']:
        assert hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest()==item['sha256']
    report=dict(status='passed',videos=validation,local_links_checked=targets,
        native_T_fields_verified=sum(x.get('native_T_hashes_verified',0) for x in manifest['sources']),
        new_cfd=False,measured_probes=False,field_interpolation=False)
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2))
    # Preview combines exactly the exported final stills.
    preview=Image.new('RGB',(1920,3240),'#10151c')
    for i,s in enumerate(SHOTS):preview.paste(Image.open(OUT/s['poster']),(0,1080*i))
    preview.save(OUT/'storyboard-preview.png')
    bundle=ROOT/'storyboard-11-13-editor-pack.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            if p.is_file() and p!=bundle and '__pycache__' not in p.parts:
                z.write(p,p.relative_to(ROOT))
    print(json.dumps(dict(status='passed',videos=len(validation),native_T_fields=report['native_T_fields_verified'],bundle_bytes=bundle.stat().st_size),indent=2))

def references(html):
    import re
    return sorted(set(unquote(urlsplit(x).path) for x in re.findall(r'(?:href|src)="([^"]+)"',html) if not urlsplit(x).scheme and urlsplit(x).path))

if __name__=='__main__':build()
