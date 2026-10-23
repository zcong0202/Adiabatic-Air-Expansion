"""Aggregate audited numerical results. Keep runs, budgets and CAD distinct."""
import json,csv,sys,hashlib
from pathlib import Path
from build import STUDY,CP
OUT=STUDY/'results'

def main():
    plan=json.loads((OUT/'campaign-plan.json').read_text());extra=json.loads((OUT/'refinement-plan.json').read_text()) if (OUT/'refinement-plan.json').exists() else {'cases':[]};rows=[]
    for f in sorted(OUT.glob('*.json')):
        try:d=json.loads(f.read_text())
        except Exception:continue
        if isinstance(d,dict) and 'final' in d and 'inputs' in d and d.get('numerical_screens_pass') and 'range20to50' in d['final']['regions'] and all('best_sampled_5cm_mean_drop_k' in q for q in d['final']['sections']):rows.append(d)
    if not rows:raise RuntimeError('No audited CFD cases')
    best=[]
    for mass in [2,27,52,77]:
        options=[r for r in rows if r['inputs']['total_g_s']==mass and not r['case'].endswith('_laminar') and not r['case'].endswith('_fine')]
        if options:
            r=max(options,key=lambda x:x['final']['regions'].get('range20to50',x['final']['regions']['walking_corridor'])['6']['mass_kg']);best.append(r['case'])
    cols=['case','total_g_s','outlets','per_outlet_g_s','design','layout','width_m','height_m','exit_speed_m_s','hydraulic_reynolds','closure','cells','source_sensible_w','range_volume_ge6_m3','range_mass_ge6_g','whole_volume_ge6_m3','whole_mass_ge6_g','area_ge6_at20_m2','area_ge6_at35_m2','area_ge6_at50_m2','best_5cm_at20_drop_k','best_5cm_at35_drop_k','best_5cm_at50_drop_k','target_band_fluid_m3','mass_closure_relative','energy_closure_relative']
    with (OUT/'comparison.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader()
        for r in rows:
            c=r['inputs'];v=r['final']['regions'].get('range20to50',r['final']['regions']['walking_corridor'])['6'];d=r['final']['regions']['domain']['6'];w.writerow({**{k:c[k] for k in cols if k in c},'case':r['case'],'source_sensible_w':r['source_cooling_w'],'range_volume_ge6_m3':v['volume_m3'],'range_mass_ge6_g':v['mass_kg']*1000,'whole_volume_ge6_m3':d['volume_m3'],'whole_mass_ge6_g':d['mass_kg']*1000,**{f'area_ge6_at{int(s["distance_m"]*100)}_m2':s['area_ge6_m2'] for s in r['final']['sections']},**{f'best_5cm_at{int(s["distance_m"]*100)}_drop_k':s.get('best_sampled_5cm_mean_drop_k') for s in r['final']['sections']},'target_band_fluid_m3':r.get('range_region',{}).get('fluid_volume_m3'),'mass_closure_relative':r['conservation']['mass_relative_error'],'energy_closure_relative':r['conservation']['energy_relative_error']})
    refined={}
    if (OUT/'refinement-status.json').exists():
        rs=json.loads((OUT/'refinement-status.json').read_text())
        for job in rs.get('selected',[]):
            if any(r['case']==job['name'] for r in rows):refined[str(job['mass_g'])]=job['name']
    cad=json.loads((STUDY/'cad/manifest.json').read_text()) if (STUDY/'cad/manifest.json').exists() else []
    validation=json.loads((OUT/'validation.json').read_text()) if (OUT/'validation.json').exists() else {}
    data=dict(grid_sensitivity=validation.get('grid_pairs',[]),representative_by_flow=refined,cad=cad,cases=rows,default_case=refined.get('77') or ('pilot_m77_n4_wide' if any(r['case']=='pilot_m77_n4_wide' for r in rows) else rows[0]['case']),best_coarse_by_flow=best,planned=plan['total_cases']+len(extra['cases']),completed=len(rows),source_c=plan['source_c'],ambient_c=30,spray_s=10,threshold_k=6,scope=plan['scope'])
    import math
    source_path=STUDY.parent/'pass-by-study/source-input.json';source=json.loads(source_path.read_text());mass=source['active_motors']*source['mass_per_motor_kg_s'];power=source['active_motors']*source['shaft_work_per_motor_w'];capacity=mass*source['cp_j_kg_k'];motor=source['inlet_c']-(power-source['motor_heat_into_air_w'])/capacity;supply=source['ambient_c']+(motor-source['ambient_c'])*math.exp(-source['cold_path_ua_w_k']/capacity)
    assert abs(supply-plan['source_c'])<1e-10
    provenance=dict(status='Assumed source boundary; not measured or vendor-guaranteed',source_inputs=source,source_inputs_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),calculated=dict(nominal_total_mass_kg_s=mass,total_shaft_work_w=power,heat_capacity_w_k=capacity,motor_exhaust_c=motor,path_temperature_rise_k=supply-motor,nozzle_supply_c=supply),equations=dict(motor='T_in - (shaft_work - heat_into_air)/(mass_flow*cp)',path='T_ambient + (T_motor-T_ambient)*exp(-UA/(mass_flow*cp))'),derivation='The original design document proposed about 1 C supply. The earlier model reproduced it with a loaded motor power/flow pair and a cold-path UA calibrated to 4 K warming at the nominal point.',limits=['40 C and 6.3 bar gauge nominal motor inlet','Four loaded motors at 840 W and 19.4 g/s each; exact flow reference state needs confirmation','Motor heat pickup zero; extracted shaft heat stays outside the cold stream and target','This sweep fixes the 0.959275 C nozzle-face temperature at 2,27,52,77 g/s; it does not predict off-design motor temperature','Earlier 5 C vortex-tube observation is a different source','No source temperature sensitivity CFD generated by dashboard controls'])
    (OUT/'source-provenance.json').write_text(json.dumps(provenance,indent=2))
    (OUT/'data.js').write_text('window.AA_SWEEP='+json.dumps(data,separators=(',',':'))+';')
    (OUT/'summary.json').write_text(json.dumps({k:v for k,v in data.items() if k!='cases'}|{'best_results':[next(r for r in rows if r['case']==name) for name in best],'selected_refined_results':[next(r for r in rows if r['case']==name) for name in refined.values()]},indent=2))
    def row(r):
        c=r['inputs'];v=r['final']['regions'].get('range20to50',r['final']['regions']['walking_corridor'])['6'];s=r['final']['sections'];return '<tr><td><button class="pick" data-case="'+r['case']+'">'+r['case']+'</button></td><td>'+str(c['total_g_s'])+'</td><td>'+str(c['outlets'])+'</td><td>'+f"{c['per_outlet_g_s']:.2f}"+'</td><td>'+f"{v['volume_m3']:.4f}"+'</td><td>'+f"{v['mass_kg']*1000:.1f}"+'</td>'+''.join('<td>'+f"{p['area_ge6_m2']:.4f}"+'</td>' for p in s)+''.join('<td>'+f"{p.get('best_sampled_5cm_mean_drop_k',0):.2f}"+'</td>' for p in s)+'</tr>'
    body=''.join(row(r) for r in sorted(rows,key=lambda x:(x['inputs']['total_g_s'],x['case'])))
    html=(STUDY/'dashboard.html').read_text()
    from nozzle_catalogue import build as build_catalogue
    html=html.replace('NOZZLE_CATALOGUE',build_catalogue())
    from components import build as build_components
    html=html.replace('COMPONENTS_SECTION',build_components())
    html=html.replace('CASE_COUNT',str(len(rows))).replace('TABLE_BODY',body).replace('COMPLETION_TEXT',f'{len(rows)} audited cases available')
    (OUT/'index.html').write_text(html)
    print(json.dumps(dict(completed=len(rows),best=best)))
if __name__=='__main__':main()
