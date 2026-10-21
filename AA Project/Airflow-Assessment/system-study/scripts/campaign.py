"""Bounded, sequential CFD -> algebra/heat/moisture screen -> CAD design loop.
All source and uncertainty inputs are explicit. No physical validation claim.
Run with the existing .venv-cfd Python. Reuses accepted R07 only as prior data.
"""
from pathlib import Path
import sys,json,math,argparse,hashlib,time,re,subprocess
import numpy as np
from numpy.polynomial.legendre import leggauss
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parent;OPT=ROOT/'optimization'
sys.path.insert(0,str(OPT/'scripts'))
from round_jet import build,run,resume,IMAGE,command
from audit_round import audit,internal
from thermal_sensitivity import equilibrium_temperature
CFG=json.loads((HERE/'config.json').read_text());S=CFG['stress_ASSUMPTIONS']
CP=1005.;R=287.05;P=101325.;RHO=P/(R*293.15)
# This saved campaign and its quadrature have one explicit target/reference.
# Reject a changed physical contract rather than reuse misleading case IDs.
for key,expected in [('ambient_c',34),('distance_m',.2),('width_m',.05),('height_m',.05)]:
 if CFG['target'][key]!=expected:raise ValueError('New target/reference needs a new named CFD campaign and matching postprocessor; use the general Lean calculator for parameter sensitivity.')
if CFG['source']['inlet_temperature_c']!=34 or CFG['source']['inlet_pressure_psig']!=100:
 raise ValueError('This manufacturer-map campaign fixes 34 C / 100 psig. Create new case IDs and source-map/state definitions for another reference.')
for key in ['source_drop_retained_fraction','mass_factor','area_fraction_factor']:
 if not 0<S[key]<=1:raise ValueError(f'{key} must be positive and at most one for this stress envelope.')
if S['overall_U_w_m2_k']<0 or not 0<=S['ambient_RH']<=1 or S['entrained_air_above_ambient_c']<0 or S['inlet_air_above_ambient_c']<0:
 raise ValueError('Use nonnegative heat conductance/hot offsets and RH between zero and one.')

def source(beta=.7,mass_factor=1):
 i=CFG['source']['cold_fractions'].index(beta);drop=CFG['source']['temperature_drop_f'][i]*5/9
 mass=CFG['source']['inlet_slpm']/60000*RHO*beta*mass_factor
 return {'beta':beta,'mass_kg_s':mass,'cold_c':34-drop,'temperature_drop_c':drop,'reference_density_kg_m3_ASSUMED':RHO}

def wall_area(info):
 d=info['diameter_mm']/1000;cone=info['diffuser']['cone_length_mm']/1000
 return math.pi*(.008+d)/2*math.hypot(cone,(d-.008)/2)+math.pi*.008*.015+math.pi*d*.010

