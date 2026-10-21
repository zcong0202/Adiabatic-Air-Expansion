"""Local reproducibility handover; no dependency caches or duplicate overview."""
from pathlib import Path
import hashlib,json,re,zipfile,tempfile,shutil,subprocess,sys
from open_flow import ROOT,STUDY,CASES

PROJECT=ROOT.parent
selected={'R00_wide_d35','L00_row4_d35','A00_pitch8_d50'}
files=set()
for p in STUDY.rglob('*'):
    if not p.is_file() or '__pycache__'in p.parts or 'tmp'in p.relative_to(STUDY).parts:continue
    rel=p.relative_to(STUDY)
    if rel.parts[:2]==('cfd','cases'):continue
    if p.name in ['package-manifest.json','package-verification.json']:continue
    files.add(p)
for case in CASES.iterdir():
    if not case.is_dir() or not (case/'case.json').exists():continue
    hashes={}
    for p in case.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(case)
        if any(part.startswith('processor') for part in rel.parts):continue
        native=bool(re.fullmatch(r'[0-9.]+',rel.parts[0])) and rel.parts[0]!='0'
        raw_probe=rel.parts[0]=='postProcessing' and 'airProbes'in rel.parts
        if native or raw_probe:
            hashes[str(rel)]=hashlib.sha256(p.read_bytes()).hexdigest()
            if case.name in selected:files.add(p)
        else:files.add(p)
    hp=case/'native-and-probe-hashes.json';hp.write_text(json.dumps(hashes,indent=2));files.add(hp)
# The tested setup writers/parsers are library dependencies, not reused seat fields.
for rel in ['motor-seat-study/cfd/scripts/seat_cfd.py','motor-seat-study/cfd/scripts/audit_seat.py',
            'scripts/foam-entry.sh','scripts/boundary_balance.py','scripts/generate_designs.py',
            'optimization/scripts/audit_round.py','optimization/scripts/round_jet.py','scripts/build_case.py']:
    files.add(ROOT/rel)
for p in (ROOT/'formal-model').rglob('*'):
    if p.is_file() and '.lake'not in p.parts and '__pycache__'not in p.parts:files.add(p)
files.add(ROOT/'current-design-scope.json')
source=PROJECT/'Project-Documents/CFD inputs outdoor cooling seat (rental compressor + 4 × LZB46).docx';files.add(source)
# Prove helper imports do not depend on unshipped files in the original workspace.
with tempfile.TemporaryDirectory(prefix='aa-passby-package-') as folder:
    temp=Path(folder)
    for p in files:
        if p.suffix=='.py':
            target=temp/p.relative_to(PROJECT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    code='import sys;sys.path.insert(0,'+repr(str(temp/'Airflow-Assessment/pass-by-study/scripts'))+');import open_flow,analyse,make_cad,animate,summarize,core_diagnostic;print("Isolated parser/CAD imports pass")'
    subprocess.run([sys.executable,'-I','-c',code],cwd=temp,check=True)
ip=STUDY/'results/reproducibility-import-verification.json';ip.write_text(json.dumps(dict(isolated_imports_passed=True,modules=['open_flow','analyse','make_cad','animate','summarize','core_diagnostic'],original_workspace_on_sys_path=False),indent=2));files.add(ip)
manifest={str(p.relative_to(PROJECT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
mp=STUDY/'results/package-manifest.json';mp.write_text(json.dumps(manifest,indent=2));files.add(mp)
out=ROOT/'AA-outdoor-pass-by-study.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(files):z.write(p,str(p.relative_to(PROJECT)))
with zipfile.ZipFile(out) as z:
    for name,digest in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
info=dict(file=str(out),bytes=out.stat().st_size,files=len(files),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
          packaged_full_native_cases=sorted(selected),other_case_native_fields='Local workspace; hashes, probe traces/audits and exact replay inputs packaged.',
          all_members_hash_verified=True,body_included=False,hardware_validated=False)
(STUDY/'results/package-verification.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
with zipfile.ZipFile(ROOT/'AA-Lean-feasibility-model.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in (ROOT/'formal-model').rglob('*'):
        if p.is_file() and '.lake'not in p.parts and '__pycache__'not in p.parts:z.write(p,str(p.relative_to(ROOT/'formal-model')))
