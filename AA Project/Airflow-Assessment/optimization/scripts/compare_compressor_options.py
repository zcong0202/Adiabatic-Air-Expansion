"""Compare reported supply options, not measured cooling or equipment approval."""
from pathlib import Path
import json,math

OPT=Path(__file__).resolve().parents[1]
reference=json.loads((OPT/'results/thermo-meeting-review-2026-10-19.json').read_text())
watts100=reference['scenarios'][0]['dry_sensible_enthalpy_deficit_w']
source='https://www.bauer-kompressoren.de/de_de/junior-ii'
result={
 'date':'2026-10-19','basis':'User-supplied screenshot of 0929 slide 4; BAUER manufacturer product page checked separately.',
 'low_pressure':{'name':'Kaneez 10 HP 4-in-1','price_aed_from_user_slide':16500,
  'listed_supply_bar':[8,10],'listed_flow_l_min':[1000,1200],
  'flow_verified_as_FAD':False,'listed_receiver_l':400,
  'listed_electrical':'380 V three phase','nominal_motor_power_kw_10hp_conversion':10*745.7/1000,
  'dryer_and_filters':'Listed in screenshot; pressure dew point, oil carryover and outlet temperature unverified.',
  'supplier_primary_datasheet':'Exact manufacturer/model and FAD table not yet available.'},
 'high_pressure':{'name':'BAUER JUNIOR II','price_aed_from_user_slide':23500,
  'manufacturer_pressure_bar':[90,330],'manufacturer_delivery_l_min':100,
  'manufacturer_delivery_basis':'Cylinder filling 0 to 200 bar, +/-5 percent. Not 100 actual litres per minute at 200/330 bar.',
  'manufacturer_electric_models':{'II-E':'400 V three phase, 2.2 kW','II-W':'230 V single phase, 2.2 kW'},
  'purification':'P21','source_url':source,
  'direct_process_supply_approved':False,'subzero_cooling_achieved':False},
 'vortex_demand':{'Jeanoko_listing_l_min':200,'Jeanoko_flow_reference_basis':'Unstated; unmeasured.',
  'EXAIR_3208_reference_SLPM':227,'EXAIR_is_installed_unit':False,
  'note':'Compare on a common reference basis and measure the installed unit.'},
 'conditional_flow_ratios':{'Kaneez_vs_BAUER':[10,12],
  'Kaneez_vs_EXAIR_reference':[1000/227,1200/227],
  'BAUER_maximum_average_vortex_duty_if_demand_200_lpm':100/200,
  'BAUER_maximum_average_vortex_duty_if_demand_227_lpm':100/227,
  'assumptions':'Comparable free-air conditions, quoted delivery maintained, compressor duty permits replenishment, zero losses. Not a commissioning or duty rating.'},
 'illustrative_capacity_not_hardware_predictions':{
  'ambient_c':34,'cold_delivery_c':5,'assumed_vortex_cold_fraction':.5,
  'one_200_lpm_vortex_potential_w':watts100,
  'matched_larger_vortex_or_bank_on_1000_to_1200_lpm_potential_w':[watts100*5,watts100*6],
  'BAUER_100_lpm_all_flow_at_minus50_potential_w':reference['scenarios'][2]['dry_sensible_enthalpy_deficit_w'],
  'note':'Illustrates mass-flow leverage only. Larger cold throughput requires a matched converter/bank and measured cold delivery. A single existing vortex cannot consume the whole larger compressor output. No -50 C result is established.'},
 'recommendation':'Prefer a verified low-pressure continuous dry-air supply for existing vortex/nozzle tests and repeated demos. Rent or borrow an appropriately sized supply before purchase where practical. Consider BAUER for a separately validated cylinder-charging/expander experiment, not as a continuous replacement supply for the current nominal 200-227 L/min vortex.',
 'open_inputs':['Kaneez exact model and supplier datasheet: FAD at 8-10 bar, duty and dryer/filters losses','Actual vortex inlet pressure and temperature while flowing through the intended hose','Pressure dew point and oil carryover for intended cold minimum','Venue three-phase power, noise and heat location','Matched high-pressure expander flow/efficiency and approved supply arrangement if pursued'],
 'not_established':['Equipment purchase authorization','Achieved cooling power','Energy efficiency from motor nameplates','Pressure-vessel or high-pressure line design','Kaneez verified FAD','BAUER approved direct continuous process supply']}
assert result['conditional_flow_ratios']['BAUER_maximum_average_vortex_duty_if_demand_227_lpm']<.45
out=OPT/'results/compressor-options-2026-10-19.json';out.write_text(json.dumps(result,indent=2))
page=OPT.parents[1]/'project-overview.html';s=page.read_text();start='<!-- compressor-options-start -->';end='<!-- compressor-options-end -->'
if start in s:
 a=s.index(start);b=s.index(end,a)+len(end);s=s[:a]+s[b:]
