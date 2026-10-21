"""Numerical companion to AA's Lean theorems. Floats/EOS are not Lean proofs.

Dry, constant-cp delivery/mixing screen. Source EOS evaluations are separate
CoolProp calculations; no empirical source/entrainment map is manufactured.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, asdict, replace
from typing import Any

CP = 1005.0
R_AIR = 287.05
P_REF = 101325.0
T_REF = 293.15
RHO_REF = P_REF / (R_AIR * T_REF)

def fad_to_mass(lpm: float) -> float:
    if lpm < 0: raise ValueError('Free-air delivery must be nonnegative.')
    return lpm / 60000 * RHO_REF

def mass_to_fad(mass: float) -> float:
    return mass / RHO_REF * 60000

@dataclass(frozen=True)
class Delivery:
    ambient_c: float = 34.0
    entrained_c: float = 34.0
    source_c: float = 5.0
    cold_mass_g_s: float = 2.0
    heat_conductance_w_k: float = 0.0
    alpha_area: float = 0.3146377977016922
    target_drop_c: float = 6.0
    capture_fraction: float = 0.6
    warm_mass_g_s: float = 5.0
    extra_heat_w: float = 0.0
    target_width_m: float = 0.05
    target_height_m: float = 0.05
    minimum_normal_speed_m_s: float = 1.0
    supply_fad_lpm: float = 200.0
    demand_fad_lpm: float = 200.0
    requested_duty: float = 1.0
    pulse_s: float = 3.0
    cold_fraction: float = 0.5

    def validate(self):
        if not all(math.isfinite(x) for x in asdict(self).values()):
            raise ValueError('All inputs must be finite.')
        if min(self.ambient_c,self.entrained_c,self.source_c) <= -273.15:
            raise ValueError('Temperature must exceed absolute zero.')
        if self.entrained_c < self.ambient_c:
            raise ValueError('This screening envelope requires entrained air at least as warm as reference ambient.')
        if self.cold_mass_g_s <= 0 or self.target_drop_c <= 0:
            raise ValueError('Cold flow and target drop must be positive.')
        if not (0 <= self.alpha_area <= 1 and 0 < self.capture_fraction <= 1):
            raise ValueError('Area fraction must be 0..1; capture must be >0 and <=1.')
        if not (0 < self.cold_fraction <= 1 and 0 < self.requested_duty <= 1):
            raise ValueError('Cold fraction and requested duty must be >0 and <=1.')
        if min(self.heat_conductance_w_k,self.warm_mass_g_s,self.extra_heat_w,
               self.supply_fad_lpm,self.demand_fad_lpm,self.pulse_s) < 0:
            raise ValueError('Loads, flows, heat conductance and duration must be nonnegative.')
        if min(self.target_width_m,self.target_height_m,self.minimum_normal_speed_m_s) <= 0:
            raise ValueError('Target dimensions and the assumed normal-speed lower bound must be positive.')

def delivery_state(p: Delivery, mass_kg_s: float | None = None) -> dict[str,float]:
    m = p.cold_mass_g_s/1000 if mass_kg_s is None else mass_kg_s
    r = math.exp(-p.heat_conductance_w_k/(m*CP))
    td = p.entrained_c-(p.entrained_c-p.source_c)*r
    return {'retention':r,'delivery_c':td,
            'sensible_potential_w':m*CP*(p.ambient_c-td)}

def uniform_mix_drop(p: Delivery, source_mass: float) -> float:
    td=delivery_state(p,source_mass)['delivery_c']
    captured=p.capture_fraction*source_mass;warm=p.warm_mass_g_s/1000
    mixed=(captured*td+warm*p.entrained_c+p.extra_heat_w/CP)/(captured+warm)
    return p.ambient_c-mixed

def minimum_mass_for_fixed_warm_load(p: Delivery) -> float | None:
    """Strict pass is m > root, with fixed warm inflow/capture/source state.
    Includes the mass dependence of hose retention. Not a jet/source map.
    """
    if p.ambient_c-p.source_c <= p.target_drop_c: return None
    lo=1e-10;hi=max(.001,p.cold_mass_g_s/1000)
    while uniform_mix_drop(p,hi) <= p.target_drop_c and hi < 1e3: hi*=2
    if hi >= 1e3: return None
    for _ in range(100):
        mid=(lo+hi)/2
        if uniform_mix_drop(p,mid)>p.target_drop_c: hi=mid
        else: lo=mid
    return (lo+hi)/2

def evaluate(p: Delivery) -> dict[str,Any]:
    p.validate();state=delivery_state(p);m=p.cold_mass_g_s/1000
    span=p.entrained_c-p.source_c;needed=p.target_drop_c+p.entrained_c-p.ambient_c
    retained_span=span*state['retention']
    drop=p.ambient_c-p.entrained_c+p.alpha_area*retained_span
    alpha_min=needed/retained_span if retained_span>0 else None
    b=p.alpha_area*span
    log_margin=math.log(b/needed) if b>0 and needed>0 else None
    ua_max=m*CP*log_margin if log_margin is not None and log_margin>0 else None
    fixed_alpha_mass=p.heat_conductance_w_k/(CP*log_margin) if log_margin is not None and log_margin>0 else None
    source_max=p.entrained_c-needed/(p.alpha_area*state['retention']) if p.alpha_area*state['retention']>0 else None
    mass_min=minimum_mass_for_fixed_warm_load(p)
    total_target_mass=P_REF/(R_AIR*(p.ambient_c+273.15))*p.target_width_m*p.target_height_m*p.minimum_normal_speed_m_s
    required_flux_power=total_target_mass*CP*p.target_drop_c
    captured_budget=p.capture_fraction*state['sensible_potential_w']-p.extra_heat_w
    max_duty=min(1,p.supply_fad_lpm/p.demand_fad_lpm) if p.demand_fad_lpm>0 else 1
    deficit_fad=max(0,p.demand_fad_lpm-p.supply_fad_lpm)
    buffer_mass=fad_to_mass(deficit_fad)*p.pulse_s
    return {'inputs':asdict(p),'cold_path':state,
      'area_model':{'drop_c':drop,'target_air_c':p.ambient_c-drop,
        'strict_pass':drop>p.target_drop_c,
        'required_alpha_strictly_above':alpha_min,
        'required_source_temperature_strictly_below_c':source_max,
        'maximum_UA_strictly_below_w_k':ua_max,
        'minimum_cold_mass_at_FIXED_alpha_g_s':None if fixed_alpha_mass is None else fixed_alpha_mass*1000,
        'possible_at_fixed_alpha_with_zero_line_heat':b>needed,
        'status':'Conditional area-mean identity. Alpha is an independent measured/assumed input, not predicted by this calculator.'},
      'uniform_mass_mixing_model':{'drop_c':uniform_mix_drop(p,m),
        'strict_pass':uniform_mix_drop(p,m)>p.target_drop_c,
        'required_source_mass_strictly_above_g_s':None if mass_min is None else mass_min*1000,
        'equivalent_source_inlet_FAD_lpm_at_chosen_cold_fraction':None if mass_min is None else mass_to_fad(mass_min)/p.cold_fraction,
        'status':'Different model: a well-mixed target with fixed incoming warm mass flow and capture fraction. Not automatically equal to the nonuniform CFD area mean.'},
      'target_energy_necessary_bound':{'area_m2':p.target_width_m*p.target_height_m,
        'required_cold_deficit_flux_w':required_flux_power,
        'captured_cold_budget_after_extra_load_w':captured_budget,
        'necessary_budget_pass':captured_budget>required_flux_power,
        'status':'Necessary only, assuming local temperature deficits nonnegative and normal speed everywhere >= specified lower bound. Neither velocity assumption nor capture is measured.'},
      'supply':{'maximum_ideal_average_duty':max_duty,
        'requested_duty_feasible_ideal_mass_budget':p.requested_duty*p.demand_fad_lpm<=p.supply_fad_lpm,
        'full_flow_continuous_feasible_ideal_mass_budget':p.demand_fad_lpm<=p.supply_fad_lpm,
        'minimum_inlet_air_inventory_swing_g_for_pulse':buffer_mass*1000,
        'status':'Common free-air basis, no losses. Compressor duty and actual pressure/flow match still require approval/measurement. Inventory is a mass requirement, not a tank design.'},
      'physical_validation':False,'new_CFD':False}

def source_state(method: str, tin_c: float, pin_bar_abs: float,
                 expansion_exit_bar_abs: float, delivery_bar_abs: float=1.01325,
                 eta: float=.6, maximum_stage_ratio: float=3.,
                 gamma: float=1.4) -> dict[str,Any]:
    """Per-stage efficiency; final regulator is isoenthalpic. Low-velocity states.
    For real-gas calculations use CoolProp HEOS pseudo-pure dry Air, no water.
    """
    tin=tin_c+273.15
    if tin<=0 or not (pin_bar_abs>=expansion_exit_bar_abs>=delivery_bar_abs>0):
        raise ValueError('Use Kelvin-positive temperature and Pin >= expansion exit >= final pressure > 0, all absolute.')
    if not(0<=eta<=1) or maximum_stage_ratio<=1 or gamma<=1:
        raise ValueError('Require 0 <= per-stage efficiency <=1, stage ratio limit >1, gamma >1.')
    n=0 if pin_bar_abs==expansion_exit_bar_abs else max(1,math.ceil(math.log(pin_bar_abs/expansion_exit_bar_abs)/math.log(maximum_stage_ratio)-1e-12))
    pressures=[pin_bar_abs*(expansion_exit_bar_abs/pin_bar_abs)**(i/n) for i in range(n+1)] if n else [pin_bar_abs]
    states=[];work=0.;tout=tin
    if method=='ideal_throttle':
        tout=tin;states=[{'pressure_bar_abs':delivery_bar_abs,'temperature_c':tin_c}]
    elif method=='ideal_expander':
        for pi,po in zip(pressures,pressures[1:]):
            ti=tout;ts=ti*(po/pi)**((gamma-1)/gamma);tout=ti-eta*(ti-ts)
            work+=CP*(ti-tout);states.append({'pressure_bar_abs':po,'temperature_c':tout-273.15})
        # Ideal-gas final regulator: no extra bulk temperature reduction.
    elif method in ['real_throttle','real_expander']:
        from CoolProp.CoolProp import PropsSI,PhaseSI
        fluid='HEOS::Air'
        h=PropsSI('Hmass','T',tin,'P',pin_bar_abs*1e5,fluid)
        if method=='real_expander':
            for pi,po in zip(pressures,pressures[1:]):
                entropy=PropsSI('Smass','Hmass',h,'P',pi*1e5,fluid)
                hs=PropsSI('Hmass','Smass',entropy,'P',po*1e5,fluid)
                hn=h-eta*(h-hs);work+=h-hn;h=hn
                t=PropsSI('T','Hmass',h,'P',po*1e5,fluid)
                phase=PhaseSI('Hmass',h,'P',po*1e5,fluid)
                if phase=='twophase':raise ValueError('Two-phase expansion excluded from the dry gas screen.')
                states.append({'pressure_bar_abs':po,'temperature_c':t-273.15,'phase':phase})
        tout=PropsSI('T','Hmass',h,'P',delivery_bar_abs*1e5,fluid)
        phase=PhaseSI('Hmass',h,'P',delivery_bar_abs*1e5,fluid)
        if phase=='twophase':raise ValueError('Two-phase final state excluded.')
        states.append({'pressure_bar_abs':delivery_bar_abs,'temperature_c':tout-273.15,'phase':phase})
    else:raise ValueError('Unknown method.')
    return {'method':method,'inlet_temperature_c':tin_c,'inlet_pressure_bar_abs':pin_bar_abs,
      'expansion_exit_bar_abs':expansion_exit_bar_abs,'delivery_bar_abs':delivery_bar_abs,
      'per_stage_isentropic_efficiency':eta,'maximum_stage_ratio_ASSUMED':maximum_stage_ratio,
      'expander_stage_count':n if 'expander' in method else 0,
      'final_source_temperature_c':tout-273.15,'shaft_work_j_kg':work,
      'states':states,'status':'Hypothetical dry source thermodynamics, not a matched expander, pressure system, or measured performance. EOS not formally verified in Lean. No water/icing or interstage heat pickup.'}

if __name__=='__main__':
    import json
    print(json.dumps(evaluate(Delivery()),indent=2))
