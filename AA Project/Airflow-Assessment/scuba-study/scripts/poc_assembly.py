"""Document-grounded POC assembly and conditional inventory/load calculations.

No new CFD, Lean proof, pressure-component qualification or hardware test.
"""
from pathlib import Path
import json
import math
from CoolProp.CoolProp import PropsSI
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

STUDY = Path(__file__).resolve().parents[1]
OUT = STUDY / 'results'


def build():
    pa, temp, volume = 101325., 295.15, .012
    fill, cutoff = pa + 200e5, pa + 20e5
    rho_fill = PropsSI('D', 'P', fill, 'T', temp, 'Air')
    entropy = PropsSI('S', 'P', fill, 'T', temp, 'Air')
    usable = {
        'adiabatic': volume * (rho_fill - PropsSI('D', 'P', cutoff, 'S', entropy, 'Air')),
        'isothermal': volume * (rho_fill - PropsSI('D', 'P', cutoff, 'T', temp, 'Air')),
    }
    rows = []
    for name, hp, lpm in [('AM0701', .9, 750), ('AM0706', 3.6, 3700)]:
        shaft = hp * 745.6998715822702
        mass = lpm / 60000 * 1.2
        rows.append(dict(model=name, power_screen_w=shaft, assumed_mass_g_s=mass*1000,
                         assumed_free_air_l_min=lpm, assumed_free_air_scfm=lpm/28.316846592,
                         mass_10s_g=mass*10000,
                         inventory_only_s={k: v/mass for k,v in usable.items()},
                         complete_10s_pulses={k: int(v/(mass*10)) for k,v in usable.items()},
                         torque_if_screen_power_at_3000rpm_nm=shaft/(3000*2*math.pi/60),
                         load_heat_10s_kj=shaft*10/1000))
    # Cv -> effective Cd*A from its water definition: US gpm at 1 psi loss.
    cda_per_cv = (3.785411784e-3/60) / math.sqrt(2*6894.757293/1000)
    gamma, gas_r, cv = 1.4, 287.05, .23
    choked_factor = math.sqrt(gamma)*(2/(gamma+1))**((gamma+1)/(2*(gamma-1)))
    valve_mass = cv*cda_per_cv*(pa+6e5)/math.sqrt(gas_r*temp)*choked_factor
    # Illustrative flywheel only. This is not a fabrication specification.
    inertia = .5*1.*.1**2
    omega = 3000*2*math.pi/60
    flywheel_energy = .5*inertia*omega**2
    for row in rows:
        row['illustrative_flywheel_spinup_s'] = flywheel_energy/row['power_screen_w']
    result = dict(
        checked_on='2026-11-02', status='Concept assembly; hardware flow remains unqualified',
        tank_reference=dict(volume_l=12, volume_status='Assumed from meeting/reference, not confirmed by source documents',
                            fill_bar_g=200, initial_c=22, cutoff_bar_g=20,
                            cutoff_status='Planning assumption; actual regulator dropout depends on flow',
                            usable_mass_kg=usable), motors=rows,
        flow_assumptions=['Both motor volume ratings treated as free air at 1.2 kg/m3',
                          'Maximum shaft power and airflow are screening combinations, not confirmed paired points',
                          'Inventory scenarios exclude purging, warm-up, leaks, pressure droop and icing',
                          'Tank temperature does not set motor inlet temperature'],
        existing_supply=dict(first_stage='Documented ~9–10 bar; generic diving set, flow map unknown',
                             secondary='ARO R37121-600-VS', secondary_listed_scfm=59,
                             secondary_rating_basis='Retail listing; reference pressure/drop not verified',
                             solenoid='USS-PSV00041', solenoid_cv=.23, solenoid_max_bar=8,
                             exact_motor_supply_pass=False),
        valve_screen=dict(model='Ideal-gas orifice analogy from water Cv, not IEC/ISA vendor sizing',
                          pressure_upstream_bar_g=6, temperature_c=22,
                          choked_mass_g_s=valve_mass*1000,
                          meaning='About 6.45 g/s only with a large pressure loss. This does not deliver 6 bar downstream. Actual gas expansion factors/geometry require vendor data.',
                          full_flow_15_or_74_g_s_supported_by_existing_valve=False),
        flywheel=dict(illustrative_mass_kg=1, illustrative_radius_m=.1, illustrative_speed_rpm=3000,
                      inertia_kg_m2=inertia, stored_energy_j=flywheel_energy,
                      meaning='Absorbs energy only while accelerating. A steady-speed flywheel is not a continuous load. Not a build prescription.'),
        equations=dict(shaft='Pshaft = torque * omega', flywheel='Pstorage = I * omega * domega/dt; E = I*omega^2/2',
                       motor='T0_in - T0_out = (Pshaft - Qinto)/(mdot*cp)',
                       tank='time_inventory = usable_mass / mdot'),
        assembly=['Restrained cylinder and compatible rated diving first stage',
                  'Manual isolation; secondary pressure control and overpressure protection within lowest downstream rating',
                  'Supplier-required air preparation, suitably rated flowmeter and full-flow test valve; automatic fail-closed valve for controller integration',
                  'Motor inlet pressure and bulk-temperature measurement, under running flow',
                  'One motor at a time, rigidly mounted; shaft coupling and guard to rated dynamometer or matched generator/load bank',
                  'Manufacturer-approved exhaust collector; pressure/temperature measurement',
                  'Short insulated large-bore exhaust path; low-backpressure passive nozzle',
                  'Bench target with 20 cm and 50 cm temperature/velocity measurement'],
        gates=['Do not connect 200 bar or documented 9–10 bar first-stage outlet directly to a 1–7 bar motor',
               'Replace/re-size Cv 0.23 valve for full screened motor flow; pressure rating and thread size do not establish flow capacity',
               'AM0706 full-flow screen exceeds listed 59 SCFM secondary-regulator rating; replace/re-size regulator and verify first-stage capacity',
               'AM0701 demand is below secondary catalogue figure, but actual droop, first-stage flow and valve/line losses remain unqualified',
               'Confirm exact shaft/port sizes, collected exhaust, lubrication, cold-temperature and backpressure limits before fitted assembly',
               'Keep POC exhaust away from people until oil carryover and delivered temperature are qualified',
               'Guard rotating parts; provide rated brake/load cooling and shut off air on loss of load or overspeed'],
        vortex='A powered vortex tube is a separate comparison branch from regulated compressed air. Do not put it in the near-atmospheric motor exhaust. A passive swirl tip is a different nozzle and must be assessed for backpressure/mixing.',
        validation='Numerical EOS and algebra checks only. No new CFD or Lean proof.',
    )
    assert 0 < usable['adiabatic'] < usable['isothermal']
    assert 6 < valve_mass*1000 < 7
    assert rows[0]['assumed_free_air_scfm'] < 59 < rows[1]['assumed_free_air_scfm']
    assert abs(flywheel_energy-246.74011002723395) < 1e-8
    for row in rows:
        assert abs(row['torque_if_screen_power_at_3000rpm_nm']*omega-row['power_screen_w']) < 1e-8
    (OUT/'poc-assembly-calculations.json').write_text(json.dumps(result, indent=2)+'\n')
    draw(result)
    write_html(result)
    print(json.dumps({'inventory': usable, 'motors': rows, 'valve_screen_g_s':valve_mass*1000}, indent=2))