def summarize(a,beta=.7):
 src=source(beta);ta=34;te=ta+S['entrained_air_above_ambient_c'];area=wall_area(a)
 m=a['cold_mass_flow_kg_s'];ua=S['overall_U_w_m2_k']*area;r=math.exp(-ua/(m*CP))
 tc=ta+S['inlet_air_above_ambient_c']-src['temperature_drop_c']*S['source_drop_retained_fraction']
 td=te-(te-tc)*r;alpha=a['target']['mean_source_fraction']*S['area_fraction_factor']
 dry_drop=ta-te+alpha*(te-td)
 f=OPT/'cases'/a['case']/'postProcessing/targetProfiles'/f"{a['target']['iteration']:g}"/'target_theta_U.xy'
 p=np.loadtxt(f);q,w=leggauss(35);rr=np.hypot(q[:,None]*.025,q[None,:]*.025);ww=w[:,None]*w[None,:]/4
 fraction=np.clip(np.interp(rr,p[:,0],p[:,1])*S['area_fraction_factor'],0,1)
 rawfraction=np.interp(rr,p[:,0],p[:,1]);ux=np.interp(rr,p[:,0],p[:,2]);rho=a['density_reference_kg_m3']
 total_mass=float(rho*.0025*np.sum(ux*ww));captured_mass=float(rho*.0025*np.sum(ux*rawfraction*ww))
 target_flows={'total_g_s':1000*total_mass,'captured_cold_origin_g_s':1000*captured_mass,'entrained_origin_g_s':1000*(total_mass-captured_mass),'source_mass_capture_fraction':captured_mass/m,'mass_flux_weighted_source_fraction':captured_mass/total_mass,'area_mean_source_fraction':a['target']['mean_source_fraction'],'scope':'Nominal dry constant-density CFD target-plane flows. Distinct from area temperature average and heat removed from skin.'}
 # Humidity ratio from assumed pressure dewpoint at the actual source inlet.
 import psychrolib as psy
 wc=psy.GetHumRatioFromTDewPoint(S['source_pressure_dewpoint_c'],100*6894.757+P)
 temperatures=np.array([equilibrium_temperature(float(f),ambient=te,cold=td,rh_ambient=S['ambient_RH'],cold_w=wc) for f in fraction.ravel()]).reshape(fraction.shape)
 moist_drop=float(ta-np.sum(temperatures*ww))
 # Buoyancy flag is an estimate at the target, not a CFD correction.
 speed=a['target']['mean_speed_m_s'];ri=9.81*max(0,ta-td)/(ta+273.15)*.2/max(speed**2,1e-12)
 # Source-port static pressure from the native patch is not its maximum rating.
 case=OPT/'cases'/a['case'];snap=a.get('native_balance',{}).get('snapshot');back=None
 if snap:
  # zeroGradient p does not necessarily serialize face values. The maximum
  # internal static p bounds its adjacent-cell face values. Add source kinetic
  # head for a conservative attachment inlet total-pressure screen.
  rho=a['density_reference_kg_m3'];uin=m/(rho*math.pi*.004**2)
  back=float(np.max(internal(case/snap/'p')))*rho+.5*rho*uin**2
 return {'case':a['case'],'target_plane_flow':target_flows,'diameter_mm':a['diameter_mm'],'half_angle_deg':a['diffuser']['half_angle_deg'],'length_mm':a['diffuser']['total_length_mm'],'mass_g_s':m*1000,'nominal_target_mean_speed_m_s':a['target']['mean_speed_m_s'],'nominal_target_advected_deficit_w':a['target']['target_advected_cooling_potential_w'],'beta':beta,'nominal_source_c':src['cold_c'],'cfd_mean_fraction':a['target']['mean_source_fraction'],'nominal_dry_drop_c':a['target']['mean_source_fraction']*(34-src['cold_c']),'stressed_dry_drop_c':dry_drop,'stressed_equilibrium_moist_drop_c':moist_drop,'stress_min_drop_c':min(dry_drop,moist_drop),'stress_source_c':tc,'stress_delivered_c':td,'stress_UA_w_K':ua,'attachment_pressure_conservative_bound_pa':back,'pressure_screen_method':'Maximum internal kinematic static p times rho plus inlet kinetic head. Conservative attachment bound, not sampled patch pressure.','backpressure_within_EXAIR_2psig_screen':back is not None and back<2*6894.757,'estimated_Richardson_number':ri,'numerically_accepted':a['numerically_accepted'],'failed_gates':[k for k,v in a['numerical_gates'].items() if not v],'passes_stress_plus_1C_margin':min(dry_drop,moist_drop)>=7 and a['numerically_accepted'] and back is not None and back<2*6894.757,'status':'Conditional still-air forced-flow screen. Moisture/heat are one-way calculations; stress ranges are assumptions, not confidence intervals.','audit_sha256':hashlib.sha256((case/'audit.json').read_bytes()).hexdigest()}

