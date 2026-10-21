"""Map a coarse Boussinesq checkpoint to its independently refined mesh."""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from build_boussinesq import build_bouss
from build_case import ROOT
from run_case import command, execute


def fine(design):
    parent=ROOT/'cases'/(design+'_bouss_w0')
    # Wait for the coarse source to finish so the mapping is reproducible.
    while True:
        status=parent/'run-status.json'
        if status.exists():
            r=json.loads(status.read_text())
            if r['status'].startswith('solver_exited_successfully'):break
            if r['status']=='failed':raise RuntimeError('Parent case failed')
        time.sleep(10)
    name=design+'_bouss_fine'
    case=ROOT/'cases'/name
    if not case.exists():
        build_bouss(design,parent.name,tag=name,iterations=400)
        shutil.rmtree(case/'constant/polyMesh')
        shutil.copyfile(ROOT/'designs'/design/'mesh_s0.8_d1/mesh.msh',case/'mesh.msh')
    defaults={'U':'(0 0 0)','T':'308.15','c':'0','k':'0.001','epsilon':'0.001','omega':'1','nut':'0','alphat':'0','p':'0','p_rgh':'0','pPotential':'0'}
    for f in (case/'0').iterdir():
        if f.name not in defaults:continue
        s=f.read_text();s=re.sub(r'internalField\s+nonuniform\s+List<\w+>\s+\d+\s*\(.*?\)\s*;',f'internalField uniform {defaults[f.name]};',s,count=1,flags=re.S);f.write_text(s)
    if not (case/'constant/polyMesh/boundary').exists():
        execute(case,['gmshToFoam','mesh.msh'],'log.gmshToFoam')
        p=case/'constant/polyMesh/boundary';p.write_text(re.sub(r'(\bwalls\s*\{\s*type\s+)patch',r'\1wall',p.read_text()))
        execute(case,['checkMesh'],'log.checkMesh')
    if 'Mesh OK.' not in (case/'log.checkMesh').read_text():raise RuntimeError('Fine mesh failed checks')
    execute(case,['mapFields',f'/work/cases/{parent.name}','-sourceTime','latestTime','-consistent','-mapMethod','cellPointInterpolate'],'log.mapFields')
    p=case/'system/fvSolution';s=p.read_text().replace('tolerance 1e-8; relTol 0.02;','tolerance 1e-9; relTol 0;').replace('nNonOrthogonalCorrectors 1;','nNonOrthogonalCorrectors 2;').replace('T 0.7;','T 1;').replace('c 0.7;','c 1;');p.write_text(s)
    p=case/'system/controlDict';p.write_text(p.read_text().replace('writeInterval 100;','writeInterval 50;'))
    p=case/'case.json';r=json.loads(p.read_text());r.update({'mesh_scale':.8,'initialization_source':parent.name,'pressure_linear_tolerance':1e-9,'pressure_linear_relative_tolerance':0,'scalar_linear_tolerance':1e-10,'scalar_relative_tolerance':0,'scalar_equation_relaxation':1,'nonorthogonal_correctors':2,'tight_pressure_start_iteration':0,'numerical_phase':'Refined mesh, mapped from completed coarse solution. Not independently validated.'});p.write_text(json.dumps(r,indent=2))
    print('FINE_READY',name,flush=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/run_case.py'),name,'--resume-prepared'],check=True)


if __name__=='__main__':fine(sys.argv[1])
