"""Evaluate the user-confirmed 50 x 50 mm, 200 mm air-temperature objective.
Numerical acceptance is independent of hardware validation.
"""
import json,math,re,sys
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss
from round_jet import ROOT,OPT
sys.path.insert(0,str(ROOT/'scripts'))
from boundary_balance import block,values


def internal(path,vector=False):
 s=path.read_text();m=re.search(r'internalField\s+nonuniform\s+List<\w+>\s+(\d+)\s*\((.*?)\)\s*;',s,re.S)
 if m:
  a=np.fromstring(m.group(2).replace('(',' ').replace(')',' '),sep=' ')
  return a.reshape(-1,3) if vector else a
 m=re.search(r'internalField\s+uniform\s+([^;]+)',s)
 return np.array([float(x) for x in m.group(1).strip('() ').split()])


def profile(path,info,n=100):
 a=np.loadtxt(path);r,theta,u=a[:,0],a[:,1],a[:,2:5]
 q,w=leggauss(n);y=q*.025;rr=np.hypot(y[:,None],y[None,:]);ww=w[:,None]*w[None,:]/4
 t=np.interp(rr,r,theta);ux=np.interp(rr,r,u[:,0]);um=np.interp(rr,r,np.linalg.norm(u,axis=1))
 mean=float(np.sum(t*ww));drop=mean*(info['ambient_temperature_c']-info['cold_temperature_c'])
 heat=info['density_reference_kg_m3']*1005*(info['ambient_temperature_c']-info['cold_temperature_c'])*.0025*np.sum(ux*t*ww)
 flux=info['density_reference_kg_m3']*float(np.trapezoid(2*math.pi*r*theta*u[:,0],r))
 return {'mean_source_fraction':mean,'mean_drop_c':drop,'mean_air_temperature_c':info['ambient_temperature_c']-drop,'center_drop_c':float(theta[0]*(info['ambient_temperature_c']-info['cold_temperature_c'])),'mean_speed_m_s':float(np.sum(um*ww)),'fraction_of_target_area_above_6c_drop':float(np.sum(((info['ambient_temperature_c']-info['cold_temperature_c'])*t>6)*ww)),'target_advected_cooling_potential_w':float(heat),'target_plane_source_flux_relative_to_inlet':flux/info['cold_mass_flow_kg_s'],'source_fraction_min_max':[float(theta.min()),float(theta.max())],'temperature_sensitivity':[{'cold_temperature_c':tc,'mean_drop_c':(info['ambient_temperature_c']-tc)*mean,'mean_air_temperature_c':info['ambient_temperature_c']-(info['ambient_temperature_c']-tc)*mean,'exceeds_6c':bool((info['ambient_temperature_c']-tc)*mean>6)} for tc in [5,10,15]],'warmest_source_temperature_for_6c_drop_c':info['ambient_temperature_c']-6/max(mean,1e-12)}


