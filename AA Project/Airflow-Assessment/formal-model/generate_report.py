"""Generate a parameter report and source-state lookup, without new CFD."""
from pathlib import Path
from dataclasses import replace
import json,itertools,math,hashlib,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import CoolProp
from model import Delivery,evaluate,source_state,RHO_REF,CP

ROOT=Path(__file__).parent
report={'schema_version':1,'date':'2026-10-19','status':'Conditional mathematical feasibility; no new hardware measurements or CFD',
 'default_inputs':evaluate(Delivery()),
 'line_heat_sensitivity':evaluate(Delivery(heat_conductance_w_k=.2)),
 'dry_CFD_fraction_sensitivity_only':evaluate(Delivery(heat_conductance_w_k=0)),
 'parameters':[
  {'symbol':'mc','meaning':'Cold source mass flow, g/s','known':'Unmeasured. Existing CFD assumed 2 g/s. Source map must pair flow and temperature.'},
  {'symbol':'Ts','meaning':'Cold source temperature after final pressure release, before modeled line heat gain, C','known':'About 5 C reported at nozzle; measurement location/steady flow must be confirmed. Do not count heat gain twice.'},
  {'symbol':'alpha_A','meaning':'Area-average cold-origin mass fraction across 50x50 mm target at 200 mm','known':'Unmeasured. CFD value 0.3146377977 applies only to R07 assumed operating point.'},
  {'symbol':'UA','meaning':'Total modeled downstream cold-line/nozzle heat conductance to surroundings, W/K','known':'Unmeasured. Default 0 is an adiabatic screen; 0.2 W/K is an illustrative stress. If Ts is measured at final nozzle exit, exclude upstream heat gain.'},
  {'symbol':'Te','meaning':'Temperature of entrained air and modeled line surroundings, C','known':'Ambient 30-34 C discussed; hot exhaust may raise Te. Reference Ta stays separate.'},
  {'symbol':'eta_capture','meaning':'Fraction of source cold mass reaching target, for uniform mixing / energy screen','known':'Unmeasured. Independent of area fraction in nonuniform flow.'},
  {'symbol':'mw','meaning':'Warm mass inflow to a well-mixed target, g/s','known':'Unmeasured. Default 5 g/s illustrates dependence; not inferred from CFD.'},
  {'symbol':'beta','meaning':'Vortex cold-branch fraction','known':'Unmeasured; changes together with source cold temperature. EXAIR curve is not Jeanoko calibration.'},
  {'symbol':'eta_stage','meaning':'Isentropic efficiency of EACH modeled expansion stage','known':'No matched turbine specified; 0.6 is an assumption, not overall plant efficiency.'},
  {'symbol':'Pin/Pout','meaning':'Expansion ratio using absolute pressures','known':'Use measured states at expander/regulator after line losses. Not gauge pressure.'},
  {'symbol':'duty','meaning':'Requested on-time / cycle time','known':'Choose demo requirement; supply and storage must satisfy mean mass and energy budget.'}],
 'source_lookup':[], 'reconfiguration_thresholds':[], 'uniform_mass_thresholds':[],
 'backend':{'CoolProp':CoolProp.__version__,'EOS':'HEOS::Air, pseudo-pure dry air','heat_capacity_j_kg_k':CP,
            'FAD_reference':'101325 Pa, 20 C; common reference for comparison',
            'rho_reference_kg_m3':RHO_REF,
            'status':'EOS and floating calculations are not Lean-verified. Single-phase dry-gas screens; no water or frost.'},
 'sources':[
  {'url':'https://lean-lang.org/doc/reference/latest/Introduction/','topic':'Lean proof-checking model; actual project pins Lean 4.31.0'},
  {'url':'https://coolprop.org/coolprop/HighLevelAPI.html','topic':'Pressure/enthalpy and pressure/entropy state calculations; version 8.0.0'},
  {'url':'https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node17.html','topic':'Isenthalpic throttling and energy balance'},
  {'url':'https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node28.html','topic':'Work-producing expansion'},
  {'url':'https://www.bauer-kompressoren.de/de_de/junior-ii','topic':'100 L/min cylinder-fill delivery; 90-330 bar; not direct process-supply approval'}],
 'limits':['Formal implications are conditional on dry constant-property mixing and supplied parameter bounds.',
           'No formal proof of the equations of state, geometry-to-entrainment map, compressor/source map, moisture, turbulence, wind or comfort.',
           'Do not extend the 2 g/s R07 CFD area fraction to new flows/methods as a prediction.',
           'A larger compressor supplies more available inlet mass but one small vortex remains flow-limited.',
           'High-pressure equipment, matched expander selection and subzero drying/icing remain separate engineering work.']}

for tin,pin in itertools.product([25,34,40],[9,11,201]):
 try:r=source_state('real_throttle',tin,pin,1.01325)
 except Exception as e:r={'method':'real_throttle','inlet_temperature_c':tin,'inlet_pressure_bar_abs':pin,'error':str(e)}
 report['source_lookup'].append(r)
 for pmid,eta in itertools.product([1.01325,5,7.9],[.4,.6,.8]):
  try:r=source_state('real_expander',tin,pin,pmid,eta=eta)
  except Exception as e:r={'method':'real_expander','inlet_temperature_c':tin,'inlet_pressure_bar_abs':pin,'expansion_exit_bar_abs':pmid,'per_stage_isentropic_efficiency':eta,'error':str(e)}
  report['source_lookup'].append(r)

