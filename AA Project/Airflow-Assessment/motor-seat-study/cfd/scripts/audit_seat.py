from pathlib import Path
import numpy as np,json,re,sys,math
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'optimization/scripts'))
from audit_round import internal
sys.path.insert(0,str(HERE.parents[2]/'scripts'))
from boundary_balance import values,block

def arr(path,n,vector=False):
 a=internal(path,vector)
 if vector:return np.tile(a,(n,1)) if a.shape==(3,) else a
 return np.full(n,float(a[0])) if len(a)==1 else a

def patchvalue(text,p,owners,internal_values):
 try:return values(text,p,len(owners))
 except ValueError:return internal_values[owners]

def audit(case):
 case=Path(case);cfg=json.loads((case/'case.json').read_text());mesh=np.load(case/'mesh-metadata.npz');c=mesh['centers'];v=mesh['volumes'];n=len(v);boundary=np.load(case/'boundary-metadata.npz');rows=[];CP=1006;ta=cfg['ambient_c']+273.15;mass=cfg['source_mass_kg_s'];pa=101325
 paths=sorted([p for p in case.iterdir() if p.is_dir() and re.fullmatch(r'[0-9.]+',p.name) and (p/'T').exists()],key=lambda p:float(p.name))
 idx=mesh['indices'];lo=np.column_stack([mesh[k][idx[:,j]] for j,k in enumerate(['x','y','z'])]);hi=np.column_stack([mesh[k][idx[:,j]+1] for j,k in enumerate(['x','y','z'])])
 weights={key:np.prod(np.maximum(0,np.minimum(hi,np.array(b)[:,1])-np.maximum(lo,np.array(b)[:,0])),axis=1) for key,b in cfg['body_regions'].items()}
 masks={key:w>1e-14 for key,w in weights.items()}
 for path in paths:
  t=float(path.name);T=arr(path/'T',n);U=arr(path/'U',n,True)
  rho=arr(path/'rho',n) if (path/'rho').exists() else arr(path/'p',n)/(287.05*T)
  orig=arr(path/'origin',n) if (path/'origin').exists() else np.zeros(n)
  h=arr(path/'h',n) if (path/'h').exists() else CP*T
  p=arr(path/'p',n)
  if t==0:
   # Initial pressure is uniform before solver hydrostatic adjustment. Energy is a separate startup reference.
   pass
  row=dict(time_s=t,temperature_min_max_c=[float(T.min()-273.15),float(T.max()-273.15)],max_speed_m_s=float(np.linalg.norm(U,axis=1).max()),origin_min_max=[float(orig.min()),float(orig.max())],mass_kg=float(np.dot(rho,v)),origin_inventory_kg=float(np.dot(rho*orig,v)),energy_j=float(np.dot(rho*(h+.5*np.sum(U**2,axis=1)+9.81*c[:,2])-p,v)),regions={})
  for key,m in masks.items():
   vv=weights[key][m];tt=T[m];uu=np.linalg.norm(U[m],axis=1)
   if not len(tt):raise ValueError('Empty region '+key)
   row['regions'][key]=dict(volume_m3=float(vv.sum()),cells=int(m.sum()),mean_c=float(np.dot(tt,vv)/vv.sum()-273.15),mean_speed_m_s=float(np.dot(uu,vv)/vv.sum()),max_speed_m_s=float(uu.max()),fraction_volume_below20c=float(np.dot(tt<=293.15,vv)/vv.sum()),mean_origin=float(np.dot(orig[m],vv)/vv.sum()))
  zone=masks['occupied'];row['cold_zone_below22_m3']=float(weights['occupied'][zone&(T<295.15)].sum())
  row['supply_deficit_inventory_j']=float(np.dot(rho[zone]*CP*(ta-T[zone]),weights['occupied'][zone]))
  row['total_ambient_deficit_j']=float(np.dot(rho*CP*(ta-T),v))
  if (path/'phi').exists():
   phit=(path/'phi').read_text();ht=(path/'h').read_text() if (path/'h').exists() else None;ot=(path/'origin').read_text();patches={};heatdiff=0
   for patch in boundary.files:
    b=boundary[patch];owners=b[:,0].astype(int)
    if patch in ['person','panels','seat','ground']:continue
    ff=values(phit,patch,len(b));hh=patchvalue(ht,patch,owners,h) if ht else CP*patchvalue((path/'T').read_text(),patch,owners,T)
    oo=patchvalue(ot,patch,owners,orig)
    # Kinetic boundary term uses owner velocity; source U boundary is evaluated from imposed flow/area.
    kin=.5*np.sum(U[owners]**2,axis=1)
    if patch.startswith('jet'):kin[:]=.5*cfg['source_mean_speed_m_s']**2
    patches[patch]=dict(mass_flux_kg_s=float(ff.sum()),origin_advective_flux_kg_s=float(np.dot(ff,oo)),enthalpy_total_flux_w=float(np.dot(ff,hh+kin+9.81*b[:,3])))
   row['boundary']=patches
   row['outward_mass_flux_kg_s']=sum(x['mass_flux_kg_s'] for x in patches.values())
   row['outward_origin_flux_kg_s']=sum(x['origin_advective_flux_kg_s'] for x in patches.values())
   row['outward_energy_flux_w']=sum(x['enthalpy_total_flux_w'] for x in patches.values())
   row['inlet_mass_kg_s']=-sum(x['mass_flux_kg_s'] for p,x in patches.items() if p.startswith('jet'))
  rows.append(row)
 s=(case/'log.solver').read_text() if (case/'log.solver').exists() else ''
 # Preserve original pilot/startup log on continued cases separately; primary gates use completed current run.
 ended='\nEnd\n' in s and 'FOAM FATAL' not in s
 last=rows[-1];recent=[r for r in rows if r['time_s']>=last['time_s']-4]
 stats={key:dict(mean_c=float(np.trapezoid([r['regions'][key]['mean_c'] for r in recent],[r['time_s'] for r in recent])/(recent[-1]['time_s']-recent[0]['time_s'])) if len(recent)>1 else recent[0]['regions'][key]['mean_c'],range_c=float(np.ptp([r['regions'][key]['mean_c'] for r in recent])),mean_speed_m_s=float(np.trapezoid([r['regions'][key]['mean_speed_m_s'] for r in recent],[r['time_s'] for r in recent])/(recent[-1]['time_s']-recent[0]['time_s'])) if len(recent)>1 else recent[0]['regions'][key]['mean_speed_m_s']) for key in masks}
 # Integral residual using 1-second native boundary samples. Not the solver's exact per-substep energy residual.
 valid=[r for r in rows if 'boundary'in r and r['time_s']>=max(1,last['time_s']-5)]
 balance={}
 if len(valid)>=2:
  dt=valid[-1]['time_s']-valid[0]['time_s'];times=np.array([r['time_s'] for r in valid]);norm=max(mass*dt,1e-12)
  for quantity,flux,name in [('mass_kg','outward_mass_flux_kg_s','mass'),('origin_inventory_kg','outward_origin_flux_kg_s','origin')]:
   residual=valid[-1][quantity]-valid[0][quantity]+np.trapezoid([r[flux] for r in valid],times)
   balance[name+'_integral_error_relative_injected_mass']=float(residual/norm)
  er=valid[-1]['energy_j']-valid[0]['energy_j']+np.trapezoid([r['outward_energy_flux_w'] for r in valid],times)-(cfg['person_heat_w']+cfg.get('additional_panel_heat_w',0))*dt
  balance['energy_integral_error_relative_source_cooling']=float(er/max(mass*CP*(ta-(cfg['source_c']+273.15))*dt,1))
  balance['window_s']=[valid[0]['time_s'],valid[-1]['time_s']]
  balance['note']='Trapezoid at saved 1-s fields; gravity and pressure work included. Open-boundary diffusive heat, exact face kinetic interpolation and wall-flux deviation excluded; not a rigorous residual bound.'
 expected=float(re.search(r'\bendTime\s+([^;]+)',(case/'system/controlDict').read_text()).group(1));state=json.loads((case/'run-status.json').read_text());complete=state.get('status','').startswith('solver ended') and abs(last['time_s']-expected)<1e-5
 gates=dict(final_snapshot_complete=complete,mesh_ok='Mesh OK.' in (case/'log.checkMesh').read_text(),solver_ended=ended,
  fields_finite=bool(np.isfinite(T).all() and np.isfinite(U).all()),
  temperature_sane=bool(T.min()>250 and T.max()<400),origin_bounds=bool(orig.min()>-.005 and orig.max()<1.005),
  source_mass=abs(last.get('inlet_mass_kg_s',0)-mass)<max(.0001,.005*mass),
  mass_integral=abs(balance.get('mass_integral_error_relative_injected_mass',99))<.03,
  origin_integral=abs(balance.get('origin_integral_error_relative_injected_mass',99))<.05,
  energy_integral=abs(balance.get('energy_integral_error_relative_source_cooling',99))<.08)
 out=dict(case=cfg,history=rows,last=last,last4s_statistics=stats,conservation_screen=balance,gates=gates,numerically_screened=all(gates.values()),target20c_last4s_means=all(stats[k]['mean_c']<=20 for k in ['torso','neck']),stable_last4s=all(stats[k]['range_c']<.5 for k in ['torso','neck']),hardware_validated=False,continuum_error_bound_proved=False,region_quadrature='Exact intersection volumes of Cartesian CFD cells with fixed region boxes; piecewise-constant cell fields; trapezoid time average over last four saved seconds')
 (case/'audit.json').write_text(json.dumps(out,indent=2,allow_nan=False));return out
if __name__=='__main__':
 for x in sys.argv[1:]:
  a=audit(x);print(json.dumps(dict(case=a['case']['case'],last=a['last']['time_s'],regions=a['last4s_statistics'],gates=a['gates'],balance=a['conservation_screen'])),flush=True)