def audit(case):
 info=json.loads((case/'case.json').read_text());cfg=json.loads((OPT/'config.json').read_text());g=cfg['quality_gates']
 out={**info,'reynolds_number':info['density_reference_kg_m3']*info['exit_speed_m_s']*info['diameter_mm']/1000/1.8e-5}
 s=(case/'log.solver').read_text() if (case/'log.solver').exists() else ''
 times=re.findall(r'^Time = (\S+)',s,re.M)
 out.update(solver_end_seen=s.rfind('\nEnd\n')>s.rfind('\nTime = ') and '\nEnd\n' in s,fatal_error='FOAM FATAL' in s or '[stack trace]' in s,last_iteration=float(times[-1]) if times else 0,solver_convergence_reported='SIMPLE solution converged' in s,mesh_ok=(case/'log.checkMesh').exists() and 'Mesh OK.' in (case/'log.checkMesh').read_text())
 records=[]
 for part in re.split(r'\nTime = ',s)[1:]:
  row={}
  for key,v in re.findall(r'Solving for (\w+), Initial residual = ([^,]+)',part):
   if key not in row:row[key]=float(v)
  if 'epsilon' in row or 'omega' in row:records.append(row)
 out['last_residuals']=records[-1] if records else {}
 relevant=['Ux','Uy','p','k','epsilon' if info['turbulence_model']=='kEpsilon' else 'omega','theta']
 tail=records[-30:];out['maximum_initial_residuals_last_30']={k:max([r.get(k,math.inf) for r in tail],default=math.inf) for k in relevant}
 # theta is solved after flow; a final converged-flow exit may omit the scalar.
 out['maximum_initial_residuals_last_30']['theta']=max([r['theta'] for r in tail if 'theta' in r],default=math.inf)
 sample=[]
 for f in sorted((case/'postProcessing/targetProfiles').glob('*/target_theta_U.xy'),key=lambda f:float(f.parent.name)):
  try:sample.append({'iteration':float(f.parent.name),**profile(f,info)})
  except (ValueError,OSError):pass
 out['history']=sample
 if sample:out['target']=sample[-1];out['recent_target_change_c']=max([v['mean_drop_c'] for v in sample[-3:]])-min([v['mean_drop_c'] for v in sample[-3:]])
 snapshots=sorted([p for p in case.iterdir() if p.is_dir() and p.name.isdigit() and p.name!='0' and (p/'theta').exists()],key=lambda p:int(p.name))
 if snapshots:
  last=snapshots[-1];th=internal(last/'theta');u=internal(last/'U',True)
  out['volume_scalar_min_max']=[float(th.min()),float(th.max())];out['maximum_swirl_component_relative_to_exit']=float(np.max(np.abs(u[:,2]))/info['exit_speed_m_s'])
  boundary=(case/'constant/polyMesh/boundary').read_text();phi=(last/'phi').read_text();theta=(last/'theta').read_text();patches={}
  for name in ['jet','ambient','far','outlet']:
   count=int(re.search(r'nFaces\s+(\d+)',block(boundary,name)).group(1));f=values(phi,name,count);t=values(theta,name,count);patches[name]={'volume_flux':float(f.sum()),'scalar_advective_flux':float(np.sum(f*t))}
  denom=abs(patches['jet']['volume_flux']);out['native_balance']={'snapshot':last.name,'mass_imbalance_relative_to_source':sum(p['volume_flux'] for p in patches.values())/denom,'scalar_advective_imbalance_relative_to_source':sum(p['scalar_advective_flux'] for p in patches.values())/denom,'patches':patches,'note':'Wedge-native boundary phi; scalar diffusive boundary flux is not included.'}
  if len(snapshots)>1:
   previous=snapshots[-2];up=internal(previous/'U',True);tp=internal(previous/'theta')
   out['field_velocity_max_change_relative_to_exit']=float(np.max(np.linalg.norm(u-up,axis=1))/info['exit_speed_m_s']);out['field_scalar_max_change']=float(np.max(np.abs(th-tp)))
 state=json.loads((case/'run-status.json').read_text()) if (case/'run-status.json').exists() else {}
 gates={'mesh_ok':out['mesh_ok'],'solver_ended':out['solver_end_seen'] and not out['fatal_error'] and state.get('status','').startswith('solver ended')}
 rr=out['maximum_initial_residuals_last_30'];gates['momentum_residuals']=max(rr.get('Ux',math.inf),rr.get('Uy',math.inf))<=g['maximum_relevant_momentum_initial_residual'];gates['pressure_residual']=rr.get('p',math.inf)<=g['maximum_pressure_initial_residual'];gates['turbulence_residuals']=max(rr.get('k',math.inf),rr.get('epsilon',rr.get('omega',math.inf)))<=g['maximum_turbulence_initial_residual'];gates['scalar_residual']=rr.get('theta',math.inf)<=g['maximum_scalar_initial_residual']
 b=out.get('native_balance',{});gates['mass_balance']=abs(b.get('mass_imbalance_relative_to_source',math.inf))<=g['maximum_native_mass_imbalance_fraction'];gates['scalar_balance']=abs(b.get('scalar_advective_imbalance_relative_to_source',math.inf))<=g['maximum_native_advective_scalar_imbalance_fraction']
 bounds=out.get('volume_scalar_min_max',[-math.inf,math.inf]);gates['scalar_bounds']=bounds[0]>=-g['maximum_thermal_fraction_bound_excursion'] and bounds[1]<=1+g['maximum_thermal_fraction_bound_excursion']
 gates['objective_stable']=len(sample)>=3 and out.get('recent_target_change_c',math.inf)<=g['maximum_target_mean_drop_change_c'];gates['full_velocity_field_stable']=out.get('field_velocity_max_change_relative_to_exit',math.inf)<=g['maximum_field_velocity_change_relative_to_exit'];gates['full_scalar_field_stable']=out.get('field_scalar_max_change',math.inf)<=g['maximum_field_scalar_change']
 # A one-cell symmetric wedge has no physical swirl. Relative Uz residuals
 # normalize round-off-sized fields, so check its absolute amplitude AND all
 # field changes; retain its reported residual in the raw record.
 gates['negligible_swirl']=out.get('maximum_swirl_component_relative_to_exit',math.inf)<1e-5
 out['numerical_gates']=gates;out['numerically_accepted']=all(gates.values());out['hardware_validated']=False
 def clean(v):
  if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
  if isinstance(v,list):return [clean(x) for x in v]
  if isinstance(v,float) and not math.isfinite(v):return None
  return v
 out=clean(out)
 out['status']='Numerically accepted prescribed-exit screen; hardware unvalidated' if out['numerically_accepted'] else 'Pending or rejected numerical checks'
 (case/'audit.json').write_text(json.dumps(out,indent=2))
 return out

if __name__=='__main__':
 records_out=[]
 for case in sorted((OPT/'cases').glob('*')):
  if not (case/'case.json').exists():continue
  try:
   r=audit(case);records_out.append(r);print(case.name,r['last_iteration'],round(r.get('target',{}).get('mean_drop_c',0),3),r['numerically_accepted'],[k for k,v in r['numerical_gates'].items() if not v])
  except Exception as e:print(case.name,'AUDIT_ERROR',repr(e))
 (OPT/'results/cfd-records.json').write_text(json.dumps(records_out,indent=2,allow_nan=False))
