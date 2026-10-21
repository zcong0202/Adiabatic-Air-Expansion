"""After layout controls finish, test one aspect-ratio change and sensitivities.
This is a manual DOE iteration, not an automatic global optimizer.
"""
import concurrent.futures,subprocess,sys,json,time
from open_flow import STUDY,CASES

def execute(name,args):
    case=CASES/name
    if not case.exists():subprocess.run([sys.executable,str(STUDY/'scripts/open_flow.py'),name,'--layout','one-side','--distance','.35','--end','10',*args,'--run'],check=True)
    subprocess.run([sys.executable,str(STUDY/'scripts/analyse.py'),name],check=True)
    return name

if __name__=='__main__':
    while not (STUDY/'results/campaign-status.json').exists():time.sleep(15)
    status=json.loads((STUDY/'results/campaign-status.json').read_text())
    if status['failures']:raise RuntimeError('Controls need review before refinement')
    jobs=[('R00_wide_d35',['--width','.28','--height','.04']),
          ('F00_base_d35',['--h','.045']),
          ('F01_wide_d35',['--h','.045','--width','.28','--height','.04']),
          ('W00_wide_opposed',['--width','.28','--height','.04','--wind','.5','--wind-direction','opposed'])]
    done=[];failed=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(execute,*j):j[0] for j in jobs}
        for f in concurrent.futures.as_completed(futures):
            try:done.append(f.result())
            except Exception as e:failed.append(dict(case=futures[f],error=str(e)))
    (STUDY/'results/refinement-status.json').write_text(json.dumps(dict(completed=done,failures=failed),indent=2))
    if failed:raise RuntimeError(failed)
