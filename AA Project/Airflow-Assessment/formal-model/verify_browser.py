"""Run optional UI checks through the user-requested gstack browse workflow."""
from pathlib import Path
import subprocess,json,os
ROOT=Path(__file__).resolve().parent
browse=Path(os.environ.get('AA_BROWSE',str(Path.home()/'.claude/skills/gstack/browse/dist/browse')))
script=(ROOT/'browser-check.js').read_text()
subprocess.run([str(browse),'js',script,'--out',str(ROOT/'browser-verification.json'),'--raw'],cwd=ROOT.parents[2],check=True)
report=json.loads((ROOT/'browser-verification.json').read_text())
print(json.dumps({'count':report['count'],'passed':report['passed'],'failed':[k for k,v in report['checks'].items() if not v]},indent=2))
if not report['passed']:raise SystemExit(1)
