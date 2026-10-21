"""Run the nine agreed open-air layout/distance screens, two jobs at a time."""
import concurrent.futures, json, subprocess, sys, time
from open_flow import STUDY, CASES

rows=[(f'P{a}{b}_{label}_d{round(distance*100):02d}',layout,distance)
      for a,label,layout in [(0,'one','one-side'),(1,'two','two-side'),(2,'over','overhead')]
      for b,distance in enumerate([.2,.35,.5])]
script=STUDY/'scripts/open_flow.py'
audit_script=STUDY/'scripts/analyse.py'

def job(row):
    name,layout,distance=row;case=CASES/name
    if not case.exists():
        subprocess.run([sys.executable,str(script),name,'--layout',layout,'--distance',str(distance),'--end','10','--run'],check=True)
    else:
        state=case/'run-status.json'
        while True:
            status=json.loads(state.read_text()) if state.exists() else {}
            if status.get('status','').startswith('solver ended'): break
            if status.get('status')=='failed': raise RuntimeError(status)
            time.sleep(10)
    subprocess.run([sys.executable,str(audit_script),name],check=True)
    data=json.loads((case/'audit.json').read_text())
    if not data['numerical_screens_pass']: raise RuntimeError(f'{name}: numerical screen failure; inspect audit')
    print(json.dumps(dict(completed=name)),flush=True)
    return name

if __name__=='__main__':
    failures=[];completed=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(job,row):row[0] for row in rows}
        for f in concurrent.futures.as_completed(futures):
            try: completed.append(f.result())
            except Exception as e: failures.append(dict(case=futures[f],error=str(e)));print(json.dumps(failures[-1]),flush=True)
    result=dict(completed=completed,failures=failures,body_included=False)
    (STUDY/'results/campaign-status.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
    if failures: sys.exit(1)
