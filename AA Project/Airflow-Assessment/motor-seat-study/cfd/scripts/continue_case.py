from pathlib import Path
import shutil,json,re,subprocess,time,sys
from seat_cfd import CFD,docker
old=CFD/'cases'/sys.argv[1];case=CFD/'cases'/sys.argv[2];end=float(sys.argv[3])
if case.exists():raise FileExistsError(case)
shutil.copytree(old,case,ignore=shutil.ignore_patterns('processor*'))
info=json.loads((case/'case.json').read_text());info['case']=case.name;info['continued_from']=old.name;(case/'case.json').write_text(json.dumps(info,indent=2))
p=case/'system/controlDict';s=p.read_text().replace('startFrom startTime','startFrom latestTime');s=re.sub(r'endTime [^;]+;',f'endTime {end};',s)
if len(sys.argv)>4:s=re.sub(r'maxCo [^;]+;',f'maxCo {float(sys.argv[4])};',s)
p.write_text(s)
shutil.copyfile(case/'log.solver',case/'log.startup')
state=dict(status='running continuation',started=time.time());(case/'run-status.json').write_text(json.dumps(state))
for args,log in [(['decomposePar','-force','-latestTime'],'log.decomposePar'),(['mpirun','--allow-run-as-root','-np','4','buoyantPimpleFoam','-parallel'],'log.solver'),(['reconstructPar'],'log.reconstructPar')]:
 with (case/log).open('w') as f:rc=subprocess.run(docker(case,args),stdout=f,stderr=subprocess.STDOUT).returncode
 if rc:state.update(status='failed',error=log);break
else:state['status']='solver ended; audit pending'
state['elapsed_s']=time.time()-state['started'];(case/'run-status.json').write_text(json.dumps(state,indent=2));print(state)
