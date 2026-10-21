from pathlib import Path
import subprocess,json,urllib.parse
from seat_cfd import STUDY
R=STUDY;page=R.parent.parent/'project-overview.html';B='/Users/egedoganay/.claude/skills/gstack/browse/dist/browse'
def cmd(*a):return subprocess.check_output([B,*a],text=True)
cmd('goto',page.as_uri()+'?seat-loop-final=1#seat-loop');cmd('reload');cmd('console','--clear');cmd('viewport','1440x1100')
local=json.loads((R/'results/cfd-cad-loop.json').read_text());checks=[]
def ck(n,v):checks.append(dict(name=n,passed=bool(v)));assert v,n
state=json.loads(cmd('js',"({sections:document.querySelectorAll('#seat-loop').length,cases:window.aaSeatLoop.data.cases.length,selected:document.querySelector('#aa-seat-case').value,formal:!!window.aaFormal,motor:!!window.aaMotorSeat,video:document.querySelector('#seat-loop video source').getAttribute('src'),links:Array.from(document.querySelectorAll('#seat-loop a[href]')).map(a=>a.getAttribute('href')),overflow:document.body.scrollWidth>innerWidth+1})"))
ck('one loop section',state['sections']==1);ck('case data matches generated results',state['cases']==len(local['cases']));ck('selected thermal candidate matches',state['selected']==local['preferred_still_air_candidate']['case']);ck('earlier calculators remain available',state['formal'] and state['motor']);ck('desktop no body overflow',not state['overflow'])
cmd('select','#aa-seat-case','C21_profile_halfCo_continuation');detail=cmd('js',"document.getElementById('aa-seat-detail').textContent");ck('case selection reports failed continuation','fails' in detail and '20.11' in detail)
cmd('select','#aa-seat-case',state['selected']);ck('selected movie exists',(page.parent/urllib.parse.unquote(state['video'])).exists())
missing=[h for h in state['links'] if not h.startswith('http') and not h.startswith('#') and not h.endswith('AA-seat-CFD-CAD-loop.zip') and not (page.parent/urllib.parse.unquote(h)).exists()];ck('supporting file links resolve',not missing)
media=json.loads(cmd('js',"({duration:document.querySelector('#seat-loop video').duration,width:document.querySelector('#seat-loop video').videoWidth,error:document.querySelector('#seat-loop video').error?.code??null})"));ck('video metadata decodes',media['duration']>10 and media['width']==1150 and media['error']is None)
cmd('js',"(async()=>{const v=document.querySelector('#seat-loop video');v.currentTime=8;await new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});setTimeout(resolve,3000)});return v.currentTime})()")
cmd('screenshot',str(R/'evidence/final-cfd-video-browser.png'),'--selector','#seat-loop video')
cmd('js',"window.scrollTo({top:document.getElementById('seat-loop').getBoundingClientRect().top+scrollY-180,behavior:'instant'})")
cmd('screenshot',str(R/'evidence/final-overview-browser.png'),'--viewport')
cmd('viewport','390x844');ck('mobile no body overflow',not json.loads(cmd('js','document.body.scrollWidth>innerWidth+1')))
errors=cmd('console','--errors');(R/'evidence/final-browser-console.txt').write_text(errors);ck('local page has no browser errors','[error]'not in errors)
cmd('viewport','1440x1100')
(R/'evidence/loop-browser-verification.json').write_text(json.dumps(dict(checks=checks,all_passed=True,media=media),indent=2));print(json.dumps(dict(checks=len(checks),all_passed=True)))
