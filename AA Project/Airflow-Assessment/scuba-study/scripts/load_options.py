"""Costed load concepts. Listed parts are not qualified complete load stations."""
from pathlib import Path
import json
import math

STUDY=Path(__file__).resolve().parents[1]
OUT=STUDY/'results'
SHAFT_URL='https://cosmostar.store/products/cosmostar-stainless-steel-mixing-gear-blade-55-gallon-paint-mixer-stirring-propeller-tools-for-paint-epoxy-resin-silicone-stirrer-paddle-with-0-47-shaft-rod-gear-3-94-in-propeller-g10s12?variant=45988974068032'
BLADE_URL='https://cosmostar.store/products/copy-of-cosmostar-stainless-steel-mixing-expandable-blade-55-gallon-paint-mixer-stirring-propeller-tools'
PMDC_URL='https://www.amazon.com/dp/B0G4PH83D3'
RESISTOR_URL='https://www.amazon.com/dp/B008DGC4WA'


def build():
    poc=json.loads((OUT/'poc-assembly-calculations.json').read_text())
    examples=[]
    for shaft,mass in [(200,.015),(400,.015),(671.1298844240432,.015),(200,.0075)]:
        examples.append(dict(assumed_shaft_w=shaft,assumed_mass_g_s=mass*1000,
                             assumed_heat_return_fraction=.25,motor_drop_k=.75*shaft/(mass*1006),
                             basis='Independent fixed-flow sensitivity, not an actual load/flow operating point'))
    requirements=[]
    for m in poc['motors']:
        p=m['power_screen_w']
        requirements.append(dict(model=m['model'],screened_shaft_power_w=p,
                                 torque_if_power_at_3000rpm_nm=p/(3000*math.pi/30),
                                 energy_10s_kj=p*.01,
                                 ideal_water_warming_10kg_10s_k=p*10/(10*4180),
                                 electrical_load_if_generator_efficiency_080_w=.8*p,
                                 generator_efficiency_status='80% illustration, not measured'))
    result=dict(checked_on='2026-11-02',
                status='Priced component candidates; no complete cheap load qualified for either full motor point',
                options=[
                    dict(type='Water agitation load',priority='Lowest-cost mechanical POC concept',
                         links=[dict(item='EX6S12 blade only, 12 mm bore',usd=39,url=BLADE_URL),
                                dict(item='Two 3.94-inch blades and 12 mm shaft',usd=109,url=SHAFT_URL)],
                         complete_station_price_usd=None,
                         qualifications_missing=['Exact motor shaft connection and supplier-approved speed/bearing limits',
                                                 'Stable torque absorption at chosen RPM in actual vessel',
                                                 'Rigid covered vessel/mount/guard and torque/RPM measurement'],
                         thermal_note='Water can receive work as heat. Heat capacity alone does not prove a paddle can absorb the required shaft power.',
                         stock_delivery='Manufacturer shop cart enabled; Nov 5–9 banner, destination checkout not verified'),
                    dict(type='Brushed PMDC motor used as generator plus resistor bank',priority='Reusable low-cost engineering candidate for AM0701',
                         links=[dict(item='Ytrica MY1020 48 V / 1000 W / 3000 rpm brushed motor',usd=89.99,url=PMDC_URL),
                                dict(item='uxcell advertised 1000 W / 3 ohm braking resistor',usd=30.09,url=RESISTOR_URL)],
                         advertised_component_subtotal_usd=120.08,complete_station_price_usd=None,
                         qualifications_missing=['Confirm permanent-magnet construction; inferred from reversible two-wire motor type, not explicitly verified by manufacturer', 'Motor listing is not a generator absorption/thermal rating',
                                                 'Generated voltage/current versus speed and load, losses, temperature and commutation',
                                                 'Resistance selection from loaded voltage and target power; 3 ohm is a cost example, not a fixed specification',
                                                 'Resistor heatsink/cooling and derating conditions',
                                                 'Exact shaft coupling, base, guard, DC switching, wiring protection and metering'],
                         limit='Not a qualified AM0706 2.68 kW full-power load. An unloaded generator or a scooter drive controller does not supply the intended resistive load.',
                         stock_delivery='Motor: 20 displayed, Oakland Nov 7 / Prime Nov 5. Resistor: in stock, Oakland Nov 7 conditional free shipping / Prime Nov 3. Exact SF checkout unverified.'),
                    dict(type='Rated brake/dynamometer, preferably borrowed or rented',priority='Best controlled test if an existing lab unit is accessible',
                         links=[dict(item='Magtrol HD Series manufacturer data',url='https://www.magtrol.com/product/hysteresis-dynamometers-hd-series/')],complete_station_price_usd=None,
                         verified_rating_examples=[dict(model='HD-710',max_torque_nm=3.1,continuous_absorption_w=935,scope='AM0701 screen at 3000 rpm; blower and controller required'),dict(model='HD-810',max_torque_nm=14,continuous_absorption_w=3000,scope='Both motor screening points at 3000 rpm; blower and controller required')],
                         rating_source='Magtrol HD datasheet page 4. Ratings are not local availability or complete-installation qualification.',
                         qualifications_missing=['Specific unit, price/stock/rental not verified','Torque, speed, continuous/slip-power or 10-second energy/duty rating and controller match'],
                         required_shared_station='About 3 kW mechanical absorption and >=8.55 N m at 3000 rpm for the AM0706 screening point; actual loaded map must set final limits')],
                requirements=requirements,fixed_flow_sensitivities=examples,
                electrical_resistor_examples=[dict(assumed_terminal_v=v,resistance_ohm=3,electrical_power_w=v*v/3,current_a=v/3) for v in (36,48)],
                mechanism=dict(rotor='I*domega/dt = torque_air - torque_load - torque_friction',
                               steady='torque_air = torque_load + torque_friction',
                               shaft='Pshaft = torque_load*omega',
                               motor='Delta T = (Pshaft-Qinto)/(mdot*cp)',
                               outlet_speed='U = mdot/(rho*A)',
                               pressure='A sufficient regulator may hold inlet pressure while speed/flow change. Exhaust pressure depends on outlet resistance, normally near ambient for this concept.',
                               unknown='Neither loaded 15 nor 74 g/s is established without the motor map and actual supply test.'),
                recommendation='Use AM0701 first. Obtain a supplier-matched paddle/shaft load for the cheapest mechanical POC, or qualify the PMDC generator/resistor route for repeatable work recovery. Do not claim full-power capacity from watt labels. Higher-power AM0706 needs upgraded air supply and a separately rated load.',
                validation='Arithmetic only. No physical motor map, generator thermal test, new CFD or Lean proof.')
    assert abs(89.99+30.09-120.08)<1e-10
    assert abs(examples[0]['motor_drop_k']-examples[3]['motor_drop_k']/2)<1e-10
    assert abs(examples[1]['motor_drop_k']-examples[3]['motor_drop_k'])<1e-10
    for r in requirements:
        assert abs(r['torque_if_power_at_3000rpm_nm']*100*math.pi-r['screened_shaft_power_w'])<1e-8
        assert r['ideal_water_warming_10kg_10s_k']<1
    (OUT/'load-options.json').write_text(json.dumps(result,indent=2)+'\n')
    section=f'''<section id="load-options"><h2>Low-cost shaft loads</h2><p><strong>No complete cheap load station is qualified yet.</strong> These are priced components and engineering routes. Mounting, guards, coupling, thermal management and instruments are additional.</p><div class="table"><table><thead><tr><th>Route</th><th>Observed component price</th><th>Use / qualification</th></tr></thead><tbody><tr><td>Water agitation</td><td><a href="{SHAFT_URL}">$109 two-blade shaft set</a>; <a href="{BLADE_URL}">$39 blade only</a></td><td>Lowest-cost mechanical concept. Exact motor fit, allowed speed and actual paddle power absorption unverified. A blade alone is not a load station.</td></tr><tr><td>PMDC generator conversion</td><td><a href="{PMDC_URL}">$89.99 motor</a> + <a href="{RESISTOR_URL}">$30.09 example resistor</a></td><td>AM0701 candidate, not generator-certified. $120.08 component subtotal, not installed cost. Not qualified for AM0706 full power. Final resistance/cooling depend on loaded voltage/current.</td></tr><tr><td>Rated brake / dynamometer</td><td>Borrow/rent if available; no local quote verified</td><td>Controlled torque/load measurement. Manufacturer examples: HD-710 has 3.1 N m / 935 W continuous, suitable for the AM0701 screening point at 3000 rpm. HD-810 has 14 N m / 3000 W continuous, covering both screening points at 3000 rpm with specified blower/controller. No price, local availability or complete installation verified.</td></tr></tbody></table></div><p><strong>Does load reduce airflow?</strong> Added torque usually reduces RPM and can reduce mass flow. The exact change needs the motor’s loaded map. A sufficient regulator can keep inlet pressure nearly fixed; shaft loading is not an exhaust valve. The motor uses pressure energy, and the passive nozzle receives low-pressure exhaust. Excess load can stall the rotor; at zero RPM, shaft power is zero even if torque or leakage remains.</p><p><code>P = τω</code> · <code>ΔT = (Pshaft − Qinto)/(ṁcp)</code>. If shaft power and airflow both halve, the first-law temperature drop can remain the same while cooled air mass and cooling power halve. At a fixed 15 g/s and assumed 25% heat return, 200 W gives 9.94 K motor drop and 400 W gives 19.88 K. These are sensitivities, not measured operating points or nozzle predictions.</p><p><a href="../evidence/load-options/Magtrol-HD-datasheet.pdf">Magtrol manufacturer ratings, page 4</a>. Torque, speed and power must all fit: a brake with adequate watts may still lack torque at 3000 rpm.</p><p>The smaller motor’s full screening point is 671 W. The larger is 2685 W. At 3000 rpm these require 2.14 and 8.55 N m respectively; 3000 rpm is an illustrative calculation speed, not a verified maximum-power point. A first measurable cooling experiment can use less power, but that does not establish the outdoor &gt;6 K target.</p><p>For a water load, 10 kg of water receiving all shaft work for 10 s would warm about 0.16 K / 0.64 K at the two screening powers. That establishes heat capacity only. It does not rate the shaft, paddle, vessel, bearings or mount. For a generator, open circuit produces little sustained external load; electrical current through the resistor supplies opposing torque. Keep generator/resistor heat away from the cooled-air path.</p><p class="note">Prices checked 2 Nov. Exact SF delivery unconfirmed. No generator/mixer load map or complete installation price verified. Existing small air valve remains restrictive; AM0706 supply also needs re-sizing. <a href="load-options.json">Calculations, source links and qualification gaps</a>.</p></section>'''
    (OUT/'load-options-section.html').write_text(section)
    print(json.dumps({'component_subtotal_usd':120.08,'fixed_flow_sensitivities':examples,'requirements':requirements},indent=2))


if __name__=='__main__':
    build()
