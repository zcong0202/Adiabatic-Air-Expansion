"""Test longer along-path layout and its explicit heat-pickup sensitivity."""
import concurrent.futures,subprocess,sys,json,time
from open_flow import STUDY,CASES

def run(name,extra):
    if not (CASES/name).exists():subprocess.run([sys.executable,str(STUDY/'scripts/open_flow.py'),name,'--layout','one-row','--distance','.35','--end','10',*extra,'--run'],check=True)
    subprocess.run([sys.executable,str(STUDY/'scripts/analyse.py'),name],check=True)
    return name

if __name__=='__main__':
    while not (STUDY/'results/refinement-status.json').exists():time.sleep(10)
    if json.loads((STUDY/'results/refinement-status.json').read_text())['failures']:raise RuntimeError('Refinement needs review')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        tasks=[pool.submit(run,'L00_row4_d35',[]),pool.submit(run,'S00_row4_source8',['--source','8'])]
        names=[f.result() for f in tasks]
    (STUDY/'results/row-status.json').write_text(json.dumps(dict(completed=names,failures=[]),indent=2))
