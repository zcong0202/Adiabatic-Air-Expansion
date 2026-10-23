"""Resumable DOE. Four independent two-rank solvers; no shared case mutation."""
from pathlib import Path
import sys,json,subprocess,time,concurrent.futures,threading,csv
from build import STUDY,ROOT,spec,IMAGE
PYTHON=sys.executable
LOCK=threading.Lock()
STATUS={'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'completed':[],'failed':[],'running':[]}

def plan():
    rows=[]
    for mass in [2,27,52,77]:
        for design in ['base','wide']:
            for count in [1,2,4]:
                name=f'm{mass:02}_n{count}_{design}'
                if design=='wide' and count==4 and mass in [2,77]:name=f'pilot_m{mass:02}_n4_wide'
                rows.append(dict(name=name,mass_g=mass,count=count,design=design,layout='side',h=.065,closure='auto',phase='baseline'))
    for mass in [2,27,52,77]:
        for layout in ['opposed','overhead']:
            rows.append(dict(name=f'm{mass:02}_n4_wide_{layout}',mass_g=mass,count=4,design='wide',layout=layout,h=.065,closure='auto',phase='layout'))
    for mass in [2,27,52,77]:
        for count in [1,2,4]:
            rows.append(dict(name=f'm{mass:02}_n{count}_adaptive',mass_g=mass,count=count,design='adaptive',layout='side',h=.065,closure='auto',phase='area-refinement'))
    # Transitional-Reynolds cases get both closures. Auto uses k-epsilon above 2300.
    for row in list(rows):
        s=spec(**{k:v for k,v in row.items() if k not in ['name','phase']})
        if s['transition'] and row['design']!='adaptive':rows.append({**row,'name':row['name']+'_laminar','closure':'laminar','phase':'transition-sensitivity'})
    return rows

def save():
    with LOCK:
        dest=STUDY/'results/campaign-status.json';tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(STATUS,indent=2));tmp.replace(dest)

def execute(row):
    name=row['name'];case=STUDY/'cfd/cases'/name
    with LOCK:STATUS['running'].append(name)
    save();print('START '+name,flush=True)
    try:
        if not case.exists():
            args=[PYTHON,str(STUDY/'scripts/build.py'),name,'--mass',str(row['mass_g']),'--count',str(row['count']),'--design',row['design'],'--layout',row['layout'],'--h',str(row['h']),'--closure',row['closure']]
            subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
        state=json.loads((case/'run-status.json').read_text()) if (case/'run-status.json').exists() else {}
        while state.get('status') in ['running','solver ended; audit pending']:
            time.sleep(2);state=json.loads((case/'run-status.json').read_text())
        ran_solver=False
        if state.get('status')!='audited' or not state.get('numerical_screens_pass'):
            with (STUDY/'results'/(name+'-run.log')).open('w') as log:subprocess.run([PYTHON,str(STUDY/'scripts/run.py'),name,str(row.get('ranks',2))],check=True,stdout=log,stderr=subprocess.STDOUT)
            ran_solver=True
        if ran_solver or not (STUDY/'results'/(name+'.json')).exists():
            with (STUDY/'results'/(name+'-extract.log')).open('w') as log:subprocess.run([PYTHON,str(STUDY/'scripts/extract.py'),name],check=True,stdout=log,stderr=subprocess.STDOUT)
        with LOCK:STATUS['completed'].append(name)
        print('DONE '+name,flush=True)
    except Exception as e:
        with LOCK:STATUS['failed'].append(dict(case=name,error=str(e)))
        print('FAILED '+name+' '+str(e),flush=True)
    finally:
        with LOCK:STATUS['running'].remove(name)
        save()

if __name__=='__main__':
    rows=plan();(STUDY/'results/campaign-plan.json').write_text(json.dumps(dict(total_cases=len(rows),source_c=.9592752761779835,ambient_c=30,wind_m_s=0,gravity_m_s2=[0,0,-9.81],spray_s=10,flows_g_s=[2,27,52,77],distances_m=[.2,.35,.5],cases=rows,image=IMAGE,scope='Prescribed source delivery screen, not a motor map or personal cooling simulation'),indent=2))
    with (STUDY/'results/calculation-screen.csv').open('w') as f:
        cols=['case','total_g_s','outlets','per_outlet_g_s','design','layout','width_m','height_m','exit_speed_m_s','hydraulic_reynolds','closure','source_cooling_w','source_mass_10s_kg'];w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader()
        for r in rows:
            s=spec(**{k:v for k,v in r.items() if k not in ['name','phase']});w.writerow({**{k:s[k] for k in cols if k in s},'case':r['name'],'source_cooling_w':r['mass_g']/1000*1006*(30-.9592752761779835),'source_mass_10s_kg':r['mass_g']/100})
    STATUS['total']=len(rows);save()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(execute,rows))
    STATUS['ended_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save()
    if STATUS['failed']:raise SystemExit(1)
