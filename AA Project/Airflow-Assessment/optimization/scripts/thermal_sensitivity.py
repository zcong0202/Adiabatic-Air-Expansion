"""One-way heat-pickup and moist-mixing sensitivity on computed dry-air fields.

This is NOT conjugate or condensing CFD. It does not alter the solved velocity.
U values and humidity values are assumed envelopes, not AA measurements.
"""
import json,math
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.optimize import brentq
import psychrolib as psy
from round_jet import OPT
psy.SetUnitSystem(psy.SI)
P=101325


def equilibrium_temperature(fraction,ambient=35,cold=5,rh_ambient=.6,rh_cold=1,cold_w=None):
 wa=psy.GetHumRatioFromRelHum(ambient,rh_ambient,P);wc=psy.GetHumRatioFromRelHum(cold,rh_cold,P) if cold_w is None else cold_w
 # Convert the transported humid-air source mass fraction to dry-air fraction.
 drycold=fraction/(1+wc);drywarm=(1-fraction)/(1+wa);f=drycold/(drycold+drywarm)
 w=f*wc+(1-f)*wa;h=f*psy.GetMoistAirEnthalpy(cold,wc)+(1-f)*psy.GetMoistAirEnthalpy(ambient,wa)
 dry=psy.GetTDryBulbFromEnthalpyAndHumRatio(h,w)
 if w<=psy.GetSatHumRatio(dry,P):return dry
 # Retain equilibrium condensate. Enthalpy includes liquid water at T.
 def residual(t):
  ws=psy.GetSatHumRatio(t,P)
  return psy.GetMoistAirEnthalpy(t,ws)+(w-ws)*4186*t-h
 return brentq(residual,dry,ambient)


def calculate():
 records=json.loads((OPT/'results/cfd-records.json').read_text());rows=[]
 q,w=leggauss(40);r=np.hypot(q[:,None]*.025,q[None,:]*.025);weights=w[:,None]*w[None,:]/4
 for case in records:
  if not case.get('internal_diffuser_modeled') or not case.get('target'):continue
  info=case['diffuser'];d=info['exit_bore_mm']/1000;cone=info['cone_length_mm']/1000
  surface=math.pi*(.008+d)/2*math.hypot(cone,(d-.008)/2)+math.pi*.008*.015+math.pi*d*.010
  heat=[]
  for U in [0,2,10,20]:
   factor=math.exp(-U*surface/(case['cold_mass_flow_kg_s']*1005))
   for tc in [5,10,15]:
    drop=case['target']['mean_source_fraction']*(35-tc)*factor
    heat.append({'assumed_overall_U_w_m2_k':U,'source_temperature_c':tc,'mean_drop_c':drop,'exceeds_6c':bool(drop>6),'lumped_heat_retention_fraction':factor})
  path=OPT/'cases'/case['case']/'postProcessing/targetProfiles'/f"{case['target']['iteration']:g}"/'target_theta_U.xy'
  a=np.loadtxt(path);theta=np.clip(np.interp(r,a[:,0],a[:,1]),0,1);humidity=[]
  for rha in [.4,.6,.8]:
   for rhc in [.1,1.]:
    moist=np.array([equilibrium_temperature(float(f),rh_ambient=rha,rh_cold=rhc) for f in theta.ravel()]).reshape(theta.shape)
    humidity.append({'assumed_ambient_RH':rha,'assumed_cold_RH':rhc,'mean_drop_c':float(35-np.sum(moist*weights)),'exceeds_6c':bool(35-np.sum(moist*weights)>6)})
  combined=[]
  for tc in [5,10,15]:
   factor=math.exp(-20*surface/(case['cold_mass_flow_kg_s']*1005));teff=35-(35-tc)*factor;wc=psy.GetHumRatioFromRelHum(tc,1,P)
   moist=np.array([equilibrium_temperature(float(f),cold=teff,rh_ambient=.8,cold_w=wc) for f in theta.ravel()]).reshape(theta.shape)
   combined.append({'source_temperature_c':tc,'assumed_overall_U_w_m2_k':20,'ambient_RH':.8,'source_RH_before_heating':1,'effective_cold_temperature_after_lumped_heat_pickup_c':teff,'mean_drop_c':float(35-np.sum(moist*weights)),'exceeds_6c':bool(35-np.sum(moist*weights)>6)})
  hot=[]
  for tc in [5,10,15]:
   for te in [35,37,40,45]:
    for U in [0,20]:
     factor=math.exp(-U*surface/(case['cold_mass_flow_kg_s']*1005));effective=te-(te-tc)*factor;mean=case['target']['mean_source_fraction']*effective+(1-case['target']['mean_source_fraction'])*te
     hot.append({'source_temperature_c':tc,'entrained_air_temperature_c':te,'reference_ambient_c':35,'overall_U_w_m2_k':U,'mean_drop_relative_to_reference_c':35-mean,'exceeds_6c':bool(35-mean>6),'note':'Uniform hot-entrainment reservoir stress, not a resolved hot exhaust plume. Wall environment assumed equal to entrained air.'})
  rows.append({'case':case['case'],'numerically_accepted':case['numerically_accepted'],'wall_area_m2':surface,'heat_pickup':heat,'humidity_equilibrium':humidity,'combined_heat_and_humidity':combined,'hot_entrainment_stress':hot,'limits':'One-way sensitivities, not coupled moist/conjugate CFD. Combined rows use U=20 W/m2/K and 80% ambient RH, with saturated source air before heating. These are assumed stresses, not statistical confidence bounds. U, RH and paired source performance are unmeasured.'})
 checks={'identical_air_streams':abs(equilibrium_temperature(.4,ambient=20,cold=20,rh_ambient=.5,rh_cold=.5)-20)<1e-8,'warm_endpoint':abs(equilibrium_temperature(0)-35)<1e-8,'cold_endpoint':abs(equilibrium_temperature(1)-5)<1e-8}
 assert all(checks.values());(OPT/'evidence/moist-mixing-checks.json').write_text(json.dumps(checks,indent=2))
 (OPT/'results/thermal-sensitivity.json').write_text(json.dumps(rows,indent=2));print(json.dumps([{'case':r['case'],'accepted':r['numerically_accepted'],'worst_humidity_mean_drop_c':min(x['mean_drop_c'] for x in r['humidity_equilibrium'])} for r in rows],indent=2))

if __name__=='__main__':calculate()
