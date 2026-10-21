"""Validate the 3-degree candidate after numerical acceptance, using warm starts."""
import concurrent.futures,json,re,shutil,subprocess,time
from round_jet import OPT,build,command,resume
from audit_round import audit
parent=OPT/'cases/R07_D24_diffuser_3deg_SST'
deadline=time.time()+1200
while time.time()<deadline:
 state=json.loads((parent/'run-status.json').read_text())
 if not state['status'].startswith('running'):break
 time.sleep(15)
r=audit(parent)
if not r['numerically_accepted']:
 (OPT/'results/internal-validation.json').write_text(json.dumps({'status':'Parent failed acceptance; validation not started','failed':[k for k,v in r['numerical_gates'].items() if not v]},indent=2));raise SystemExit(1)
def task(name,scale,order):
 case=build(name,d=24,model='kOmegaSST',iterations=6000,order=order,diffuser=True,angle_deg=3,scale=scale)
 if scale==1:
  shutil.copytree(parent/'constant/polyMesh',case/'constant/polyMesh');shutil.copyfile(parent/'log.checkMesh',case/'log.checkMesh')
  latest=max([p for p in parent.iterdir() if p.is_dir() and p.name.isdigit() and p.name!='0'],key=lambda p:int(p.name))
  for f in ['U','p','k','omega','epsilon','nut','theta']:
   if (latest/f).exists():shutil.copyfile(latest/f,case/'0'/f)
 else:
  for args,log in [(['blockMesh'],'log.blockMesh'),(['checkMesh'],'log.checkMesh'),(['mapFields',f'/work/optimization/cases/{parent.name}','-consistent','-sourceTime','latestTime','-mapMethod','cellPointInterpolate'],'log.mapFields')]:
   with (case/log).open('w') as out:code=subprocess.run(command(case,args),stdout=out,stderr=subprocess.STDOUT).returncode
   if code:raise RuntimeError(f'{name}: {args[0]} failed')
  if 'Mesh OK.' not in (case/'log.checkMesh').read_text():raise RuntimeError('Mesh failed')
 p=case/'system/fvSolution';s=p.read_text().replace('p { solver GAMG; tolerance 1e-9;','p { solver GAMG; tolerance 1e-12;').replace('smoother symGaussSeidel; tolerance 1e-9;','smoother symGaussSeidel; tolerance 1e-11;');p.write_text(s)
 info=json.loads((case/'case.json').read_text());info.update(initialization_source=parent.name,initialization_parent_iteration=r['last_iteration'],tighter_linear_solve={'p_tolerance':1e-12,'U_tolerance':1e-11});(case/'case.json').write_text(json.dumps(info,indent=2));resume(case,6000);rr=audit(case)
 return {'case':name,'accepted':rr['numerically_accepted'],'mean_drop_c':rr.get('target',{}).get('mean_drop_c')}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(task,'R12_D24_a3_second_order',1,2),pool.submit(task,'R13_D24_a3_fine',.75,1)]
 results=[f.result() for f in futures]
(OPT/'results/internal-validation.json').write_text(json.dumps({'status':'Validation jobs finished; inspect accepted comparisons','results':results},indent=2))
