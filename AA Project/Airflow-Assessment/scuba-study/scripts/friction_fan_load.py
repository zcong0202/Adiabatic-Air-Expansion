"""AM0701 brake/fan sizing. Conditional energy balances, not a motor map."""
from pathlib import Path
import csv
import json
import math

STUDY = Path(__file__).resolve().parents[1]
OUT = STUDY / 'results'
OFFICIAL = 'https://www.cosmostar.net/product/air-motor-and-agitator/255-am0701-0-9-hp-air-operated-vane-type-air-motor'
UIUC = 'https://m-selig.ae.illinois.edu/props/volume-4/data/apce_14x10_static_2140od.txt'
CP = 1006.0


def brake(power, rpm, radius, mu):
    omega = rpm * math.pi / 30
    torque = power / omega
    return dict(shaft_w=power, rpm=rpm, contact_radius_m=radius,
                torque_nm=torque, tangential_force_n=torque / radius,
                total_pad_normal_force_n=torque / radius / mu,
                assumed_mu=mu, energy_10s_j=power * 10)


def required_power(mass, tin, ambient, target, fraction, ua, heat_fraction):
    capacity = mass * CP
    return max(0, capacity * (tin - ambient + target / fraction * math.exp(ua / capacity)) / (1 - heat_fraction))


