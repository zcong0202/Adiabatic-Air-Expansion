"""Integration checks: source provenance, accepted CFD, quadrature and CAD."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from numpy.polynomial.legendre import leggauss
import trimesh
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parent
sys.path.insert(0,str(HERE/'scripts'));from campaign import source,CFG
r=json.loads((HERE/'results/campaign.json').read_text());checks={};details=[]
checks['case_budget_respected']=len(r['cases'])<=CFG['search']['max_new_cases']
checks['no_numerical_failures_ranked']=all(next(c for c in r['cases'] if c['case']==name)['numerically_accepted'] for name in r['ranked_case_names'])
for row in r['cases']:
 p=ROOT/'optimization/cases'/row['case'];a=json.loads((p/'audit.json').read_text());cfg=json.loads((p/'case.json').read_text())
 checks[row['case']+'_audit_hash']=hashlib.sha256((p/'audit.json').read_bytes()).hexdigest()==row['audit_sha256']
 factor=CFG['stress_ASSUMPTIONS']['mass_factor'] if 'lowflow' in row['case'] else 1
 checks[row['case']+'_paired_source_matches']=abs(cfg['cold_mass_flow_kg_s']-source(row['beta'],factor)['mass_kg_s'])<1e-12 and abs(cfg['cold_temperature_c']-source(row['beta'])['cold_c'])<1e-10
 flow=row['target_plane_flow'];checks[row['case']+'_captured_source_within_feed_budget']=0<=flow['captured_cold_origin_g_s']<=1.02*row['mass_g_s'] and flow['entrained_origin_g_s']>=0
 f=p/'postProcessing/targetProfiles'/f"{a['target']['iteration']:g}"/'target_theta_U.xy';v=np.loadtxt(f)
 q,w=leggauss(180);rr=np.hypot(q[:,None]*.025,q[None,:]*.025);mean=float(np.sum(np.interp(rr,v[:,0],v[:,1])*w[:,None]*w[None,:]/4));change=abs(mean-a['target']['mean_source_fraction'])*(34-row['nominal_source_c'])
 checks[row['case']+'_independent_area_quadrature']=change<.02;details.append({'case':row['case'],'higher_order_area_quadrature_change_c':change})
mesh=trimesh.load_mesh(HERE/'cad/nozzle-print-mm.stl',process=True);cad=json.loads((HERE/'cad/cad-verification.json').read_text())
checks['CAD_one_closed_consistent_body']=mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
checks['CAD_matches_selected_geometry']=cad['selected_case']==r['selected_case']['case'] and abs(mesh.extents[2]-cad['total_length_mm'])<1e-3
proof=json.loads((ROOT/'formal-model/proof-verification.json').read_text());checks['Lean_build_succeeded']=proof['build_succeeded'];checks['Lean_sources_match_verified_hashes']=all(hashlib.sha256((ROOT/'formal-model'/p).read_bytes()).hexdigest()==h for p,h in proof['source_sha256'].items())
checks={k:bool(v) for k,v in checks.items()}
out={'passed':all(checks.values()),'count':len(checks),'checks':checks,'independent_integration':details,'physical_validation':False,'scope':'Integration/provenance checks. Native CFD conservation and stability gates are in each audit.'};(HERE/'evidence/study-verification.json').write_text(json.dumps(out,indent=2));print(json.dumps({'passed':out['passed'],'count':out['count'],'failed':[k for k,v in checks.items() if not v]},indent=2))
if not out['passed']:raise SystemExit(1)
