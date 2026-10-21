"""Package reproducible inputs, accepted/rejected evidence and candidate CAD."""
import argparse,hashlib,json,zipfile
from round_jet import ROOT,OPT

def pack(path,files):
 files=sorted(set(files))
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
  for p in files:z.write(p,str(p.relative_to(ROOT)))
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 return {'file':path.name,'bytes':path.stat().st_size,'entries':len(files),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'integrity':'passed'}

p=argparse.ArgumentParser();p.add_argument('--cad-only',action='store_true');a=p.parse_args()
cad=[f for f in (OPT/'designs').rglob('*') if f.is_file() and '__pycache__' not in str(f)]
cad+=[OPT/'READ-ME.txt',OPT/'config.json',OPT/'results/iterated-designs.png',OPT/'results/candidate-cad.json',OPT/'evidence/candidate-geometry-verification.json']
reports=[pack(ROOT/'AA-iterated-designs-v2.zip',cad)]
if not a.cad_only:
 files=[f for f in OPT.rglob('*') if f.is_file() and '__pycache__' not in str(f) and f.suffix not in ['.zip','.pyc'] and f.name!='package-manifest.json']
 files.extend(ROOT/'scripts'/n for n in ['foam-entry.sh','generate_designs.py','boundary_balance.py','build_case.py'])
 reports.append(pack(ROOT/'AA-design-search-v2.zip',files))
(OPT/'evidence/package-manifest.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports,indent=2))