def draw(result):
    ink, air, work, alert = '#15191d', '#087e8b', '#b06b10', '#b14720'
    fig, ax = plt.subplots(figsize=(19.2,10.2))
    fig.patch.set_facecolor('white')
    ax.set(xlim=(0,19.2), ylim=(0,10.2)); ax.axis('off')
    ax.text(.35,9.7,'Scuba tank → loaded motor → passive nozzle',fontsize=24,weight='bold',color=ink)
    ax.text(.35,9.2,'POC assembly concept · test one motor at a time · exact supply flow remains unqualified',fontsize=12,color='#555')
    def box(x,y,w,h,title,body,edge=ink):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.04,rounding_size=.06',facecolor='#fafafa',edgecolor=edge,lw=1.5))
        ax.text(x+w/2,y+h-.30,title,ha='center',va='center',fontsize=11,weight='bold',color=edge)
        ax.text(x+w/2,y+.49,body,ha='center',va='center',fontsize=10,color=ink,linespacing=1.45)
    def arrow(a,b,color=air):
        ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='-|>',lw=2.5,color=color))
    xs=[.4,3.3,6.2,9.1,12.,15.2]
    boxes=[('CYLINDER','200 bar reference\n12 L assumed',ink),
           ('DIVING FIRST STAGE','~9–10 bar in documents\nRated cylinder connection',ink),
           ('PRESSURE CONTROL','~6 bar(g) design target\nSecondary regulator + relief',alert),
           ('FLOW CONTROLS','Sized valve + flowmeter\nAir preparation as required',alert),
           ('ONE LOADED MOTOR','AM0701 or AM0706\nMeasure inlet P and T',ink),
           ('EXHAUST → NOZZLE','Approved exhaust collector\nShort insulated wide path',ink)]
    for i,(x,(title,body,edge)) in enumerate(zip(xs,boxes)):
        box(x,6.9,2.35,1.55,title,body,edge)
        if i<5: arrow((x+2.41,7.65),(xs[i+1]-.08,7.65))
    arrow((17.62,7.65),(18.75,7.65))
    ax.text(18.25,8.2,'20–50 cm\nbench target',ha='center',fontsize=10,color=air)
    ax.text(5.5,6.35,'ARO listed: 59 SCFM. Full-flow AM0706 screen: 131 SCFM.',fontsize=11,color=alert)
    ax.text(5.5,5.95,'Owned Cv 0.23 valve: restrictive. Replace/re-size for screened motor flow.',fontsize=11,color=alert)
    arrow((13.17,6.8),(13.17,5.25),work)
    ax.text(13.4,5.8,'Rotating shaft\nAligned, rated coupling + guard',fontsize=10,color=work,va='center')
    box(10.45,3.45,5.5,1.7,'CONTINUOUS SHAFT LOAD','Rated dynamometer / brake\nor matched generator + electrical load bank',work)
    arrow((16.,4.25),(18.45,4.25),work)
    ax.text(17.3,4.8,'Reject load heat\naway from cold air',ha='center',fontsize=10,color=work)
    ax.text(.45,5.0,'A flywheel is not a continuous load.',fontsize=17,weight='bold',color=ink)
    ax.text(.45,4.5,'It stores work while speed rises. At steady speed, storage power is zero.',fontsize=11,color=ink)
    ax.text(.45,3.95,'Continuous cooling needs work removed continuously: P = torque × speed.',fontsize=11,color=ink)
    ax.text(.45,3.4,'The load is attached to the shaft. Air goes through the motor and exhaust.',fontsize=11,color=ink)
    y=2.6
    ax.text(.45,y,'Conditional screen',fontsize=11,weight='bold');ax.text(5.6,y,'AM0701',fontsize=11,weight='bold');ax.text(9.1,y,'AM0706',fontsize=11,weight='bold')
    for j,(label,vals) in enumerate([
        ('Free-air assumption / mass flow',('750 L/min · 15 g/s','3700 L/min · 74 g/s')),
        ('Screened shaft-load power',('0.67 kW','2.68 kW')),
        ('12 L / 200 bar / 22°C inventory-only time',tuple('%.0f–%.0f s'%(min(r['inventory_only_s'].values()),max(r['inventory_only_s'].values())) for r in result['motors']))]):
        yy=y-.45*(j+1);ax.text(.45,yy,label,fontsize=11);ax.text(5.6,yy,vals[0],fontsize=11);ax.text(9.1,yy,vals[1],fontsize=11)
    ax.text(.45,.55,'A vortex tube needs its own regulated compressed-air branch. It is not the passive nozzle shown above.',fontsize=11,color=air)
    ax.text(.45,.12,'Engineering concept, not a qualified build drawing. No new CFD. Confirm flow, motor exhaust/lubrication, interfaces and pressure protection.',fontsize=9,color='#555')
    fig.tight_layout(pad=.3)
    fig.savefig(OUT/'poc-assembly.svg',metadata={'Date':None})
    fig.savefig(OUT/'poc-assembly.png',dpi=145)
    plt.close(fig)


