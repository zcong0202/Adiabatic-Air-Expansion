"""Sequential local solver queue; at most two campaign queues are launched."""
from pathlib import Path
import subprocess,sys,time,json
from seat_cfd import CFD
waitfor=sys.argv[1];jobs=sys.argv[2:]
p=CFD/'cases'/waitfor/'run-status.json'
while True:
 state=json.loads(p.read_text())
 if state['status'].startswith('solver ended'):break
 if state['status']=='failed':raise RuntimeError(state)
 time.sleep(5)
for job in jobs:
 if job.startswith('internal'):
  args=['internal_nozzle.py',job.removeprefix('internal')]
 else:args=['run_stage.py',job]
 subprocess.run([sys.executable,str(Path(__file__).parent/args[0]),*args[1:]],check=True)
