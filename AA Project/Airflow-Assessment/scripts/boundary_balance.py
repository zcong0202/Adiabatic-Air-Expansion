"""Check native finite-volume boundary fluxes, independent of cut planes."""
import json
import re
from pathlib import Path
import numpy as np
from build_case import ROOT, PATCHES


def block(text,name):
    start=re.search(r'\b'+re.escape(name)+r'\s*\{',text)
    if not start:raise ValueError(name)
    a=start.end();depth=1;i=a
    while depth:
        if text[i]=='{':depth+=1
        if text[i]=='}':depth-=1
        i+=1
    return text[a:i-1]


def values(text,name,count):
    part=block(text[text.index('boundaryField'):],name)
    m=re.search(r'\bvalue\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;',part,re.S)
    if m:
        arr=np.fromstring(m.group(2),sep=' ');assert len(arr)==count,(name,len(arr),count);return arr
    m=re.search(r'\bvalue\s+uniform\s+([0-9.eE+-]+)',part)
    if m:return np.full(count,float(m.group(1)))
    raise ValueError('No scalar boundary value for '+name)


def balance(case):
    info=json.loads((case/'case.json').read_text());rho=info.get('rho_reference_kg_m3')
    if rho is None:return None
    latest=max([p for p in case.iterdir() if p.is_dir() and p.name.isdigit()],key=lambda p:int(p.name))
    if not (latest/'phi').exists():return None
    phi=(latest/'phi').read_text();temp=(latest/'T').read_text();c=(latest/'c').read_text();boundary=(case/'constant/polyMesh/boundary').read_text()
    patches={}
    for name in PATCHES:
        if name=='walls':
            patches[name]={'mass_flux_kg_s':0.,'source_mass_flux_kg_s':0.,'cooling_potential_flux_w':0.}
            continue
        count=int(re.search(r'nFaces\s+(\d+)',block(boundary,name)).group(1))
        f=values(phi,name,count);t=values(temp,name,count);source=values(c,name,count)
        patches[name]={'mass_flux_kg_s':float(rho*f.sum()),'source_mass_flux_kg_s':float(rho*np.sum(f*source)),'cooling_potential_flux_w':float(rho*1005*np.sum(f*(308.15-t)))}
    net={key:sum(p[key] for p in patches.values()) for key in patches['coldInlet']}
    return {'iteration':int(latest.name),'patches':patches,'net':net,'net_mass_error_relative_to_cold_source':net['mass_flux_kg_s']/info['cold_mass_flow_kg_s'],'net_tracer_advective_error_relative_to_source':net['source_mass_flux_kg_s']/info['cold_mass_flow_kg_s'],'net_thermal_advective_error_relative_to_source':net['cooling_potential_flux_w']/info['nominal_source_sensible_capacity_w'],'note':'Native boundary phi, not interpolated planes. Boundary diffusion is not included in the tracer/thermal advective balances. Positive flux leaves the domain.'}


if __name__=='__main__':
    for case in sorted((ROOT/'cases').glob('*bouss*')):
        try:
            result=balance(case)
            if result:
                (case/'boundary-balance.json').write_text(json.dumps(result,indent=2))
                print(case.name,result['iteration'],'mass',round(result['net_mass_error_relative_to_cold_source'],4),'tracer',round(result['net_tracer_advective_error_relative_to_source'],4),'thermal',round(result['net_thermal_advective_error_relative_to_source'],4))
        except Exception as exc:print('NOT READY',case.name,str(exc))
