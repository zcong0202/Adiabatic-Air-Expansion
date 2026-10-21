"""First-law screening of the 16 October meeting. NOT new CFD or hardware data."""
from pathlib import Path
import json,math

OPT=Path(__file__).resolve().parents[1]
OUT=OPT/'results/thermo-meeting-review-2026-10-19.json'
cp=1005.;R=287.05;pref=101325.;tref=293.15;ta=34.;target=6.
flow_lpm=100.;rho=pref/(R*tref);mass=rho*flow_lpm/60000
rows=[]
for tc in [5,-40,-50,-100]:
 span=ta-tc
 rows.append({'cold_delivery_temperature_c':tc,'cold_mass_flow_g_s':mass*1000,
              'dry_sensible_enthalpy_deficit_w':mass*cp*span,
              'cold_mass_fraction_for_6c_drop':target/span,
              'maximum_warm_to_cold_mass_ratio_for_6c_drop':span/target-1,
              'status':'Ideal dry mixing at final delivery pressure. Assumes ALL rated air reaches cold branch; not achieved hardware performance.'})
tau=.5
extra=tau*math.log((ta+100)/(ta+50))
stage_ratio=(200/5)**.25
stages=[200/(stage_ratio**i) for i in range(5)]
result={'date':'2026-10-19','meeting_date':'2026-10-16',
 'reference_air':{'pressure_pa':pref,'temperature_c':20,'density_kg_m3':rho,
                  'flow_l_min':flow_lpm,'mass_flow_kg_s':mass,
                  'rating_status':'Meeting assumption. Need compressor free-air delivery at working pressure; cold-branch fraction unmeasured.'},
 'dry_cp_j_kg_k':cp,'ambient_c':ta,'target_drop_c':target,'scenarios':rows,
 'exponential_example':{'equation':'DeltaT(t)=DeltaT(0)*exp(-t/tau)',
                        'tau_s_assumed_not_measured':tau,
                        'extra_time_above_same_threshold_minus100_vs_minus50_s':extra,
                        'capacity_ratio_minus100_to_minus50':(ta+100)/(ta+50),
                        'limitation':'Fixed-capacitance, fixed-conductance toy model. Not a validated jet warming law; no measured 0.5 s decay.'},
 'staging':{'absolute_inlet_bar':200,'absolute_outlet_bar':5,
            'maximum_stage_ratio_if_actual_hardware_limit':3,
            'minimum_stages_under_that_limit':math.ceil(math.log(200/5)/math.log(3)),
            'four_equal_ratio_stages_bar':stages,
            'note':'A maximum ratio of 3 is a proposed machine constraint, not a universal thermodynamic law. Use absolute pressures.'},
 'mixing_example':{'warm_temperature_c':20,'cold_temperature_c':0,
                   'cold_to_initial_warm_mass_ratio':.5,'mixed_temperature_c':20/1.5,
                   'cold_to_initial_warm_mass_ratio_for_10c_mix':1,
                   'note':'Adding mass to initial warm air. Replacing part of a fixed-volume region is a different problem. Actual volumes require density at their stated pressures and temperatures.'},
 'burst_example':{'cold_production_g_s':2,'burst_delivery_g_s':10,'pulse_s':3,
                  'delivered_mass_per_pulse_g':30,'minimum_cycle_period_s':15,
                  'maximum_duty_fraction':.2,'buffer_mass_swing_g_with_continuous_production':24,
                  'note':'Illustrative mass balance only. No heat leak, pressure loss or startup allowance; not a pressure-vessel design.'},
 'meeting_decisions_reported_by_user':{'no_DFF_shower_build':True,'primary_demo_artifact':'Video of existing tests; hose demo remains an option, decision due 19 October.'},
 'recommendation':'Measure installed cold-branch flow, final-pressure delivery temperature, target map, on/off response and wind. Improve delivery/nozzle against the local target. Add a buffer only for a specified peak/duty requirement. Treat expanders as a separate source feasibility project.',
 'limitations':['No new CFD','No source performance measurement','No demonstrated passive trapping of cold air for 3-4 seconds','No moist-air, real-gas or turbine efficiency calculation','No 200 bar pressure-system design'],
 'sources':[
 {'url':'https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node17.html','topic':'Throttling, enthalpy, insulated tank filling'},
 {'url':'https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node129.html','topic':'Conditions and time constant of lumped exponential heating'},
 {'url':'https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node28.html','topic':'Ideal work-producing expansion and mass-flow power'}]}
