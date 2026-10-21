from pathlib import Path
import json,math,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_seat import audit
from seat_cfd import CFD,STUDY
OUT=STUDY/'results'
NAMES=['C00_back_control','C01_side_startup','C02_three_motor_refinement','C10_rear_final','C12_three_motor_final','C13_three_motor_fine','C14_four_motor_front05','C20_three_motor_profile','C21_profile_halfCo_continuation','C22_four_motor_profile','C24_four_profile_continued','C23_four_motor_panel500','C15_four_motor_front10','C16_four_motor_side05','C17_four_motor_side10','C18_four_motor_warm8','C19_four_motor_ambient35','C26_large_domain_side10']
rows=[];full={}
for name in NAMES:
 p=CFD/'cases'/name
 if not (p/'run-status.json').exists() or not json.loads((p/'run-status.json').read_text())['status'].startswith('solver ended'):continue
 a=audit(p);full[name]=a;cfg=a['case'];stats=a['last4s_statistics'];last=a['last'];neckmax=max(r['regions']['neck']['max_speed_m_s'] for r in a['history'] if r['time_s']>=last['time_s']-4)
 intervals=[]
 for k in ['torso','neck']:
  times=[r['time_s'] for r in a['history'] if r['regions'][k]['mean_c']<=20 and all(q['regions'][k]['mean_c']<=20 for q in a['history'] if q['time_s']>=r['time_s'])];intervals.append(min(times) if times else None)
 row=dict(duration_s=last['time_s'],initialization_note=cfg.get('initialized_from','Cold startup except listed continuations'),case=name,active_motors=cfg.get('active_motors',round(cfg['source_mass_kg_s']/.0194)),mass_g_s=cfg['source_mass_kg_s']*1000,supply_c=cfg['source_c'],ambient_c=cfg['ambient_c'],panel_heat_w=cfg.get('additional_panel_heat_w',0),wind_m_s=cfg['wind_m_s'],wind_direction=cfg['wind_direction'],variant=cfg['variant'],cells=cfg['cells'],profile_transferred='inlet_profile'in cfg,torso_c=stats['torso']['mean_c'],neck_c=stats['neck']['mean_c'],occupied_c=stats['occupied']['mean_c'],neck_speed_mean=stats['neck']['mean_speed_m_s'],neck_speed_max_last4s=neckmax,neck_fraction_below20=last['regions']['neck']['fraction_volume_below20c'],cold_volume_below22_m3=last['cold_zone_below22_m3'],torso_range_last4s=stats['torso']['range_c'],neck_range_last4s=stats['neck']['range_c'],sustained_mean20_from_s=intervals,numerical_gates_pass=a['numerically_screened'],target20_means_pass=a['target20c_last4s_means'],local_speed_screen_pass=neckmax<=1,legacy_delta6_means_pass=min(cfg['ambient_c']-stats[k]['mean_c'] for k in ['torso','neck'])>6,combined_upward_error_budget_for20=min(20-stats[k]['mean_c'] for k in ['torso','neck']),combined_upward_error_budget_for_delta6=min(cfg['ambient_c']-6-stats[k]['mean_c'] for k in ['torso','neck']),pressure_revision='exact hydrostatic atmosphere' if 'pressure_boundary_revision'in cfg else 'preliminary uniform p_rgh open boundary',conservation=a['conservation_screen'])
 row['region_mixing_diagnostics']={}
 for region in ['torso','neck']:
  recent=[q for q in a['history'] if q['time_s']>=last['time_s']-4];tt=np.array([q['time_s'] for q in recent]);ff=np.array([q['regions'][region]['mean_origin'] for q in recent]);fm=float(np.trapezoid(ff,tt)/(tt[-1]-tt[0]));excess=row[region+'_c']-(cfg['ambient_c']-(cfg['ambient_c']-cfg['source_c'])*fm)
  row['region_mixing_diagnostics'][region]=dict(mean_cold_origin_fraction=fm,inferred_temperature_excess_k=excess,required_origin_for20_if_excess_fixed=(cfg['ambient_c']-20+excess)/(cfg['ambient_c']-cfg['source_c']),note='Diagnostic identity from the same CFD fields, not an independent prediction. A changed source requires re-solving density/flow.')
 rows.append(row)
