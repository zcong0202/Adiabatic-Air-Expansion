"""Independent analytic checks for objective integration and search rejection."""
import json,math,tempfile
from pathlib import Path
import numpy as np
from audit_round import profile
from search import propose
from round_jet import OPT
checks={};info={'ambient_temperature_c':35,'cold_temperature_c':5,'density_reference_kg_m3':1.2,'cold_mass_flow_kg_s':.002}
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'profile.xy';r=np.linspace(0,.15,5001);u=np.ones_like(r)
 np.savetxt(p,np.column_stack([r,np.ones_like(r),u,np.zeros_like(r),np.zeros_like(r)]))
 v=profile(p,info);assert abs(v['mean_drop_c']-30)<1e-10;checks['uniform_cold_field_drop_c']=v['mean_drop_c']
 b=.018;peak=.6;theta=peak*np.exp(-(r/b)**2)
 np.savetxt(p,np.column_stack([r,theta,u,np.zeros_like(r),np.zeros_like(r)]))
 v=profile(p,info);exact=30*peak*(math.sqrt(math.pi)*b/(2*.025)*math.erf(.025/b))**2
 assert abs(v['mean_drop_c']-exact)<.0001
 checks['gaussian_square_integration_absolute_error_c']=abs(v['mean_drop_c']-exact)
 assert abs(v['temperature_sensitivity'][-1]['mean_drop_c']/v['mean_drop_c']-2/3)<1e-12
 checks['temperature_rescaling']='passed for a passive constant-property scalar'
def row(d,f,accepted):return {'case':f'fixture_{d}','diameter_mm':d,'numerically_accepted':accepted,'internal_diffuser_modeled':False,'turbulence_model':'kEpsilon','convection_order':2,'mesh_scale':1,'domain_scale':1,'cold_mass_flow_kg_s':.002,'reynolds_number':6000,'target':{'mean_source_fraction':f}}
result=propose([row(16,.25,True),row(24,.38,True),row(20,10,False)])
assert 'fixture_20' not in result['fit_case_names'];assert 21<result['predicted_minimum_diameter_mm']<=24
checks['failed_case_exclusion_and_bounded_crossing']='passed'
checks['scope']='Mathematical and software checks. Not validation of the AA hardware or turbulence closure.'
(OPT/'evidence/computation-verification.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