def run_with_seed(case,d,angle,src):
 """Same geometric boundaries only. A seed accelerates, never accepts, CFD."""
 seeds=[]
 for p in (OPT/'cases').glob('S0*stock*'):
  if p==case or not (p/'audit.json').exists():continue
  old=json.loads((p/'audit.json').read_text())
  if old.get('numerically_accepted') and old.get('diameter_mm')==d and old.get('diffuser',{}).get('half_angle_deg')==angle:seeds.append((p,old))
 if not seeds:return run(case)
 seed,old=seeds[-1];templates={f:(case/'0'/f).read_text() for f in ['U','p','k','omega','nut','theta']}
 state={'status':'running seeded solve','start_epoch':time.time(),'image':IMAGE,'initialization_source':seed.name};(case/'run-status.json').write_text(json.dumps(state,indent=2))
 for args,log in [(['blockMesh'],'log.blockMesh'),(['checkMesh'],'log.checkMesh'),(['mapFields','-sourceTime','latestTime','-consistent','-mapMethod','mapNearest',f'/work/optimization/cases/{seed.name}'],'log.mapFields')]:
  with (case/log).open('w') as out:code=subprocess.run(command(case,args),stdout=out,stderr=subprocess.STDOUT).returncode
  if code:raise RuntimeError(f'{args[0]} failed: {case/log}')
 ratio=src['mass_kg_s']/old['cold_mass_flow_kg_s']
 for f,template in templates.items():
  vals=internal(case/'0'/f,vector=f=='U');factor=ratio if f in ['U','omega','nut'] else ratio**2 if f in ['p','k'] else 1;vals=vals*factor
  entries='\n'.join('('+' '.join(f'{x:.12g}' for x in row)+')' for row in vals) if f=='U' else '\n'.join(f'{x:.12g}' for x in vals)
  field=f'internalField nonuniform List<{"vector" if f=="U" else "scalar"}>\n{len(vals)}\n(\n{entries}\n);'
  (case/'0'/f).write_text(re.sub(r'internalField\s+uniform\s+[^;]+;',lambda _:field,template))
 with (case/'log.solver').open('w') as out:code=subprocess.run(command(case,['simpleFoam']),stdout=out,stderr=subprocess.STDOUT).returncode
 state.update(status='solver ended; audit required' if code==0 else 'failed',elapsed_s=time.time()-state['start_epoch'],return_code=code);(case/'run-status.json').write_text(json.dumps(state,indent=2))
 if code:raise RuntimeError(f'Solver failed: {case}')

def solve(name,d,angle=5,mass_factor=1,scale=1,beta=.7):
 case=OPT/'cases'/name;src=source(beta,mass_factor=mass_factor)
 if case.exists():
  old=json.loads((case/'case.json').read_text())
  checks=[abs(old['cold_mass_flow_kg_s']-src['mass_kg_s'])<1e-12,abs(old['cold_temperature_c']-src['cold_c'])<1e-10,old['ambient_temperature_c']==34,old['diameter_mm']==d,old['mesh_scale']==scale,old.get('diffuser',{}).get('half_angle_deg')==angle]
  if not all(checks):raise ValueError(f'Case {name} already belongs to another operating point. Archive it or use a new case ID; cached fields cannot be silently reused.')
 if not case.exists():
  case=build(name,d=d,mass=src['mass_kg_s'],cold=src['cold_c'],ambient=34,model='kOmegaSST',scale=scale,iterations=2200,order=2,diffuser=True,angle_deg=angle)
  info=json.loads((case/'case.json').read_text());info['system_campaign']={'source':src,'config_sha256':hashlib.sha256((HERE/'config.json').read_bytes()).hexdigest(),'source_status':'EXAIR approximate curve and assumed reference-flow conversion; not Jeanoko'};(case/'case.json').write_text(json.dumps(info,indent=2))
  run_with_seed(case,d,angle,src)
 a=audit(case)
 while not a['numerically_accepted'] and a['last_iteration']<CFG['search']['max_iterations_per_case']:
  end=min(CFG['search']['max_iterations_per_case'],int(a['last_iteration'])+1000)
  resume(case,end);a=audit(case)
 result=summarize(a,beta);print(json.dumps(result),flush=True);return result

