from pathlib import Path
import json
from xml.sax.saxutils import escape as esc
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
R=Path(__file__).resolve().parents[2];A=R.parent;r=json.loads((R/'results/cfd-cad-loop.json').read_text());by={x['case']:x for x in r['cases']};p=r['preferred_still_air_candidate'];proof=json.loads((A/'formal-model/proof-verification.json').read_text())
S=getSampleStyleSheet();S.add(ParagraphStyle(name='AA',fontName='Helvetica',fontSize=10,leading=13.6,spaceAfter=8,textColor=colors.HexColor('#163b4d')));S.add(ParagraphStyle(name='SmallAA',parent=S['AA'],fontSize=8,leading=10.5,spaceAfter=5));S.add(ParagraphStyle(name='EqAA',fontName='Courier',fontSize=9,leading=14,spaceAfter=10,backColor=colors.HexColor('#eff5f6'),borderPadding=7))
for x in ['Title','Heading1','Heading2']:S[x].textColor=colors.HexColor('#153f53')
S['Title'].fontSize=25;S['Title'].leading=29
story=[]
def text(x,style='AA'):story.append(Paragraph(x,S[style]))
def h(x):text(x,'Heading2')
def eq(x):text(esc(x).replace('\n','<br/>'),'EqAA')
def page(x):story.append(PageBreak());text(x,'Heading1')
def table(rows,widths):
 t=Table([[Paragraph(str(x),S['SmallAA']) for x in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3eff2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#cbdde3')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,8))
def image(name,w=507,h=None):
 q=R/'results'/name
 if q.exists():
  from PIL import Image as PIL
  if h is None:
   im=PIL.open(q);h=w*im.height/im.width
  story.append(Image(str(q),width=w,height=h))
text('AA / COMPUTATIONAL ITERATION / 19 OCTOBER 2026','SmallAA');text('Loaded air motors → targeted seat cooling','Title')
text('<b>Executed engineering models, not physical system validation.</b> The first loop couples the loaded-motor energy budget, conditional Lean proofs, transient 3D CFD and parametric nozzle CAD. The user accepted the reference seat dimensions: 0.9 × 0.85 × 1.8 m, open front, side panels and roof.')
if p:
 text(f'<b>Current still-air candidate:</b> {p["case"]}. {p["active_motors"]} active motors, {p["mass_g_s"]:.1f} g/s, {p["supply_c"]:.2f}°C calculated supply. Torso/neck fixed-box time means: <b>{p["torso_c"]:.2f} / {p["neck_c"]:.2f}°C</b>. The 20°C mean target {"passes" if p["target20_means_pass"] else "fails"} in this model. The largest saved neck-cell speed over the averaging window is {p["neck_speed_max_last4s"]:.2f} m/s.')
 text(f'The occupied region averages {p["occupied_c"]:.1f}°C. Only {p["neck_fraction_below20"]*100:.0f}% of the neck sampling volume is below20°C at the final output. This is local cooling, not a uniformly20°C enclosure.')
if p and not p['local_speed_screen_pass']:text(f'<b>Remaining design limit:</b> the conservative1 m/s peak-speed screen fails ({p["neck_speed_max_last4s"]:.2f}m/s). Neck mean varies {p["neck_range_last4s"]:.2f}K over the final window. This is a thermal candidate, not a design shown to meet every comfort/stability requirement.')
rows=[['Case / step','Torso mean','Neck mean','Neck peak speed']]
for name in ['C10_rear_final','C01_side_startup','C12_three_motor_final','C13_three_motor_fine','C20_three_motor_profile','C21_profile_halfCo_continuation','C22_four_motor_profile','C24_four_profile_continued']:
 if name in by:
  x=by[name];rows.append([name,f'{x["torso_c"]:.2f}°C',f'{x["neck_c"]:.2f}°C',f'{x["neck_speed_max_last4s"]:.2f}m/s'])
table(rows,[232,85,85,105])
text('Means use exact Cartesian-cell intersection volumes with fixed torso/neck boxes and trapezoid averaging over the last four saved seconds. The preliminary C01 case used an approximate pressure boundary. Final C10/C12 onward use the corrected hydrostatic atmosphere.','SmallAA')
image('seat-iteration-history.png',507,203)
page('1 / Mathematics and Lean')
eq('C = N * 0.0194 * 1006\nPshaft = N * 840\nTmotor = Tin - (Pshaft-Qmotor)/C\nTs = Ta + (Tmotor-Ta)*exp(-UA/C)\nQcold = C*(Ta-Ts)')
text('The model uses a paired catalogue operating point, not independent flow and temperature choices. Mass uses the document’s19.4g/s conversion of16.2 atmosphericL/s per motor; the exact reference state needs supplier confirmation. Tin =40°C; motor heat into air =0 in the nominal reference; UA ≈10.074 W/K. That UA reproduces the document’s4 K path gain with four motors at30°C ambient.')
table([['Operating mode','Free air','Shaft work','Supply / cold capacity'],['4 active motors','3.888m³/min','3.36kW','0.96°C / 2.27kW at30°C'],['3 active motors','2.916m³/min','2.52kW','About2.18°C / 1.63kW at30°C']], [145,100,100,162])
text('The three-motor candidate can use a four-installed architecture with one isolated source. The source calculation is conditional on the catalogue power/consumption pair being sustained. A suitable stock load assembly, supplier thermal map, drying and inlet-temperature control are still required. Returning the extracted shaft work as heat to the seat cancels its cooling benefit.')
eq('(Cz+W)*Tzone = Cz*Ts + W*Ta + L\nCz = captured_mdot*cp; W = warm_mdot*cp\nweighted_region_T = sum(cell_volume*T)/sum(cell_volume)\nIf Tmodel <= Tcomputed + error, target is met only\nwhen Tcomputed + error <= Ttarget.')
text(f'<b>{proof["printed_axiom_checks"]} printed Lean axiom checks pass.</b> Nine new CFD/design theorems check finite-region averaging, source-temperature limits, heat allowance, flow-area/speed limits, refinement ranking and the admissible temperature-error budget. All use standard Lean/mathlib foundations. No unproved placeholders or added physics axioms are used.')
if p:text(f'The selected case’s raw mean margin to20°C is only {p["combined_upward_error_budget_for20"]:.2f}K at the limiting region. Its margin to the separate legacy6 K cooling target is {p["combined_upward_error_budget_for_delta6"]:.2f}K. These are allowable upward-error budgets, not demonstrated physical error bounds.')
text('Lean does not prove the motor catalogue state, heat-transfer coefficients, turbulent flow, CFD convergence to the continuum solution, source uncertainty or human comfort. It proves the stated implications once their hypotheses hold.','SmallAA')
h('Reproduce and inspect')
text('Source: cfd/scripts/. Case dictionaries, meshes, native fields, run logs and audit.json remain in cfd/cases/. Summary: results/cfd-cad-loop.json. Proofs: ../formal-model/AAThermo/CFDDesign.lean plus build.log and proof-verification.json. CAD: cad/. Animation metadata lists the native temperature hashes and interpolation. The overview links all artifacts.','SmallAA')
text('Component evidence and the original first-law derivation remain in the earlier AA-motor-seat-viability.pdf and FIRST-PRINCIPLES.txt. All component ratings and cold-source states remain conditional engineering inputs.','SmallAA')
page('2 / CFD method and numerical checks')
text('OpenFOAM v2506 buoyantPimpleFoam solves transient, variable-density ideal-gas flow with gravity. The atmospheric model uses k-epsilon URANS and energy transport. A source-origin scalar tracks the supplied air. Panels, seat and ground are adiabatic. The block manikin adds100 W to the air; no independent fixed skin temperature is imposed.')
text('Domain: x =[-0.5,1.65]m, y =[-1,1]m, z =[0,2.2]m. The enclosure has0.9m clear width,0.85m depth and1.8m height. The body, seat and panels are resolved as rectangular solids. The two target air boxes lie up to20cm in front of the torso/head; these are air regions, not skin surfaces.')
text('The source uses four140 ×80mm side outlets centred at x=0.49m, y=±0.45m, z=0.84/1.24m. Uniform-patch cases screen placement and source count. The refined case transfers the CAD-linked internal nozzle’s predicted mean velocity and turbulence profile, then normalises each branch to the prescribed source mass flow.')
m=r['mesh_sensitivity']
if m:text(f'<b>Two-grid sensitivity:</b> {m["coarse_cells"]:,} versus {m["fine_cells"]:,} cells. Torso mean changes {m["torso_change_c"]:.3f}K; neck mean changes {m["neck_change_c"]:.3f}K. Both are below the declared0.5 K screen. This comparison uses uniform outlet profiles and does not establish a rigorous discretisation-error bound.')
if r.get('time_step_sensitivity'):
 t=r['time_step_sensitivity'];text(f'<b>Time-step/continuation check:</b> after the profile case, halve the Courant limit and continue5s. Torso/neck mean changes: {t["torso_change_c"]:.3f}/{t["neck_change_c"]:.3f}K. This combines continued physical evolution and time-step change; it is not an isolated restart-from-zero convergence study.')
text('The zero-flow hydrostatic test gives about0.001m/s residual velocity and less than0.00001 K temperature drift after2s. It led to replacement of the preliminary open-boundary approximation before final cases.')
text('Each accepted thermal case is checked for valid mesh, solver completion, finite/bounded fields, source mass, and integrated mass, source-tracer and energy closure. Energy checks include gravity and pressure work. They use saved1s fields and omit open-boundary diffusive heat and exact boundary kinetic interpolation. They are engineering conservation screens, not exact residual bounds.')
if p:
 b=p['conservation'];text('Selected-case conservation screen: mass {:.3f}%, source origin {:.3f}%, energy {:.3f}% of the respective injected-mass or source-cooling normalisation.'.format(100*b['mass_integral_error_relative_injected_mass'],100*b['origin_integral_error_relative_injected_mass'],100*b['energy_integral_error_relative_source_cooling']))
text('Wind cases may remain unsteady. Report the window range as well as its mean. A20s startup mean is not a long-duration outdoor performance guarantee. The animation interpolates actual1s temperature outputs; it does not add resolved turbulent motion.','SmallAA')
page('3 / CAD changed after internal CFD')
text('The first205mm-long nozzle expanded a50mm nominal spigot into a140 ×80mm slot. Its internal SST calculation showed large reverse flow and did not converge as a steady solution. It was rejected. A100mm inlet reduced the expansion ratio and removed reverse flow in the tested model.')
profile=R/'cfd/cases/N02_D100_transient/profile-audit.json'
if profile.exists():
 q=json.loads(profile.read_text());text(f'The100mm inlet candidate received a0.3s URANS follow-up from its steady initialization. Mean exit axial-speed CV is {q["axial_speed_CV"]:.3f}; its range over0.1–0.3s is {q["CV_range"]:.4f}. Reverse-flow area is {q["reverse_area_fraction"]*100:.1f}%. The actual nonuniform exit profile is fed back into the seat case.')
text('This short follow-up checks profile stability, not long-time internal-flow convergence. The four-motor mapped wind tests scale the three-motor exit-profile shape; that Reynolds-number sensitivity still needs a separate internal solve.')
image('slot-cad.png',300,310)
text('<b>Delivered flow body:</b>100mm nominal hose spigot,95.2mm clear inlet,140 ×80mm outlet,205mm total length,2.4mm nominal wall. STL is in millimetres. STEP declares metres and is re-import checked. The mesh is watertight, consistently oriented and one connected component.')
text('PLA /0.4mm nozzle starting settings:0.2mm layers,4–6 walls. Inspect support and overhangs in the slicer. The50mm body is retained as a rejected variant. The assembly STEP contains actual outlet bodies and assumed seat/body/source envelopes, not manufacturing drawings for commercial parts.')
text('The nominal hose fit, clamp retention, branching/flow balance, thermal insulation and motor interfaces are unverified. The printed body is for near-atmospheric exhaust flow. The high-pressure compressor, treatment, regulator and motor hardware remain commercial components.','SmallAA')
page('4 / Stress cases and next decision')
rows=[['Case / condition','Torso','Neck','Last4s range T/N','Mean20 target']]
for x in r['cases']:
 if x['case'].startswith(('C14','C15','C16','C17','C18','C19','C23','C26')):
  label=f'{x["case"].split("_")[0]}: '+(f'{x["wind_m_s"]:g}m/s {x["wind_direction"]}' if x['wind_m_s'] else 'panel+500W' if x.get('panel_heat_w') else f'supply{x["supply_c"]:.1f}°C; ambient{x["ambient_c"]:g}°C')
  rows.append([label,f'{x["torso_c"]:.1f}°C',f'{x["neck_c"]:.1f}°C',f'{x["torso_range_last4s"]:.1f}/{x["neck_range_last4s"]:.1f}K','pass' if x['target20_means_pass'] else 'fail'])
table(rows,[200,60,60,110,77])
image('seat-stress-tests.png',450,196)
text('These are separate sensitivities, not one combined worst case. The35°C ambient state keeps the motor inlet at40°C and recomputes path heat gain. It does not use the invalid45°C inlet assumption. The8°C source is an explicit heat-pickup stress, not an independently chosen turbine efficiency. C23 adds500 W prescribed panel-to-air heat globally as a rough heat-load sensitivity; it is not a solar ray-tracing or conjugate wall model.')
if r.get('domain_sensitivity'):
 d=r['domain_sensitivity'];text(f'Wind credibility check:170,302 cells in x[-1.3,2.5]m, y±1.8m, z[0,3]m; explicit ambient tangential inflow and5s continuation changes torso/neck means by {d["torso_change_c"]:+.2f}/{d["neck_change_c"]:+.2f}K versus the original side-wind window. This combines boundary/domain changes and further physical evolution; it is not an isolated discretisation-error bound.')
text('Some wind and panel-heating cases predict improved local cooling. Treat this as an unvalidated recirculation effect. It does not establish that wind or solar heating is beneficial. Longer averaging, far-field and turbulence checks remain necessary.')
h('What remains unresolved')
text('The selected design is a computational candidate. It does not establish a globally optimal or physically validated system. Major next checks: a full matched commercial motor-load/air-treatment assembly; the actual motor thermal state; collector and branch balance; longer wind statistics; domain, turbulence and profile-mesh sensitivities; solar/radiation and moist surfaces; and person heat-transfer/comfort.')
text('The present model cannot show that all1m³ around a person is cooled by10K. It supports local front-of-body air regions under stated conditions. Do not equate supplied air-cooling capacity with extra heat removed from a human.')
def footer(c,d):
 c.setStrokeColor(colors.HexColor('#c9d9df'));c.line(44,38,551,38);c.setFillColor(colors.HexColor('#5b737c'));c.setFont('Helvetica',8);c.drawString(44,25,'AA / CFD-CAD-Lean loop / Reference geometry / Hardware unvalidated');c.drawRightString(551,25,str(d.page))
out=R/'output/pdf/AA-seat-CFD-CAD-Lean-iteration.pdf';SimpleDocTemplate(str(out),pagesize=(595.28,841.89),leftMargin=44,rightMargin=44,topMargin=40,bottomMargin=48,title='AA seat CFD CAD Lean iteration',author='AA Project').build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
