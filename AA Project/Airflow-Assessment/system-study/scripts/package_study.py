"""Package reproducible relative project layout, source, profiles and evidence."""
from pathlib import Path
import json,hashlib,zipfile
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parent
r=json.loads((HERE/'results/campaign.json').read_text());files=set()
for folder in [HERE,ROOT/'formal-model']:
 for p in folder.rglob('*'):
  if p.is_file() and not any(x in p.relative_to(folder).parts for x in ['.lake','.gstack','__pycache__','tmp','.DS_Store']):files.add(p)
common=['optimization/scripts/round_jet.py','optimization/scripts/audit_round.py','optimization/scripts/thermal_sensitivity.py','optimization/config.json','optimization/requirements.txt','scripts/foam-entry.sh','scripts/boundary_balance.py','scripts/build_case.py','scripts/generate_designs.py']
for rel in common:files.add(ROOT/rel)
native=[]
for row in r['cases']:
 case=ROOT/'optimization/cases'/row['case']
 for rel in ['case.json','audit.json','run-status.json','log.blockMesh','log.checkMesh','log.potentialFoam','log.mapFields','log.solver']:
  p=case/rel
  if p.exists():files.add(p)
 for folder in ['system','0']:
  files.update(p for p in (case/folder).rglob('*') if p.is_file())
 files.update(p for p in (case/'constant').glob('*') if p.is_file())
 latest=json.loads((case/'audit.json').read_text())['native_balance']['snapshot']
 native.extend({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'in_archive':False} for p in (case/latest).glob('*') if p.is_file())
 samples=sorted((case/'postProcessing/targetProfiles').glob('*/target_theta_U.xy'),key=lambda p:float(p.parent.name))[-3:]
 for f in samples:
  files.add(f);center=f.parent/'centerline_theta_U.xy'
  if center.exists():files.add(center)
mf=HERE/'evidence/archive-manifest.json';files.discard(mf)
def member(p):
 rel=p.relative_to(ROOT)
 if rel.parts[:2]==('optimization','cases'):return Path('Airflow-Assessment/system-study/evidence/executed-cases')/Path(*rel.parts[2:])
 return Path('Airflow-Assessment')/rel
manifest={'date':'2026-10-19','hardware_validated':False,'archive_scope':'Relative Airflow-Assessment code layout. Executed case evidence is archived under system-study/evidence/executed-cases so fresh CFD can generate optimization/cases. Complete native volume fields remain local.','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},'archive_members':{str(p.relative_to(ROOT)):str(member(p)) for p in sorted(files)},'native_fields_local_hashes':native}
mf.write_text(json.dumps(manifest,indent=2));files.add(mf)
archive=ROOT/'AA-stock-system-study.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,member(p))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
# Refresh the earlier proof-package link after extending its Lean source.
formal=ROOT/'formal-model'
with zipfile.ZipFile(ROOT/'AA-Lean-feasibility-model.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in formal.rglob('*'):
  if p.is_file() and not any(x in p.relative_to(formal).parts for x in ['.lake','.gstack','__pycache__','.DS_Store']):z.write(p,Path('AA-Lean-feasibility-model')/p.relative_to(formal))
print(json.dumps({'archive':str(archive),'files':len(files),'bytes':archive.stat().st_size,'integrity':'passed'},indent=2))
