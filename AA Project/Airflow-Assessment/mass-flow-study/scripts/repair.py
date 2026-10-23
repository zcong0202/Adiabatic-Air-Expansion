"""Rerun only repaired, rejected meshes after the main solver pool finishes."""
import json,subprocess,sys,time,concurrent.futures
from build import STUDY
OUT=STUDY/'results'
if __name__=='__main__':
    while True:
        status=json.loads((OUT/'campaign-status.json').read_text())
        if 'ended_utc' in status:break
        time.sleep(10)
    failures=list(status['failed']);names=[f['case'] for f in failures];assert set(names)<=set(['m02_n2_adaptive','m02_n4_adaptive']),failures
    def job(name):
        case=STUDY/'cfd/cases'/name;assert 'Mesh OK.' in (case/'log.mesh-preflight').read_text()
        with (OUT/(name+'-repair.log')).open('w') as log:
            subprocess.run([sys.executable,str(STUDY/'scripts/run.py'),name,'4'],check=True,stdout=log,stderr=subprocess.STDOUT)
            subprocess.run([sys.executable,str(STUDY/'scripts/extract.py'),name],check=True,stdout=log,stderr=subprocess.STDOUT)
        from archive import archive
        archive(name);return name
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:completed=list(pool.map(job,names))
    status['rejected_mesh_attempts']=failures;status['completed'].extend(completed);status['failed']=[];status['repaired_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());tmp=OUT/'campaign-status.repaired';tmp.write_text(json.dumps(status,indent=2));tmp.replace(OUT/'campaign-status.json');print('Repaired',completed,flush=True)
