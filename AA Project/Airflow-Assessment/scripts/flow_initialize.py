"""Stage a stable isothermal RANS flow before coupling the thermal solver."""
import json
import re
import shutil
import sys
from pathlib import Path
from build_case import ROOT, PATCHES, field, write

name=sys.argv[1]
source=ROOT/'cases'/name
case=ROOT/'cases'/(name+'_flowInit')
case.mkdir(exist_ok=False)
shutil.copytree(source/'constant',case/'constant')
shutil.copytree(source/'0',case/'0')
shutil.copytree(source/'system',case/'system')
info=json.loads((source/'case.json').read_text())
info.update({'solver':'simpleFoam','analysis':'Isothermal initialization only','parent_case':name})
(case/'case.json').write_text(json.dumps(info,indent=2))
pbcs={p:('type zeroGradient;' if p in ['coldInlet','walls'] else 'type fixedValue; value uniform 0;') for p in PATCHES}
if info['crosswind_m_s']>0:pbcs['windIn']='type zeroGradient;'
field(case,'p','0 2 -2 0 0 0 0','0',pbcs)
write(case,'constant/transportProperties','transportProperties','transportModel Newtonian; nu [0 2 -1 0 0 0 0] 1.5e-5;')
write(case,'constant/turbulenceProperties','turbulenceProperties','simulationType RAS; RAS { RASModel kEpsilon; turbulence on; printCoeffs on; }')
p=case/'0/U';s=p.read_text();s=re.sub(r'massFlowRate\s*\{[^}]+\}',f'massFlowRate constant {info["cold_mass_flow_kg_s"]};',s);p.write_text(s)
p=case/'system/fvSchemes';s=p.read_text().replace('div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;','div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;\n div((nuEff*dev2(T(grad(U))))) Gauss linear;');p.write_text(s)
p=case/'system/fvSolution';s=p.read_text().replace('solvers {','solvers {\n p { solver GAMG; tolerance 1e-8; relTol 0.01; smoother DICGaussSeidel; }').replace('p_rgh 0.15','p 0.3; p_rgh 0.15').replace('p_rgh 0.25','p 0.3; p_rgh 0.25').replace('p_rgh 1e-5;','p 1e-5;').replace('U 0.2;','U 0.4;').replace('k 0.3; epsilon 0.3;','k 0.5; epsilon 0.5;');p.write_text(s)
p=case/'system/controlDict';s=p.read_text();s=s[:s.index('functions {')];s=s.replace('application buoyantSimpleFoam;','application simpleFoam;').replace('endTime 800;','endTime 600;');s+='functions {}\n';p.write_text(s)
shutil.copyfile(source/'log.checkMesh',case/'log.checkMesh')
print(case)