for alpha in [.1,.15,.2,.25,.3146377977016922,.4,.5]:
 p=replace(Delivery(),alpha_area=alpha,heat_conductance_w_k=.2)
 r=evaluate(p)
 report['reconfiguration_thresholds'].append({'area_cold_fraction':alpha,
  'source_max_c_at_2g_s_UA_0p2':r['area_model']['required_source_temperature_strictly_below_c'],
  'UA_max_at_2g_s_5C':r['area_model']['maximum_UA_strictly_below_w_k'],
  'minimum_mass_g_s_at_FIXED_alpha_and_5C':r['area_model']['minimum_cold_mass_at_FIXED_alpha_g_s'],
  'source_5C_possible_at_fixed_alpha_even_with_no_line_heat':r['area_model']['possible_at_fixed_alpha_with_zero_line_heat']})
for warm,ua in itertools.product([1,5,10,20],[0,.2]):
 p=replace(Delivery(),warm_mass_g_s=warm,heat_conductance_w_k=ua)
 report['uniform_mass_thresholds'].append({'warm_g_s':warm,'UA_w_K':ua,'capture_fraction':.6,'source_c':5,
    **evaluate(p)['uniform_mass_mixing_model']})

# Independent pressure-stage range is recorded for each lookup, no interpolation.
report['source_examples']=[r for r in report['source_lookup'] if r.get('inlet_temperature_c')==34 and
 (r.get('method')=='real_throttle' or r.get('expansion_exit_bar_abs') in [1.01325,5] and r.get('per_stage_isentropic_efficiency')==.6)]
report['exposure_time_toy_model']={
 'equation':'delta(t)=delta0*exp(-t/tau); pass iff t < tau*ln(delta0/target)',
 'status':'A separate lumped parcel model, IF a positive fitted tau applies. Not a jet prediction or evidence for 0.5 s reheating.',
 'ambient_c':34,'target_drop_c':6,'tau_ASSUMED_s':.5,
 'rows':[{'initial_c':tc,'strict_pass_time_below_s':.5*math.log((34-tc)/6)} for tc in [5,-40,-100]],
 'extra_time_minus100_vs_minus40_s':.5*math.log(134/74)}
(ROOT/'parameter-results.json').write_text(json.dumps(report,indent=2,allow_nan=False))

fig,axes=plt.subplots(1,2,figsize=(13,5.8),layout='constrained')
alphas=np.linspace(.08,.65,240)
for ua in [0,.2,1]:
 r=math.exp(-ua/(.002*CP));ts=34-6/(alphas*r)
 axes[0].plot(alphas*100,ts,label=f'UA={ua:g} W/K; source 2 g/s')
axes[0].axhline(5,color='#4b6472',ls=':',label='Reported 5°C source')
axes[0].axvline(.3146377977016922*100,color='#4b6472',ls='--',label='R07 assumed CFD fraction')
axes[0].set(xlabel='Area-average cold mass fraction (%)',ylabel='Source must be COLDER than this boundary (°C)',ylim=(-100,30),title='Area target: 6°C drop at 34°C ambient')
axes[0].grid(alpha=.2);axes[0].legend(fontsize=8)
flows=np.geomspace(.2,20,220)
for tc in [5,-10,-50]:
 vals=[evaluate(replace(Delivery(),source_c=tc,cold_mass_g_s=float(m),heat_conductance_w_k=.2))['uniform_mass_mixing_model']['drop_c'] for m in flows]
 axes[1].plot(flows,vals,label=f'{tc}°C source')
axes[1].axhline(6,color='#137549',ls='--',label='6°C threshold')
axes[1].axvline(2,color='#4b6472',ls=':',label='Assumed current 2 g/s')
axes[1].set(xlabel='Source cold mass flow (g/s)',ylabel='Uniform-target drop (°C)',xscale='log',title='Alternative uniform mixing model')
axes[1].grid(alpha=.2);axes[1].legend(fontsize=8)
fig.suptitle('Conditional design boundaries · NOT new CFD or measured performance\nArea model and fixed-warm-flow model are different assumptions',fontsize=13)
fig.text(.5,-.01,'Right: fixed 5 g/s warm inflow, 60% cold capture, UA=0.2 W/K. Source flow and temperature are assumed achievable.',ha='center',fontsize=9)
fig.savefig(ROOT/'parameter-boundaries.png',dpi=155,bbox_inches='tight');plt.close(fig)

prooflog=(ROOT/'build.log').read_text() if (ROOT/'build.log').exists() else ''
proofs=re.findall(r"'AA\.([^']+)' depends on axioms: \[([^\]]*)\]",prooflog)
allowed={'propext','Classical.choice','Quot.sound'}
for _,axioms in proofs:assert set(x.strip() for x in axioms.split(',') if x.strip())<=allowed
sources={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in ROOT.rglob('*.lean') if '.lake' not in f.parts}
check={'lean_version':'4.31.0','mathlib_tag':'v4.31.0','mathlib_commit':'fabf563a7c95a166b8d7b6efca11c8b4dc9d911f',
 'build_succeeded':'Build completed successfully' in prooflog,'printed_axiom_checks':len(proofs),
 'theorems':[{'name':name,'foundational_axioms':[x.strip() for x in ax.split(',')]} for name,ax in proofs],
 'source_sha256':sources,'new_physics_axioms':False,'EOS_formally_verified':False,'hardware_validated':False}
for name in sources:
 code=(ROOT/name).read_text()
 assert not re.search(r'^\s*(axiom|sorry|admit)\b|\bby\s+sorry\b',code,re.M)
(ROOT/'proof-verification.json').write_text(json.dumps(check,indent=2))
print(json.dumps({'source_states':len(report['source_lookup']),'source_errors':sum('error'in r for r in report['source_lookup']),
 'proof_checks':len(proofs),'proof_build_success':check['build_succeeded'],
 'baseline_area_drop':report['default_inputs']['area_model']['drop_c'],
 'baseline_uniform_mass_drop':report['default_inputs']['uniform_mass_mixing_model']['drop_c']},indent=2))
