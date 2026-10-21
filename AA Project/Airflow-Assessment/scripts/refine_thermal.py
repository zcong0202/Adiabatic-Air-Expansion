"""Checkpoint restart: consistent tracer-based thermal initialization and
bounded second-order convection. Initialization values are not results.
"""
import json
import sys
from pathlib import Path
import numpy as np
from restart_thermal import ROOT, internal, replace_internal


def refine(name):
    case=ROOT/'cases'/name
    if '\nEnd\n' not in (case/'log.solver').read_text():
        raise RuntimeError('Wait for clean solver checkpoint')
    latest=max([p for p in case.iterdir() if p.is_dir() and p.name.isdigit()],key=lambda p:int(p.name))
    info=json.loads((case/'case.json').read_text())
    c=np.clip(internal(latest/'c'),0,1)
    u=internal(latest/'U')
    temp=308.15-(35-info['cold_total_temperature_c'])*c-(u*u).sum(axis=1)/(2*1005)
    replace_internal(latest/'T',temp)
    p=case/'system/fvSchemes';s=p.read_text()
    s=s.replace('div(phi,U) bounded Gauss upwind;','div(phi,U) bounded Gauss limitedLinearV 1;')
    for f in ['h','K','c']:
        s=s.replace(f'div(phi,{f}) bounded Gauss upwind;',f'div(phi,{f}) bounded Gauss limitedLinear 1;')
    p.write_text(s)
    p=case/'system/controlDict';s=p.read_text().replace('startFrom startTime;','startFrom latestTime;').replace('stopAt writeNow;','stopAt endTime;').replace('endTime 1000;','endTime 900;').replace('writeInterval 200;','writeInterval 100;');p.write_text(s)
    p=case/'system/fvSolution';s=p.read_text().replace('h 0.4;','h 0.7;');p.write_text(s)
    info['convection_scheme']='Bounded second order for U/h/K/c; upwind turbulence transport'
    info['thermal_restart_iteration']=int(latest.name)
    info['temperature_initialization']='Tracer-consistent field at checkpoint; subsequent solver iterations are results.'
    (case/'case.json').write_text(json.dumps(info,indent=2))
    (case/'log.solver-initialization').write_text((case/'log.solver').read_text())
    print(name,latest.name)


if __name__=='__main__':refine(sys.argv[1])