by={r['case']:r for r in rows}
mesh=None
if all(k in by for k in ['C12_three_motor_final','C13_three_motor_fine']):
 co=by['C12_three_motor_final'];fi=by['C13_three_motor_fine'];mesh=dict(coarse_cells=co['cells'],fine_cells=fi['cells'],torso_change_c=abs(co['torso_c']-fi['torso_c']),neck_change_c=abs(co['neck_c']-fi['neck_c']),both_changes_below_0_5c=max(abs(co['torso_c']-fi['torso_c']),abs(co['neck_c']-fi['neck_c']))<.5,note='Two-grid sensitivity of uniform-inlet model. Not a rigorous continuum-error bound; profile-transferred case needs its own mesh study.')
profile_change=None
if all(k in by for k in ['C12_three_motor_final','C20_three_motor_profile']):profile_change={k+'_change_c':by['C20_three_motor_profile'][k+'_c']-by['C12_three_motor_final'][k+'_c'] for k in ['torso','neck']}
preferred=by.get('C21_profile_halfCo_continuation',by.get('C20_three_motor_profile',by.get('C13_three_motor_fine',by.get('C12_three_motor_final'))))
if preferred and (not preferred['target20_means_pass']) and 'C22_four_motor_profile' in by:preferred=by.get('C24_four_profile_continued',by['C22_four_motor_profile'])
if preferred and not preferred['numerical_gates_pass']:preferred=None
time_step=None
if all(k in by for k in ['C20_three_motor_profile','C21_profile_halfCo_continuation']):time_step=dict(torso_change_c=abs(by['C20_three_motor_profile']['torso_c']-by['C21_profile_halfCo_continuation']['torso_c']),neck_change_c=abs(by['C20_three_motor_profile']['neck_c']-by['C21_profile_halfCo_continuation']['neck_c']),note='Combined5s continuation and halved Courant limit, not an isolated restart-from-zero timestep study.')
domain=None
if all(k in by for k in ['C17_four_motor_side10','C26_large_domain_side10']):domain=dict(torso_change_c=by['C26_large_domain_side10']['torso_c']-by['C17_four_motor_side10']['torso_c'],neck_change_c=by['C26_large_domain_side10']['neck_c']-by['C17_four_motor_side10']['neck_c'],note='Combined larger domain, ambient tangential inflow and5s continuation from mapped C17@20s. Not an isolated domain-only comparison or a full cold-start wind prediction.')
joint=[x['case'] for x in rows if x['target20_means_pass'] and x['local_speed_screen_pass'] and x['numerical_gates_pass'] and not x['pressure_revision'].startswith('preliminary')]
report=dict(domain_sensitivity=domain,joint_20c_and_peak_speed_screen_cases=joint,selection_note='Thermal candidate selected after continuation checks. No global optimum or comfort claim. Conservative neck-box peak speed screen is separate from mean temperature.',time_step_sensitivity=time_step,status='Executed conditional CFD/CAD/Lean campaign; hardware unvalidated',cases=rows,mesh_sensitivity=mesh,profile_transfer_sensitivity=profile_change,preferred_still_air_candidate=preferred,
 objective='Torso and neck FIXED BOX VOLUME/TIME mean <=20 C at30C; also report legacy >6 K target separately. Local neck max speed1 m/s is an engineering draft screen.',
 region_definition=full[next(iter(full))]['case']['body_regions'] if full else {},
 proof_scope='Lean checks balance/area/heat/error-budget implications. No proof of Navier-Stokes solution, error bounds, catalogue boundary data, comfort or real hardware.',
 source_scope='Loaded catalogue motor pair and fixed-UA path; not measured exhaust map. Three motors active in a four-installed architecture is a candidate, not a required meeting change.',
 limitations=['No solar/radiation or moisture field; adiabatic panels. 35C case has Tin40C, not45C.',
 'Body is a block manikin with100W heat input; fixed skin temperature and human comfort not solved.',
 'Only reference geometry accepted by user. Real mounting, stock part selection and interfaces remain unverified.',
 'Two-grid study applies to uniform profile; transferred profile uses coarse mesh. Internal short URANS follow-up is not long-time validation.',
 'Four-motor mapped wind cases scale the three-motor exit-profile shape; source flow and temperature remain coupled, but internal profile Reynolds sensitivity is untested.',
 'Panel temperature/solar, turbulence closure, turbulent Prandtl number, ambient-domain size and source heat pickup need wider sensitivity before robust claims.'])
