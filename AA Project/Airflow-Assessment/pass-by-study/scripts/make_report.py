"""Presentation-ready note for the executed open-air reach screen."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'results/cfd-summary.json').read_text());by={r['case']:r for r in d['cases']}
proof=json.loads((R.parent/'formal-model/proof-verification.json').read_text())
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='AA',fontName='Helvetica',fontSize=10,leading=13.6,spaceAfter=8,textColor=colors.HexColor('#193c4f')))
styles.add(ParagraphStyle(name='SmallAA',parent=styles['AA'],fontSize=8,leading=10.5,spaceAfter=5))
styles.add(ParagraphStyle(name='EqAA',fontName='Courier',fontSize=9,leading=14,spaceAfter=10,backColor=colors.HexColor('#eef4f6'),borderPadding=6))
for name in ['Title','Heading1','Heading2']:styles[name].textColor=colors.HexColor('#194556')
story=[]
def text(s,style='AA'):story.append(Paragraph(s,styles[style]))
def eq(s):text(escape(s).replace('\n','<br/>'),'EqAA')
def page(s):story.append(PageBreak());text(s,'Heading1')
def image(name,width=507,height=None):
    path=R/'results'/name
    if not path.exists():return
    if height is None:
        from PIL import Image as PIL
        with PIL.open(path) as im:height=width*im.height/im.width
    story.append(Image(str(path),width=width,height=height));story.append(Spacer(1,7))
def table(rows,widths):
    rows=[[Paragraph(str(x),styles['SmallAA']) for x in row] for row in rows]
    obj=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
    obj.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2eef2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#c6d9e0')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(obj);story.append(Spacer(1,8))

text('AA / OUTDOOR PASS-BY / COMPUTATIONAL SCREEN / 21 OCTOBER 2026','SmallAA')
text('Cold air for people walking past','Title')
text('<b>Corrected use:</b> outdoor nozzles activate while people walk past. No seat, roof or enclosure is assumed. Study nearest nominal distances of20,35 and50cm. Valve opening is at most30s; each person crosses the jet much faster.')
text(f'<b>Executed:</b> {d["controls_completed"]} layout-distance controls plus {len(d["cases"])-d["controls_completed"]} refinement/sensitivity cases. This stage samples moving air patches through unconfined jets. <b>No human body, wake, skin heat transfer or hardware validation is included.</b>')
image('outdoor-layouts.png',507,290)
text('Same source and four nominal outlet faces in every control:77.6g/s total,0.96°C calculated supply,30°C ambient. Source state depends on the loaded motor/heat budget. It is not a manufacturer exhaust-temperature guarantee.')
text('One-side and two-side nozzles target assumed1.15/1.55m heights. Overhead nozzles stand20-50cm above the1.75m reference plane. Side and overhead incident patches differ; their numbers are not a global human-comfort ranking.')
text('The retired seat GIF and temperatures remain historical. They are not used to infer performance in this corrected outdoor scenario.','SmallAA')

page('1 / First principles and formal checks')
eq('mdot*(h_in-h_motor) = P_shaft - Q_into_air\nT_motor = T_in - (P_shaft-Q_into_air)/(mdot*cp)\nT_supply = T_a + (T_motor-T_a)*exp(-UA/(mdot*cp))\nQ_cold = mdot*cp*(T_a-T_supply)')
text('Nominal hypothesis:4 loaded LZB46 motors;19.4g/s and840W shaft work each; inlet40°C; nominal motor heat into air zero; cold-path UA about10.074W/K. This gives about0.959°C supply and2.267kW sensible cold-air power at30°C ambient. Exact flow reference state, thermal map, external shaft load, treatment and stock distribution remain unverified.')
eq('Pulse mass = mdot*t; free-air volume = 3.888*t/60\nAt 30s: 2.328kg; 1.944m3 free-air equivalent; about68kJ\nGeometric crossing time = cooled width / walking speed\nFor 0.30m and1.2m/s: 0.25s')
text('Cold-air energy supplied to outdoors is not heat removed from one person. The full nominal source is prescribed at the nozzle from startup. Upstream valve response, motor spin-up and cold-line cooldown are not resolved.')
text('A regulator approximates isenthalpic throttling; an ideal gas has no temperature drop from that alone. A loaded motor extracts shaft work and is irreversible. The current rated flow/work pair permits about43K motor temperature drop before heat pickup, not arbitrary-40/-100°C exhaust. A cold buffer changes timing; it does not stop mixing after discharge.','SmallAA')
eq('Ideal dry mixing: Delta = f_cold*(T_a-T_supply)\nDelta>6K requires f_cold>0.206606... at nominal source\nMoving area: Delta_A(t) = T_a - area_mean(T at A(t))\nDose_air = integral max(Delta_A,0) dt   [K s]')
text('Report peak deficit, total and longest continuous time above6K, and air-exposure dose. Neither K s nor cold-area coverage is joules removed from skin. The jet has no universal0.5s thermal lifetime: mixing, velocity, geometry and wind determine its evolution.')
text(f'<b>Lean/mathlib:</b> {proof["printed_axiom_checks"]} printed axiom checks pass, including seven new pass-by theorems. They check timing bounds, valve/exposure separation, air budgets, sampled dose and a cold-fraction threshold. No unproved placeholders or new physics axioms are introduced.')
text('Conditional error certificate: if actual air temperature is at most computed temperature plus e, then computed deficit greater than6+e implies actual deficit greater than6. The e=0,1,2,3K duration sensitivities are hypothetical error allowances, not proved physical bounds. Lean does not validate the CFD, the hardware or comfort.','SmallAA')

page('2 / Nine layout-distance comparisons')
rows=[['Layout / distance','Reference patch','Peak deficit','Total >6K','Longest >6K']]
for r in d['cases']:
    if not r['case'].startswith('P'):continue
    p=r['reference'];rows.append([f'{r["layout"]} /{r["distance_m"]*100:g}cm',r['reference_patch'],f'{p["peak_area_deficit_k"]:.2f}K',f'{p["time_above_delta6_s"]:.3f}s',f'{p["longest_continuous_above_delta6_s"]:.3f}s'])
table(rows,[145,100,85,85,92])
text('Common reference:1.2m/s; path x=-0.8 to+0.8m; centre crosses at5s after ideal nozzle startup. Each sample is a moving5x5cm air square. Side reference: y=-0.2m,z=1.15m. Overhead: z=1.75m,y=0. Every case also reports the other four air patches.','SmallAA')
image('layout-comparison.png',507,210)
text('The controls run for10s; selected early controls run for30s. Their common5s passage is compared above. Longer cases also sample15/28.5s centre arrivals;10s cases use8.5s late arrivals. These are ideal nozzle-on events within the user’s30s limit. Valve shutdown is not simulated.')
text('One-sided controls place two outlets along the path at each height; two-sided controls cover both sides at one along-path position. The overhead reference lies between jet rows; its trend likely reflects overlap as the jets spread. These geometry-specific air-probe results do not establish a best whole-person layout.','SmallAA')

page('3 / Nozzle refinement and wind')
text('Exploratory change:140x80mm horizontal slot to280x40mm. Four outlets keep the same total open area and prescribed mass flow, so nominal mean exit speed is unchanged. The wider shape may lengthen passage exposure; the thinner vertical footprint may reduce coverage. This is not free cooling capacity.')
rows=[['Case','Cells','Peak deficit','Total >6K','Band area >6K']]
for name in ['P01_one_d35','R00_wide_d35','F00_base_d35','F01_wide_d35','W00_wide_opposed','L00_row4_d35','S00_row4_source8']:
    if name not in by:continue
    r=by[name];p=r['reference'];b=r['incident_air_band_snapshot'];rows.append([name,f'{r["cells"]:,}',f'{p["peak_area_deficit_k"]:.2f}K',f'{p["time_above_delta6_s"]:.3f}s',f'{b.get("area_above_delta6_m2",0):.3f}m2'])
table(rows,[170,75,85,85,92])
image('refinement-comparison.png',507,195)
text('Band area is a5s air snapshot on the same y=-0.2m plane, across x=-0.8..0.8m and z=1.0..1.7m. It guards against improving one small patch while losing vertical coverage. It is not a skin surface. The wind case imposes0.5m/s ambient wind against the one-sided jets.')
for label in ['base','wide']:
    if label in d['refinement']:
        q=d['refinement'][label];text(f'{label.title()} two-grid change: peak deficit {q["peak_deficit_change_k"]:+.2f}K; total time above6K {q["total_duration_change_s"]:+.3f}s. This is a sensitivity, not a rigorous error bound.','SmallAA')
text('No global optimum is established. A variant must retain useful coverage and exposure under source, grid, domain, turbulence and wind uncertainty. Actual internal loft loss/profile, the commercial branch network and a moving person remain separate checks.','SmallAA')
text('L00 puts four140x80mm outlets at one height, x=±0.2/±0.6m, instead of two heights. This trades vertical coverage for more along-path encounters. S00 keeps that geometry and flow but raises supply to8°C, equivalent to about550W extra net motor/path heat pickup; it is not a measured source state.','SmallAA')

page('4 / Aim and cold-core displacement')
text('In the horizontal50cm case, the coldest sampled point is about7cm below the original outlet height at the incident plane. This can reduce a fixed-height reading even while colder air remains nearby. The core-location estimate is limited by the coarse CFD grid; fine plotting interpolation does not add resolution.')
image('cold-core-height.png',370,245)
if 'A00_pitch8_d50' in by:
    rows=[['50cm case','Peak area deficit','Total >6K','Longest >6K']]
    for name in ['P02_one_d50','A00_pitch8_d50']:
        p=by[name]['reference'];rows.append([name,f'{p["peak_area_deficit_k"]:.2f}K',f'{p["time_above_delta6_s"]:.3f}s',f'{p["longest_continuous_above_delta6_s"]:.3f}s'])
    table(rows,[200,102,102,103])
image('pitch-comparison.png',507,215)
text('The8° test prescribes an oblique velocity on the original vertical slot patches. It does not resolve physically tilted CAD faces. Normal source flow is nominally unchanged; total velocity rises by1/cos(8°), about1%. The native mass-flow gate checks the actual source. This is an aim sensitivity, not proof that8° is optimal.','SmallAA')

page('5 / CFD method, evidence and limits')
text('OpenFOAM v2506 buoyantPimpleFoam solves transient dry perfect-gas flow with gravity, k-epsilon URANS, energy and a source-origin scalar. The domain is x=±1.25m,y=±1.1m,z=0..2.7m. It contains ground and short nozzle blocks only. All other boundaries are open; there is no seated or standing obstacle.')
text('Uniform slot inflow uses a5% turbulence-intensity hypothesis. Atmospheric pressure and initial p/p_rgh follow the hydrostatic ideal-gas profile. A zero-source rest test gives less than0.0005m/s spurious speed and less than0.000001K temperature drift. Every case passes checkMesh before solving.')
text('Native probes use cellPoint interpolation at about25ms output intervals. Moving traces use linear spatial/time interpolation and3x3 Gauss quadrature across5cm squares. Trace sampling at5ms does not add solver resolution. Native full fields are saved each second and supply conservation checks and animation.')
text('Numerical screens test completion, final native snapshot, finite/bounded fields, source mass and integrated mass, origin and energy closure. The closure integral uses1s output over the final5s. It includes gravity and pressure work but omits open-boundary diffusion and exact boundary kinetic interpolation. These are engineering screens, not proof of continuum accuracy.')
failed=[r['case'] for r in d['cases'] if not r['numerical_screens_pass']]
text(f'Case numerical-screen failures: {", ".join(failed) if failed else "none"}. Results and per-gate values remain in each audit.json. The completed meshes, dictionaries, fields, logs and probe traces are retained locally.')
text('<b>Material limits:</b> no body blockage or wake; no human heat-transfer comparison; ideal prescribed source; no actual line cooldown or switching; one turbulence closure; finite outdoor domain; limited grid refinement; no moisture, icing or radiation. A walking air probe is not a moving person simulation.')
text('Next model: retain supported layouts, add an upright moving body or verified equivalent method, compare skin heat transfer against ambient flow, and resolve practical source/valve/line startup. No purchase, physical build or hardware performance certification follows from this screen.')
text('Reproduction: scripts/open_flow.py builds cases; analyse.py audits fields and moving patches; summarize.py builds tables/plots; FIRST-PRINCIPLES.txt gives editable equations. The exact pinned Docker image and case inputs are in run-status.json/case.json.','SmallAA')

page('6 / Prototype CAD and handover')
image('outdoor-nozzle-assembly.png',410,415)
text('Delivered prototype variants:140x80mm and280x40mm outlets. Both use a100mm nominal slip spigot,95.2mm clear inlet,205mm total length and2.4mm nominal wall. STL uses millimetres; STEP uses metres and is independently reimported/remeshed for unit checks. Each printable mesh is watertight, consistently oriented and one connected component.')
text('Bambu H2S / PLA /0.4mm nozzle: start0.2mm layers and4-6 walls. Check overhangs/supports and fit coupons in the slicer. No G-code is supplied. Hose fit, clamps, stands and commercial adapters are unverified. The part is a near-atmospheric exhaust prototype, not a high-pressure component.')
text('CAD and external CFD share outlet dimensions. The full internal nozzle loft is not resolved by this pass-by campaign. Wider-slot internal losses and actual exit uniformity must be checked before treating it as an improved physical nozzle.','SmallAA')

def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#c9dbe2'));canvas.line(44,38,551,38);canvas.setFillColor(colors.HexColor('#5b7580'));canvas.setFont('Helvetica',8);canvas.drawString(44,25,'AA / Open-air reach screen / No human body or hardware validation');canvas.drawRightString(551,25,str(doc.page))
out=R/'output/pdf/AA-outdoor-pass-by-screen.pdf';out.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(out),pagesize=(595.28,841.89),leftMargin=44,rightMargin=44,topMargin=40,bottomMargin=48,title='AA outdoor pass-by CFD screen',author='AA Project').build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
