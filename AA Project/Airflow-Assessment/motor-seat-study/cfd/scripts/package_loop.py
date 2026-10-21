from pathlib import Path
import json,zipfile,hashlib,re,sys
from seat_cfd import STUDY,CFD
R=STUDY;A=R.parent;PROJECT=A.parent
summary=json.loads((R/'results/cfd-cad-loop.json').read_text());selected=summary['preferred_still_air_candidate']['case'];case_names=[x['case'] for x in summary['cases']]+['N00_D50','N01_D100','N02_D100_transient','V03_exact_hydrostatic_rest'];files=set()
# Reports, CAD, source, animations and review evidence; native case data handled explicitly.
for p in R.rglob('*'):
 if not p.is_file() or '__pycache__'in p.parts or 'cases'in p.relative_to(R).parts:continue
 if p.name.startswith('note-') or p.name.startswith('iteration-page-') or p.name in ['package-manifest.json','package.py','loop-package-manifest.json','loop-package-verification.json']:continue
 files.add(p)
for name in case_names:
 case=CFD/'cases'/name
 if not case.exists():continue
 fields={}
 for p in case.rglob('*'):
  if not p.is_file() or any(x.startswith('processor') for x in p.relative_to(case).parts):continue
  rel=p.relative_to(case);top=rel.parts[0]
  if re.fullmatch(r'[0-9.]+',top) and top!='0':
   fields[str(rel)]=hashlib.sha256(p.read_bytes()).hexdigest()
   if name in [selected,'N02_D100_transient']:files.add(p)
  else:files.add(p)
 hp=case/'native-field-hashes.json';hp.write_text(json.dumps(fields,indent=2));files.add(hp)
for p in (A/'formal-model').rglob('*'):
 if p.is_file() and '.lake'not in p.parts and '__pycache__'not in p.parts:files.add(p)
# Existing helper modules used by CAD and field parsing. Preserve their expected layout.
for rel in ['scripts/foam-entry.sh','scripts/build_case.py','scripts/boundary_balance.py','scripts/generate_designs.py','optimization/scripts/audit_round.py','optimization/scripts/round_jet.py']:
 files.add(A/rel)
source=PROJECT/'Project-Documents/CFD inputs outdoor cooling seat (rental compressor + 4 × LZB46).docx';files.add(source)
manifest={str(p.relative_to(PROJECT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
mp=R/'results/loop-package-manifest.json';mp.write_text(json.dumps(manifest,indent=2));files.add(mp)
out=A/'AA-seat-CFD-CAD-loop.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files):z.write(p,str(p.relative_to(PROJECT)))
with zipfile.ZipFile(out) as z:
 for name,digest in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
info=dict(file=str(out),files=len(files),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),selected_case=selected,
 selected_and_internal_profile_native_fields_packaged=True,other_case_native_fields='Local workspace only; hashes, exact initial fields, mesh, dictionaries and audit records packaged for rerun.')
(R/'results/loop-package-verification.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
# Keep the existing standalone formal-model download current.
with zipfile.ZipFile(A/'AA-Lean-feasibility-model.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in (A/'formal-model').rglob('*'):
  if p.is_file() and '.lake'not in p.parts and '__pycache__'not in p.parts:z.write(p,str(p.relative_to(A/'formal-model')))
