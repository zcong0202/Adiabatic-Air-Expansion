"""Reuse the audited external-jet solver in a separate scuba study.
Single nozzle, 19.4 g/s; source temperature is a conditional first-law budget.
"""
from pathlib import Path
import sys,json,argparse
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];STUDY=HERE.parent
sys.path.insert(0,str(ROOT/'mass-flow-study/scripts'))
import build
build.STUDY=STUDY
sys.path.insert(0,str(HERE))
from calculate import calculate

def execute(name,h=.065,tin=30,ranks=2):
    inputs=calculate();source=next(s for s in inputs['sources'] if s['motor_inlet_c']==tin)
    build.SOURCE_C=source['nozzle_c']
    case=STUDY/'cfd/cases'/name
    if not (case/'run-status.json').exists():
        case=build.build(name,mass_g=19.4,count=1,design='wide',layout='side',h=h)
        info=json.loads((case/'case.json').read_text());info.update(source_thermal_status='Scuba study: conditional ONE loaded motor; 30 or 40 C inlet, 840 W shaft load, 19.4 g/s, full previous path UA=10.0737 W/K. Not measured.',scuba_source=source,source_pressure_status='12 L / 200 bar tank reduced to 6.3 bar gauge at motor; regulator flow unqualified; tank transient not solved inside CFD')
        (case/'case.json').write_text(json.dumps(info,indent=2))
    status=json.loads((case/'run-status.json').read_text()) if (case/'run-status.json').exists() else {}
    from run import run
    if status.get('status')!='audited':run(case,ranks)
    from extract import extract
    from range_metrics import update as ranges
    from patch import update as patches
    from render import render
    from archive import archive
    from timeline import create
    if not (STUDY/'results'/(name+'.json')).exists():extract(case)
    ranges(name);patches(name);render(name);archive(name);create(name)
    result=json.loads((STUDY/'results'/(name+'.json')).read_text())
    print(json.dumps(dict(case=name,cells=result['inputs']['cells'],source_c=result['inputs']['source_c'],final=result['final'],conservation=result['conservation'])),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--h',type=float,default=.065);p.add_argument('--tin',type=float,default=30);p.add_argument('--ranks',type=int,default=2);a=p.parse_args();execute(a.name,a.h,a.tin,a.ranks)
