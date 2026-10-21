"""Warm start a like-for-like internal cone turbulence-model check."""
import json,re,shutil
import numpy as np
from round_jet import OPT,build,resume
from audit_round import audit,internal
parent=OPT/'cases/R07_D24_diffuser_3deg_SST'
r=audit(parent)
if not r['numerically_accepted']:raise RuntimeError('Parent must pass numerical acceptance')
case=build('R14_D24_a3_kEpsilon',d=24,model='kEpsilon',order=1,diffuser=True,angle_deg=3,iterations=6000)
shutil.copytree(parent/'constant/polyMesh',case/'constant/polyMesh');shutil.copyfile(parent/'log.checkMesh',case/'log.checkMesh')
latest=max([p for p in parent.iterdir() if p.is_dir() and p.name.isdigit() and p.name!='0'],key=lambda p:int(p.name))
for f in ['U','p','k','nut','theta']:shutil.copyfile(latest/f,case/'0'/f)
eps=.09*internal(latest/'k')*internal(latest/'omega');p=case/'0/epsilon';s=p.read_text();s=re.sub(r'internalField uniform [^;]+;',f'internalField nonuniform List<scalar>\n{len(eps)}\n(\n'+'\n'.join(f'{v:.12g}' for v in eps)+'\n);',s);p.write_text(s)
info=json.loads((case/'case.json').read_text());info.update(initialization_source=parent.name,initialization_iteration=int(latest.name),epsilon_initialization='0.09*k*omega from the SST parent; final solution uses the k-epsilon equations.');(case/'case.json').write_text(json.dumps(info,indent=2));resume(case,6000)