def save(rows):
 accepted=[r for r in rows if r['numerically_accepted'] and r['backpressure_within_EXAIR_2psig_screen']]
 # Rank a source/geometry by its WORST executed corner, including both meshes.
 # Preserve every individual result; never let a better mesh hide a worse one.
 groups={}
 for row in accepted:groups.setdefault((row['beta'],row['diameter_mm'],row['half_angle_deg']),[]).append(row)
 conservative=[min(g,key=lambda r:r['stress_min_drop_c']) for g in groups.values()]
 ranked=sorted(conservative,key=lambda r:(r['passes_stress_plus_1C_margin'],-r['length_mm'] if r['passes_stress_plus_1C_margin'] else r['stress_min_drop_c']),reverse=True)
 mesh=[]
 for fine in [r for r in rows if r['case'].endswith('_fine')]:
  coarse=next((r for r in rows if not r['case'].endswith('_fine') and r['beta']==fine['beta'] and r['diameter_mm']==fine['diameter_mm'] and r['half_angle_deg']==fine['half_angle_deg'] and abs(r['mass_g_s']-fine['mass_g_s'])<1e-8),None)
  if coarse:
   change=abs(fine['stress_min_drop_c']-coarse['stress_min_drop_c']);mesh.append({'coarse':coarse['case'],'fine':fine['case'],'stress_drop_change_c':change,'passes_0p5C_gate':change<=.5})
 report={'date':'2026-10-19','config':CFG,'solver_image':IMAGE,'cases':rows,'mesh_comparisons':mesh,'ranked_case_names':[r['case'] for r in ranked],'selected_case':ranked[0] if ranked else None,'hardware_validated':False,'global_optimum_established':False,'next_required_physics':CFG['pending_physics']}
 (HERE/'results/campaign.json').write_text(json.dumps(report,indent=2,allow_nan=False));return report

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');args=parser.parse_args()
 if not args.run:
  rows=[]
  for c in sorted((OPT/'cases').glob('S0*stock*')):
   if (c/'log.solver').exists() and (c/'run-status.json').exists() and json.loads((c/'run-status.json').read_text())['status'].startswith('solver ended'):
    a=audit(c)
    if a.get('target'):rows.append(summarize(a,beta=.6 if 'b60' in c.name else .7))
  print(json.dumps(save(rows),indent=2));return
 rows=[]
 rows.append(solve(CFG['search']['initial_case'],24));save(rows)
 # Recursive choice uses the completed baseline; thresholds never change.
 neighbour=20 if rows[-1]['passes_stress_plus_1C_margin'] else 24
 beta=.7 if rows[-1]['passes_stress_plus_1C_margin'] else .6
 b=round(beta*100)
 rows.append(solve(f'S01_stock_b{b}_D{neighbour}_a5',neighbour,beta=beta));save(rows)
 winner=max([r for r in rows if r['numerically_accepted']],key=lambda r:r['stress_min_drop_c'],default=rows[0])
 if rows[-1]['passes_stress_plus_1C_margin']:winner=rows[-1]
 d=winner['diameter_mm'];angle=winner['half_angle_deg'];beta=winner['beta'];b=round(beta*100)
 rows.append(solve(f'S02_stock_b{b}_D{d:g}_a{angle:g}_lowflow',d,angle,mass_factor=S['mass_factor'],beta=beta));save(rows)
 # Low-flow corner may force a wider outlet; otherwise shorten/compare cone.
 if not rows[-1]['passes_stress_plus_1C_margin'] and d<32:
  nextd=min(32,d+4);rows.append(solve(f'S03_stock_b{b}_D{nextd:g}_a5_lowflow',nextd,5,mass_factor=S['mass_factor'],beta=beta))
 else:
  rows.append(solve(f'S03_stock_b{b}_D{d:g}_a{angle:g}_lowflow_fine',d,angle,mass_factor=S['mass_factor'],scale=.8,beta=beta))
 save(rows)
 if not rows[-1]['case'].endswith('_fine'):
  if not rows[-1]['passes_stress_plus_1C_margin'] and rows[-1]['diameter_mm']<32:
   d=rows[-1]['diameter_mm']+4;rows.append(solve(f'S04_stock_b{b}_D{d:g}_a5_lowflow',d,5,mass_factor=S['mass_factor'],beta=beta));save(rows)
  if rows[-1]['passes_stress_plus_1C_margin']:
   r=rows[-1];rows.append(solve(r['case']+'_fine',r['diameter_mm'],r['half_angle_deg'],mass_factor=S['mass_factor'],scale=.8,beta=beta))
 # A widened geometry has only its low-flow corner so far. Verify nominal
 # flow too if budget remains; never repeat a point already executed.
 passing=next((r for r in reversed(rows) if r['passes_stress_plus_1C_margin']),None)
 if passing and len(rows)<CFG['search']['max_new_cases']:
  nominal=source(passing['beta'])['mass_kg_s']*1000
  matched=any(r['diameter_mm']==passing['diameter_mm'] and r['half_angle_deg']==passing['half_angle_deg'] and r['beta']==passing['beta'] and abs(r['mass_g_s']-nominal)<1e-8 for r in rows)
  if not matched:
   rows.append(solve(f"S05_stock_b{round(passing['beta']*100)}_D{passing['diameter_mm']:g}_a{passing['half_angle_deg']:g}_nominal",passing['diameter_mm'],passing['half_angle_deg'],beta=passing['beta']))
 report=save(rows);print(json.dumps({'completed_cases':len(rows),'selected':report['selected_case']},indent=2),flush=True)

if __name__=='__main__':main()
