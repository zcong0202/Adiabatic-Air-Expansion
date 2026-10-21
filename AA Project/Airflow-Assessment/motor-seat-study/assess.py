"""Reproducible dry first-law and humid-mixing screens; NOT motor-map/seat CFD."""
from pathlib import Path
import json,math,hashlib,zipfile,xml.etree.ElementTree as E
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import CoolProp
from CoolProp.CoolProp import PropsSI as P
from CoolProp.HumidAirProp import HAPropsSI as HA
R=Path(__file__).resolve().parent; OUT=R/'results'; OUT.mkdir(exist_ok=True)
CP=1006.; GAS=287.05; PA=101325.; MDOT=4*.0194; C=MDOT*CP; POWER=4*840.; FAD=4*16.2*60/1000
sources={
'motor':'https://www.atlascopco.com/en-us/itba/products/air-motors/lzb46-rl-a025-11-sku8411047249',
'motor_manual':'https://picontent.atlascopco.com/cont/external/dir/0e/410867083_B4770001_html5_external/en-US/print-section.html?section=all',
'motor_rating_basis':'https://www.atlascopco.com/en-us/itba/industry-solutions/airmotors/technicalguide/catalogue-performance',
'motor_consumption':'https://www.atlascopco.com/en-us/itba/industry-solutions/airmotors/technicalguide/performance',
'compressor':'https://www.atlascopco.com/en-ae/construction-equipment/products/mobile-air-compressors/ready-to-go-compressor-range/xas-lrc-range',
'compressor_brochure':'https://www.atlascopco.com/content/dam/atlas-copco/construction-technique/portable-energy/documents/1_compressors/diesel-range/8-series-lrc/small-air-lrc-range-brochure.pdf'}
doc=R.parent.parent/'Project-Documents/CFD inputs outdoor cooling seat (rental compressor + 4 × LZB46).docx'
if not doc.exists(): doc=R/'evidence/source-environment.docx'
with zipfile.ZipFile(doc) as z:
 root=E.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 paras=[''.join(y.text or '' for y in x.findall('.//w:t',ns)) for x in root.findall('.//w:p',ns)]
(R/'evidence/environment-extract.txt').write_text('\n'.join(paras))
def state(ta=30,tin=40,load_fraction=1,gain=4,extra_heat=0):
 w=POWER*load_fraction; tm=tin-(w-extra_heat)/C; ts=tm+gain
 return dict(ambient_c=ta,inlet_c=tin,shaft_fraction=load_fraction,shaft_w=w,motor_exhaust_c=tm,supply_c=ts,
  sensible_cooling_w=C*(ta-ts),inlet_within_40c=tin<=40,
  heat_capacity_w_k=C,mass_kg_s=MDOT,duct_gain_k=gain,extra_heat_w=extra_heat)
def zone(s,target=20,load=100,capture=1,returned_work_fraction=0,wind=1,cd=1):
 ta=s['ambient_c'];dt=ta-target; q=capture*s['sensible_cooling_w']; cc=capture*C
 heat=load+returned_work_fraction*s['shaft_w']; head=q-cc*dt-heat
 rho=PA/(GAS*(ta+273.15)); warm=head/(CP*dt)
 return dict(target_c=target,net_heat_w=heat,cold_capture=capture,shaft_work_return_fraction=returned_work_fraction,
  target_headroom_w=head,max_warm_kg_s=warm,max_warm_m3_s=warm/rho,
  max_effective_wind_area_m2=warm/(rho*wind*cd),wind_m_s=wind,exchange_coefficient=cd,
  interpretation='Negative bound means impossible even with zero warm inflow in this uniform dry model.')
base=state(); rho=PA/(GAS*274.15); Q=MDOT/rho
models=[('XAS 38',7,2),('XAS 48',7,2.5),('XAS 58',7,3),('XAS 68',7,3.6),('XAS 78',7,4.5),('XAS 88',7,5),('XAS 98',7,5.4),('XAHS 38',12,2),('XATS 68',10.3,3.6)]
supply=[dict(model=n,pressure_bar_g=p,fad_m3_min=q,ideal_four_motor_duty=min(1,q/FAD),spare_fraction_of_demand=q/FAD-1,
 pass_15pct_engineering_allowance=q>=1.15*FAD) for n,p,q in models]
# Motor and brochure rating references need harmonising before procurement. 19.4 g/s per motor is the source document's nominal conversion.
# Optional dry real-gas cross-check. The net specific shaft work is fixed by the catalogue pair, not an independent eta guess.
pin=PA+6.3e5;tin=313.15;h=P('H','T',tin,'P',pin,'Air');ss=P('S','T',tin,'P',pin,'Air');his=P('H','P',PA,'S',ss,'Air')
eos=dict(backend='CoolProp '+CoolProp.__version__+' HEOS::Air',inlet_pa=pin,inlet_k=tin,
 isentropic_outlet_c=P('T','P',PA,'S',ss,'Air')-273.15,
 effective_shaft_isentropic_efficiency=(POWER/MDOT)/(h-his),
 loaded_exhaust_c=P('T','P',PA,'H',h-POWER/MDOT,'Air')-273.15,
 throttle_exhaust_c=P('T','P',PA,'H',h,'Air')-273.15)
