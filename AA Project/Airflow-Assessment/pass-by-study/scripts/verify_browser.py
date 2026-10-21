"""Verify current overview data, controls, media and responsive layout via gstack."""
from pathlib import Path
import json,subprocess
from open_flow import STUDY,ROOT
B='/Users/egedoganay/.agents/skills/gstack/browse/dist/browse'
evidence=STUDY/'evidence';evidence.mkdir(exist_ok=True)
def call(*args):
    r=subprocess.run([B,*args],text=True,capture_output=True)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    return r.stdout
def js(code):return json.loads(call('js',code))
call('viewport','1440x1000')
call('goto',(ROOT.parent/'project-overview.html').as_uri()+'?passby-final=1#pass-by-results')
data=js("({count:window.aaPassByCFD.data.cases.length,results:document.querySelectorAll('#pass-by-results').length,scope:document.querySelectorAll('#pass-by-scope').length,overflow:document.documentElement.scrollWidth>innerWidth,oldCalculators:!!window.aaFormal&&!!window.aaMotorSeat&&!!window.aaSeatLoop,body:window.aaPassByCFD.data.body_included})")
assert data['count']==16 and data['results']==1 and data['scope']==1 and not data['overflow'] and data['oldCalculators'] and not data['body']
warm=js("(()=>{const r=window.aaPassByCFD.select('S00_row4_source8');return {supply:r.source_c,text:document.getElementById('aa-passby-case-detail').textContent};})()")
assert warm['supply']==8 and '8.00°C supply' in warm['text']
call('screenshot',str(evidence/'browser-selected-case.png'),'--selector','#aa-passby-case-detail')
aim=js("(()=>{const r=window.aaPassByCFD.select('A00_pitch8_d50');return {duration:r.reference.time_above_delta6_s,source:r.source_c};})()")
assert abs(aim['duration']-.47368411400533944)<1e-9
js("(()=>{window.aaPassByCFD.select('R00_wide_d35');const v=document.querySelector('#pass-by-results video');v.currentTime=5;return {width:v.videoWidth,duration:v.duration,error:v.error?.code??null};})()")
media=js("(()=>{const v=document.querySelector('#pass-by-results video');return {width:v.videoWidth,height:v.videoHeight,duration:v.duration,error:v.error?.code??null};})()")
assert media['width']==1200 and media['height']==660 and media['duration']>10 and media['error'] is None
call('screenshot',str(evidence/'browser-cfd-video.png'),'--selector','#pass-by-results video')
links=js("Array.from(document.querySelectorAll('#pass-by-results a')).map(a=>a.getAttribute('href'))")
from urllib.parse import unquote
missing=[]
for link in links:
    if link.startswith(('http:','https:','#')) or link.endswith('.zip'):continue
    path=ROOT.parent/unquote(link.split('#')[0])
    if not path.exists():missing.append(link)
assert not missing,missing
call('viewport','390x844')
mobile=js("({overflow:document.documentElement.scrollWidth>innerWidth,details:document.getElementById('aa-passby-case-detail').textContent.includes('0.558s')})")
assert not mobile['overflow'] and mobile['details']
call('screenshot',str(evidence/'browser-mobile-case.png'),'--selector','#aa-passby-case-detail')
console=call('console');(evidence/'browser-console.txt').write_text(console)
assert '(no console messages)' in console,console
call('viewport','1440x1000')
out=dict(all_passed=True,desktop=data,warm_source_selection=warm,aim_selection=aim,media=media,mobile=mobile,missing_non_archive_links=missing,archive_link='Verified by the separate package hash check after archive creation.')
(evidence/'browser-verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(all_passed=True,cases=data['count'],media=media,mobile=mobile)))
