"""First-principles supply/pressure/energy screens. No installed-flow guarantee."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1];c=json.loads((ROOT/'config.json').read_text());rho=101325/(287.05*293.15);m=227/60000*rho
rows=[]
for o in c['compression_options']:
 q=o['flow_lpm'];rows.append({'id':o['id'],'name':o['name'],'ideal_max_single_vortex_duty':min(1,q/227),'single_vortex_continuous_mass_budget':q>=227,'maximum_whole_vortices_ideal_flow_only':int(q//227),'inlet_inventory_swing_g_3second_pulse':max(0,227-q)/60000*rho*3*1000,'status':o['status']})
for d in [.008,.010,.012]:
 area=math.pi*d*d/4;density=7.9e5/(287.05*307.15);v=m/(density*area);re=4*m/(math.pi*d*1.8e-5);f=.3164/re**.25;dp=f*10/d*density*v*v/2
 rows.append({'hose_id_mm':d*1000,'upstream_compressed_hose_length_m':10,'assumed_mean_pressure_bar_abs':7.9,'darcy_pressure_drop_bar':dp/1e5,'speed_m_s':v,'Re':re,'limits':'Smooth turbulent Darcy screen at mean density; fittings, dryer and regulator losses excluded.'})
p2=101325+100*6894.757;wmin=m*287.05*307.15*math.log(p2/101325)
energy=[{'beta':b,'source_sensible_potential_w':m*b*1005*drop*5/9,'isothermal_compression_lower_bound_w':wmin,'cold_potential_over_min_compression_work':m*b*1005*drop*5/9/wmin} for b,drop in zip(c['source']['cold_fractions'],c['source']['temperature_drop_f'])]
report={'source_demand_reference_lpm':227,'common_density_reference_ASSUMED':rho,'results':rows,'source_energy_screens':energy,'energy_limits':'Isothermal ideal-gas compression lower bound from atmosphere to source inlet, aftercooled state 34 C. Not total electrical power, actual COP, skin cooling, or a complete plant model. BAUER high-pressure regulation and hose heating are not credited as unmodeled source precooling.','no_physical_validation':True}
report['smaller_stock_sources_UNTESTED_CFD']=[{'model':model,'inlet_reference_lpm':q,'ideal_BAUER_100Lpm_duty':min(1,100/q),'cold_mass_g_s_at_beta_0p6_ASSUMED_reference':q/60000*rho*.6*1000,'status':'Supplier family catalogue option. Source-map applicability, source port and target CFD are not checked for this model. Smaller flow may change buoyancy and reach.'} for model,q in [('3202',57),('3204',113),('3208',227)]]
(ROOT/'results/supply-screen.json').write_text(json.dumps(report,indent=2));print(json.dumps(energy,indent=2))
