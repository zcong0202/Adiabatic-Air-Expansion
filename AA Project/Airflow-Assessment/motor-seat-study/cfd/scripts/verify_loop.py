from pathlib import Path
import json,hashlib,math,re,subprocess
import numpy as np,trimesh
from seat_cfd import STUDY,CFD
R=STUDY;A=R.parent;r=json.loads((R/'results/cfd-cad-loop.json').read_text());p=r['preferred_still_air_candidate'];proof=json.loads((A/'formal-model/proof-verification.json').read_text());checks=[]
def ck(name,val):
 checks.append(dict(name=name,passed=bool(val)));assert val,name
ck('Lean build succeeded',proof['build_succeeded'])
ck('new CFD design/error/source proofs present',len([x for x in proof['theorems'] if x['name'] in ['finite_region_temperature_bound','cfd_region_upper_certificate','cad_flow_speed_limit','cold_path_heat_allowance','refinement_upper_bound_improves','three_motor_source_certificate','four_motor_warm_source_certificate','three_motor_supply_with_allowance','strict_cooling_error_budget']])==9)
for rel,h in proof['source_sha256'].items():ck('proof source current '+rel,hashlib.sha256((A/'formal-model'/rel).read_bytes()).hexdigest()==h)
ck('reference hydrostatic test passes',json.loads((CFD/'cases/V03_exact_hydrostatic_rest/rest-verification.json').read_text())['passed'])
ck('uniform source mesh comparison below0.5K',r['mesh_sensitivity']['both_changes_below_0_5c'])
ck('continuation exposed three-motor20C failure',any(x['case']=='C21_profile_halfCo_continuation' and not x['target20_means_pass'] for x in r['cases']))
ck('selected case uses a transferred CAD exit profile',p and p['profile_transferred'])
ck('selected case numerical screens pass',p['numerical_gates_pass'])
# A performance failure is a result, not a failed verification.
ck('all recorded thermal cases pass numerical screens',all(x['numerical_gates_pass'] for x in r['cases']))
for x in r['cases']:
 a=json.loads((CFD/'cases'/x['case']/'audit.json').read_text());neck=a['last']['regions']['neck'];torso=a['last']['regions']['torso']
 ck('fixed neck volume '+x['case'],abs(neck['volume_m3']-.2*.32*.2)<1e-10)
 ck('fixed torso volume '+x['case'],abs(torso['volume_m3']-.2*.44*.44)<1e-10)
 ck('stored thermal target is consistent '+x['case'],x['target20_means_pass']==(max(x['torso_c'],x['neck_c'])<=20))
 ck('source pair count '+x['case'],abs(x['mass_g_s']-19.4*x['active_motors'])<1e-9)
ck('all four wind cases completed',all(any(x['case']==n for x in r['cases']) for n in ['C14_four_motor_front05','C15_four_motor_front10','C16_four_motor_side05','C17_four_motor_side10']))
ck('warm supply and35C ambient cases completed',all(any(x['case']==n for x in r['cases']) for n in ['C18_four_motor_warm8','C19_four_motor_ambient35']))
ck('panel heat-load sensitivity completed',any(x['case']=='C23_four_motor_panel500' for x in r['cases']))
mesh=trimesh.load_mesh(R/'cad/side-slot-140x80-print-mm.stl',process=True)
ck('CAD watertight and normals consistent',mesh.is_watertight and mesh.is_winding_consistent)
ck('CAD single component',len(mesh.split())==1)
ck('CAD STL height205mm',abs(mesh.extents[2]-205)<1e-4)
meta=json.loads((R/'cad/cad-verification.json').read_text());ck('100mm inlet refinement exported',meta['inlet_spigot_od_mm']==100)
ck('CAD exit area matches CFD geometry',abs(4*meta['exit_open_area_m2']-json.loads((CFD/'cases'/p['case']/'case.json').read_text())['source_area_m2'])<1e-12)
step=(R/'cad/side-slot-140x80-flow-body.step').read_text();ck('STEP declares metres','SI_UNIT($,.METRE.)'in step and 'SI_UNIT(.MILLI.,.METRE.)'not in step)
profile=json.loads((CFD/'cases/N02_D100_transient/profile-audit.json').read_text());ck('refined internal profile no reversal',profile['reverse_area_fraction']==0)
ck('refined internal profile short-window CV stable',profile['CV_range']<.03)
ck('refined internal profile CV below0.25',profile['axial_speed_CV']<.25)
video=R/'results'/f'{p["case"]}-cooling.mp4';ck('selected animation exists',video.exists())
ff=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(video)],text=True));stream=next(x for x in ff['streams'] if x['codec_type']=='video');ck('animation121frames',int(stream['nb_frames'])==121)
prov=json.loads((R/'results'/f'{p["case"]}-animation-provenance.json').read_text());ck('animation is actual transient fields',prov['type'].startswith('Time-dependent'))
for t,h in prov['temperature_field_sha256'].items():ck('animation field hash '+t,hashlib.sha256((CFD/'cases'/p['case']/t/'T').read_bytes()).hexdigest()==h)
out=dict(checks=checks,all_passed=True,checks_count=len(checks),performance_failures_preserved=[x['case'] for x in r['cases'] if not x['target20_means_pass']],hardware_validated=False,physical_error_bound_established=False)
(R/'results/loop-verification.json').write_text(json.dumps(out,indent=2));print(json.dumps({'checks':len(checks),'all_passed':True,'performance_failures':out['performance_failures_preserved']}))
