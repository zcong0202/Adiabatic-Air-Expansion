"""Receiver and hose screens. Engineering estimates; not new CFD or Lean proofs."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / 'source-input.json').read_text())
N = S['active_motors']
M = N * S['mass_per_motor_kg_s']
CP = S['cp_j_kg_k']
QREF = N * S['free_air_per_motor_l_s'] / 1000
PREF = 101325.0
TREF, TTANK = 293.15, 313.15
R = 287.05
TMOTOR = S['inlet_c'] - N * S['shaft_work_per_motor_w'] / (M * CP)


def receiver_litres(seconds, pressure_swing_bar, compressor_fad_m3_min=0):
    """Constant-temperature inventory; FAD references must be matched."""
    deficit = max(0, QREF - compressor_fad_m3_min / 60)
    return deficit * seconds * PREF / (pressure_swing_bar * 1e5) * TTANK / TREF * 1000


def hose(mdot, diameter_m, length_m, temperature_c, pressure_abs_pa):
    rho = pressure_abs_pa / (R * (temperature_c + 273.15))
    speed = mdot / (rho * math.pi * diameter_m ** 2 / 4)
    # Assumed Darcy factor. Smooth hose only; no fittings, dryer or valve losses.
    dp = 0.02 * length_m / diameter_m * rho * speed ** 2 / 2
    return {'id_mm': diameter_m * 1000, 'length_m': length_m,
            'speed_m_s': speed, 'straight_loss_pa': dp,
            'fraction_of_absolute_pressure': dp / pressure_abs_pa}


result = {
    'status': 'Conditional first-principles screen; not hardware validation, new CFD or new Lean verification',
    'reference': {'fad_pressure_pa': PREF, 'fad_temperature_k_ASSUMED': TREF,
                  'receiver_temperature_k_ASSUMED': TTANK,
                  'warning': 'Motor flow reference temperature is not confirmed. FAD figures require common reference states.'},
    'source': {'mass_kg_s': M, 'fad_m3_min': QREF * 60,
               'shaft_w': N * S['shaft_work_per_motor_w'], 'motor_c_ASSUMED': TMOTOR},
    'receiver_equation': 'V=(Qref_load-Qref_compressor)*t*Pref/(Phi-Plo)*Ttank/Tref; clip negative deficit to zero',
    'receiver_limits': [
        'Isothermal inventory estimate. Rapid blowdown can cool the receiver and reduce usable inventory.',
        'A 7 barg source cannot charge a receiver to 9 barg.',
        'Example 6.8 barg minimum receiver pressure reserves 0.5 bar for losses/regulation above 6.3 barg motor inlet; this is an assumed network budget.',
        'A 7 to 6.8 barg swing is only an illustrative 0.2 bar allowance, not a validated operating envelope.',
        'Compressor air/oil separator volume is not assumed usable receiver inventory.',
        'Final size requires compressor transient delivery, usable operating pressure range, line losses and thermal blowdown model.'
    ],
    'receiver_examples': [
        {'purpose': '30s with compressor supplying no flow', 'swing_bar': .2, 'litres': receiver_litres(30, .2)},
        {'purpose': '30s with compressor supplying no flow; needs higher-pressure source', 'swing_bar': 2, 'litres': receiver_litres(30, 2)},
        {'purpose': '2s with compressor supplying no flow', 'swing_bar': .2, 'litres': receiver_litres(2, .2)},
        {'purpose': '30s deficit with 3.6m3/min compressor', 'swing_bar': .2, 'litres': receiver_litres(30, .2, 3.6)},
        {'purpose': '30s with fully established 5m3/min compressor', 'swing_bar': .2, 'inventory_deficit_litres': receiver_litres(30, .2, 5)}
    ],
    'receiver_300l_no_compressor_seconds_at_0_2bar': 300 / receiver_litres(1, .2),
    'compressor_candidates': [
        {'model': model, 'fad_m3_min': fad, 'working_pressure_bar_g': 7,
         'margin_of_motor_demand_percent': 100 * (fad / (QREF * 60) - 1)}
        for model, fad in [('XAS 68', 3.6), ('XAS 78', 4.5), ('XAS 88', 5)]
    ],
    'compressed_main_10m': [hose(M, d, 10, 40, 801325) for d in (.025, .032, .040)],
    'cold_branch_10m_each_of_four': [hose(M / N, d, 10, .959275276, PREF) for d in (.032, .050, .100)],
    'hose_assumptions': 'Darcy f=0.02, smooth straight hose. Local density approximation. No bends, couplers, pulsation or flexible-hose roughness. Thermal and pressure tables are separate sensitivities, not a coupled network solution.',
    'thermal_equation': 'T(L)=Ta+(Tmotor-Ta)*exp(-UA_per_length*L/(mdot_branch*cp))',
    'cold_branch_heat_sensitivity': [
        {'length_m': length, 'ua_w_m_k_ASSUMED': ua,
         'nozzle_c': S['ambient_c'] + (TMOTOR - S['ambient_c']) * math.exp(-ua * length / (M / N * CP))}
        for length in (1, 3, 5, 10) for ua in (.5, 1.5)
    ],
    'heat_sensitivity_limits': 'UA values 0.5 and 1.5 W/(m K) are illustrative low/high heat-leak cases, not rated insulated/bare hose products. Start at motor -3.04C; do not add the existing 4K duct allowance again.',
    'sources': [
        'https://www.atlascopco.com/en-ae/construction-equipment/products/mobile-air-compressors/ready-to-go-compressor-range/xas-lrc-range',
        'https://www.atlascopco.com/en-us/itba/products/air-motors/lzb46-rl-a025-11-sku8411047249',
        'https://www.atlascopco.com/en-us/itba/industry-solutions/airmotors/technicalguide/performance'
    ]
}

# Useful consistency checks: stored free-air inventory equals the demand deficit.
v = receiver_litres(30, .2) / 1000
stored = v * .2e5 / PREF * TREF / TTANK
assert math.isclose(stored, QREF * 30, rel_tol=1e-12)
assert receiver_litres(30, .2, 5) == 0
assert all(x['fraction_of_absolute_pressure'] < .1 for x in result['compressed_main_10m'])

out = ROOT / 'results/system-sizing.json'
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
