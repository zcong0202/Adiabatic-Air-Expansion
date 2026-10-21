"""Constrained, adaptive CFD search. Never fit a surrogate to failed runs.

Two tasks are distinct: highest drop within explicit diameter bounds, and the
smallest tested diameter that preserves a 1 C margin with a 15 C cold source.
The latter is a declared engineering choice, not a universal optimum.
"""
import argparse,json,math,sys,time
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from round_jet import OPT,build,run
from audit_round import audit


def read_cases():
 records=[]
 for case in sorted((OPT/'cases').iterdir()):
  if not (case/'case.json').exists():continue
  try:records.append(audit(case))
  except (ValueError,OSError,KeyError):continue
 return records


def propose(records,order=2,warm=15):
 cfg=json.loads((OPT/'config.json').read_text());source=cfg['nominal_source'];mass=source['cold_mass_flow_kg_s'];ambient=source['ambient_temperature_c'];bound=cfg['search']['bounds_mm'];margin=cfg['target']['minimum_mean_drop_design_margin_c'];target=cfg['target']['mean_temperature_drop_c_strictly_greater_than']+margin
 candidates=[r for r in records if r.get('numerically_accepted') and not r.get('internal_diffuser_modeled') and r['turbulence_model']=='kEpsilon' and r['convection_order']==order and r['mesh_scale']==1 and r['domain_scale']==1 and abs(r['cold_mass_flow_kg_s']-mass)<1e-9 and r['reynolds_number']>=cfg['search']['minimum_reynolds_for_fully_turbulent_screen']]
 by_d={r['diameter_mm']:r for r in candidates};ds=sorted(by_d)
 proposed={'status':'Need at least two numerically accepted diameters','fit_case_names':[by_d[d]['case'] for d in ds],'objective':'Minimum diameter with >6 C drop plus 1 C design margin at a 15 C source, nominal 2 g/s, 35 C ambient','global_optimum_claim':False}
 if len(ds)<2:return proposed
 vals=[by_d[d]['target']['mean_source_fraction']*(ambient-warm) for d in ds]
 interp=PchipInterpolator(ds,vals,extrapolate=False)
 grid=np.arange(math.ceil(ds[0]),math.floor(ds[-1])+1,1.0);pred=interp(grid);passes=grid[pred>target]
 proposed['predicted_feasible_diameters_mm']=passes.tolist();proposed['sampled_warm_case_drops_c']=[{'diameter_mm':d,'mean_drop_c':v} for d,v in zip(ds,vals)]
 tested={r['diameter_mm'] for r in records if r['convection_order']==order and not r.get('internal_diffuser_modeled') and r['mesh_scale']==1 and r['domain_scale']==1 and r['turbulence_model']=='kEpsilon'}
 if len(passes):
  # Verify the interpolated crossing with a NEW CFD evaluation.
  first=float(passes[0]);check=[first]+[float(x) for x in [first-1,first+1] if bound[0]<=x<=bound[1]]
  nextd=next((x for x in check if x not in tested),None)
  proposed.update(status='Predicted crossing requires CFD verification' if nextd else 'Crossing bracket evaluated at 1 mm resolution',predicted_minimum_diameter_mm=first,next_diameter_mm=nextd)
 else:
  widest=max(ds)
  nextd=min(bound[1],widest+4)
  maxre=4*mass/(math.pi*1.8e-5*(nextd/1000))
  if nextd not in tested and maxre>=cfg['search']['minimum_reynolds_for_fully_turbulent_screen']:proposed.update(status='Expand evaluated diameter range',next_diameter_mm=nextd)
  else:proposed.update(status='No verified feasible design in admissible evaluated range',next_diameter_mm=None)
 return proposed


def save(records,proposal):
 (OPT/'results/cfd-records.json').write_text(json.dumps(records,indent=2))
 (OPT/'results/search-decision.json').write_text(json.dumps(proposal,indent=2))
 print(json.dumps(proposal,indent=2),flush=True)


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='store_true');p.add_argument('--budget-new',type=int,default=3);p.add_argument('--order',type=int,default=2);args=p.parse_args()
 if not 0<=args.budget_new<=10:raise ValueError('Explicit new-case budget must be 0..10')
 for attempt in range(args.budget_new+1):
  records=read_cases();proposal=propose(records,args.order);save(records,proposal)
  d=proposal.get('next_diameter_mm')
  if not args.run or d is None or attempt==args.budget_new:break
  name=f'A{int(d):02d}_D{d:g}_o{args.order}'
  if (OPT/'cases'/name).exists():raise FileExistsError(name)
  source=json.loads((OPT/'config.json').read_text())['nominal_source']
  case=build(name,d=d,mass=source['cold_mass_flow_kg_s'],cold=source['cold_temperature_c'],ambient=source['ambient_temperature_c'],iterations=5000,order=args.order)
  run(case)

if __name__=='__main__':main()
