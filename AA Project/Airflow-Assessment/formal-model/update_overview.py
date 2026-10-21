"""Add the formal-model work to the ONE existing AA project overview."""
from pathlib import Path
import json,html

ROOT=Path(__file__).parent
page=ROOT.parent.parent/'project-overview.html'
data=json.loads((ROOT/'parameter-results.json').read_text())
proof=json.loads((ROOT/'proof-verification.json').read_text())
checks=json.loads((ROOT/'numerical-verification.json').read_text())
assert proof['build_succeeded'] and checks['passed']
prefix='Airflow-Assessment/formal-model/'

def number(id,label,value,step='1',minval=None,maxval=None):
 bounds=(' min="'+str(minval)+'"' if minval is not None else '')+(' max="'+str(maxval)+'"' if maxval is not None else '')
 return f'<label for="af{id}">{label}<input id="af{id}" type="number" value="{value}" step="{step}"{bounds}></label>'
def select(id,label,items,selected=None):
 opts=''.join(f'<option value="{html.escape(str(v))}"'+(' selected' if v==selected else '')+f'>{html.escape(str(t))}</option>' for v,t in items)
 return f'<label for="af{id}">{label}<select id="af{id}">{opts}</select></label>'
def slider(id,label,value,minval,maxval,step):
 return f'<label for="af{id}">{label} <strong id="af{id}Value"></strong><input id="af{id}" type="range" min="{minval}" max="{maxval}" step="{step}" value="{value}"></label>'

source_controls=''.join([
 select('Mode','Source method',[('manual','Measured / assumed cold outlet'),('vortex','Vortex: assumed paired cold operating point'),('ideal_throttle','Ideal-gas isenthalpic regulator'),('real_throttle','Real-gas isenthalpic regulator (EOS lookup)'),('ideal_expander','Ideal-gas expander + final regulator'),('real_expander','Real-gas expander + final regulator (EOS lookup)')],'manual'),
 select('Provider','Inlet supply budget',[('current','Current nominal 200 L/min — unmeasured'),('lp','Kaneez assumed 1,100 L/min FAD — unverified'),('bauer','BAUER quoted 100 L/min cylinder-fill rate')],'current'),
 number('Demand','Required total inlet flow (reference L/min)',200,10,.1),
 slider('Beta','Vortex cold fraction (vortex mode only)',.5,.1,.9,.05),
 number('Mass','Cold mass flow (g/s; manual mode only)',2,.1,.01),
 number('Cold','Cold source temperature (°C; manual/vortex)',5,1,-170,100)])
thermo_controls=''.join([
 select('Tin','Source inlet temperature (°C)',[(25,'25'),(34,'34'),(40,'40')],34),
 select('Pin','Source inlet ABSOLUTE pressure (bar)',[(9,'9 bar(a), about 8 bar(g)'),(11,'11 bar(a), about 10 bar(g)'),(201,'201 bar(a), about 200 bar(g)')],9),
 select('Pmid','Expander exit ABSOLUTE pressure (bar)',[(1.01325,'1.01325: direct atmospheric delivery'),(5,'5: then isenthalpic release to 1.01325'),(7.9,'7.9: then isenthalpic release to 1.01325')],1.01325),
 select('Eta','Isentropic efficiency of EACH stage',[(.4,'0.4'),(.6,'0.6'),(.8,'0.8')],.6)])
delivery_controls=''.join([
 number('Ambient','Reference ambient (°C)',34,1,20,45),
 number('Warm','Entrained air / line surroundings (°C)',34,1,20,70),
 slider('Alpha','Area-average cold-origin fraction αA',.3146377977016922,0,1,'any'),
 slider('UA','Downstream line/nozzle heat conductance UA',0,0,3,.05),
 number('Delta','Strict target drop (°C)',6,.5,.1,30)])
advanced=''.join([
 slider('Capture','Cold-source mass captured by target (uniform model)',.6,.05,1,.01),
 number('WarmFlow','Fixed warm inflow (g/s; uniform model)',5,1,0,200),
 number('Load','Extra sensible heat load (W; uniform model / energy budget)',0,1,0,1000),
 number('Speed','Assumed minimum NORMAL target speed (m/s)',1,.1,.01,10),
 number('Width','Target width (mm; original goal 50)',50,10,1,1000),
 number('Height','Target height (mm; original goal 50)',50,10,1,1000),
 number('Duty','Requested on-time / cycle-time',1,.05,.01,1),
 number('Pulse','Pulse duration (s; ideal buffer inventory)',3,.5,.1,60)])
