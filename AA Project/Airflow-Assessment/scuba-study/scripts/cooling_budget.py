"""Steady motor/nozzle/mixing budgets. No spatial CFD or startup prediction."""
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'results'


def build(data):
    cp = data['assumptions']['cp_j_kg_k']
    ambient = data['assumptions']['ambient_c']
    inlet = data['assumptions']['motor_inlet_c']
    target = 6.0
    rows, checks = [], []
    for motor in data['motors']:
        m, power = motor['mass_kg_s'], motor['power_w']
        cap = m * cp
        scenarios = []
        for ua in data['assumptions']['comparison_ua_w_k']:
            for heat_fraction in [0.0, 0.25]:
                heat = heat_fraction * power
                exhaust = inlet - (power - heat) / cap
                nozzle = ambient + (exhaust - ambient) * math.exp(-ua / cap)
                cooling = cap * (ambient - nozzle)
                mixed_flow = cooling / (cp * target)
                ratio = mixed_flow / m - 1.0
                scenarios.append(dict(ua_w_k=ua,heat_into_motor_w=heat,
                    motor_exhaust_c=exhaust,nozzle_c=nozzle,
                    sensible_cooling_vs_ambient_w=cooling,
                    max_total_mixed_g_s_at_6k=mixed_flow*1000,
                    max_ambient_per_source_mass_ratio_at_6k=max(0,ratio),
                    target_possible_before_mixing=ratio >= 0,
                    ideal_total_mixed_mass_10s_g=mixed_flow*10000))
                assert abs(cap*(inlet-exhaust)+heat-power) < 1e-8
                assert abs(cooling-mixed_flow*cp*target) < 1e-8
                if ratio >= 0:
                    mixture = (nozzle+ratio*ambient)/(1+ratio)
                    assert abs(mixture-(ambient-target)) < 1e-9
                checks.append(motor['id']+f' UA={ua} heat={heat_fraction}: energy/mixing closure')
        rows.append(dict(id=motor['id'],name=motor['name'],mass_g_s=m*1000,
            shaft_power_w=power,rpm=motor['rpm'],pressure_bar_g=motor['pressure_bar_g'],
            curve_source=motor['curve_source'],manufacturer_url=motor['manufacturer_url'],
            source_mass_10s_g=m*10000,
            tank_inventory_10s_possible=data['assumptions']['usable_adiabatic_kg'] >= m*10,
            heat_into_motor_limit_for_6k_motor_drop_w=power-cap*target,
            shaft_energy_10s_j=power*10,scenarios=scenarios))
    # Rating-only sensitivity. None of these airflow values is a V1 specification.
    globe = dict(name='GLOBE V1',listed_max_shaft_w=520,
        status='Not qualified: no paired loaded power/airflow curve obtained',
        source='https://mechatronics.ae/product/v1-vane-motor/',
        hypothetical_flow_sweep=[dict(assumed_g_s=g,ideal_motor_drop_k=520/(g/1000*cp))
            for g in [10,20,30,40]],
        warning='520 W at every swept flow is hypothetical, not a motor map or predicted V1 output')
    result=dict(status='Conditional steady budgets; not hardware validation',
        assumptions=data['assumptions'],target_drop_k=target,motors=rows,globe=globe,
        limits=['22 C is motor inlet, not cylinder temperature.',
            'Requires sustained measured shaft load and the paired airflow operating point.',
            'Cooling includes inlet air already 8 K below 30 C ambient; it is not all motor-generated.',
            'UA and 25% heat return are sensitivity assumptions, not uncertainty bounds.',
            'Mixed mass is a calorimetric ceiling for ideal mixing, not an achieved outdoor cold volume.',
            'No distance, velocity, area-average target, startup conditioning or post-shutoff persistence is predicted.',
            'Source mass is released during 10 s. Mixed mass includes entrained ambient air.',
            'New motors have no source-specific CFD results. Standard Gast exhaust requires lubrication containment.'])
    (OUT/'cooling-budget.json').write_text(json.dumps(result,indent=2))
    (OUT/'cooling-budget-validation.json').write_text(json.dumps(dict(status='passed',
        checks=len(checks),items=checks,scope='Steady energy and ideal mixing closure only'),indent=2))
    table=''
    for row in rows:
        nominal=next(s for s in row['scenarios'] if s['ua_w_k']==1 and s['heat_into_motor_w']==0)
        table+=f'<tr><td>{row["name"]}</td><td>{nominal["sensible_cooling_vs_ambient_w"]:.0f}</td><td>{nominal["max_total_mixed_g_s_at_6k"]:.0f}</td><td>{nominal["max_ambient_per_source_mass_ratio_at_6k"]:.1f}</td></tr>'
    return f'''<details class="compact-details" id="cooling-budget"><summary>Enough cooling? Energy / mixing limits</summary><p>Gast points can support a bench POC under the stated assumptions. No new motor is validated at 20–50 cm. Sustained shaft load is required.</p><div class="formula-equation">ΔTmotor = (Pshaft − Qinto)/(ṁ cp)<br>Qcold = ṁ cp (Tambient − Tnozzle)<br>ṁmixed,max = Qcold/(cp × 6 K)</div><div class="table"><table><thead><tr><th>Motor</th><th>Cold budget W</th><th>Max mixed g/s at 6 K</th><th>Ambient / source mass</th></tr></thead><tbody>{table}</tbody></table></div><p class="note">Table: 22°C motor inlet, 30°C ambient, UA=1 W/K, zero motor heat pickup. Includes the inlet's existing 8 K temperature deficit. Ideal mixing ceilings, not achieved volumes or CFD. JSON includes inherited UA and 25% heat-return scenarios. Startup metal heat can erase early cooling.</p><p>GLOBE V1: 520 W listed; paired airflow is missing. Hypothetical 10 / 20 / 30 / 40 g/s would give 52 / 26 / 17 / 13 K motor drop at 520 W with zero heat pickup. These are sensitivity examples, not V1 predictions.</p><a href="cooling-budget.json">Calculation / assumptions</a> · <a href="cooling-budget-validation.json">20 balance checks</a></details>'''