(OUT/'cfd-cad-loop.json').write_text(json.dumps(report,indent=2,allow_nan=False))
# Plot executed design sequence, with speed and averaging definition explicit.
compare=[by[k] for k in ['C10_rear_final','C01_side_startup','C12_three_motor_final','C13_three_motor_fine','C20_three_motor_profile','C21_profile_halfCo_continuation','C22_four_motor_profile','C24_four_profile_continued'] if k in by]
fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained');x=np.arange(len(compare));axes[0].bar(x-.18,[r['torso_c'] for r in compare],.35,label='Torso air mean',color='#237e99');axes[0].bar(x+.18,[r['neck_c'] for r in compare],.35,label='Neck air mean',color='#dc9950');axes[0].axhline(20,color='#a84232',ls='--');axes[0].set_xticks(x,[r['case'].split('_')[0]+'\n'+str(r['active_motors'])+' motors' for r in compare],fontsize=9);axes[0].set(ylabel='Fixed-box air-temperature mean (°C)',title='Executed design and source-mode iterations');axes[0].legend(fontsize=9)
axes[1].bar(x,[r['neck_speed_max_last4s'] for r in compare],color='#3c8c80');axes[1].axhline(1,color='#a84232',ls='--',label='1 m/s engineering screen');axes[1].set_xticks(x,[r['case'].split('_')[0] for r in compare]);axes[1].set(ylabel='Largest saved neck-cell speed (m/s)',title='Speed trade-off; not a comfort model');axes[1].legend(fontsize=9)
for ax in axes:ax.grid(axis='y',alpha=.15)
fig.suptitle('Reference seat · last 4 s of20 s startup · conditional model results',fontsize=14);fig.savefig(OUT/'seat-iteration-history.png',dpi=170);plt.close(fig)
# Wind/temperature stress table plot, only when cases exist.
stress=[r for r in rows if r['case'].startswith(('C14','C15','C16','C17','C18','C19','C23','C26'))]
if stress:
 fig,ax=plt.subplots(figsize=(11,4.8),layout='constrained');xx=np.arange(len(stress));ax.bar(xx-.18,[r['torso_c'] for r in stress],.35,label='Torso',color='#237e99');ax.bar(xx+.18,[r['neck_c'] for r in stress],.35,label='Neck',color='#dc9950');ax.axhline(20,color='#a84232',ls='--',label='20°C');ax.set_xticks(xx,[r['case'].split('_')[0]+'\n'+(f"{r['wind_m_s']:g}m/s {r['wind_direction']}" if r['wind_m_s'] else 'panel+500W' if r.get('panel_heat_w') else f"supply{r['supply_c']:.1f}°C\nambient{r['ambient_c']:g}°C") for r in stress],fontsize=9);ax.set(ylabel='Air-temperature mean (°C)',title='Four-motor stress tests · inlet representation varies; see case metadata');ax.legend();ax.grid(axis='y',alpha=.15);fig.savefig(OUT/'seat-stress-tests.png',dpi=170);plt.close(fig)
print(json.dumps(dict(cases=len(rows),preferred=preferred,mesh=mesh),indent=2))
