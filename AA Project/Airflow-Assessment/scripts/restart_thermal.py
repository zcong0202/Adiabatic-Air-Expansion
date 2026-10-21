"""Initialize thermal RANS cases from an existing flow on the same mesh.

An analytical jet profile initializes temperature only. It is not a result.
All reported fields must come from the subsequent CFD solution.
"""
import argparse
import json
import re
import shutil
import subprocess
import numpy as np
from build_case import ROOT, build, field, PATCHES
from run_case import command


def internal(path):
    s=path.read_text()
    m=re.search(r'internalField\s+nonuniform\s+List<(scalar|vector)>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;',s,re.S)
    if m:
        values=np.fromstring(m.group(3).replace('(',' ').replace(')',' '),sep=' ')
        return values.reshape(-1,3) if m.group(1)=='vector' else values
    raise ValueError(f'Expected nonuniform data: {path}')


def replace_internal(path,values):
    s=path.read_text();vector=values.ndim==2
    vals='\n'.join('('+ ' '.join(f'{v:.10g}' for v in row)+')' for row in values) if vector else '\n'.join(f'{v:.10g}' for v in values)
    block=f'internalField nonuniform List<{"vector" if vector else "scalar"}>\n{len(values)}\n(\n{vals}\n);'
    pattern=r'internalField\s+(?:nonuniform\s+List<\w+>\s+\d+\s*\(.*?\)\s*;|uniform\s+[^;]+;)'
    s,n=re.subn(pattern,lambda m:block,s,count=1,flags=re.S);assert n==1
    path.write_text(s)


def restart(source_name,tag,wind=None,iterations=1000):
    source=ROOT/'cases'/source_name
    info=json.loads((source/'case.json').read_text())
    latest=max([p for p in source.iterdir() if p.is_dir() and p.name.replace('.','',1).isdigit()],key=lambda p:float(p.name))
    if float(latest.name)==0:raise ValueError('No solved initialization available')
    build(info['design'],info['crosswind_m_s'] if wind is None else wind,info['cold_mass_flow_kg_s'],info['cold_total_temperature_c'],iterations,tag,info['mesh_scale'],info['domain_scale'],'kEpsilon',info['Prt'])
    case=ROOT/'cases'/tag
    shutil.copytree(source/'constant/polyMesh',case/'constant/polyMesh')
    shutil.copyfile(source/'log.checkMesh',case/'log.checkMesh')
    # Boundary conditions from newly generated case stay intact.
    for name in ['U','k','epsilon','nut']:
        replace_internal(case/'0'/name,internal(latest/name))
    with (case/'log.centres').open('w') as log:
        subprocess.run(command(case,['postProcess','-func','writeCellCentres','-time','0']),stdout=log,stderr=subprocess.STDOUT,check=True)
    xyz=internal(case/'0/C');velocity=internal(case/'0/U')
    width=.004+.1*np.maximum(xyz[:,0],0)
    fraction=np.minimum(1,.004/width)*np.exp(-(xyz[:,1]**2+xyz[:,2]**2)/width**2)
    fraction[xyz[:,0]<0]=1
    temp=308.15-(35-info['cold_total_temperature_c'])*fraction-(velocity**2).sum(axis=1)/(2*1005)
    assert temp.min()>200
    replace_internal(case/'0/T',temp)
    # macOS volumes are commonly case-insensitive: writeCellCentres' C can
    # replace scalar c. Restore its scalar header and boundary conditions.
    cbcs={p:'type inletOutlet; inletValue uniform 0; value uniform 0;' for p in PATCHES[2:]}
    cbcs.update({'coldInlet':'type fixedValue; value uniform 1;','walls':'type zeroGradient;'})
    field(case,'c','0 0 0 0 0 0 0','0',cbcs)
    replace_internal(case/'0/c',fraction)
    p=case/'system/fvSolution';s=p.read_text().replace('rho 0.5; p_rgh 0.25','rho 0.3; p_rgh 0.2').replace('U 0.5; h 0.6; k 0.5; epsilon 0.5; omega 0.5','U 0.3; h 0.4; k 0.5; epsilon 0.5; omega 0.5');p.write_text(s)
    info=json.loads((case/'case.json').read_text());info['initialization_source']=source_name;info['initialization_iteration']=float(latest.name);info['temperature_initialization']='Analytical jet seed, not reported as a result; relaxed by CFD.';(case/'case.json').write_text(json.dumps(info,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('tag');p.add_argument('--wind',type=float);p.add_argument('--iterations',type=int,default=1000);a=p.parse_args();restart(a.source,a.tag,a.wind,a.iterations)