def write_html(result):
    rows=''.join('<tr><td>{model}</td><td>{assumed_mass_g_s:.0f} g/s*</td><td>{power_screen_w:.0f} W*</td><td>{lo:.0f}–{hi:.0f} s</td><td>{mass_10s_g:.0f} g</td></tr>'.format(**r,lo=min(r['inventory_only_s'].values()),hi=max(r['inventory_only_s'].values())) for r in result['motors'])
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Scuba motor POC assembly</title><style>body{font:16px/1.5 system-ui,sans-serif;color:#15191d;margin:0;background:#fff}main{max-width:1180px;margin:auto;padding:30px 24px}h1{font-size:32px;letter-spacing:-1px}h2{font-size:21px;margin-top:34px}a{color:inherit;text-underline-offset:3px}p{max-width:950px}img{width:100%;height:auto}table{border-collapse:collapse;width:100%;font-size:15px}td,th{padding:12px 10px;border-bottom:1px solid #ddd;text-align:left}nav{display:flex;gap:20px;flex-wrap:wrap;font-size:14px}summary{cursor:pointer;font-weight:600}small,.note{color:#555;font-size:14px}.table{overflow:auto}li{margin:8px 0}code{background:#f3f3f3;padding:2px 5px}@media(max-width:600px){main{padding:20px 14px}h1{font-size:27px}}</style><main><nav><a href="../../../project-overview.html#scuba-source">Project overview</a><a href="poc-assembly.png">PNG</a><a href="poc-assembly.svg">Editable SVG</a><a href="poc-assembly-calculations.json">Calculations</a><a href="../evidence/poc-assembly/document-audit.json">Document evidence</a></nav><h1>Scuba motor POC assembly</h1><p><strong>The tank is a plausible source. The existing full supply path is not yet adequate for the screened motor flows.</strong> Start with AM0701, one motor at a time. The current valve needs replacement/re-sizing for the screened flows. AM0706 also exceeds the secondary regulator’s listed flow; plan a larger regulator unless its manufacturer curve qualifies the required operating point.</p><img src="poc-assembly.svg" alt="Scuba tank through two pressure stages and sized flow controls to a loaded motor, collected exhaust and passive nozzle; guarded shaft coupling to external load"><h2>What the documents establish</h2><p><a href="../../../Project-Documents/0730.pptx">0730, slides 7–8</a> identifies a 200 bar cylinder, generic diving first stage at 130–150 psi, and an ARO R37121-600-VS secondary regulator. <a href="../../../1008.pptx">1008, slide 5</a> shows an 8–10 bar first-stage line. The first-stage outlet exceeds the motors’ published 7 bar range. Secondary pressure control is required.</p><p>The ARO regulator is <a href="https://www.amazon.com/dp/B0057D8LMY">listed at 59 SCFM</a>. Screened AM0701 demand is 26.5 SCFM, AM0706 130.7 SCFM. A catalogue figure alone does not establish acceptable pressure droop. Exact diving-regulator flow remains unknown.</p><p>The <a href="../../../Controller-App/dist/AA%20Controller%20Mac/BoM%20-%20Procurement%20List.pdf">controller BoM</a> identifies the owned USS-PSV00041 valve: 12 V, normally closed, ¼ NPT, max 8 bar, Cv 0.23. An ideal-orifice Cv analogy gives only about 6.45 g/s at 6 bar(g) upstream even with choked discharge. This is an illustrative restriction screen, not a vendor-certified flow limit. It does not maintain 6 bar downstream. Replace/re-size it for full-flow motor tests.</p><h2>Inventory and load</h2><div class="table"><table><thead><tr><th>Motor</th><th>Air mass</th><th>Shaft power</th><th>Inventory-only time</th><th>10 s pulse</th></tr></thead><tbody>ROWS</tbody></table></div><p class="note">*Assumed free-air basis and coincident advertised power/flow. Reference tank: 12 L, 200 bar(g), 22°C, cutoff 20 bar(g). Volume is not verified in the documents. Runtime spans separate adiabatic/isothermal real-air inventory scenarios. Purging, warm-up, leaks, pressure droop and icing reduce usable test time. Neither motor nor regulator is hardware-qualified by this table.</p><p>Attach the motor and a rated load unit to a rigid common base. Use an aligned shaft coupling selected for the exact shaft size, torque and speed. Guard the rotating parts. A dynamometer/brake absorbs shaft work as heat. A generator needs an electrical load bank; an unloaded generator is not enough. Size mechanical input and heat rejection, including generator losses. Keep rejected heat away from the exhaust path. Shut off air on load loss or overspeed.</p><p><code>P = τω</code> and <code>ΔT = (Pshaft − Qinto)/(ṁcp)</code>. A flywheel has <code>E = Iω²/2</code>, so it absorbs power only while speed rises. Illustrative 1 kg / 0.1 m solid disc at 3000 rpm stores 247 J, equivalent to only 0.37 s at 671 W or 0.092 s at 2685 W. These figures explain the limitation; they are not flywheel build dimensions.</p><h2>Nozzle or vortex tube</h2><p><strong>Motor route:</strong> regulated supply → loaded motor → approved exhaust collector → short insulated large-bore hose → passive nozzle → target. Measure exhaust backpressure. Start with a low-restriction outlet. Pressure-rated metal components belong on the compressed-air side; existing printed nozzle CAD is not a pressure rating or a verified motor fitting.</p><p><strong>Vortex comparison:</strong> regulated supply → vortex tube → cold outlet/nozzle, with its hot outlet rejected away. A vortex tube normally needs pressurized inlet air. Near-atmospheric motor exhaust cannot provide the original vortex inlet condition. Do not put a compressed-air vortex tube after the motor. A passive swirl nozzle is a separate design case.</p><h2>First experiment</h2><ol><li>Have the cylinder-side assembly and pressure protection checked by a qualified pressure-system technician. Verify cylinder/valve compatibility and labels.</li><li>Measure the regulated supply pressure under the required flow before attaching the motor. Use a suitably rated, full-flow manual valve for the first bench test if the automatic valve is not ready. The controller’s existing small valve cannot qualify the screened full-flow point.</li><li>Use AM0701 with the rated load fixture. Record motor inlet pressure/temperature, collected exhaust pressure/temperature, mass flow and shaft torque/RPM together. Adjust pressure and load within manufacturer limits; do not apply maximum load at startup.</li><li>Compare against a regulator-only bypass at matched measured flow. Report motor cooling separately from regulator cooling and hose heat gain.</li><li>Characterize the source first. Then add the nozzle and measure 5 × 5 cm mean air temperature and velocity at 20 cm and 50 cm during pulses up to 10 s. Include warm-up inventory. Do not use skin sensation or the metal housing as proof.</li><li>Move to AM0706 after the larger regulator, first-stage supply, valve, lines and load fixture are qualified.</li></ol><p>Confirm lubrication, oil carryover, low-temperature limits and exhaust collection before person-facing tests. No cold-output buffer is selected for this first POC.</p><details><summary>Evidence status and open items</summary><p>Source decks establish the architecture and listed parts. They do not prove the installed cylinder volume, exact regulator model identity/condition, sustained flow, motor thermal output, shaft/port fits or target cooling. This report adds EOS/algebra checks only. No new CFD, Lean proof or physical measurements.</p><p><a href="am0701-assessment.json">AM0701 assessment</a> · <a href="am0706-assessment.json">AM0706 assessment</a> · <a href="../../mass-flow-study/results/index.html#nozzle-catalogue">Existing nozzle CAD catalogue</a></p></details></main></html>'''.replace('ROWS',rows)
    inlet_check=OUT/'am0706-inlet-check.json'
    if inlet_check.exists():
        html=html.replace('<h2>What the documents establish</h2>', '<p><strong>AM0706 source conflict found:</strong> Amazon gallery labels the model 1.7 HP / 6.3 N m; title and manufacturer web page say 3.6 HP / 13 N m. Exact supplied version and inlet thread remain unverified. Hold its purchase/connection selection. The earlier 74 g/s screen does not validate supplied hardware. <a href="am0706-inlet-check.json">Source evidence and interface status</a>.</p><h2>What the documents establish</h2>')
    attachment=OUT/'generator-attachment-section.html'
    if attachment.exists():
        html=html.replace('<h2>First experiment</h2>',attachment.read_text()+'<h2>First experiment</h2>')
        html=html.replace('<nav>','<nav><a href="#generator-attachment">Shaft connection</a>',1)
    load_section=OUT/'load-options-section.html'
    if load_section.exists():
        html=html.replace('<h2>First experiment</h2>', load_section.read_text()+'<h2>First experiment</h2>')
    (OUT/'poc-assembly.html').write_text(html)


if __name__ == '__main__':
    build()