rows=''.join(f'<tr><td>{100*r["area_cold_fraction"]:.1f}%</td><td>{r["source_max_c_at_2g_s_UA_0p2"]:.1f}°C</td></tr>' for r in data['reconfiguration_thresholds'])
states=[]
for method,pin,pmid in [('real_throttle',9,1.01325),('real_throttle',201,1.01325),('real_expander',9,1.01325),('real_expander',201,5)]:
 state=next(r for r in data['source_lookup'] if r.get('method')==method and r.get('inlet_temperature_c')==34 and r.get('inlet_pressure_bar_abs')==pin and (method=='real_throttle' or r.get('expansion_exit_bar_abs')==pmid and r.get('per_stage_isentropic_efficiency')==.6))
 path=f'{pin} → {pmid:g}'+(' → 1.01325' if pmid!=1.01325 else '')+' bar(a)'
 states.append(f'<tr><td>{"Regulator" if method=="real_throttle" else "Work-producing expansion"}</td><td>{path}</td><td>{state["expander_stage_count"]}</td><td>{state["final_source_temperature_c"]:.1f}°C</td></tr>')

start='<!-- formal-model-start -->';end='<!-- formal-model-end -->'
block=f'''{start}
<section id="formal-model"><div class="eyebrow">Lean 4 · mathematical design envelope</div><h2>Which parameters make more than 6°C possible?</h2>
<p><strong>Completed:</strong> Lean {proof['lean_version']} + pinned mathlib: {proof['printed_axiom_checks']} theorem axiom checks; {checks['count']} numerical conservation and limiting-case checks passed. The formal algebra, finite-cell area mean, heat-leak bounds, ideal expansion and storage budgets are checked. Actual source maps, nozzle entrainment, EOS numerics and hardware performance remain unverified.</p>
<div class="stateflow"><span>Source<br>flow, pressure, cold fraction, method</span><b>→</b><span>Cold path<br>heat leakage / mass flow</span><b>→</b><span>Target at 200 mm<br>area fraction, capture, wind</span><b>→</b><span>Dose<br>pulse and supply duty</span></div>
<p><strong>Core area equation:</strong> ΔT<sub>A</sub> = T<sub>a</sub> − T<sub>e</sub> + α<sub>A</sub>(T<sub>e</sub> − T<sub>s</sub>) exp[−UA/(ṁ<sub>c</sub>c<sub>p</sub>)]. Success means ΔT<sub>A</sub> &gt; 6°C across the original 50 × 50 mm area at 200 mm. This equation requires the stated dry pointwise mixing law and a common cold-delivery temperature; Lean also proves the finite-cell area averaging identity.</p>
<p><strong>Inputs are not independent in real hardware:</strong> a vortex’s cold fraction changes its cold temperature; nozzle geometry changes pressure loss and source flow; wind and geometry change α<sub>A</sub> and capture. The calculator does not invent those maps. Changing flow while holding α<sub>A</sub> fixed is a sensitivity assumption.</p>
<details><summary>Does exponential heating impose a universal 0.5-second limit?</summary><p>No. For a separate lumped parcel model ΔT(t)=ΔT₀ exp(−t/τ), Lean proves that ΔT(t)&gt;δ exactly when t&lt;τ ln(ΔT₀/δ). The time constant τ depends on heat transfer and geometry; turbulent entrainment needs a flow model. A 0.5-second reheating observation would not by itself establish τ=0.5 s.</p><p>Illustration only: at 34°C ambient and assumed τ=0.5 s, an initially 5°C, −40°C or −100°C parcel remains more than 6°C below ambient for less than 0.788 s, 1.256 s or 1.553 s respectively. The extra time from −40°C to −100°C is 0.297 s under this same assumed τ. Colder air still carries more sensible cooling per kg. These times are not predictions for this jet.</p><p>A steady jet continuously replaces air; it need not keep the same parcel cold for 3–4 seconds. At 200 mm, transit time is roughly distance / representative stream speed. Distribution and source cooling rate govern continuous delivery. A buffer raises peak flow but leaves dilution and average production constraints.</p></details>
<style>.af-controls{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:18px 0}}.af-controls label{{display:block;font-size:14px;font-weight:600}}.af-controls input[type=number],.af-controls select{{display:block;width:100%;margin-top:5px;border:1px solid var(--line);border-radius:6px;padding:8px;font:inherit;background:#fff;color:var(--ink)}}.af-controls input[type=range]{{display:block;width:100%;margin-top:14px}}.af-results{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:18px 0}}.af-results>div{{padding:18px;background:#edf5f7;border:1px solid var(--line);border-radius:9px}}.af-results strong{{font-size:23px;display:block}}#afMap{{display:block;width:100%;max-width:780px;height:auto}}#afError{{color:#a53932;font-weight:700}}@media(max-width:760px){{.af-controls,.af-results{{grid-template-columns:1fr}}}}</style>
<h3>Try a complete candidate configuration</h3><div class="tabs">
<button type="button" data-af-preset="current">Current assumptions</button><button type="button" data-af-preset="lp">LP supply · one vortex</button><button type="button" data-af-preset="bauer">BAUER · one vortex</button><button type="button" data-af-preset="bank">LP supply · larger vortex/bank</button><button type="button" data-af-preset="jt">HP regulator</button><button type="button" data-af-preset="lpExp">LP expander</button><button type="button" data-af-preset="hpExp">HP expander</button></div>
<div class="af-controls">{source_controls}</div>
<p class="sub">Manual mode uses the entered cold mass and temperature. Vortex mode uses inlet flow × chosen cold fraction, but assumes the entered cold temperature is achievable. Regulator/expander modes use the whole chosen inlet flow. Increasing compressor capacity alone does not increase one vortex’s throughput.</p>
<details><summary>Pressure-method parameters</summary><div class="af-controls">{thermo_controls}</div><p>All pressures are absolute. Final delivery is 1.01325 bar(a). Each expansion stage uses the entered efficiency. Stage count is the minimum under an <em>assumed</em> 3:1 maximum ratio; this is not a universal turbine law. No interstage heat pickup is modeled. Real-gas choices are exact entries in a precomputed dry CoolProp lookup; no interpolation or fallback is hidden.</p></details>
<h3>Delivery and target mixing</h3><div class="af-controls">{delivery_controls}</div>
<p class="sub">Default α<sub>A</sub>=0.3146378 comes from the uncalibrated R07 CFD at 2 g/s, 5°C source, 35°C ambient and still air. The 34°C default here is a dry scalar sensitivity, not a new CFD run. UA=0 is an adiabatic screen. Keep temperature measurement location and modeled downstream heat gain consistent.</p>
<p id="afError" role="alert"></p>
<div class="af-results"><div><span>Area-average target criterion</span><strong id="afAreaResult"></strong><p id="afAreaStatus"></p></div><div><span>Candidate cold source</span><strong id="afSourceResult"></strong><p id="afSourceDetail"></p></div><div><span>Required delivery quality</span><strong id="afFractionResult"></strong><p id="afFractionDetail"></p></div><div><span>Mean air-production budget</span><strong id="afSupplyResult"></strong><p id="afSupplyDetail"></p></div></div>
<p id="afLimits"></p><div class="warn" id="afWarnings"></div>
<h3>Flow versus dilution envelope</h3><canvas id="afMap" width="780" height="360" aria-label="Conditional temperature-drop map versus cold flow and area fraction"></canvas><p class="sub">Line = exact 6°C boundary of the displayed model; points above it pass the strict target. Dot = chosen flow/fraction. Colours show temperature drop, not statistical confidence. Source temperature is held fixed as mass varies. This is not a prediction of how the nozzle changes mixing.</p>
<details><summary>Alternative uniform-target mass model, energy budget and pulse sizing</summary><div class="af-controls">{advanced}</div><p id="afMassResult"></p><p id="afEnergyResult"></p><p>The uniform model uses captured cold flow η<sub>capture</sub>ṁ<sub>c</sub> and a specified warm inflow. Its minimum mass is distinct from the hose-only mass bound. The energy-flux bound is necessary only and assumes normal speed everywhere exceeds the entered lower bound, with nonnegative local cold deficits. No hot spots or skin heat-transfer result is certified.</p></details>
<h3>Ways to re-establish the system</h3><div class="scroll"><table><tr><th>Knob</th><th>What it can do</th><th>What must be established</th></tr><tr><td>Improve α<sub>A</sub> and capture</td><td>Less dilution or better coverage can meet the target at a warmer source.</td><td>Measure the target map; use appropriate CFD for geometry, wind and flow.</td></tr><tr><td>Increase cold mass</td><td>More cooling power, lower line heat gain per kg; better temperature at fixed warm load.</td><td>Lean proves no loss-free temperature gain if cold and warm inflow scale together. Source temperature and entrainment may change.</td></tr><tr><td>Reduce UA</td><td>Preserve the source temperature through the cold path.</td><td>Measure before/after line temperature at the same mass flow; avoid double-counting losses.</td></tr><tr><td>Change source method</td><td>Work extraction can reduce enthalpy of all delivered flow; vortex splits cold/hot flow.</td><td>Matched source maps, real-gas states, drying/icing, pressure installation and input power.</td></tr><tr><td>Add a buffer</td><td>Higher peak flow for a chosen pulse.</td><td>Average production still bounds duty. Ideal inventory output is mass, not a pressure-vessel drawing.</td></tr></table></div>
<h3>Required source temperature if dilution is poorer</h3><p>34°C reference/entrainment, source mass 2 g/s, assumed UA=0.2 W/K. Source must be strictly colder than the boundary. These rows hold α<sub>A</sub> fixed; no nozzle/source map is implied.</p><div class="scroll"><table><tr><th>Area cold fraction</th><th>Source-temperature boundary</th></tr>{rows}</table></div>
<h3>Source-method examples, not purchased-equipment performance</h3><p>Dry real-gas Air model, 34°C inlet. Expander rows assume 60% efficiency per stage and a 3:1 ratio cap. A final regulator releases to atmospheric pressure. Floats/EOS are not formally verified in Lean. Output is a low-velocity thermodynamic state, not a prediction of a thermometer inside a high-speed nozzle.</p><div class="scroll"><table><tr><th>Method</th><th>Absolute pressure path</th><th>Expansion stages</th><th>Final source state</th></tr>{''.join(states)}</table></div>
<p><strong>Interpretation:</strong> Low-pressure air also contains expansion work potential. High pressure is not a prerequisite for a work-producing cooling stage. The source map and throughput decide whether an actual machine is suitable. A regulator-only 9 bar(a) route in this dry calculation cannot reach a 6°C drop even before dilution; ideal-gas throttling has no bulk temperature drop.</p>
<details><summary>Standalone boundary plots</summary><img src="{prefix}parameter-boundaries.png" style="width:100%" alt="Conditional source-temperature and mass-flow design boundaries"></details>
<p><strong>Next measured inputs:</strong> Paired cold mass and temperature with the chosen attachment; final-pressure state and measurement location; target temperature/normal-speed map; hot-exhaust exposure and wind; cold-line heat pickup. For November, validate the existing source/delivery before committing to a new pressure or storage architecture.</p>
<p><a href="Airflow-Assessment/AA-Lean-feasibility-model.zip">Lean model, calculator sources and report ZIP</a> · <a href="{prefix}MODEL-GUIDE.txt">Equations, parameter guide and interpretation</a> · <a href="{prefix}AAThermo/Model.lean">Lean theorems</a> · <a href="{prefix}AAThermo/Certificates.lean">Conditional scenario certificates</a> · <a href="{prefix}proof-verification.json">Proof/dependency record</a> · <a href="{prefix}numerical-verification.json">Numerical checks</a> · <a href="{prefix}parameter-results.json">All inputs and results</a> · <a href="{prefix}build.log">Lean build log</a></p>
<p class="sub">Proof scope: standard Lean/mathlib foundational axioms only, no new physics axioms or unproved placeholders. EOS numerical correctness, source feasibility, moisture, turbulence, wind and human comfort are not established by these proofs.</p>
<script id="aaFormalData" type="application/json">{json.dumps(data,separators=(',',':'))}</script><script>{(ROOT/'viewer.js').read_text()}</script>
</section>
{end}'''
s=page.read_text()
if start in s:
 a=s.index(start);b=s.index(end,a)+len(end);s=s[:a]+s[b:]
marker='<!-- compressor-options-start -->';assert marker in s
s=s.replace(marker,block+'\n'+marker,1)
if 'href="#formal-model"' not in s:s=s.replace('<nav aria-label="Sections">','<nav aria-label="Sections"><a href="#formal-model">Lean model & parameters</a>',1)
s=s.replace('Prototype record · Updated 15 Oct 2026','Prototype record · Updated 19 Oct 2026')
page.write_text(s);print(page)
