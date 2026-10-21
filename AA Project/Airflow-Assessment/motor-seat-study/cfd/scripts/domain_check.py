"""Combined far-field/domain sensitivity from an existing wind state.
NOT an independent cold-start prediction or an isolated grid-error estimate.
"""
import json,subprocess,time,shutil
from seat_cfd import build,CFD,docker,run
from profile_transfer import apply
c=build('C26_large_domain_side10','side',.075,5,wind=1,direction='side',large_domain=True,freestream_tangent=True);apply(c)
backup=c/'initial-boundary-backup';shutil.copytree(c/'0',backup)
with (c/'log.mapFields').open('w') as f:
 rc=subprocess.run(docker(c,['mapFields','../C17_four_motor_side10','-sourceTime','20','-consistent','-mapMethod','cellPointInterpolate']),stdout=f,stderr=subprocess.STDOUT).returncode
if rc:raise RuntimeError('mapFields failed')
# Keep mapped INTERNAL fields. Restore every target boundary condition.
for p in backup.iterdir():
 if not p.is_file():continue
 target=c/'0'/p.name
 if target.exists():
  text=target.read_text();original=p.read_text();target.write_text(text[:text.index('boundaryField')]+original[original.index('boundaryField'):])
info=json.loads((c/'case.json').read_text());info.update(initialized_from='C17 at20s; mapped interiors only; target BCs restored',domain_sensitivity='Larger domain and explicit ambient tangential inflow velocity, plus5s continuation. These changes are not separated.',source_mean_time_offset_s=20);(c/'case.json').write_text(json.dumps(info,indent=2));run(c)
