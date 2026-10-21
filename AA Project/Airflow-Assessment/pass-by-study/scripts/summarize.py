"""Summarise completed open-jet controls and explicit refinement cases."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from open_flow import STUDY,CASES

def primary_name(layout):return 'top1.75' if layout=='overhead' else 'left1.15'
def reference(data,patch=None):
    patch=patch or primary_name(data['case']['layout'])
    return next(p for p in data['passages'] if p['walking_speed_m_s']==1.2 and p['center_crossing_s']==5 and p['patch']==patch)

def summarise():
    rows=[]
    for path in sorted(CASES.glob('*/audit.json')):
        d=json.loads(path.read_text());cfg=d['case'];p=reference(d)
        rows.append(dict(case=cfg['case'],layout=cfg['layout'],distance_m=cfg['nominal_standoff_m'],cells=cfg['cells'],
                         width_m=cfg.get('outlet_width_m',.14),height_m=cfg.get('outlet_height_m',.08),
                         wind_m_s=cfg['wind_m_s'],wind_direction=cfg['wind_direction'],
                         source_c=cfg['source_c'],source_mass_kg_s=cfg['source_mass_kg_s'],
                         duration_s=d['history'][-1]['time_s'],reference_patch=p['patch'],reference=p,
                         all_reference_patches=[v for v in d['passages'] if v['walking_speed_m_s']==1.2 and v['center_crossing_s']==5],
                         numerical_screens_pass=d['numerical_screens_pass'],gates=d['gates'],conservation=d['conservation'],incident_air_band_snapshot=d.get('incident_air_band_snapshot',{})))
    by={r['case']:r for r in rows};controls=[r for r in rows if r['case'].startswith('P')]
    refinement={}
    if all(k in by for k in ['P01_one_d35','R00_wide_d35','F00_base_d35','F01_wide_d35']):
        for coarse,fine,label in [('P01_one_d35','F00_base_d35','base'),('R00_wide_d35','F01_wide_d35','wide')]:
            a,b=[by[k] for k in [coarse,fine]]
            refinement[label]=dict(coarse=coarse,fine=fine,cells=[a['cells'],b['cells']],
                                   peak_deficit_change_k=b['reference']['peak_area_deficit_k']-a['reference']['peak_area_deficit_k'],
                                   total_duration_change_s=b['reference']['time_above_delta6_s']-a['reference']['time_above_delta6_s'])
        refinement['wide_minus_base_fine']={k:by['F01_wide_d35']['reference'][k]-by['F00_base_d35']['reference'][k] for k in ['peak_area_deficit_k','time_above_delta6_s','longest_continuous_above_delta6_s','positive_deficit_dose_k_s']}
    result=dict(status='Executed unconfined-jet screen; human body, wake, comfort and hardware unvalidated',
                controls_expected=9,controls_completed=len(controls),cases=rows,refinement=refinement,
                source=json.loads((STUDY/'results/timing-and-energy.json').read_text())['source_budget'],
                reference_passage='1.2 m/s along x=-0.8 to +0.8 m; centre crossing at 5 s after ideal nozzle activation; moving 5x5 cm square.',
                comparison_limit='Side reference is y=-0.2 m,z=1.15 m; overhead reference is z=1.75 m,y=0. These differ in incident body region. No global comfort/layout ranking.',
                error_budget_note='Duration/error sensitivity uses hypothetical upward temperature bounds. No physical error bound is established.',
                body_included=False,hardware_validated=False,globally_optimal=False)
    (STUDY/'results/cfd-summary.json').write_text(json.dumps(result,indent=2))
    if not controls:return result
    colors={'one-side':'#087f92','two-side':'#bf6a18','overhead':'#7257a2'}
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    for layout in colors:
        group=sorted([r for r in controls if r['layout']==layout],key=lambda r:r['distance_m'])
        if not group:continue
        x=[100*r['distance_m'] for r in group]
        axes[0].plot(x,[r['reference']['time_above_delta6_s'] for r in group],'o-',color=colors[layout],label=layout)
        axes[1].plot(x,[r['reference']['peak_area_deficit_k'] for r in group],'o-',color=colors[layout],label=layout)
    axes[0].set(xlabel='Nominal incident-patch standoff (cm)',ylabel='Total time above 6 K deficit (s)',title='Air exposure during one crossing')
    axes[1].set(xlabel='Nominal incident-patch standoff (cm)',ylabel='Peak moving-area temperature deficit (K)',title='Peak is separate from duration');axes[1].axhline(6,color='#6d7680',ls='--')
    for ax in axes:ax.grid(alpha=.2);ax.legend(fontsize=9);ax.set_xticks([20,35,50])
    fig.suptitle('Open-air CFD screen / 1.2 m/s virtual passage / no human body',fontsize=15)
    fig.supxlabel('Side and overhead reference patches differ. Prescribed 0.96°C source at 30°C ambient. Model results, not comfort validation.',fontsize=9)
    fig.savefig(STUDY/'results/layout-comparison.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained')
    for r in controls:
        traces=json.loads((CASES/r['case']/'moving-probe-traces.json').read_text());key=r['reference_patch']+'_v1.2_t5.0';q=traces[key]
        ax.plot(np.array(q['time_s'])-5,30-np.array(q['area_temperature_c']),color=colors[r['layout']],ls={.2:'-',.35:'--',.5:':'}[r['distance_m']],label=f'{r["layout"]} {r["distance_m"]*100:g}cm')
    ax.axhline(6,color='#70777e',ls='--',lw=1);ax.set(xlabel='Time relative to passage centre (s)',ylabel='Moving 5x5 cm air-area deficit (K)',title='Actual resolved-field sampling through each ideal jet layout');ax.grid(alpha=.2);ax.legend(ncol=3,fontsize=8)
    fig.savefig(STUDY/'results/passage-traces.png',dpi=160);plt.close(fig)
    if refinement:
        names=['P01_one_d35','R00_wide_d35','F00_base_d35','F01_wide_d35']+(['W00_wide_opposed'] if 'W00_wide_opposed'in by else [])
        fig,ax=plt.subplots(figsize=(10,4.5),layout='constrained')
        values=[by[k]['reference']['time_above_delta6_s'] for k in names]
        ax.bar(range(len(names)),values,color=['#7c929e','#17889c','#7c929e','#17889c','#bd6b22'][:len(names)])
        ax.set_xticks(range(len(names)),['140x80\ncoarse','280x40\ncoarse','140x80\nfiner','280x40\nfiner','280x40\nopposing wind'][:len(names)])
        ax.set(ylabel='Time above 6 K deficit (s)',title='One-side / 35 cm / 1.2 m/s / same total flow and outlet area');ax.grid(axis='y',alpha=.2)
        fig.supxlabel('Virtual left lower patch only. Wind = 0.5 m/s against the jet. Different turbulence and body models remain unresolved.',fontsize=9)
        fig.savefig(STUDY/'results/refinement-comparison.png',dpi=160);plt.close(fig)
    if 'L00_row4_d35' in by:
        names=['P01_one_d35','L00_row4_d35']+(['S00_row4_source8'] if 'S00_row4_source8'in by else [])
        fig,ax=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
        labels=['2 heights × 2 positions','1 height × 4 positions','4 positions / 8°C source'][:len(names)]
        for i,key in enumerate(['time_above_delta6_s','longest_continuous_above_delta6_s']):
            ax[i].bar(range(len(names)),[by[name]['reference'][key] for name in names],color=['#778e9a','#148a9a','#bc7229'][:len(names)])
            ax[i].set_xticks(range(len(names)),labels,rotation=12,ha='right',fontsize=8)
            ax[i].set(ylabel='Time above 6 K deficit (s)',title='Total exposure' if i==0 else 'Longest continuous encounter');ax[i].grid(axis='y',alpha=.2)
        fig.suptitle('Four outlets along the walking path / 35 cm / virtual lower-side patch',fontsize=14)
        fig.supxlabel('Same air mass. One-height row trades vertical coverage for more encounters. The 8°C state is an explicit heat-pickup sensitivity.',fontsize=9)
        fig.savefig(STUDY/'results/row-comparison.png',dpi=160);plt.close(fig)
    print(json.dumps(dict(cases=len(rows),controls=len(controls),refinement=refinement)),flush=True)
    return result

if __name__=='__main__':summarise()