eos['loaded_supply_after_4k_c']=eos['loaded_exhaust_c']+4
outlets=[]
for name,area,dh,frac in [('A perforated open holes',.1,.01,1),('A face average',.5,None,1),('B 150 mm duct',math.pi*.15**2/4,.15,1),('C four 70 mm nozzles',4*math.pi*.07**2/4,.07,1),('D plate holes',.1,.01,.8),('D two 50 mm neck outlets',2*math.pi*.05**2/4,.05,.2)]:
 v=Q*frac/area
 outlets.append(dict(name=name,area_m2=area,fraction=frac,speed_m_s=v,dynamic_head_pa=rho*v*v/2,
  archimedes=None if dh is None else 9.81*(30-1)/303.15*dh/v**2,
  note='Hole diameter for A/D = assumed 10 mm for Ar only; source document gives no hole pattern.'))
branches=[]
for d in [.016,.032,.04,.05]:
 v=Q/4/(math.pi*d*d/4);dyn=.5*rho*v*v
 branches.append(dict(id_mm=d*1000,speed_m_s=v,dynamic_head_pa=dyn,one_m_straight_loss_pa=.02/d*dyn,
  status='Darcy f=0.02 assumed; incompressible screen, not a compressible network solution. Dynamic head is not all irreversible loss.'))
hum=[]
# pressure dew point +3 C converted using enhanced humid-air partial pressure, all mixtures by dry-air mass.
pv=HA('P_w','T',276.15,'P',pin,'R',1);wc=.621945*pv/(pin-pv)
for ta in [30,35]:
 wa=HA('W','T',ta+273.15,'P',PA,'R',.55)
 for tc in [-3,1,8]:
  hc=HA('H','T',tc+273.15,'P',PA,'W',wc);ha=HA('H','T',ta+273.15,'P',PA,'W',wa)
  values=[]
  for a in np.linspace(0,1,1001):
   w=float(a)*wc+(1-float(a))*wa; ent=float(a)*hc+(1-float(a))*ha
   t=HA('T','H',ent,'P',PA,'W',w); rh=HA('R','T',t,'P',PA,'W',w)
   values.append((rh,float(a)))
  peak=max(values)
  hum.append(dict(ambient_c=ta,ambient_rh=.55,supply_c=tc,supply_w=wc,ambient_w=wa,max_mix_rh=peak[0],cold_dry_mass_fraction_at_peak=peak[1]))
report=dict(date='2026-10-19',status='Conditional mathematical viability. No seat CFD, hardware validation, or vendor motor thermal map.',
 sources=sources,environment_sha256=hashlib.sha256(doc.read_bytes()).hexdigest(),
 assumptions=dict(motors='Four in parallel, not series; exhaust all collected.',mass_basis='Source document: 19.4 g/s each. 16.2 atmospheric L/s each is confirmed; exact reference temperature/humidity not stated on product page.',
  inlet='6.3 bar gauge,40 C; catalogue output/consumption pair at loaded maximum power.',
  motor_heat_w=0,duct_gain_k=4,cp_j_kg_k=CP,ambient_pressure_pa=PA,source_flow_is_coupled_to_load=True,
  shaft_sink='External load extracts power; its dissipated heat is excluded from seat and cold path.',zone='Dry, steady, uniform; all source captured unless stated; 100 W net heat to zone; no solar/panel load in baseline.'),
 baseline=base,free_air_demand_m3_min=FAD,actual_supply_m3_s=Q,source_contrast_k=30-base['supply_c'],
 compressor_screen=supply,real_gas_crosscheck=eos,
 target_20c=zone(base),target_delta6=zone(base,target=24),
 wind_limits=[zone(base,wind=v) for v in [.5,1]],
 supply_heat_limits=dict(total_motor_plus_duct_heat_w_for_supply_1c=POWER-C*39,
  total_motor_plus_duct_heat_w_for_supply_8c=POWER-C*32,
  shaft_w_for_supply_1c=C*43,shaft_w_for_supply_8c=C*36,
  required_shaft_nm_at_1270rpm_for_1c_each=C*43/4/(1270*2*math.pi/60)),
 scenarios=[state(load_fraction=x) for x in [0,.5,.75,1]]+[state(ta=35,tin=45),state(ta=35,tin=40)],
 zone_scenarios=[dict(name=n,**zone(base,load=l,capture=k,returned_work_fraction=r)) for n,l,k,r in [('baseline',100,1,0),('50% capture',100,.5,0),('100W occupant + 500W sun/panels',600,1,0),('all shaft heat returned',100,1,1)]],
 outlets=outlets,exhaust_branch_screens=branches,humidity_mixing_checks=hum,
 historical_nozzle=dict(status='Geometry must be rescaled and re-solved. Prior CFD is not evidence for this source/seat.',per_branch_28mm_exit_speed_m_s=Q/4/(math.pi*.028**2/4),per_branch_8mm_throat_incompressible_speed_m_s=Q/4/(math.pi*.008**2/4)),
 plant_limit=dict(xas78_engine_rating_kw=33,cooling_over_engine_nameplate=base['sensible_cooling_w']/33000,
  interpretation='Not measured fuel COP. Actual fuel energy, part-load use, drying auxiliaries and load recovery unknown.'),
 limits=['No manufacturer exhaust temperature or refrigeration efficiency guarantee found.',
  'No matched commercial shaft load, load controller, dryer, aftercooler or exhaust collector selected.',
  'Product web page says 7 bar max; model-specific ATEX manual says 6.3 bar/nameplate. Use stricter 6.3 until supplier resolves.',
  'A refrigerated dryer is not established as part of compressor rental. Aftercooler and water separator do not establish +3 C pressure dew point.',
  '35 C plus 10 K inlet rise violates 40 C inlet limit; improve aftercooling, do not accept it as an approved case.',
  'Moist mixing check supports no fog only for stated dry source, ambient 55% RH and sampled temperatures; not internal motor icing or wet surfaces.',
  'Wind area = Cd*A exchange model; not seat geometry or a guarantee. Buoyancy and wind exchange need 3D variable-density CFD.',
  '100 W human load and fixed 34 C skin boundary are different models. Do not impose both as independent fixed conditions.',
  'Cooling capacity is air enthalpy deficit, not human heat removal or comfort.'])
