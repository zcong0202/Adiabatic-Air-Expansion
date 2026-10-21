"""Cross-artifact engineering checks. No physical performance certification."""
import hashlib,json,math
from pathlib import Path
import numpy as np,trimesh
from open_flow import STUDY,ROOT,CASES

d=json.loads((STUDY/'results/cfd-summary.json').read_text());checks=[]
def check(name,condition):
    checks.append(dict(name=name,passed=bool(condition)))
    if not condition:print('FAILED:',name)
check('nine layout-distance controls completed',d['controls_completed']==9)
check('current scenario excludes human obstacle and hardware validation',not d['body_included'] and not d['hardware_validated'])
for row in d['cases']:
    name=row['case'];case=CASES/name;a=json.loads((case/'audit.json').read_text());cfg=a['case']
    check(name+': solver/mesh/conservation screens',a['numerical_screens_pass'])
    check(name+': no seat/enclosure/body geometry',len(cfg['geometry'])==4 and all(b['name'].startswith('jet') for b in cfg['geometry']) and not cfg['body_regions'])
    check(name+': same total nominal flow/area',abs(cfg['source_mass_kg_s']-.0776)<1e-12 and abs(cfg['source_area_m2']-.0448)<1e-10)
    check(name+': activation within 30 second limit',0<row['duration_s']<=30)
    check(name+': preserves pulse versus passage distinction',all(p['complete_path_window_s'][1]-p['complete_path_window_s'][0]<3 for p in a['passages']))
    check(name+': continuous duration does not exceed total',all(0<=p['longest_continuous_above_delta6_s']<=p['time_above_delta6_s']+1e-10<=p['complete_path_window_s'][1]-p['complete_path_window_s'][0]+1e-9 for p in a['passages']))
    check(name+': 5cm area and three walking speeds',all(p['patch_side_m']==.05 for p in a['passages']) and set(p['walking_speed_m_s'] for p in a['passages'])=={.6,1.2,1.8})
    check(name+': preserves hypothetical error-budget sensitivity',all(p['assumed_upward_temperature_error_k_sensitivity']['3']['total_s']<=p['time_above_delta6_s']+1e-10 for p in a['passages']))
    check(name+': resolved probe interval, not oversampled trace interval',a['sampling']['native_probe_interval_max_s']<.08)
    check(name+': bounded fixed air-band coverage',0<=a['incident_air_band_snapshot']['area_above_delta6_m2']<=1.12)
    check(name+': temperature provenance matches native fields',all(hashlib.sha256((case/t/'T').read_bytes()).hexdigest()==v for t,v in a['temperature_field_sha256'].items()))
    if cfg['wind_m_s']:
        u=(case/'0/U').read_text();check(name+': opposing cross-path wind prescribed','(0 -0.5 0)' in u and 'opposed'==cfg['wind_direction'])
for shape in ['140x80','280x40']:
    mesh=trimesh.load_mesh(STUDY/f'cad/outlet-{shape}-print-mm.stl',process=True);info=json.loads((STUDY/f'cad/outlet-{shape}-verification.json').read_text())
    check(shape+': watertight consistently oriented single-part STL',mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1)
    check(shape+': millimetre dimensions and equal area',abs(mesh.extents[2]-205)<.01 and abs(info['outlet_area_m2']-.0112)<1e-12)
proof=json.loads((ROOT/'formal-model/proof-verification.json').read_text())
check('57 printed Lean checks build successfully',proof['build_succeeded'] and proof['printed_axiom_checks']==57)
check('all recorded Lean source hashes match',all(hashlib.sha256((ROOT/'formal-model'/path).read_bytes()).hexdigest()==sha for path,sha in proof['source_sha256'].items()))
check('no new physics axioms or hardware proof claim',not proof['new_physics_axioms'] and not proof['hardware_validated'])
rest=json.loads((CASES/'V00_rest/rest-verification.json').read_text());check('hydrostatic rest test passed',rest['passed'])
out=dict(checks=checks,all_passed=all(c['passed'] for c in checks),checks_count=len(checks),body_included=False,hardware_validated=False,
         performance_failures_preserved=[r['case'] for r in d['cases'] if r['reference']['time_above_delta6_s']==0])
(STUDY/'results/verification.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
if not out['all_passed']:raise SystemExit(1)
