"""Outdoor pass-by timing and energy screens. No jet CFD or comfort claim."""
from pathlib import Path
import json,math

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'pass-by-study/results'
OUT.mkdir(parents=True, exist_ok=True)
inputs=json.loads((ROOT/'pass-by-study/source-input.json').read_text())
mass=inputs['active_motors']*inputs['mass_per_motor_kg_s']
ta,cp=inputs['ambient_c'],inputs['cp_j_kg_k']
shaft=inputs['active_motors']*inputs['shaft_work_per_motor_w']
motor=inputs['inlet_c']-(shaft-inputs['motor_heat_into_air_w'])/(mass*cp)
ts=ta+(motor-ta)*math.exp(-inputs['cold_path_ua_w_k']/(mass*cp))
pressure,gas=101325.,287.05
power = mass * cp * (ta-ts)
rho = pressure / (gas*(ts+273.15))
distances = [.2, .35, .5]
speed = 1.2
data = {
    'status': 'First-principles and kinematic screen only; no pass-by CFD run',
    'confirmed': {'outdoor': True, 'no_seat_or_enclosure': True,
                  'nozzle_person_distance_m': {'minimum_study': .2, 'maximum': .5},
                  'layout': 'undecided; compare', 'valve_max_open_s': 30,
                  'person_motion': 'walks past; does not stay for the valve duration'},
    'assumptions': {'walking_speed_m_s': speed, 'walking_speed_sensitivity_m_s': [.6,1.2,1.8],
                    'distance_sweep_m': distances,
                    'effective_cooled_widths_m': [.05,.14,.3,.5],
                    'width_note': 'Hypothetical widths along walking path. Not predicted nozzle reach or observed cooling footprint.',
                    'source_note': 'Loaded-motor first-law state calculated from source-input.json. No seat temperature result is used.',
                    'source_requirements': 'Sustained catalogue load/flow pair, 40 C inlet, external shaft heat sink, nominal motor heat pickup zero, cold-path UA about 10.074 W/K. No supplier thermal guarantee.',
                    'pulse_note': 'Ideal full nominal flow and source temperature throughout valve opening. Motor spin-up, line cooldown, valves and collectors are not resolved.'},
    'source_budget': {'active_motors':inputs['active_motors'], 'mass_kg_s':mass, 'supply_c':ts, 'inlet_c':inputs['inlet_c'], 'shaft_work_w':shaft,
                      'ambient_c':ta, 'cp_j_kg_k':cp, 'cold_air_power_w':power,
                      'free_air_demand_m3_min':3.888,
                      'nominal_flow_per_four_equal_outlets_kg_s':mass/4},
    'pulse_budgets': [dict(valve_open_s=t, cold_air_mass_kg=mass*t,
                          free_air_m3=3.888*t/60, supply_volume_m3=mass/rho*t,
                          available_cold_air_energy_j=power*t)
                      for t in [1,5,10,30]],
    'crossing_times': [dict(effective_cooled_width_m=w, walking_speed_m_s=v,
                           ideal_geometric_crossing_s=w/v)
                       for w in [.05,.14,.3,.5] for v in [.6,1.2,1.8]],
    'jet_travel_scales': [dict(distance_m=d, representative_speed_m_s=u,
                              travel_scale_s=d/u)
                          for d in distances for u in [1,2,5]],
    'mixing_necessary_condition': {
        'model': 'Dry adiabatic two-stream mixing; same cp; no local heat input. Strict greater-than target requires strict inequalities.',
        'target_delta_k':6., 'source_contrast_k':ta-ts,
        'minimum_cold_mass_fraction_for_delta6':6/(ta-ts),
        'maximum_warm_to_cold_mass_ratio_for_delta6':(ta-ts)/6-1,
        'caveat': 'A necessary local enthalpy condition. Not a predicted volume, reach, exposure or comfort result. An area-average sample requires its own resolved field.'},
    'candidate_matrix': [dict(layout=layout, distance_m=d,
                             total_mass_kg_s=mass, total_cold_air_power_w=power,
                             status='proposed; not simulated', nozzle='controls plus custom variants; not selected')
                         for layout in ['one-side','two-side','overhead'] for d in distances],
    'evaluation': {
        'proposed': ['5 x 5 cm moving air-area deficit versus time',
                     'Longest continuous time above 6 K deficit per passage',
                     'Time integral of positive area-mean deficit, K s',
                     'Air speed at person and free-air use per valve event',
                     'Human heat removal versus ambient baseline, with separate body heat-transfer model'],
        'timing': 'Sweep person arrival relative to valve opening. Distinguish cold startup, established jet and valve closing. A 30 s activation is not a 30 s personal exposure.',
        'cfd_stages': ['Unconfined pulsed jets and virtual moving air probes: reach screen only; omits body blockage and wake.',
                       'Retain promising layouts; add upright moving body and thermal boundaries, wind and source/line startup sensitivities.',
                       'Refine nozzle CAD and repeat internal/external CFD. Recheck conditional mathematical constraints.'],
        'unresolved': ['Exact mounting heights and walking path', 'Measured walking speed / crowd arrival pattern',
                       'Valve and line response', 'Wind envelope', 'Required minimum cooling duration per person',
                       'Supplier motor/load thermal state and balanced commercial distribution']}
}
assert len(data['candidate_matrix']) == 9
assert 0 < data['mixing_necessary_condition']['minimum_cold_mass_fraction_for_delta6'] < 1
assert abs(data['pulse_budgets'][-1]['cold_air_mass_kg']-2.328) < 1e-12
assert abs(data['pulse_budgets'][-1]['free_air_m3']-1.944) < 1e-12
(OUT/'timing-and-energy.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'power_w':power, 'pulse_30s':data['pulse_budgets'][-1],
                  'mixing_condition':data['mixing_necessary_condition'], 'candidate_count':9},indent=2))
