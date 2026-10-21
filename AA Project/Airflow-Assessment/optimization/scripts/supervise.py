"""Stop only owned cases once every predeclared numerical gate passes.
Uses OpenFOAM's clean stopAt writeNow. Does not loosen any criterion.
"""
import json,re,time
from round_jet import OPT
from audit_round import audit
end=time.time()+1800;stopped=set()
while time.time()<end:
 running=0
 for case in sorted((OPT/'cases').iterdir()):
  f=case/'run-status.json'
  if not f.exists():continue
  try:
   state=json.loads(f.read_text())
   if not state['status'].startswith('running'):continue
   running+=1
   if case.name in stopped:continue
   r=audit(case);g={k:v for k,v in r['numerical_gates'].items() if k!='solver_ended'}
   if g and all(g.values()):
    p=case/'system/controlDict';s=p.read_text();p.write_text(re.sub(r'stopAt \w+;', 'stopAt writeNow;',s));stopped.add(case.name)
    (case/'stop-decision.json').write_text(json.dumps({'reason':'Every predeclared numerical check except final solver exit passed; request clean checkpoint and exit.','last_iteration':r['last_iteration'],'checks':g},indent=2));print('Clean stop requested',case.name,r['last_iteration'],flush=True)
  except Exception as exc:print('Pending audit',case.name,type(exc).__name__,flush=True)
 time.sleep(30)
(OPT/'results/supervisor.json').write_text(json.dumps({'stopped_after_checks':sorted(stopped),'scope':'Owned optimization cases only'},indent=2))
