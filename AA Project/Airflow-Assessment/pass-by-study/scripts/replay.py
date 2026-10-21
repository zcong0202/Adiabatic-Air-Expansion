"""Replay exact saved mesh/inputs into a new case, preserving all old evidence."""
import sys,shutil,json
from open_flow import CASES,run
src=CASES/sys.argv[1];dst=CASES/sys.argv[2]
if dst.exists():raise FileExistsError(dst)
dst.mkdir()
for directory in ['0','constant','system']:shutil.copytree(src/directory,dst/directory)
for file in ['mesh-metadata.npz','boundary-metadata.npz','probe-metadata.json']:shutil.copyfile(src/file,dst/file)
data=json.loads((src/'case.json').read_text());data.update(case=dst.name,replay_of=src.name);(dst/'case.json').write_text(json.dumps(data,indent=2))
run(dst)
