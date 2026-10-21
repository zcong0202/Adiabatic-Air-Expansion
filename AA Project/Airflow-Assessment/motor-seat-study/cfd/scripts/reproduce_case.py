"""Replay a saved thermal case from its exact mesh, BCs and initial fields.
Usage: python reproduce_case.py C24_four_profile_continued REPLAY_C24
No prior CFD results are changed. Uses the pinned Docker solver.
"""
import sys,json,shutil,re
from seat_cfd import CFD,run
src=CFD/'cases'/sys.argv[1];dst=CFD/'cases'/sys.argv[2]
if dst.exists():raise FileExistsError(dst)
dst.mkdir()
for name in ['0','constant','system']:shutil.copytree(src/name,dst/name)
for name in ['mesh-metadata.npz','boundary-metadata.npz']:shutil.copyfile(src/name,dst/name)
info=json.loads((src/'case.json').read_text());info.update(case=dst.name,reproduced_from=src.name);(dst/'case.json').write_text(json.dumps(info,indent=2))
p=dst/'system/controlDict';s=p.read_text().replace('startFrom latestTime','startFrom startTime');s=re.sub(r'startTime [^;]+;','startTime 0;',s);p.write_text(s)
run(dst)
