"""Package concept CAD separately from the larger CFD inputs and diagnostics."""
import hashlib
import argparse
import json
import zipfile
from pathlib import Path
from build_case import ROOT


def pack(path,files):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p in sorted(set(files)):
            z.write(p,str(p.relative_to(ROOT)))
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'entries':len(set(files))}


cad=[ROOT/'READ-ME.txt',ROOT/'results/design-concepts.png',ROOT/'results/outlet-profiles.png',ROOT/'results/design-summary.json',ROOT/'scripts/generate_designs.py',ROOT/'requirements-cfd.txt']
for d in (ROOT/'designs').glob('*'):
    if not d.is_dir():continue
    cad.extend(p for p in d.iterdir() if p.is_file() and p.suffix in ['.step','.stl','.json'])
cad.extend([ROOT/'evidence/geometry-checks.json',ROOT/'evidence/step-unit-checks.json'])
records=[pack(ROOT/'AA-CFD-concepts-v1.zip',cad)]
parser=argparse.ArgumentParser();parser.add_argument('--cad-only',action='store_true');args=parser.parse_args()
if args.cad_only:
    print(json.dumps(records,indent=2));raise SystemExit(0)
study=list(cad)
study.extend(p for p in (ROOT/'scripts').glob('*') if p.is_file())
study.extend(p for p in ROOT.glob('*.json'))
study.extend(p for p in (ROOT/'results').glob('*') if p.is_file())
study.extend(p for p in (ROOT/'evidence').glob('*') if p.is_file() and (p.suffix in ['.json','.log'] or p.name=='exair-small-dimensions-screen-2026-10-15.png'))
for d in (ROOT/'designs').glob('*'):
    if d.is_dir():study.extend(p for p in d.rglob('*') if p.is_file() and p.suffix in ['.msh','.json','.step'])
for c in (ROOT/'cases').glob('*bouss*'):
    if not c.is_dir():continue
    for part in ['0','constant','system','postProcessing']:
        if (c/part).exists():study.extend(p for p in (c/part).rglob('*') if p.is_file())
    study.extend(p for p in c.iterdir() if p.is_file() and (p.name.startswith('log.') or p.suffix in ['.json','.msh','.foam']))
records.append(pack(ROOT/'AA-CFD-study-v1.zip',study))
(ROOT/'evidence/package-manifest.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