def build():
    mass, beta = .015, .25
    rows = []
    for power in (100, 200, 400, 600):
        for rpm in (1000, 1500, 2000, 2500, 3000):
            for radius in (.05, .10, .20):
                row = brake(power, rpm, radius, .30)
                row['motor_drop_k'] = (1 - beta) * power / (mass * CP)
                row['motor_exhaust_c_if_inlet22'] = 22 - row['motor_drop_k']
                row['within_separate_catalogue_limits'] = power <= 671.13 and row['torque_nm'] <= 3 and rpm <= 3000
                rows.append(row)
    scenarios = []
    for tin in (22, 30):
        for ua in (1, 10):
            for fraction in (.2, .25, .5):
                p = required_power(mass, tin, 30, 6, fraction, ua, beta)
                scenarios.append(dict(inlet_c=tin, ambient_c=30, target_drop_k=6,
                                      assumed_target_cold_mass_fraction=fraction,
                                      assumed_path_ua_w_k=ua, required_shaft_w=p,
                                      below_advertised_max_power=p <= 671.1298844240432))
    # UIUC static APC 14x10 E measured coefficient at 2960 rpm.
    evidence = (STUDY/'evidence/friction-fan/uiuc-apce-14x10-static.txt').read_text()
    measured = next(line.split() for line in evidence.splitlines() if line.strip().startswith('2960.000'))
    fan_rpm, _, fan_cp = map(float, measured)
    assert fan_cp == .042579
    fan_power = fan_cp * 1.2 * (fan_rpm / 60)**3 * .3556**5
    fans = [dict(diameter_m=d, rpm=rpm, assumed_power_coefficient=coef,
                 shaft_w=coef * 1.2 * (rpm / 60)**3 * d**5)
            for d in (.20, .30, .40) for rpm in (2000, 3000) for coef in (.04, .08, .12)]
    fan_requirements = [dict(required_shaft_w=p, diameter_m=.4, rpm=3000,
                             required_cp=p/(1.2*50**3*.4**5)) for p in (200, 400, 600)]
    # Independent arithmetic checks, not Lean proofs or hardware qualification.
    for row in rows:
        assert math.isclose(row['torque_nm'] * row['rpm'] * math.pi / 30, row['shaft_w'])
        assert math.isclose(row['tangential_force_n'] * row['contact_radius_m'], row['torque_nm'])
        assert math.isclose(row['total_pad_normal_force_n'] * .3, row['tangential_force_n'])
    for s in scenarios:
        p = s['required_shaft_w']
        tout = s['inlet_c'] - .75 * p / (mass * CP)
        tn = 30 + (tout - 30) * math.exp(-s['assumed_path_ua_w_k']/(mass*CP))
        assert math.isclose(s['assumed_target_cold_mass_fraction'] * (30 - tn), 6, abs_tol=1e-10)
    assert math.isclose(brake(400, 2000, .1, .3)['torque_nm'], 6/math.pi)
    assert math.isclose(.75*400/(mass*CP), 19.880715705765407)
    # Ideal-gas isentropic ceiling: illustrative 7 bar absolute to 1 bar, Tin22.
    ideal_drop = 295.15 * (1 - (1/7)**(2/7))
    result = dict(date='2026-11-10', hardware_status='User has Amazon B08L6BXZBT AM0701. Nameplate and loaded map not inspected.',
        source=dict(manufacturer=OFFICIAL, published_power_w=671.1298844240432,
                    max_torque_nm=3, max_rpm=3000, published_operation_bar=[1,7],
                    max_consumption_l_min=750, consumption_condition='6 bar / 3000 RPM', mass_kg=2.61,
                    verified_on='2026-11-10', note='Separate maxima. Free-air basis and simultaneous loaded power/flow unconfirmed.'),
        assumptions=dict(mass_flow_g_s=15, mass_flow_basis='750 L/min treated as free air at 1.2 kg/m3; unconfirmed',
                         cp_j_kg_k=CP, motor_inlet_c=22, ambient_c=30,
                         heat_return_fraction=beta, heat_status='Illustrative; not measured or a bound',
                         max_radius_m=.20, mu=.30, max_pulse_s=10,
                         steady='Settled total temperatures, negligible KE/PE changes and negligible stored-energy rate.'),
        equations=dict(steady='mdot*cp*(Tin-Tout)=Pshaft-Qinto',
                       transient='mdot*cp*(Tin-Tout)=Pshaft-Qinto+dE_control_volume/dt',
                       shaft='P=tau*2*pi*rpm/60', brake='tau=Ft*r=mu*Ntotal*r',
                       fan='P=Cp*rho*(rpm/60)^3*D^5',
                       hose='Tnozzle=Tamb+(Tout-Tamb)*exp(-UA/(mdot*cp))',
                       mixing='target_drop=f*(Tamb-Tnozzle)',
                       target='P=mdot*cp*(Tin-Tamb+(target_drop/f)*exp(UA/(mdot*cp)))/(1-beta)'),
        brake_sweep=rows, target_sensitivities=scenarios, fan_coefficient_sensitivities=fans,
        fan_requirements=fan_requirements,
        fan_primary_example=dict(url=UIUC, manufacturer='APC', model='14x10 E', diameter_m=.3556,
                                 uiuc_measured_rpm=2960, uiuc_measured_cp=.042579,
                                 assumed_density_kg_m3=1.2, calculated_absorption_w=fan_power,
                                 conditional_motor_drop_k=.75*fan_power/(mass*CP),
                                 status='Measured aerodynamic coefficient, calculated power at assumed density. Not tested on AM0701.'),
        ideal_expansion_ceiling=dict(assumed_inlet_abs_bar=7, outlet_abs_bar=1, inlet_c=22,
                                    ideal_drop_k=ideal_drop, ideal_air_power_w=mass*CP*ideal_drop,
                                    status='Ideal gas, reversible adiabatic benchmark. Not motor prediction.'),
        decision='Use an adjustable, guarded friction brake first. Aim for measured 200 W, then 400 W; 600 W only if the measured operating point and thermal limits allow it.',
        unknowns=['Actual shaft diameter, usable length, key/flat and retention; manufacturer drawing/nameplate',
                  'Paired motor torque/RPM/airflow and actual inlet temperature/pressure',
                  'Brake friction coefficient versus temperature, torque/speed/energy rating, external bearings and guard',
                  'Fan thrust/radial loads, shaft limits, measured Cp curve and surrounding-air interference',
                  'Hose UA, target dilution at 20/50 cm, transient warm metal, oil carryover/icing'],
        validation=dict(brake_balance_rows=len(rows), target_inverse_checks=len(scenarios),
                        status='Arithmetic checks pass. No new CFD, Lean proof, fabricated brake or motor measurement.'))
    (OUT/'friction-fan-load.json').write_text(json.dumps(result, indent=2)+'\n')
    with (OUT/'friction-brake-sweep.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    def rowhtml(row):
        return f"<tr><td>{row['shaft_w']:.0f} W</td><td>{row['torque_nm']:.2f}</td><td>{row['tangential_force_n']:.1f}</td><td>{row['total_pad_normal_force_n']:.1f}</td><td>{row['energy_10s_j']/1000:.1f}</td><td>{row['motor_drop_k']:.1f}</td></tr>"
    table = ''.join(rowhtml(r) for r in rows if r['rpm']==2000 and r['contact_radius_m']==.1)
    targets = ''.join(f"<tr><td>{s['inlet_c']}</td><td>{s['assumed_path_ua_w_k']}</td><td>{s['assumed_target_cold_mass_fraction']:.0%}</td><td>{s['required_shaft_w']:.0f}</td><td>{'Below' if s['below_advertised_max_power'] else 'Above'} 671 W</td></tr>" for s in scenarios)
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AM0701 friction and fan loads</title>
<style>body{font:16px/1.55 system-ui;color:#171717;margin:0}main{max-width:1000px;margin:auto;padding:28px 22px}h1{letter-spacing:-1px;font-size:32px}h2{font-size:22px;margin-top:34px}a{color:inherit}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;border-bottom:1px solid #ddd;text-align:left}.scroll{overflow:auto}code{background:#f3f3f3;padding:3px 5px}.note{font-size:14px;color:#555}.controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:16px;background:#f5f5f5;padding:20px}label{font-size:14px}input{display:block;width:100%;box-sizing:border-box;padding:7px;font:inherit}#answer{padding:16px 0;font-weight:600}svg{width:100%;height:auto}.status{border-left:3px solid #111;padding-left:16px}</style>
<main><nav><a href="../../../project-overview.html#scuba-source">Overview</a> · <a href="poc-assembly.html">Assembly</a> · <a href="friction-fan-load.json">Inputs / calculations</a> · <a href="friction-brake-sweep.csv">Brake sweep</a></nav>
<h1>AM0701: friction brake or fan</h1><p class="status">Motor received. Adjustable friction brake selected as first test candidate. Calculated loads below are design targets. No loaded motor point, brake fit or outdoor cooling result is verified.</p>
<p>Maximum radius: 20 cm, taken from the user’s available envelope. A 10 cm contact radius is used for examples. A heavy flywheel is unnecessary for steady loading.</p>
<h2>Motor limits</h2><p><a href="OFFICIAL">Cosmostar AM0701</a>: 0.9 HP (671 W), max 3 N·m, max 3000 RPM, operating range 1–7 bar, 2.61 kg. Published max consumption: 750 L/min at 6 bar / 3000 RPM. These are separate maxima. Confirm actual unit nameplate. Exact shaft drawing and loaded performance map remain unavailable.</p>
<p>15 g/s assumes the 750 L/min figure is free-air flow at 1.2 kg/m³. This basis is unverified. A 22°C cylinder does not fix motor inlet temperature after pressure reduction. Use regulated, flow-qualified supply; never connect the scuba cylinder pressure directly to the motor.</p>
<h2>Required work</h2><p><code>ṁcₚ(T₀,in − T₀,out) = Pshaft − Q̇into</code><br><code>Pshaft = τω = τ × 2π × RPM / 60</code><br><code>W = Pshaft × time</code></p>
<p>Temperatures are total temperatures. Use cₚ = 1006 J/kg/K. At assumed 15 g/s, each 1 K motor drop needs 15.09 W net work extraction. Illustrative 25% heat return gives <code>ΔTmotor = 0.75P / 15.09</code>. Heat return is an assumption, not a measured loss factor. This is a work-extracting expander, not isenthalpic throttling.</p>
<div class="scroll"><table><thead><tr><th>Load</th><th>Torque N·m</th><th>Friction force N</th><th>Total pad normal force N</th><th>10 s energy kJ</th><th>Motor drop K</th></tr></thead><tbody>TABLE</tbody></table></div><p class="note">All rows assume 2000 RPM, 10 cm contact radius, μ = 0.30, 15 g/s and 25% heat return. Total normal force sums all rubbing interfaces. Not a caliper actuator force. Being below catalogue maxima does not prove the operating point exists.</p>
<h2>Brake geometry</h2><p><code>τ = Fₜr = μNtotal r</code>. Fₜ is total tangential friction force. Ntotal is the sum of pad normal forces. At fixed power and RPM, doubling radius halves both forces. It does not change torque, work or heat generation.</p>
<svg viewBox="0 0 1000 165" role="img" aria-label="Scuba tank through regulated supply to air motor, with cold exhaust separate from a guarded friction brake on a supported coupling"><g fill="none" stroke="#333" stroke-width="2"><rect x="10" y="25" width="130" height="65"/><path d="M140 58H190"/><rect x="190" y="25" width="180" height="65"/><path d="M370 58H420"/><rect x="420" y="25" width="145" height="65"/><path d="M565 58H640"/><rect x="640" y="25" width="330" height="65" stroke-dasharray="5 4"/><path d="M490 90V135H780"/></g><g font-family="system-ui" font-size="16" text-anchor="middle"><text x="75" y="63">Scuba tank</text><text x="280" y="63">Regulated supply</text><text x="492" y="63">AM0701</text><text x="805" y="53">Supported coupling → friction brake</text><text x="805" y="77">Guarded · heat rejected away</text><text x="625" y="157">Collected cold exhaust → short hose → nozzle</text></g></svg>
<p>Use a purpose-made friction lining on a balanced, speed-rated disc or drum. Use a rigid frame, guarded coupling and external support where needed. Do not press an abrasive against an improvised flywheel. Keep pad dust and brake heat out of the exhaust. Verify motor shaft radial/axial limits before applying side load. Brake torque is measured from reaction force × reaction-arm length; this is a different radius from pad contact radius.</p>
<p>At 400 W, the brake receives 4 kJ per 10 s pulse; at 600 W, 6 kJ. A simplified 0.5 kg steel heat sink at c = 500 J/kg/K rises 16 K / 24 K if it receives all this heat uniformly. Pad contact temperatures can be much higher. This heat-capacity check does not qualify a brake. Repeated pulses need cooling and a duty rating.</p>
<h2>Does a propeller fit the envelope?</h2><p><code>Pfan = Cₚ ρ n³ D⁵</code>, with n in revolutions/second and D as diameter. Cₚ is the aerodynamic power coefficient, distinct from air heat capacity cₚ.</p>
<p>Primary example: <a href="UIUC_URL">UIUC’s measured APC 14×10 E static data</a> give Cₚ = 0.042579 at 2960 RPM. Diameter 35.56 cm fits the envelope. At assumed density 1.2 kg/m³, calculated absorption is FAN_W W, giving only FAN_DT K motor drop at assumed 15 g/s / 25% heat return. This is aerodynamic data, not an AM0701 test.</p>
<p>Even a 40 cm propeller at 3000 RPM and assumed Cₚ = 0.04–0.12 absorbs only 61–184 W. These coefficient limits are sensitivities, not universal fan limits. To absorb 200 / 400 / 600 W at this diameter and RPM needs Cₚ = 0.130 / 0.260 / 0.391. A selected fan or blower needs its own power curve. The tested small propeller is a weak candidate for the 400 W target. Do not modify blades or exceed their speed rating. Fan thrust, bearing loads and warm slipstream also affect mounting and jet mixing. Direct the slipstream away from the cold plume.</p>
<h2>Can this meet &gt;6 K at 20–50 cm?</h2><p><code>Tnozzle = Tamb + (Tout − Tamb) exp[−UA/(ṁcₚ)]</code><br><code>ΔTtarget = f(Tamb − Tnozzle)</code></p><p>f is the effective cold-source mass fraction after mixing, averaged over the 5×5 cm target area. It is not known at either distance. A 25% value is a sensitivity, not a result. In the table, UA is assumed hose heat conductance in W/K. Target is exactly 6 K; &gt;6 K needs additional margin.</p>
<div class="scroll"><table><thead><tr><th>Motor inlet °C</th><th>UA W/K</th><th>Cold fraction f</th><th>Required shaft W</th><th>Power screen only</th></tr></thead><tbody>TARGETS</tbody></table></div>
<h2>Explore a conditional operating point</h2><div class="controls"><label>Shaft power W<input id="power" type="number" min="0" max="671" value="400"></label><label>Measured / assumed flow g/s<input id="mass" type="number" min="0.1" step="0.1" value="15"></label><label>RPM<input id="rpm" type="number" min="100" max="3000" value="2000"></label><label>Contact radius cm<input id="radius" type="number" min="1" max="20" value="10"></label><label>Pad friction coefficient μ<input id="mu" type="number" min="0.01" step="0.01" value="0.3"></label><label>Heat return fraction<input id="beta" type="number" min="0" max="0.99" step="0.05" value="0.25"></label></div><p id="answer" aria-live="polite"></p><p class="note">Changing power and flow independently is a sensitivity. The real combination must satisfy the measured motor/load curves. The calculator does not predict flow or an operating RPM.</p>
<h2>First test</h2><p>Start with light brake load. Record actual RPM, brake reaction torque, mass flow, motor inlet pressure/temperature and collected exhaust pressure/temperature together. Seek 200 W, then 400 W. Attempt 600 W only if stable within the actual motor and brake limits. Excess load stalls the motor: at zero speed, shaft power is zero. Do not infer useful power from torque alone.</p>
<p>During spin-up, a flywheel absorbs <code>Iω dω/dt</code>. At steady speed its stored energy stops increasing. For a 10 s cold pulse, warm motor metal can erase early cooling. The transient energy balance is <code>ṁcₚ(Tin − Tout) = Pshaft − Q̇into + dEcv/dt</code>, neglecting KE/PE changes. Measure the time trace. Compare a regulator-only bypass at matched actual mass flow. Then measure the 5×5 cm mean temperature at 20 and 50 cm.</p>
<p class="note">10 Nov 2026. Numeric balances and inverse checks pass. No new CFD or Lean proof. No fitted CAD; shaft dimensions, brake ratings, actual flow, heat transfer and dilution remain open.</p></main>
<script>function update(){const ids=['power','mass','rpm','radius','mu','beta'];const [p,m,n,r,mu,b]=ids.map(id=>Number(document.getElementById(id).value));const out=document.getElementById('answer');if(![p,m,n,r,mu,b].every(Number.isFinite)||p<0||m<=0||n<=0||r<=0||mu<=0||b<0||b>=1){out.textContent='Enter valid positive values; heat fraction 0–0.99.';return}const t=p/(n*Math.PI/30),ft=t/(r/100),dt=(1-b)*p/(m/1000*1006);out.textContent=`${t.toFixed(2)} N·m torque · ${ft.toFixed(1)} N tangential force · ${(ft/mu).toFixed(1)} N total pad normal force · ${(p/100).toFixed(1)} kJ / 10 s · ${dt.toFixed(1)} K motor drop.${t>3||n>3000||p>671.13?' Exceeds one or more published motor maxima.':''}${r>20?' Exceeds 20 cm radius envelope.':''}`;}document.querySelectorAll('input').forEach(e=>e.addEventListener('input',update));update();</script></html>'''
    html = html.replace('OFFICIAL',OFFICIAL).replace('UIUC_URL',UIUC).replace('FAN_W',f'{fan_power:.1f}').replace('FAN_DT',f'{.75*fan_power/(mass*CP):.2f}').replace('TABLE',table).replace('TARGETS',targets)
    (OUT/'friction-fan-load.html').write_text(html)
    print(json.dumps(dict(brake400=brake(400,2000,.1,.3),fan_w=fan_power,
                          target355=scenarios[1],checks=result['validation']),indent=2))


if __name__ == '__main__':
    build()
