"""Compare accepted actual diffuser flows including declared thermal stresses.

Report both margin and length. Do not hide the competing objectives in a
weighted scalar. Unmeasured source states remain distinct scenarios.
"""
import argparse,json,math
from round_jet import OPT,build,run
from search import read_cases
from thermal_sensitivity import calculate


def decision():
 cfg=json.loads((OPT/'config.json').read_text());mass=cfg['nominal_source']['cold_mass_flow_kg_s'];diameter=cfg['shape_search']['exit_bore_mm'];margin_target=cfg['target']['mean_temperature_drop_c_strictly_greater_than']+cfg['target']['minimum_mean_drop_design_margin_c'];max_length=cfg['shape_search']['maximum_proposed_length_mm']
 records=read_cases();(OPT/'results/cfd-records.json').write_text(json.dumps(records,indent=2));calculate()
 thermal=json.loads((OPT/'results/thermal-sensitivity.json').read_text());rows=[]
 for r in records:
  if not r.get('numerically_accepted') or not r.get('internal_diffuser_modeled') or r['mesh_scale']!=1 or r['convection_order']!=1 or r['turbulence_model']!='kOmegaSST' or abs(r['cold_mass_flow_kg_s']-mass)>1e-9 or r['diameter_mm']!=diameter:continue
  t=next((t for t in thermal if t['case']==r['case']),None)
  if t is None:continue
  rows.append({'case':r['case'],'angle_deg':r['diffuser']['half_angle_deg'],'diameter_mm':r['diameter_mm'],'length_mm':r['diffuser']['total_length_mm'],'dry_nominal_drop_c':r['target']['mean_drop_c'],'stressed_drop_by_source_c':{str(v['source_temperature_c']):v['mean_drop_c'] for v in t['combined_heat_and_humidity']},'status':'Numerically accepted; physical thermal stresses are assumed one-way sensitivities'})
 scenarios=[]
 for tc in [5,10,15]:
  feasible=[r for r in rows if r['stressed_drop_by_source_c'][str(tc)]>margin_target and r['length_mm']<=max_length]
  scenarios.append({'source_c':tc,'target':'More than 6 C plus a 1 C design margin','highest_margin_case':max(feasible,key=lambda r:r['stressed_drop_by_source_c'][str(tc)])['case'] if feasible else None,'shortest_tested_case':min(feasible,key=lambda r:r['length_mm'])['case'] if feasible else None,'feasible_cases':[r['case'] for r in feasible]})
 next_probe=None
 # For the nominal 5 C source, bracket the shortest feasible taper.
 passed=sorted(r['angle_deg'] for r in rows if r['stressed_drop_by_source_c']['5']>margin_target)
 failed=sorted(r['angle_deg'] for r in rows if r['stressed_drop_by_source_c']['5']<=margin_target)
 if passed and failed:
  a=max(passed);b=next((x for x in failed if x>a),None)
  if b is not None and b-a>.5:next_probe=(a+b)/2
 result={'scope':'Bounded still-air 8-to-24 mm cone search: 3..7 degrees, total length <=180 mm. Bounds are proposed prototype limits, not measured installation constraints.','nominal_flow_kg_s':.002,'thermal_stress':'U=20 W/m2/K, ambient RH80%, source RH100% before heating; one-way estimate, no coupled moist/conjugate CFD.','candidates':rows,'scenarios':scenarios,'next_angle_probe_deg':next_probe,'global_hardware_optimum_claim':False,'wind_validated':False,'open_inputs':['Actual paired source flow, temperature and pressure after fitting the nozzle','Ambient humidity and real wall/insulation heat transfer','Actual installation length/diameter and source connector']}
 (OPT/'results/shape-decision.json').write_text(json.dumps(result,indent=2));return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');a=p.parse_args();r=decision();print(json.dumps(r,indent=2))
 if a.run and r['next_angle_probe_deg'] is not None:
  angle=r['next_angle_probe_deg'];name=f'Adaptive_D24_a{angle:g}_SST';case=build(name,d=24,model='kOmegaSST',order=1,diffuser=True,angle_deg=angle,iterations=8000);run(case);decision()
