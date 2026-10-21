from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parent;A=R.parent
files=[p for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('note-') and p.name!='package-manifest.json']
F=A/'formal-model'
files += [p for p in F.rglob('*') if p.is_file() and '.lake' not in p.parts and '__pycache__' not in p.parts and (p.suffix in ['.lean','.toml','.json','.log'] or p.name=='lean-toolchain')]
manifest={str(p.relative_to(A)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(R/'results/package-manifest.json').write_text(json.dumps(manifest,indent=2))
files.append(R/'results/package-manifest.json')
out=A/'AA-motor-seat-viability.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,str(p.relative_to(A)))
with zipfile.ZipFile(out) as z:
 for name,sha in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==sha
print(json.dumps({'archive':str(out),'files':len(files),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
# Refresh the previous standalone proof archive to match its current overview link.
with zipfile.ZipFile(A/'AA-Lean-feasibility-model.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in F.rglob('*'):
  if p.is_file() and '.lake' not in p.parts and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(F)))