block=f'''{start}
<section id="compressor-options"><div class="eyebrow">19 October · supplied slide comparison</div><h2>Choose air mass delivery for the current vortex demo</h2>
<p><strong>Recommendation, conditional:</strong> A verified low-pressure dry-air supply is the better fit for continuous testing of the installed vortex and nozzle. Renting or borrowing a suitable supply can establish performance before purchase. The high-pressure unit belongs to a separately validated charging/expander route.</p>
<div class="scroll"><table><tr><th>Item</th><th>Kaneez 10 HP 4-in-1</th><th>BAUER JUNIOR II</th></tr><tr><td>Pressure</td><td>8–10 bar, user slide</td><td>90–330 bar, manufacturer</td></tr><tr><td>Air delivery</td><td>Listed 1,000–1,200 L/min; FAD basis unverified</td><td>100 L/min; measured by cylinder filling 0–200 bar, ±5%</td></tr><tr><td>Electric supply</td><td>Listed 380 V three phase</td><td>II-E: 400 V three phase; II-W: 230 V single phase; 2.2 kW motor</td></tr><tr><td>Quoted purchase price</td><td>AED 16,500, from supplied slide</td><td>AED 23,500, from supplied slide</td></tr><tr><td>Current vortex compatibility</td><td>Likely ample supply if FAD is confirmed; verify inlet pressure under flow</td><td>Quoted flow below nominal 200–227 L/min vortex demand; storage cannot fix long-term mass deficit</td></tr></table></div>
<p><strong>Correction to the earlier 100 L/min screen:</strong> That budget applies to the BAUER route. The Kaneez listing claims 10–12 times that flow. Confirm comparable reference conditions before treating this ratio as delivered air.</p>
<p><strong>Installed-unit distinction:</strong> The Jeanoko listing says 0.2 m³/min with no stated reference conditions. The slide’s 227 SLPM is the EXAIR 3208 reference, not a measured Jeanoko consumption. At either approximate demand, a 100 L/min replenishment source does not sustain continuous full flow. An ideal loss-free duty budget is about 44–50%; the compressor’s approved operating duty and real system losses still apply.</p>
<p><strong>One vortex remains flow-limited:</strong> A larger compressor does not push its entire 1,000–1,200 L/min through the existing small vortex. Additional cold throughput needs a matched larger converter or multiple outlets. More available flow helps repeatability and operating continuity first.</p>
<p><strong>Illustration, not predicted hardware performance:</strong> At a 50% cold fraction and an achieved 5°C delivery temperature in 34°C ambient, one 200 L/min inlet vortex has about {watts100:.0f} W dry cold-stream sensible potential. A matched converter using 1,000–1,200 L/min would have about {watts100*5:.0f}–{watts100*6:.0f} W under those same assumptions. All of the BAUER flow at −50°C would give about {reference['scenarios'][2]['dry_sensible_enthalpy_deficit_w']:.0f} W. Neither the cold fraction nor these delivery temperatures has been demonstrated for these compressor systems.</p>
<p><strong>Pressure is not refrigeration:</strong> Buying a 200–330 bar compressor does not establish a −50°C or −100°C air source. A regulator and a work-producing expander have different energy balances. The latter requires a matched pressure/flow/efficiency map. The BAUER page describes a cylinder-filling system, not an approved direct continuous low-pressure process-air installation.</p>
<p><strong>Before purchase:</strong> Obtain the Kaneez exact model, guaranteed FAD at operating pressure, continuous-duty rating, dryer/filter losses, pressure dew point and oil carryover. Confirm voltage and site capacity. Then test inlet pressure and temperature at the vortex while flowing through the intended hose. If current cold output benefits from scuba-regulator precooling, do not assume a compressor-fed vortex reaches the same temperature.</p>
<p><strong>Energy boundary:</strong> A 10 HP nameplate is about 7.5 kW motor output; the BAUER electric motor is rated 2.2 kW. These are not measured wall power or cooling efficiency. The low-pressure route is a prototype/demo recommendation, not proof of an efficient final product.</p>
<p><a href="Airflow-Assessment/optimization/results/compressor-options-2026-10-19.json">Assumptions and comparison calculations</a> · <a href="{source}">BAUER manufacturer data</a> · <a href="Airflow-Assessment/vortex-reference.json">Installed Jeanoko and EXAIR reference distinction</a></p>
</section>
{end}'''
marker='<!-- thermo-review-start -->';assert marker in s
s=s.replace(marker,block+'\n'+marker,1)
if 'href="#compressor-options"' not in s:s=s.replace('<nav aria-label="Sections">','<nav aria-label="Sections"><a href="#compressor-options">Compressor options</a>',1)
page.write_text(s)
print(json.dumps({'result':str(out),'BAUER_maximum_ideal_vortex_duty':[100/227,.5],'illustrative_matched_LP_capacity_w':[watts100*5,watts100*6]},indent=2))
