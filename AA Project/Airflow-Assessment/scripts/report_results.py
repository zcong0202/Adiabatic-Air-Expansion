"""Plot sampled CFD fields and publish status without inventing validation."""
import json
import math
import re
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.patches import Rectangle
import numpy as np
from postprocess import ROOT, read_vtp, audit
from boundary_balance import balance

DESIGNS=['D0_round','D1_compact','D2_slot','D3_shield']
LABELS={'D0_round':'Round baseline','D1_compact':'Compact 6 mm','D2_slot':'Rounded slot','D3_shield':'Open shield'}


def last_metrics(result):
    if not result.get('latest_target'):return {}
    latest=result['latest_target'];keys=list(result['samples']);change=None
    if len(keys)>1:
        previous=result['samples'][keys[-2]]['target']['patch_net_cooling_potential_w']
        change=abs(latest['patch_net_cooling_potential_w']-previous)/max(abs(previous),1e-6)
    return {'latest_target':latest,'patch_flux_change_fraction':change}


def report():
    rows=[]
    for design in DESIGNS:
        for wind in [0,1]:
            case=ROOT/'cases'/f'{design}_bouss_w{wind}'
            if not (case/'case.json').exists():continue
            r=audit(case);r['boundary_balance']=balance(case)
            r.update(last_metrics(r))
            if r.get('latest_target'):
                path=case/'postProcessing/cuts'/r['latest_sample']/'target.vtp'
                pts,faces,d=read_vtp(path)
                r['target_temperature_tracer_mismatch_k']=float(np.max(np.abs(d['T']-(308.15-20*d['c']))))
            r['screening_status']='Unvalidated screening result'
            if r['fatal_error'] or not r['solver_end_seen']:r['screening_status']='Not complete'
            elif not r['convergence_reported']:r['screening_status']='Iteration limit reached; not converged'
            bal=r.get('boundary_balance')
            if r.get('quality_rejection') or (bal and abs(bal['net_mass_error_relative_to_cold_source'])>.05):
                r['screening_status']='Rejected: conservation failure'
                r['exclude_quantitative_comparison']=True
            rows.append(r)
    (ROOT/'results/screening-results.json').write_text(json.dumps(rows,indent=2))
    # Target plane maps at the same 200 mm distance from the primary jet exit.
    for kind in ['target','midplane']:
        fig,axes=plt.subplots(4,2,figsize=(12,13),layout='constrained')
        image=None
        for i,design in enumerate(DESIGNS):
            for j,wind in enumerate([0,1]):
                ax=axes[i,j];r=next((v for v in rows if v['design']==design and v['crosswind_m_s']==wind),None)
                ax.set_title(f'{design[:2]} · {LABELS[design]} · {wind} m/s crosswind',loc='left',fontsize=11)
                if not r or not r.get('latest_sample'):
                    ax.text(.5,.5,'Awaiting sampled CFD output',ha='center',transform=ax.transAxes);continue
                if r.get('exclude_quantitative_comparison'):
                    ax.set_facecolor('#eeeeee');ax.text(.5,.5,'Run rejected\nConservation failure\nNo prediction reported',ha='center',va='center',transform=ax.transAxes)
                    if kind=='target':ax.set_xlim(-65,65);ax.set_ylim(-65,65)
                    else:ax.set_xlim(-40,260);ax.set_ylim(-55,55)
                    ax.set_aspect('equal',adjustable='box');ax.set_xticks([]);ax.set_yticks([]);continue
                path=ROOT/'cases'/r['case']/'postProcessing/cuts'/r['latest_sample']/(kind+'.vtp')
                points,faces,d=read_vtp(path)
                a,b=(1,2) if kind=='target' else (0,1)
                tri=mtri.Triangulation(points[:,a]*1000,points[:,b]*1000,faces)
                temp=d['T']-273.15
                image=ax.tripcolor(tri,temp,shading='gouraud',vmin=28 if kind=='target' else 15,vmax=35,cmap='coolwarm')
                if kind=='target':
                    ax.set_xlim(-65,65);ax.set_ylim(-65,65);ax.add_patch(Rectangle((-25,-25),50,50,fill=False,color='black',lw=1.3,ls='--'));ax.set_xlabel('y (mm)');ax.set_ylabel('z (mm)')
                else:
                    ax.set_xlim(-40,260);ax.set_ylim(-55,55);ax.axvline(200,color='black',ls='--',lw=.8);ax.set_xlabel('x (mm)');ax.set_ylabel('y (mm)')
                ax.set_aspect('equal',adjustable='box')
                ax.text(.02,.02,f'Iteration {r["latest_sample"]}',transform=ax.transAxes,fontsize=8,bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
        if image is not None:fig.colorbar(image,ax=axes,label='Transported temperature (°C); low-Mach approximation',shrink=.7)
        label='200 mm target-plane temperature' if kind=='target' else 'Jet midplane temperature'
        fig.suptitle(label+' — UNCONVERGED snapshots\nAssumed 2 g/s, 15°C cold source, 35°C ambient. First-order RANS screening, not lab measurements.',fontsize=14)
        fig.savefig(ROOT/f'results/{kind}-temperature.png',dpi=160);plt.close(fig)
    # Values and iteration history; do not label these as human heat removal.
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for i,design in enumerate(DESIGNS):
        ax=axes.flat[i]
        for wind in [0,1]:
            r=next((v for v in rows if v['design']==design and v['crosswind_m_s']==wind),None)
            if not r:continue
            x=[];y=[]
            for t,entry in r['samples'].items():
                x.append(float(t));y.append(entry['target']['patch_net_cooling_potential_w'])
            ax.plot(x,y,'o-',label=f'{wind} m/s',markersize=3)
        ax.axhline(40.2,color='gray',ls=':',label='Source sensible capacity')
        ax.set_title(LABELS[design],loc='left');ax.set_xlabel('Steady solver iteration');ax.set_ylabel('50 × 50 mm patch flux (W)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Iteration history catches incomplete or unstable comparisons\nAdvected cooling potential through a plane, not heat removed from skin.',fontsize=14)
    fig.savefig(ROOT/'results/iteration-history.png',dpi=160);plt.close(fig)
    fine=[]
    for case in sorted((ROOT/'cases').glob('*bouss_fine')):
        if not (case/'log.solver').exists():continue
        r=audit(case);r['boundary_balance']=balance(case);r.update(last_metrics(r));fine.append(r)
    (ROOT/'results/refinement-results.json').write_text(json.dumps(fine,indent=2))
    html='<p><strong>Diagnostic CFD only: no reliable steady convergence; no design ranking.</strong> Actual meshes and solver outputs are saved. The source is assumed, not measured. Failed ideal-gas runs and early loose-tolerance samples are excluded from design recommendations.</p>'
    html+='<details><summary>Unconverged diagnostic values — do not use for design selection</summary><div class="scroll"><table><tr><th>Design / wind</th><th>Target air temperature</th><th>Target mean speed</th><th>Run status</th></tr>'
    for r in rows:
        t=r.get('latest_target')
        if not t:continue
        if r.get('exclude_quantitative_comparison'):
            html+=f'<tr><td>{r["design"][:2]} / {r["crosswind_m_s"]:g} m/s</td><td>Withheld</td><td>Withheld</td><td>{r["screening_status"]}</td></tr>'
            continue
        html+=f'<tr><td>{r["design"][:2]} / {r["crosswind_m_s"]:g} m/s</td><td>{t["patch_area_mean_temperature_c"]:.1f}°C</td><td>{t["patch_area_mean_speed_m_s"]:.1f} m/s</td><td>{r["screening_status"]}</td></tr>'
    html+='</table></div></details><p>Values average an assumed 50 × 50 mm region at 200 mm from the core exit. The shield also has a separate 232 mm sample to preserve 200 mm clear distance from its mouth. These are not comfort predictions.</p>'
    html+='<p><a href="Airflow-Assessment/results/target-temperature.png">Target maps</a> · <a href="Airflow-Assessment/results/midplane-temperature.png">Jet maps</a> · <a href="Airflow-Assessment/results/iteration-history.png">Iteration history</a> · <a href="Airflow-Assessment/results/screening-results.json">Numbers and checks</a> · <a href="Airflow-Assessment/results/refinement-results.json">Mesh refinement</a></p>'
    html+='<details><summary>CFD maps</summary><img src="Airflow-Assessment/results/target-temperature.png" style="width:100%" alt="CFD target-plane temperatures for four geometries and two wind conditions"></details>'
    html+='<p><strong>Model used:</strong> Low-Mach Boussinesq buoyancy, constant density in continuity, approximate total-temperature transport, k–epsilon RANS and first-order upwind convection. First-order numerical mixing and the finite domain require sensitivity checks. No human body, skin heat transfer, moisture or internal vortex is simulated. No validated winning geometry is claimed.</p>'
    summary={'status':'Screening calculations; no validated winner','source_capacity_w':40.2,'cases_with_samples':sum(bool(r.get('latest_target')) for r in rows),'completed_cases':sum(r['solver_end_seen'] and not r['fatal_error'] for r in rows),'converged_cases':sum(r['convergence_reported'] for r in rows),'rejected_cases':sum(bool(r.get('exclude_quantitative_comparison')) for r in rows),'fine_cases':len(fine),'overview_html':html}
    (ROOT/'results/study-summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='overview_html'},indent=2))


if __name__=='__main__':report()