(OUT/'assessment.json').write_text(json.dumps(report,indent=2,allow_nan=False))
# Engineering plots.
fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
fractions=np.linspace(0,1,101)
ax[0].plot(fractions*100,[state(load_fraction=float(f))['supply_c'] for f in fractions],color='#096f73',lw=2)
ax[0].axhline(20,color='#af452d',ls='--');ax[0].axhline(1,color='#596f7c',ls=':');ax[0].set(xlabel='Extracted shaft power / catalogue maximum (%)',ylabel='Supply temperature (°C)',title='Shaft work controls source cooling')
ax[0].text(.04,.96,'Rated flow held fixed for sensitivity only.\nNot a motor operating curve.\nInlet 40°C; +4 K duct rise.',transform=ax[0].transAxes,va='top',fontsize=9)
areas=np.linspace(0,1,200);rho_a=PA/(GAS*303.15)
for v in [.5,1]:
 vals=(C*base['supply_c']+rho_a*areas*v*CP*30+100)/(C+rho_a*areas*v*CP)
 ax[1].plot(areas,vals,label=f'{v} m/s wind; Cd=1')
ax[1].axhline(20,color='#af452d',ls='--',label='20°C target');ax[1].set(xlabel='Effective wind exchange area (m²)',ylabel='Uniform zone air temperature (°C)',title='Shelter controls ambient heat influx');ax[1].legend(fontsize=9)
for a in ax:a.grid(alpha=.18)
fig.suptitle('First-law screens · not CFD or measured performance',fontsize=14)
fig.savefig(OUT/'viability-boundaries.png',dpi=180);plt.close(fig)
checks=[]
def check(n,v):
 checks.append(dict(name=n,passed=bool(v)));assert v,n
check('four motors FAD = 3.888 m3/min',abs(FAD-3.888)<1e-12)
check('torque-speed agrees with catalogue power within 1%',abs(6.3*1270*2*math.pi/60-840)/840<.01)
check('nominal source 0.9 to 1.1 C',.9<base['supply_c']<1.1)
check('nominal sensible cooling 2.2 to 2.4 kW',2200<base['sensible_cooling_w']<2400)
check('first-law identity',(abs(C*(40-base['motor_exhaust_c'])-POWER)<1e-8))
check('zone boundary closes',abs(C*(20-base['supply_c'])-report['target_20c']['max_warm_kg_s']*CP*10-100)<1e-8)
check('equal target boundary gives 20 C',abs((C*base['supply_c']+CP*report['target_20c']['max_warm_kg_s']*30+100)/(C+CP*report['target_20c']['max_warm_kg_s'])-20)<1e-10)
check('minimum rated compressor with 15% allowance is XAS78',[s['model'] for s in supply if s['pass_15pct_engineering_allowance']][0]=='XAS 78')
check('EOS effective eta agrees with assumed 25-40%',.25<eos['effective_shaft_isentropic_efficiency']<.4)
check('all shaft heat return prevents net cooling',report['zone_scenarios'][-1]['target_headroom_w']<0)
check('nominal humid mixing remains unsaturated',all(x['max_mix_rh']<1 for x in hum))
check('35+10 violates manual inlet temperature',not report['scenarios'][-2]['inlet_within_40c'])
check('all temperature/flow results finite',all(math.isfinite(s['supply_c']) for s in report['scenarios']))
proof=json.loads((R.parent/'formal-model/proof-verification.json').read_text()) if (R.parent/'formal-model/proof-verification.json').exists() else {}
(OUT/'verification.json').write_text(json.dumps(dict(checks=checks,all_passed=True,software=dict(CoolProp=CoolProp.__version__,numpy=np.__version__),proof_reference='../formal-model/proof-verification.json'),indent=2))
print(json.dumps(dict(baseline=base,zone=report['target_20c'],source_heat_limits=report['supply_heat_limits'],checks=len(checks)),indent=2))
