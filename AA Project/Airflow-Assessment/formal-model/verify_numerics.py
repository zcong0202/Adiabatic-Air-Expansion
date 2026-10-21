"""Meaningful limiting-case / conservation checks. Separate from Lean proofs."""
from dataclasses import replace
import math,json
from pathlib import Path
from model import Delivery,evaluate,source_state,uniform_mix_drop,CP,fad_to_mass
from CoolProp.CoolProp import PropsSI

checks={}
def check(name,condition):
    checks[name]=bool(condition)
    if not condition:raise AssertionError(name)

p=Delivery(heat_conductance_w_k=0)
a=evaluate(p)
check('matches_saved_area_fraction_identity',abs(a['area_model']['drop_c']-29*p.alpha_area)<1e-12)
check('fixed_area_fraction_poor_delivery_fails',not evaluate(replace(p,alpha_area=.15))['area_model']['strict_pass'])
check('cold_source_too_warm_cannot_pass',evaluate(replace(p,source_c=30))['uniform_mass_mixing_model']['required_source_mass_strictly_above_g_s'] is None)
check('warmer_entrained_air_reduces_area_drop',evaluate(replace(p,entrained_c=40))['area_model']['drop_c']<a['area_model']['drop_c'])
check('positive_line_heat_reduces_drop',evaluate(replace(p,heat_conductance_w_k=.5))['area_model']['drop_c']<a['area_model']['drop_c'])
q=Delivery(heat_conductance_w_k=.2);root=evaluate(q)['uniform_mass_mixing_model']['required_source_mass_strictly_above_g_s']/1000
check('required_mass_root_brackets_strict_target',uniform_mix_drop(q,root*.999)<6<uniform_mix_drop(q,root*1.001))
q0=replace(q,heat_conductance_w_k=0,extra_heat_w=0)
d1=evaluate(q0)['uniform_mass_mixing_model']['drop_c'];d2=evaluate(replace(q0,cold_mass_g_s=q0.cold_mass_g_s*4,warm_mass_g_s=q0.warm_mass_g_s*4))['uniform_mass_mixing_model']['drop_c']
check('scaling_both_mass_flows_no_temperature_gain',abs(d1-d2)<1e-12)
ua=a['area_model']['maximum_UA_strictly_below_w_k']
check('formal_heat_bound_matches_direct_equation',evaluate(replace(p,heat_conductance_w_k=ua*.999))['area_model']['strict_pass'] and not evaluate(replace(p,heat_conductance_w_k=ua*1.001))['area_model']['strict_pass'])
s=source_state('ideal_throttle',34,201,5)
check('ideal_gas_regulator_has_no_bulk_temperature_drop',abs(s['final_source_temperature_c']-34)<1e-12)
s=source_state('real_throttle',34,201,5)
hin=PropsSI('Hmass','T',307.15,'P',201e5,'HEOS::Air')
hout=PropsSI('Hmass','T',s['final_source_temperature_c']+273.15,'P',101325,'HEOS::Air')
check('real_regulator_enthalpy_balance',abs(hin-hout)<1e-5)
zero=source_state('real_expander',34,201,5,eta=0)
check('zero_efficiency_expander_equals_throttle',abs(zero['final_source_temperature_c']-s['final_source_temperature_c'])<1e-8)
full=source_state('real_expander',34,201,5,eta=.6)
hout=PropsSI('Hmass','T',full['final_source_temperature_c']+273.15,'P',101325,'HEOS::Air')
# Independent P,T -> h round-trip flash has finite numeric tolerance.
energy_residual=hin-hout-full['shaft_work_j_kg']
check('expander_shaft_work_equals_enthalpy_reduction',abs(energy_residual)<1e-3)
check('four_stages_needed_for_201_to_5_at_ratio_3',full['expander_stage_count']==4)
check('each_stage_respects_assumed_ratio',all(x/y<=3+1e-10 for x,y in zip([201]+[x['pressure_bar_abs'] for x in full['states'][:-2]],[x['pressure_bar_abs'] for x in full['states'][:-1]])))
check('bauer_current_vortex_continuous_budget_fails',not evaluate(replace(p,supply_fad_lpm=100))['supply']['full_flow_continuous_feasible_ideal_mass_budget'])
check('bauer_50_percent_ideal_duty_bound',evaluate(replace(p,supply_fad_lpm=100))['supply']['maximum_ideal_average_duty']==.5)
check('oversized_supply_does_not_change_one_vortex_temperature',evaluate(replace(p,supply_fad_lpm=1100))['area_model']['drop_c']==a['area_model']['drop_c'])
check('flow_conversion_is_common_reference_not_compressed_litres',abs(fad_to_mass(100)*1000-2.0068638606243594)<1e-12)
check('energy_budget_does_not_imply_area_success',evaluate(replace(p,alpha_area=.15))['target_energy_necessary_bound']['necessary_budget_pass'] and not evaluate(replace(p,alpha_area=.15))['area_model']['strict_pass'])

result={'checks':checks,'passed':all(checks.values()),'count':len(checks),'EOS_round_trip_energy_residual_j_kg':energy_residual,'EOS_round_trip_energy_tolerance_j_kg':1e-3,'not_a_formal_numeric_proof':True,'physical_validation':False}
(Path(__file__).parent/'numerical-verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
