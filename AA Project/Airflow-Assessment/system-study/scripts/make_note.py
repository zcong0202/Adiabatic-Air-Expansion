"""Create the first-principles technical note from actual saved results."""
from pathlib import Path
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle,Preformatted
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
r=json.loads((ROOT/'results/campaign.json').read_text());rows=r['cases'];chosen=r['selected_case'];cfg=r['config'];proof=json.loads((ROOT.parent/'formal-model/proof-verification.json').read_text());cad=json.loads((ROOT/'cad/cad-verification.json').read_text())
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyAA',fontName='Helvetica',fontSize=10.2,leading=14,spaceAfter=8,textColor=colors.HexColor('#263e4a')));styles.add(ParagraphStyle(name='TitleAA',fontName='Helvetica-Bold',fontSize=22,leading=27,spaceAfter=16,textColor=colors.HexColor('#173947')));styles.add(ParagraphStyle(name='SubAA',fontName='Helvetica-Bold',fontSize=12,leading=16,spaceBefore=8,spaceAfter=7,textColor=colors.HexColor('#176b76')));styles.add(ParagraphStyle(name='SmallAA',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=6,textColor=colors.HexColor('#546875')))
story=[]
def p(t):story.append(Paragraph(t,styles['BodyAA']))
def h(t):story.append(Paragraph(t,styles['TitleAA']))
def sub(t):story.append(Paragraph(t,styles['SubAA']))
def image(path,width=500):
 from PIL import Image as PI
 w,hh=PI.open(path).size;story.append(Image(str(path),width=width,height=width*hh/w));story.append(Spacer(1,8))
