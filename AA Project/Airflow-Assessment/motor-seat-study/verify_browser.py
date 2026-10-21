from pathlib import Path
import json,subprocess,math
R=Path(__file__).parent.resolve();B='/Users/egedoganay/.claude/skills/gstack/browse/dist/browse';page=R.parent.parent/'project-overview.html'
def cmd(*args):return subprocess.check_output([B,*args],text=True)
cmd('goto',page.as_uri()+'?motor-seat-review=2#motor-seat');cmd('reload');cmd('console','--clear')
js="""(()=>{const a=window.aaMotorSeat,x=a.inputs();return {baseline:a.update(),half:a.evaluate({...x,capture:.5}),returned:a.evaluate({...x,return:1}),invalid:a.evaluate({...x,ti:45}),wide:a.evaluate({...x,area:1}),sections:document.querySelectorAll('#motor-seat').length,localLinks:Array.from(document.querySelectorAll('#motor-seat a[href]')).map(a=>a.getAttribute('href')).filter(h=>!h.startsWith('http'))}})()"""
r=json.loads(cmd('js',js));ref=json.loads((R/'results/assessment.json').read_text());checks=[]
def ck(n,b):checks.append({'name':n,'passed':bool(b)});assert b,n
ck('single new scope section',r['sections']==1)
ck('source matches Python',abs(r['baseline']['source_cooling']-ref['baseline']['sensible_cooling_w'])<1e-8)
ck('warm exchange matches Python',abs(r['baseline']['max_warm_volume']-ref['target_20c']['max_warm_m3_s'])<1e-10)
ck('half capture fails 20 C in example',r['half']['zone']>20)
ck('returned work causes heating',r['returned']['zone']>30)
ck('45 C motor inlet flagged',not r['invalid']['motor_limit_ok'] and not r['invalid']['passed'])
ck('wide opening worsens zone',r['wide']['zone']>r['baseline']['zone'])
# Check DOM event wiring, then restore the default.
cmd('fill','#ms-capture','0.5');actual=json.loads(cmd('js','window.aaMotorSeat.inputs()'));ck('input field event wired',actual['capture']==.5)
cmd('fill','#ms-capture','1')
errors=cmd('console','--errors');(R/'evidence/browser-console.txt').write_text(errors)
ck('no new local JS errors','[error]' not in errors)
# Package link is generated after verification.
import urllib.parse
missing=[h for h in r['localLinks'] if not (page.parent/urllib.parse.unquote(h)).exists() and not h.endswith('AA-motor-seat-viability.zip')]
ck('all existing artifact links resolve',not missing)
(R/'evidence/browser-verification.json').write_text(json.dumps({'checks':checks,'results':r,'all_passed':True},indent=2))
cmd('viewport','1440x1000');cmd('js',"window.scrollTo({top:document.getElementById('motor-seat').getBoundingClientRect().top+window.scrollY-210,behavior:'instant'})")
cmd('screenshot',str(R/'evidence/overview-desktop.png'),'--viewport')
print(json.dumps({'checks':len(checks),'all_passed':True}))
