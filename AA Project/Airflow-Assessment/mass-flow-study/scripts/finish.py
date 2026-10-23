"""Finalise only after the refinement solver stage ended successfully."""
import json,sys,subprocess,time,concurrent.futures
from build import STUDY
OUT=STUDY/'results'
if __name__=='__main__':
    while True:
        status=json.loads((OUT/'refinement-status.json').read_text()) if (OUT/'refinement-status.json').exists() else {}
        if status.get('status')=='complete':break
        time.sleep(15)
    from archive import archive
    for name in json.loads((OUT/'campaign-status.json').read_text())['completed']:archive(name)
    for script in ['range_metrics.py','patch.py','calculation.py','assembly.py','verify.py','report.py','update_overview.py']:
        print('FINALISE '+script,flush=True);subprocess.run([sys.executable,str(STUDY/'scripts'/script)],check=True)
    data=json.loads((OUT/'campaign-status.json').read_text())
    def figures(name):
        print('FIGURES '+name,flush=True);subprocess.run([sys.executable,str(STUDY/'scripts/render.py'),name],check=True,stdout=subprocess.DEVNULL)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(figures,data['completed']))
    subprocess.run([sys.executable,str(STUDY/'scripts/validate_delivery.py')],check=True)
    (OUT/'finished.json').write_text(json.dumps(dict(status='complete',cases=len(data['completed']),native_archive_verified=True,all_case_figures_rendered=True,scope='External CFD delivery screen only; stock source and nozzle interiors unvalidated'),indent=2))