def eq(name):image(ROOT/'results/equations'/f'{name}.png',490)
def table(data,widths):
 cells=[[Paragraph(str(x),styles['SmallAA']) for x in row] for row in data];t=Table(cells,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8f1f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#a2bdc5')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#d9e4e8'))]));story.append(t);story.append(Spacer(1,10))
def new():story.append(PageBreak())

h('AA outdoor cooling\nFirst principles and computational design')
p('<b>19 October 2026. No hardware currently available.</b> This note links stock-component constraints, Lean proofs, executed CFD and custom nozzle CAD. It supports a computational shortlist and a clear research presentation.')
sub('The demonstration objective')
eq('target')
p('A = 0.05 x 0.05 m. Place the target plane 0.20 m from the final outlet. Reference ambient is 34 C. First assess still air. Aim for at least 7 C in the declared stress screen, to leave a 1 C design margin.')
image(ROOT/'results/system-architecture.png')
table([['Evidence','What it establishes'],['Lean','Consequences of explicit mathematical assumptions.'],['CFD','A numerical flow/scalar solution under its stated physics and boundaries.'],['Stock maps','Approximate supplier operating points. Assembly performance remains conditional.'],['CAD','A watertight flow body corresponding to the tested cone. Fitted adapter remains open.']], [95,410])
p('Meeting scope: movable hose demonstration, compressor remote, localized release, no shower construction. Cooling a cubic metre or proving whole-body comfort requires a separate objective.')
p('For a person, heat transfer also depends on surface area and h: extra heat removal = h*A*air-temperature improvement at fixed h. An illustrative assumed h=20 W/(m2 K) and a 6 C improvement across 25 cm2 give only 0.30 W. This is not a comfort prediction. Source cold enthalpy flow is not heat delivered to skin.')
new()

h('1. Conservation laws define the limits')
eq('continuity');eq('energy')
p('Mass cannot disappear. A continuous source must supply the delivered mass. The steady energy balance accounts for heat transfer, shaft work and kinetic energy. The detailed momentum and total-energy PDEs appear in the editable FIRST-PRINCIPLES.txt source.')
sub('Three different source mechanisms')
eq('regulator')
p('<b>Regulator:</b> isenthalpic in the low-speed adiabatic approximation. Ideal air keeps the same bulk temperature. Real air can cool through the Joule-Thomson effect. Its final state requires a real-gas calculation.')
eq('expander')
p('<b>Expander:</b> extracts shaft work. Isentropic expansion is its ideal limit. Use Kelvin and absolute pressure. A hypothetical efficiency does not identify a stock machine. No matched commercial turbine chain enters the build shortlist.')
eq('vortex')
p('<b>Vortex:</b> splits the inlet into hot and cold branches. The dry no-work energy balance is T_in = beta*T_c + (1-beta)*T_h. The supplier curve, not that identity alone, determines a candidate cold operating point.')
new()

h('2. Cold flow and temperature must change together')
image(ROOT/'results/source-operating-map.png')
table([['Cold fraction','Cold flow*','Nominal cold state'],['0.6','2.73 g/s','-13.78 C'],['0.7','3.19 g/s','-5.44 C'],['0.8','3.64 g/s','+4.00 C']], [120,140,245])
p('*227 reference L/min inlet, converted using an assumed 20 C and 1 atm reference. The source map uses the approximate EXAIR family curve at 100 psig and a 34 C source inlet. Its application to the selected 3208 generator and full assembly needs confirmation.')
p('Jeanoko remains a historical comparison. Its listing does not supply a verified paired flow/temperature map. EXAIR data cannot calibrate it.')
sub('Stock selection status')
p('The current computational candidate uses an EXAIR 3208 reference source. Compressor, receiver, dryer, filter, regulator, valve and hoses remain commercial parts. The quoted Kaneez dryer dew point and pressure-specific FAD are still open. Manufacturer CAD and outlet bore/thread are needed before fitting the custom nozzle.')
new()

h('3. The nozzle preserves and distributes cold enthalpy')
eq('line');eq('area');eq('threshold')
p('Ts is the source before the modeled cold-path heat gain. Td is after it. Te is the simplified entrained-air and wall-surroundings temperature. UA is total conductance in W/K. The current sensitivity uses UA = U times nozzle wall area.')
p('Alpha_A is the area-average cold-origin fraction over the target. It differs from the vortex split beta and from the fraction of source mass captured by the target. CFD must recompute it after flow or geometry changes.')
sub('The five main design controls')
table([['Control','Useful effect','Coupling'],['Source flow','More cold power and less heat pickup per kg.','Changes velocity, pressure loss and entrainment.'],['Source temperature','More cooling per kg.','Changes with vortex cold fraction.'],['Nozzle diameter / angle','Changes coverage and mixing.','Also changes length and wall heat pickup.'],['Insulation / cold-path length','Preserves delivery temperature.','U remains a declared input until characterized.'],['Hot exhaust location','Lowers entrained temperature.','The present hot-air reservoir is a sensitivity, not a resolved plume.']], [115,190,200])
p('A passive adiabatic nozzle exchanges static enthalpy and kinetic energy. It cannot remove stagnation enthalpy. A cold static-temperature reading in fast flow needs a clear measurement interpretation.')
new()

h('4. Nominal success can disappear under stress')
eq('uniform');eq('robust')
p('For the uniform alternative, eta_c is source capture and m_w is warm inflow. It is a different model from the nonuniform area mean. Scaling cold and warm flows equally leaves the loss-free mixture temperature unchanged. Lean checks that implication.')
p('The robust dry bound assumes alpha_A >= alpha_min, retention >= r_min, source contrast >= S_min, and Ta-Te >= -H. Lean proves the resulting lower bound. It does not establish that physical variation obeys the chosen envelopes.')
p('<b>Concrete Lean certificate:</b> effective area fraction at least 27%, source flow at least 2.4 g/s, UA at most 0.16 W/K, source contrast Te-Ts at least 36 K, hot-air offset at most 2 K, and moisture warming at most 0.5 K imply a drop of at least 6.5396 K. The exponential bound uses exp(x) >= 1+x. Supplier/CFD/moisture bounds remain hypotheses.')
table([['Declared screen','Value'],['Source performance','20% smaller supplier temperature drop; inlet 4 K above ambient.'],['Delivery / entrainment','Surroundings and entrained air 2 K above ambient; U = 20 W/(m2 K).'],['Flow and mixing','Fresh CFD at 90% source flow; an additional 10% erosion of calculated area fraction.'],['Moisture','80% ambient RH; assumed +3 C pressure dew point at the vortex inlet.']], [145,360])
p('The moisture companion conserves dry-air mass, water and enthalpy. It allows equilibrium liquid condensation at the target. It does not solve droplets, ice or wet walls. These are one-way corrections on the computed dry flow.')
sub('Exponential heating has no universal 0.5-second limit')
eq('exposure')
p('The fitted time constant tau depends on transfer area, thermal mass and flow. Turbulent dilution needs its own flow description. A steady jet continuously replaces air parcels. It does not need to keep one parcel cold for the whole demonstration.')
new()

h('5. Executed recursive CFD campaign')
image(ROOT/'results/iteration-history.png')
table([['Case','Source / outlet','Nominal drop','Stress minimum','Numerical gates'],*[[(x['case'].split('_')[0]+('f' if x['case'].endswith('_fine') else '')),f"beta {x['beta']:.1f}, {x['diameter_mm']:g} mm"+(' / low flow' if 'lowflow' in x['case'] else ''),f"{x['nominal_dry_drop_c']:.2f} C",f"{x['stress_min_drop_c']:.2f} C",'pass' if x['numerically_accepted'] else 'FAIL'] for x in rows]], [45,170,85,95,110])
p('Every changed source flow or geometry gets a new numerical solve. The decision changes source cold fraction first when baseline margin fails, then tests the low-flow corner and widens the outlet if needed. A passing design receives a mesh refinement when the six-case budget permits.')
p('Acceptance checks include mesh quality, solver completion, residuals, native mass/scalar balance, bounded source scalar, target stability and full-field stability. Failed cases cannot enter the ranking. The conservative pressure screen includes maximum internal static pressure plus inlet kinetic head.')
p(f"Selected computational geometry: <b>{chosen['case']}</b>. Its declared stress minimum is <b>{chosen['stress_min_drop_c']:.2f} C</b>. Numerical acceptance is separate from physical validation and global optimization.")
p(f"At its nominal target plane, CFD gives {chosen['target_plane_flow']['captured_cold_origin_g_s']:.2f} g/s cold-origin flow plus {chosen['target_plane_flow']['entrained_origin_g_s']:.2f} g/s entrained-origin flow. These are incoming flow rates, not a cubic-metre inventory. The area mean and mass-flux-weighted mean remain different.")
new()

h('6. The geometry has traceable CAD and field data')
image(ROOT/'results/nozzle-cad.png',400)
table([['Parameter','Value'],['Inlet / outlet bore',f"8 / {cad['outlet_bore_mm']:g} mm"],['Cone half angle / total length',f"{cad['half_angle_deg']:g} degrees / {cad['total_length_mm']:.1f} mm"],['Radial wall thickness','2 mm'],['Files','Editable STEP, millimetre STL, parameterized OpenSCAD, verification JSON.'],['Fit status','Flow body only. EXAIR outlet adapter and installed mounting geometry remain unverified.']], [165,340])
p('The flow body is a printable computational prototype. CFD matches its internal contour but omits the exterior body and idealizes the outlet lip as zero thickness. The printed 2 mm lip needs 3D checking. The 8 mm source interface is an abstraction. The historical Milton/Jeanoko fit does not establish EXAIR fit.')
image(ROOT/'results/target-field.png',220)
new()

h('7. Supply and buffer change duty, not average capacity')
eq('duty')
table([['Supply','One 227 L/min source','Key limit'],['Kaneez quoted 1000-1200 L/min','Passes ideal flow budget.','Pressure-specific FAD, total electrical input and dryer performance remain unverified.'],['BAUER 100 L/min','At most 44.1% ideal duty.','A 3 s pulse needs at least a 6.81 s period. Process supply and duty need confirmation.']], [145,160,200])
p('For a 3 s pulse against 100 L/min replenishment, the ideal inlet mass swing is 7.65 g on the assumed common reference basis. A stock receiver can support that swing. Its actual volume depends on pressure window, transient gas cooling, line losses and minimum regulator pressure.')
p('Smaller stock sources remain alternatives: EXAIR 3202 lists 57 L/min and could pass the BAUER ideal continuous mass budget. Model 3204 lists 113 L/min, giving 88.5% ideal duty. Their target reach, dilution and buoyancy require new CFD. The 44.1% limit applies to the studied 3208, not every stock source.')
p('A cold buffer adds heat leakage and charging/withdrawal balances. It can increase peak flow, but cannot increase average cold production or prevent dilution after release.')
p('A mean-density Darcy screen for 10 m of compressed feed at 7.9 bar(a) predicts about 0.128 / 0.044 / 0.019 bar loss for 8 / 10 / 12 mm hose IDs at one source demand. Add stock fitting, dryer, filter and regulator losses. These are screening calculations, not guaranteed installed flow.')
p('At the beta=0.6 reference point, cold sensible potential is about 131 W. Ideal isothermal compression of its full inlet feed already requires at least 825 W in this model. Actual electrical input is higher. This ratio is not measured COP or heat removed from a person. The 10 HP motor conversion also does not establish electrical demand. Remote placement leaves local vortex noise to assess.')
sub('Computational stopping condition')
p('Promote a candidate only within its declared model envelope. The next models are 3D variable-density flow with buoyancy, crosswind, hot exhaust and valve transients. Then add wall heat transfer and person heat transfer. Hardware validation remains a later stage.')
new()

h('8. Evidence, reproducibility and presentation claims')
p(f"<b>Lean:</b> pinned Lean 4.31.0 and mathlib v4.31.0. The successful build records {proof['printed_axiom_checks']} theorem axiom checks. No new physics axioms or unproved placeholders. The kernel checks symbolic implications, including the new conservative area-envelope, nozzle energy and isothermal inventory identities.")
p('<b>Execution:</b> the OpenFOAM 2506 Docker image is pinned by SHA-256. Case input files, raw logs, saved profiles, gate audits, case decisions and CAD verification remain in the project. The model uses dry, constant-density, axisymmetric still-air flow with passive temperature deficit. Moisture and wall heating are separate numerical sensitivities.')
sub('Claims supported now')
p('We can compare source/nozzle candidates under explicit equations, supplier curves and declared stress ranges. We can identify infeasible supply/duty combinations. We can check numerical consistency and produce a traceable computational shortlist.')
sub('Claims still open')
p('Actual source-map accuracy, fitted mounting, final pressure loss, icing, local exhaust/noise, gust tolerance, electrical efficiency, skin heat removal and comfort. No claim of a finished outdoor cooling product or a globally optimal design follows from this campaign.')
sub('Suggested six-slide research narrative')
p('1. Local temperature objective and meeting scope.<br/>2. Conservation laws and regulator/vortex/expander distinction.<br/>3. Stock source map and compressor mass budget.<br/>4. Nozzle CFD, stresses and the failed baseline.<br/>5. Recursive design changes and matching CAD.<br/>6. Evidence limits and the next computational tests.')
sub('Primary sources and project files')
for url in ['https://www.exair.com/vt.html','https://www.bauer-kompressoren.de/de_de/junior-ii','https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node17.html','https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node28.html']:
 story.append(Paragraph(f'<link href="{url}" color="#176b76">{url}</link>',styles['SmallAA']))
p('Editable formulation: FIRST-PRINCIPLES.txt. Equations: results/equations/ (LaTeX JSON, SVG and PNG). Inputs: config.json. Executed decisions: results/campaign.json. Proofs: ../formal-model/AAThermo/. CAD: cad/. Reproduction: README.txt.')

def footer(canvas,doc):
 canvas.setStrokeColor(colors.HexColor('#c6d8de'));canvas.line(42,35,553,35);canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#546875'));canvas.drawString(42,23,'AA / Computational research / 19 Oct 2026 / Hardware unvalidated');canvas.drawRightString(553,23,str(doc.page))
doc=SimpleDocTemplate(str(OUT/'AA-first-principles-and-design.pdf'),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=48,title='AA first principles and computational design',author='AA project')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT/'AA-first-principles-and-design.pdf')