assert result['staging']['minimum_stages_under_that_limit']==4
assert abs(result['mixing_example']['mixed_temperature_c']-13.3333333333)<1e-8
assert all(abs((ta-r['cold_delivery_temperature_c'])/(1+r['maximum_warm_to_cold_mass_ratio_for_6c_drop'])-target)<1e-12 for r in rows)
OUT.write_text(json.dumps(result,indent=2))

page=OPT.parents[1]/'project-overview.html'
s=page.read_text();start='<!-- thermo-review-start -->';end='<!-- thermo-review-end -->'
if start in s:
 a=s.index(start);b=s.index(end,a)+len(end);s=s[:a]+s[b:]
table=''.join(f'<tr><td>{r["cold_delivery_temperature_c"]}°C</td><td>{r["dry_sensible_enthalpy_deficit_w"]:.0f} W</td><td>{100*r["cold_mass_fraction_for_6c_drop"]:.1f}%</td></tr>' for r in rows)
block=f'''{start}
<section id="thermo-review"><div class="eyebrow">19 October · meeting review</div><h2>Design around delivered cold-air mass and enthalpy</h2>
<p><strong>Assessment:</strong> A small cold stream can dilute rapidly. A universal 0.5-second lifetime is not established. Jet warming depends on entrainment, geometry, wind and supply. The existing steady CFD does not establish switch-off decay time or a 3–4 second trapped cold pocket.</p>
<p><strong>First-law screen:</strong> P = cold mass flow × cp × (ambient − cold delivery temperature). For dry mixing, target drop = (ambient − cold delivery temperature)/(1 + warm/cold mass ratio). Use delivery temperature after pressure release and hose heat pickup. These are energy balances, not new CFD.</p>
<div class="scroll"><table><tr><th>Cold delivery</th><th>Cold-stream sensible potential</th><th>Cold mass share for 6°C drop</th></tr>{table}</table></div>
<p>Assumptions: 34°C ambient; 100 L/min free air at 20°C and 1 atm ≈ {mass*1000:.2f} g/s; ALL of it becomes cold delivery flow. A vortex cold-branch split reduces these powers. No moisture load, wall heat gain or source-response losses. Values are not heat removed from a person or compressor efficiency.</p>
<h3>Explore dilution at the target</h3><p>Assumed local cold mass fraction, not a nozzle prediction. The model does not predict the mass fraction, distance, wind resistance, or cold-pocket lifetime.</p>
<p><label>Ambient <input id="thermoAmbient" type="range" min="20" max="40" step="1" value="34"> <span id="thermoAmbientValue"></span></label></p>
<p><label>Cold delivery <input id="thermoCold" type="range" min="-100" max="15" step="1" value="5"> <span id="thermoColdValue"></span></label></p>
<p><label>Cold mass flow <input id="thermoFlow" type="range" min="0.2" max="4" step="0.1" value="2"> <span id="thermoFlowValue"></span></label></p>
<p><label>Local cold mass share <input id="thermoFraction" type="range" min="0" max="100" step="1" value="20"> <span id="thermoFractionValue"></span></label></p>
<p id="thermoOutput" aria-live="polite"></p><p>Below-freezing scenarios are mathematical screens. Humidity, icing, density changes and the pressure system require separate analysis. Use a bench target before any personal demonstration.</p>
<p><strong>Continuous jet versus parcel lifetime:</strong> A steady cold region can exist while individual air parcels pass through it quickly. Continuous cold inflow balances warm-air replacement. The design does not require each parcel to remain cold for several seconds.</p><h3>Exponential model: what it establishes</h3><p>For an assumed fixed time constant, ΔT(t)=ΔT(0) exp(−t/τ). Time above a threshold is τ ln(ΔT(0)/ΔTthreshold). If τ were 0.5 s, lowering delivery from −50°C to −100°C at 34°C ambient adds {extra:.2f} s above the same threshold, while increasing sensible capacity by {(134/84-1)*100:.0f}% at fixed mass flow. The assumed τ is not measured or universal. A jet entrains additional mass and does not retain the fixed lump used in that model.</p>
<p><strong>Cold hose:</strong> A simplified steady line with a uniform ambient and constant properties has ΔTout = ΔTin exp[−UA/(cold mass flow × cp)]. Heat pickup along a long cold-delivery hose can therefore be substantial at low mass flow. Measure temperature at the final outlet and keep the cold-delivery path short or insulated. This line model is separate from turbulent open-jet mixing.</p><h3>Compare the three development routes</h3><div class="scroll"><table><tr><th>Route</th><th>Purpose</th><th>Decision</th></tr><tr><td>Nozzle and short cold delivery</td><td>Control coverage, momentum, dilution, leaks and heat pickup</td><td>First: compare at measured flow and temperature. No geometry creates additional cold-stream capacity.</td></tr><tr><td>Cold buffer</td><td>Trade charging time for a larger peak discharge</td><td>Only after choosing pulse flow, duration and duty. It cannot increase long-term cold production. A large outlet alone can reduce velocity and worsen reach.</td></tr><tr><td>Work-producing expansion</td><td>Lower source enthalpy while extracting shaft work</td><td>Separate feasibility study: actual flow, real-gas properties, expander efficiency, drying/icing, final delivery pressure and energy consumption.</td></tr></table></div>
<p><strong>Terminology:</strong> A regulator is approximately isenthalpic; an ideal turbine is isentropic. Ideal-gas throttling has no bulk temperature drop when inlet/outlet kinetic changes are negligible. Real air needs a real-gas calculation. An adiabatic nozzle can lower static temperature by increasing speed; that kinetic energy can later dissipate.</p>
<p><strong>Staging correction:</strong> 200 → 5 bar absolute is a 40:1 ratio. If each stage really is limited to 3:1, at least four stages are needed: 200 → 79.5 → 31.6 → 12.6 → 5 bar. The proposed three-stage example exceeds its stated limit. A threefold maximum is not a universal law.</p>
<p><strong>Meeting mixing example:</strong> Adding cold air at 0°C with half the mass of an initial 20°C air mass gives 13.3°C, not 10°C. A 10°C mixture needs equal cold and warm masses under that dry constant-cp model. Replacing warm air in a fixed region is a different flow problem.</p>
<p><strong>Meeting decisions reported by user:</strong> Do not commission DFF showers. Video of existing tests is the primary November artifact. A hose demonstration remains an option; its go/no-go decision was due 19 October. No demo choice is inferred here.</p>
<p><strong>Next experiment:</strong> Measure cold-branch mass flow and final-pressure delivery temperature with the attachment fitted. Map the existing 50 × 50 mm target at 200 mm during steady flow and valve on/off. Record ambient, wind and sensor response. Compare a heated patch with matched ambient-air flow to quantify useful sensible cooling. Retain the nozzle route if delivered cooling meets the target; size a buffer only if a measured peak-flow requirement exceeds the source.</p>
<p><strong>Open inputs:</strong> Compressor free-air delivery at its actual working pressure; cold-branch flow fraction; source temperature/pressure with each nozzle fitted; required cooled area, pulse duration and duty.</p>
<p><a href="Airflow-Assessment/optimization/results/thermo-meeting-review-2026-10-19.json">Calculation inputs and results</a> · <a href="https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node17.html">MIT: throttling and enthalpy</a> · <a href="https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node129.html">MIT: transient heating model</a> · <a href="https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node28.html">MIT: work-producing expansion</a></p>
<script>(()=>{{const ids=['Ambient','Cold','Flow','Fraction'];function update(){{const vals={{}};ids.forEach(id=>{{const e=document.getElementById('thermo'+id);vals[id]=Number(e.value);document.getElementById('thermo'+id+'Value').textContent=e.value+(id==='Flow'?' g/s':id==='Fraction'?'%':'°C')}});const span=vals.Ambient-vals.Cold,drop=vals.Fraction/100*span,power=vals.Flow/1000*1005*span;const o=document.getElementById('thermoOutput');o.textContent='Mixed air '+(vals.Ambient-drop).toFixed(1)+'°C · drop '+drop.toFixed(1)+'°C · cold-stream sensible potential '+power.toFixed(0)+' W · '+(drop>6?'above':'at or below')+' the >6°C target. '+(span<=6?'A drop above 6°C is unattainable at these delivery temperatures.':'Required local cold mass share for 6°C: '+(600/span).toFixed(1)+'%.');o.style.fontWeight='700'}}ids.forEach(id=>document.getElementById('thermo'+id).addEventListener('input',update));update()}})();</script>
</section>
{end}'''
marker='<!-- design-search-start -->';assert marker in s
s=s.replace(marker,block+'\n'+marker,1)
if 'href="#thermo-review"' not in s:s=s.replace('<nav aria-label="Sections">','<nav aria-label="Sections"><a href="#thermo-review">Thermodynamics</a>',1)
page.write_text(s)
print(json.dumps({'results':str(OUT),'mass_g_s':mass*1000,'scenarios':rows,'extra_toy_time_s':extra,'minimum_stages':4},indent=2))
