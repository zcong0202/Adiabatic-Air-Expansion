"""Recompute conditional torque/heat screening. No material strength model."""
from pathlib import Path
import json, math
root=Path(__file__).resolve().parent
p=json.loads((root/'parameters.json').read_text())
r=json.loads((root/'load-screen.json').read_text())
a=r['assumptions']
a['reference_torque_Nm']=p['reference_torque_Nm']
a['sensitivity_torque_Nm']=p['screening_torque_Nm']
a['motor_hole_pitch_m']=abs(p['motor_mount_xy'][0][1]-p['motor_mount_xy'][1][1])/1000
r['cases']=[]
for t in [a['reference_torque_Nm'],a['sensitivity_torque_Nm']]:
    r['cases'].append(dict(torque_Nm=t,pad_tangential_force_N=round(t/a['effective_pad_radius_m'],2),ideal_motor_hole_couple_force_N=round(t/a['motor_hole_pitch_m'],2),ideal_IS_hole_couple_force_N=round(t/a['IS_hole_pitch_m'],2),scope='Ideal force/couple only. Net force, eccentric bending, preload and dynamics excluded.'))
r['thermal']['energy_J']=a['example_power_W']*a['duration_s']
r['plate_comparison']['ratio']=round((p['back_thickness']/6)**3,3)
(root/'load-screen.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'conditional_cases':r['cases'],'heat_J':r['thermal']['energy_J']}))
