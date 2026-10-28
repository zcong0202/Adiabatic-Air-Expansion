"""Coupled power/flow shopping screen. Cheap air tools remain unqualified donors."""
from pathlib import Path
from html import escape
import csv,json,math

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'
DATE='2026-10-28'

def build():
    cp=1006.;alpha=.25;ua=1.;ambient=30.;f=.25;target=6.
    rows=[];checks=[]
    for g in [2,5,10,15,20]:
        cap=g*.001*cp
        row=dict(flow_g_s=g,free_l_min_assumed_rho1_2=g/1.2*60,
            net_power_for20k_w=cap*20,
            shaft_power_for20k_with25pct_heat_return_w=cap*20/(1-alpha),
            shaft_power_for30k_with25pct_heat_return_w=cap*30/(1-alpha))
        for tin in [22,30]:
            required=cap*(tin-ambient+target/f*math.exp(ua/cap))/(1-alpha)
            row[f'shaft_w_target6k_tin{tin}_f0_25_ua1_heat25pct']=max(0,required)
            tm=tin-(1-alpha)*required/cap
            tn=ambient+(tm-ambient)*math.exp(-ua/cap)
            assert abs(f*(ambient-tn)-target)<1e-10
            checks.append(f'{g} g/s / inlet {tin} C: target/path first-law closure')
        for dt in [20,30]:
            power=row[f'shaft_power_for{dt}k_with25pct_heat_return_w']
            assert abs((1-alpha)*power/cap-dt)<1e-10
            checks.append(f'{g} g/s: {dt} K net motor-energy closure')
        rows.append(row)
    products=[dict(name='WUFU WFD-1050S',url='https://www.hirdavatburada.com/urun/wufu-wfd-1050s-kabzali-havali-matkap-10mm-sag-sol',
        listed_usd_ex_vat=39,listed_tl=2340,listed_rpm=1800,listed_air_l_min=141,listed_inlet='1/4 inch; thread standard not specified',
        listed_weight_kg=1.16,conditional_g_s_if_free_continuous=2.82),
        dict(name='WUFU WFD-3050',url='https://www.hirdavatburada.com/urun/wufu-wfd-3050-kompozit-govdeli-havali-matkap-10mm-sag-sol',
        listed_usd_ex_vat=44,listed_tl=2640,listed_rpm=1800,listed_air_l_min=113,listed_inlet='1/4 inch; thread standard not specified',
        listed_weight_kg=.92,conditional_g_s_if_free_continuous=2.26)]
    for p in products:
        p.update(checked=DATE,category='Complete pneumatic drill; experimental motor donor, not a bare expander',
            cart_status='Sepete Ekle and Hemen Al visible; add-to-cart control enabled; no purchase made',
            stock_status='Physical inventory and delivery date not confirmed; checkout not completed',
            technical_status='Retail listing only. Shaft power absent; pressure and continuous/average airflow basis unresolved. No thermal qualification.',
            exhaust_status='Capture geometry, backpressure, lubrication and temperature limits unresolved')
    result=dict(date=DATE,status='Conditional shopping screen, not hardware qualification',
        target='>6 K average air-temperature drop over 5 x 5 cm at 20 cm; assess 50 cm; still air + gravity; spray <=10 s',
        equations=dict(motor='DeltaTmotor=(Pshaft-Qinto)/(mdot cp)',shopping='Pshaft=mdot cp DeltaTmotor/(1-alpha)',
            target='DeltaTtarget=f (Ta-Tnozzle)',path='Tnozzle=Ta+(Tin-(1-alpha)Pshaft/(mdot cp)-Ta) exp(-UA/(mdot cp))'),
        assumptions=dict(cp_j_kg_k=cp,ambient_c=ambient,motor_inlet_c=[22,30],motor_drop_screen_k=[20,30],
            heat_return_fraction=alpha,path_ua_w_k=ua,retained_temperature_fraction_at_target=f,free_air_reference_density_kg_m3=1.2),
        preferred_shopping_band=dict(continuous_g_s=[10,20],free_l_min=[500,1000],paired_shaft_w_approx=[300,800],
            pressure_bar_g=[5.5,6.3],scope='Practical design band, not a proven minimum or guarantee. Match power to flow; prefer upper drop band for warm inlet.'),
        rows=rows,turkey_online_donor_listings=products,
        qualified_bare_motor_below_100_usd_found=False,
        qualified_bare_motor_turkey_online_checkout_found=False,
        requirements=['Continuous rotary vane or piston motor; not impact wrench, cylinder, oscillating actuator or electric compressor motor',
            'Loaded power, rpm and continuous free-air use at the same running inlet/exhaust pressures; no arbitrary pairing of headline maxima',
            'Suitable guarded shaft coupling and controlled load rated for the selected power/speed; all calculations require shaft extraction',
            'Collectable exhaust with low manufacturer-approved backpressure',
            'Oil-free preferred for person-facing use; lubricated models confined to bench testing with exhaust containment',
            'Manufacturer-approved temperatures; 1/4 NPT convenient but thread size is not a cooling criterion'],
        limits=['No motor wattage alone establishes the outdoor area-temperature target; nozzle dilution, area, distance, startup and heat pickup matter',
            '20/30 K motor drops, alpha=25%, UA and f are design assumptions, not measured bounds',
            'Motor inlet temperature differs from cylinder temperature',
            'Cheap drill air use might be averaged/intermittent. Conditional 2.82/2.26 g/s conversions are not continuous-flow ratings',
            'No shaft-power data for the WUFU donors; no exhaust-temperature or outdoor cooling prediction is justified',
            'Visible cart controls do not establish dispatch date or final checkout availability',
            'Budget excludes load, coupling, regulator, collector, sensors and any added freight/tax',
            'No new CFD, Lean proof or motor/CAD fit verification'])
    (OUT/'motor-shopping-spec.json').write_text(json.dumps(result,indent=2))
    (OUT/'motor-shopping-validation.json').write_text(json.dumps(dict(status='passed',checks=len(checks),items=checks,
        scope='Conditional energy/path/mixing closure only; not qualification of a cheap motor'),indent=2))
    with (OUT/'motor-shopping-spec.csv').open('w') as file:
        w=csv.DictWriter(file,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    body=''.join(f'<tr><td>{r["flow_g_s"]:g}</td><td>{r["free_l_min_assumed_rho1_2"]:.0f}</td><td>{r["shaft_power_for20k_with25pct_heat_return_w"]:.0f}–{r["shaft_power_for30k_with25pct_heat_return_w"]:.0f}</td></tr>' for r in rows if r['flow_g_s']>=10)
    listings=''.join(f'<li><a href="{p["url"]}">{escape(p["name"])}</a>: ${p["listed_usd_ex_vat"]} + VAT / ₺{p["listed_tl"]:,}. Complete air drill; unqualified experimental donor.</li>' for p in products)
    return f'''<details class="compact-details" id="motor-shopping"><summary>Broader motor specification / Turkey under-$100 search</summary><p>Checked 28 Oct 2026. Search for continuous rotary pneumatic motors at about 5.5–6.3 bar running pressure. Practical band: 10–20 g/s with <strong>matched</strong> loaded shaft power of about 0.3–0.8 kW. This is a design starting point, not proof of the 20–50 cm target.</p><div class="formula-equation">ΔTmotor = (Pshaft − Qinto)/(ṁ cp)<br>Pshaft = ṁ cp ΔTmotor/(1 − α)</div><div class="table"><table><thead><tr><th>g/s</th><th>Free L/min</th><th>Shaft W for 20–30 K motor drop</th></tr></thead><tbody>{body}</tbody></table></div><p class="note">Table assumes cp=1006 J/kg K and heat pickup equal to 25% of shaft power. Air conversion uses assumed 1.2 kg/m³ free-air density. Prefer the upper drop band for warm motor inlet. A nozzle mixing/path screen is in the JSON; it assumes UA=1 W/K and 25% temperature-deficit retention. Neither is verified.</p><ul>{listings}</ul><p><strong>No qualified bare motor under $100 found.</strong> Both Turkish listings show enabled cart controls. Shaft power is missing. Listed air use is 141/113 L/min; if continuous free air, that is only 2.82/2.26 g/s. Exhaust collection and lubrication are unresolved. Do not buy these expecting the outdoor target to be established.</p><div class="links"><a href="motor-shopping-spec.json">Requirements / listing record</a><a href="motor-shopping-spec.csv">Calculation CSV</a><a href="motor-shopping-validation.json">20 balance checks</a></div></details>'''

if __name__=='__main__':build()
