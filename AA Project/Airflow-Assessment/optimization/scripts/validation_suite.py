"""Run declared sensitivities only after the parent has passed numerical gates."""
import concurrent.futures,json,time
from round_jet import OPT,build,run
from audit_round import audit
parent=OPT/'cases/R02_D24'
deadline=time.time()+1800
while time.time()<deadline:
 state=json.loads((parent/'run-status.json').read_text())
 if not state['status'].startswith('running'):break
 time.sleep(10)
r=audit(parent)
if not r['numerically_accepted']:
 (OPT/'results/validation-queue.json').write_text(json.dumps({'status':'Parent numerical checks failed; sensitivity queue not run','failed':[k for k,v in r['numerical_gates'].items() if not v]},indent=2));raise SystemExit(1)
jobs=[('R09_D24_SST',{'model':'kOmegaSST'}),('R10_D24_domain',{'domain':1.5}),('R11_D24_lowflow',{'mass':.001})]
def task(job):
 name,options=job
 if (OPT/'cases'/name).exists():return {'case':name,'status':'already exists; not overwritten'}
 c=build(name,d=24,iterations=4000,**options);run(c);r=audit(c)
 return {'case':name,'numerically_accepted':r['numerically_accepted'],'mean_drop_c':r.get('target',{}).get('mean_drop_c')}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(task,jobs))
(OPT/'results/validation-queue.json').write_text(json.dumps({'status':'Sensitivity jobs finished; comparisons require audit','results':results},indent=2))
