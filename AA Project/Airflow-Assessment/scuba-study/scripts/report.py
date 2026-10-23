"""Scuba calculation and native CFD delivery. Existing viewer, separate source data."""
from pathlib import Path
import json,sys,math,hashlib,shutil
from lxml import html as H
from calculate import calculate,STUDY,ROOT
OUT=STUDY/'results';OLD=ROOT/'mass-flow-study'

def report():
    c=calculate();rows=[]
    for p in sorted(OUT.glob('scuba*.json')):
        d=json.loads(p.read_text())
        if isinstance(d,dict) and d.get('numerical_screens_pass') and 'final' in d and (OUT/(d['case']+'-timeline.js')).exists():rows.append(d)
    assert rows,'No completed native CFD frames'
    for d in rows:
        d['label']=f"{'Warm inlet 40°C' if d['inputs']['scuba_source']['motor_inlet_c']==40 else 'Nominal inlet 30°C'} · nozzle {d['inputs']['source_c']:.2f}°C · {'fine' if d['case'].endswith('_fine') else 'coarse'}"
    fine=next((r for r in rows if r['case'].endswith('_fine')),None);coarse=next(r for r in rows if r['case']=='scuba19_n1_wide');default=fine or coarse;pairs=[]
    if fine:
        cv=coarse['final']['regions']['range20to50']['6']['volume_m3'];fv=fine['final']['regions']['range20to50']['6']['volume_m3'];pairs=[dict(coarse=coarse['case'],fine=fine['case'],coarse_cells=coarse['inputs']['cells'],fine_cells=fine['inputs']['cells'],coarse_volume_m3=cv,fine_volume_m3=fv,relative_change=(fv-cv)/cv)]
    data=dict(cases=rows,default_case=default['case'],grid_sensitivity=pairs,cad=[],source_c=default['inputs']['source_c'],ambient_c=30,spray_s=10)
    (OUT/'data.js').write_text('window.AA_SWEEP='+json.dumps(data,separators=(',',':'))+';')
    for f in ['dashboard.css','scl-theme.css']:shutil.copyfile(OLD/'results'/f,OUT/f)
    view=(OLD/'results/viewer.js').read_text().replace("fmt(c.total_g_s,0)","fmt(c.total_g_s,1)")
    start="c.total_g_s+' g/s · '+c.outlets+' outlets · '+c.design+' / '+c.layout+' · '+c.closure+(r.case.endsWith('_fine')?' · fine':'')"
    assert start in view;view=view.replace(start,'r.label')
    view=view.replace("$('description').textContent=id+' · '","$('description').textContent=id+' · source '+fmt(c.source_c,2)+'°C · '")
    (OUT/'viewer.js').write_text(view)
    tree=H.fromstring((OLD/'dashboard.html').read_text().replace('FORMULAS_SECTION','').replace('COMPONENTS_SECTION','').replace('NOZZLE_CATALOGUE',''))
    tree.xpath('//title')[0].text='Scuba tank · single-nozzle results'
    for node in tree.xpath('//script|//*[@id="dashboardTabs"]|//*[@id="source-temperature"]|//details[contains(@class,"matrix")]'):node.getparent().remove(node)
    main=tree.xpath('//main')[0]
    context=tree.xpath('//*[@class="run-context"]')[0];context.text='19.4 g/s · 1 loaded motor · 1 nozzle · 30°C ambient · still air · gravity · 10 s ON'
    for child in list(context):context.remove(child)
    ctrl=tree.xpath('//aside')[0];caseLabel=tree.xpath('//*[@id="case"]/..')[0];caseLabel.getparent().remove(caseLabel);caseLabel.text='CFD scenario';hidden=H.Element('div',hidden='hidden')
    for child in list(ctrl):ctrl.remove(child);hidden.append(child)
    ctrl.append(caseLabel);ctrl.append(hidden);ctrl.set('style','display:block')
    for q in tree.xpath('//*[@id="flowRange"]'):q.set('min','19.4');q.set('max','19.4');q.set('step','.1')
    runfiles=tree.xpath('//*[@id="run-files"]')[0]
    for node in runfiles.xpath('.//div[contains(@class,"links")][last()]/a'):
        href=node.get('href','')
        if href in ['comparison.csv','calculations.json','validation.json','timeline-validation.json','../cad/manifest.json','../README.md']:
            if href=='validation.json':node.set('href','calculation-validation.json');node.text='Calculation checks'
            elif href=='../cad/manifest.json':node.set('href','../../mass-flow-study/cad/manifest.json')
    cadlinks=tree.xpath('//*[@id="cadLinks"]')[0]
    # Viewer writes this node after load, so keep fixed CAD links in a separate sibling.
    fixed=H.fragment_fromstring('<p class="links"><a href="../../mass-flow-study/cad/outlet-280x40-print-mm.stl" download>Matching nozzle STL · mm</a> <a href="../../mass-flow-study/cad/outlet-280x40-metres.step">STEP</a> · Unfitted 100 mm cold-hose interface; not pressure-rated tank hardware.</p>')
    cadlinks.addnext(fixed)
    source=c['sources'][0];nom=c['nominal'];motor=c['motor'];runtime_rows=''.join(f'<tr><td>{x["motors"]}</td><td>{x["total_g_s"]:.1f}</td><td>{x["free_air_l_min"]:.0f}</td><td>{x["shaft_load_w"]:.0f}</td><td>{x["adiabatic_s"]:.0f}–{x["isothermal_s"]:.0f}</td><td>{x["complete_10s_pulses_adiabatic"]}–{x["complete_10s_pulses_isothermal"]}</td></tr>' for x in c['motor_count_options'])
    result_rows=''.join(f'<tr><td>{r["label"]}</td><td>{r["inputs"]["cells"]:,}</td><td>{r["final"]["sections"][0]["best_sampled_5cm_mean_drop_k"]:.2f}</td><td>{r["final"]["sections"][2]["best_sampled_5cm_mean_drop_k"]:.2f}</td><td>{1000*r["final"]["regions"]["range20to50"]["6"]["volume_m3"]:.2f}</td><td>{1000*r["final"]["regions"]["range20to50"]["6"]["mass_kg"]:.2f}</td></tr>' for r in rows)
    block=f'''<section class="card" id="scuba-summary"><div class="section-head"><h2>Scuba tank → one loaded motor → one nozzle</h2><a href="../../mass-flow-study/results/index.html">All configurations ↗</a></div><p class="compact-context">Assumed cylinder: 12 L / 200 bar gauge / 30°C · planning cutoff: 20 bar</p><div class="plant-flow"><span>Scuba tank<br><b>200 bar</b></span><i>→</i><span>Rated pressure reduction<br><b>6.3 bar g at running motor</b></span><i>→</i><span>Loaded LZB46<br><b>840 W / 1270 rpm</b></span><i>→</i><span>Short insulated path<br><b>1 × 280 × 40 mm nozzle</b></span></div><p><strong>Air inventory supports short tests. Direct tank-to-motor connection is incompatible.</strong> Motor running target is 6.3 bar g. The product page lists 7 bar g maximum; the manual says 6.3 bar or nameplate. Confirm the unit limit. The stock pressure-reduction package needs proven full-flow delivery and downstream overpressure protection.</p><div class="metrics"><div><small>One motor</small><b>19.4 g/s</b></div><div><small>Inventory-limited spray time</small><b>105–123 s</b></div><div><small>Complete 10 s pulses</small><b>10–12</b></div><div><small>Nominal nozzle source · assumed</small><b>{source['nozzle_c']:.2f}°C</b></div></div><p class="note">Runtime range: adiabatic / isothermal real-air scenarios, not guaranteed operating time. Tank cooling, regulator droop/icing and motor temperature limits may stop delivery earlier. Each 10 s pulse consumes 194 g. Pauses change tank heat transfer.</p><details class="compact-details"><summary>Motor count, tank inventory and required flow</summary><div class="table"><table><thead><tr><th>Motors</th><th>Total g/s</th><th>Free air L/min</th><th>External shaft load W</th><th>Spray time s</th><th>Full 10 s pulses</th></tr></thead><tbody>{runtime_rows}</tbody></table></div><p class="note">All rows use the same tank and cutoff. Several motor exhausts can feed one nozzle in principle; only the one-motor 19.4 g/s cases below were newly simulated. One motor is not rated to give 77 g/s at the listed loaded point. Regulator/manifold capacity is unqualified.</p></details><details class="compact-details"><summary>Calculations and source temperature</summary><div class="formula-equation">M = ρ(P,T)V<br>t = V(ρ₀−ρcutoff)/(N ṁmotor)<br>Tmotor = Tin − Wshaft/(ṁcp)<br>Tnozzle = Ta + (Tmotor−Ta) exp[−UA/(ṁcp)]</div><p>Initial real-air inventory: {nom['initial_real_mass_kg']:.3f} kg. Usable to 20 bar: {nom['usable_adiabatic_kg']:.3f}–{nom['usable_isothermal_kg']:.3f} kg. Use absolute pressure in the EOS.</p><p>At 30°C motor inlet: 30 − 840/(0.0194 × 1006) = −13.04°C exhaust. Assumed cold path UA=10.0737 W/K warms this to 4.31°C. At 40°C motor inlet, the same model gives 10.28°C at the nozzle. Source budgets: 501 W / 385 W. The earlier 0.96°C source belonged to four motors and is not reused here.</p><p class="note">UA reuses the full earlier four-motor-path conductance for one path; it is an assumption, not a measured conservative guarantee. Shaft heat returns outside the cold stream. Fixed motor power/flow is a catalogue-point hypothesis, not a coupled motor/regulator map. The regulator throttles most of the pressure ratio. The LZB46 does not expand directly from 200 bar. The real-air isenthalpic regulator calculation can cool air initially; wall heat and falling tank state change it. No fixed Joule–Thomson cooling credit is included in the CFD source.</p><p class="note">A free-spinning motor does not supply the assumed 840 W load. A sustained external load needs about 6.32 Nm at 1270 rpm. The cylinder already is the warm-side buffer. No extra cold receiver is selected; it adds wall heat, cooldown delay and exhaust backpressure.</p><div class="links"><a href="calculations.json">All calculations / tank sizes</a><a href="calculation-validation.json">10 numerical checks</a><a href="../README.md">Method and limits</a><a href="https://www.atlascopco.com/en-us/itba/products/air-motors/lzb46-rl-a025-11-sku8411047249">Manufacturer motor data</a><a href="https://coolprop.org/fluid_properties/fluids/Air.html">Real-air EOS</a></div></details></section>'''
    main.insert(0,H.fragment_fromstring(block))
    from load22 import build as load22_section
    main.insert(1,H.fragment_fromstring(load22_section()))
    summary=f'''<section class="card"><h2>New single-nozzle CFD · at 10 s</h2><div class="table"><table><thead><tr><th>Saved scenario</th><th>Cells</th><th>20 cm best 5 cm ΔT K</th><th>50 cm best 5 cm ΔT K</th><th>20–50 cm cold air L</th><th>Cold air g</th></tr></thead><tbody>{result_rows}</tbody></table></div><p class="note">Cold air = native cells ≥6 K below ambient. Best sampled 5 × 5 cm means are local patches, not whole-section or human cooling. Native frames at integer seconds 0–10; no post-shutoff decay. Fixed source boundary; tank transient is not coupled to CFD.</p><a href="comparison.csv">Result CSV</a> · <a href="validation.json">CFD / mesh checks</a></section>'''
    main.append(H.fragment_fromstring(summary))
    animation=OUT/(default['case']+'-cooling.gif')
    if animation.exists():main.append(H.fragment_fromstring('<details class="card compact-details"><summary>Native cooling animation / download</summary><a href="'+animation.name+'" download>Download GIF</a><img loading="lazy" style="width:100%;height:auto;margin-top:12px" src="'+animation.name+'" alt="Native single-nozzle CFD: saved 20/50 cm sections and cold-air volume over ten seconds"></details>'))
    foot=tree.xpath('//footer')[0];foot.text='Conditional source · native 3D CFD · hardware unqualified';foot.getparent().remove(foot);main.append(foot)
    for src in ['data.js','viewer.js']:tree.append(H.Element('script',src=src))
    reveal=H.Element('script');reveal.text="function revealLoad22(){if(location.hash==='#shaft-load-22')document.getElementById('shaft-load-22').open=true;}window.addEventListener('hashchange',revealLoad22);revealLoad22();";tree.append(reveal)
    (OUT/'index.html').write_text('<!doctype html>\n'+H.tostring(tree,encoding='unicode',method='html'))
    import csv
    with (OUT/'comparison.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(['case','flow_g_s','source_c','cells','best_5cm_delta20_k','best_5cm_delta50_k','target_cold_l','target_cold_g'])
        for r in rows:writer.writerow([r['case'],r['inputs']['total_g_s'],r['inputs']['source_c'],r['inputs']['cells'],r['final']['sections'][0]['best_sampled_5cm_mean_drop_k'],r['final']['sections'][2]['best_sampled_5cm_mean_drop_k'],1000*r['final']['regions']['range20to50']['6']['volume_m3'],1000*r['final']['regions']['range20to50']['6']['mass_kg']])
    validation=dict(status='passed',cases=len(rows),numerical_screens_pass=all(r['numerical_screens_pass'] for r in rows),native_frames=len(rows)*11,grid_pairs=pairs,scope='Numerical integrity and two-grid sensitivity, not continuum accuracy or hardware validation')
    for r in rows:
        for suffix in ['-sections.png','-volume.png','-range-volume.png','-range-volume.js','-sections.js']:
            assert (OUT/(r['case']+suffix)).stat().st_size>0
        archive=STUDY/'archives'/(r['case']+'.zip');ar=json.loads((OUT/(r['case']+'-archive.json')).read_text());assert hashlib.sha256(archive.read_bytes()).hexdigest()==ar['sha256']
        a=json.loads((OUT/(r['case']+'-timeline-audit.json')).read_text());assert a['file_sha256']==hashlib.sha256((OUT/(r['case']+'-timeline.js')).read_bytes()).hexdigest();assert a['native_temperature_hashes_verified']==11
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2))
    (OUT/'timeline-validation.json').write_text(json.dumps(dict(status='passed',cases=len(rows),native_frames=len(rows)*11,native_temperature_hashes_verified=len(rows)*11,volume_checks=len(rows)*22,new_cfd_runs=True,scope='Each frame extracted from its native source-specific solver archive; fixed source boundaries, no post-shutoff decay'),indent=2))
    # Verify all local report references.
    from urllib.parse import unquote,urlsplit
    links=[]
    for el in tree.xpath('//*[@href or @src]'):
        link=el.get('href') or el.get('src');u=urlsplit(link)
        if not u.scheme and u.path:
            assert (OUT/unquote(u.path)).resolve().exists(),link;links.append(link)
    validation['local_links_checked']=links
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2));print(json.dumps(validation,indent=2))
if __name__=='__main__':report()
