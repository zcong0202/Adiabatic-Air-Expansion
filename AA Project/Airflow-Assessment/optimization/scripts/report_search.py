"""Publish accepted calculations, explicit uncertainties and reusable datasets."""
import json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
from round_jet import OPT
from search import read_cases,propose


def report():
 records=read_cases();proposal=propose(records);(OPT/'results/cfd-records.json').write_text(json.dumps(records,indent=2));(OPT/'results/search-decision.json').write_text(json.dumps(proposal,indent=2))
 accepted=[r for r in records if r['numerically_accepted']]
 profiles={}
 for r in records:
  if not r.get('target'):continue
  path=OPT/'cases'/r['case']/'postProcessing/targetProfiles'/f"{r['target']['iteration']:g}"/'target_theta_U.xy'
  a=np.loadtxt(path);profiles[r['case']]={'case':r['case'],'diameter_mm':r['diameter_mm'],'internal_diffuser':r.get('diffuser'),'mass_flow_g_s':r['cold_mass_flow_kg_s']*1000,'reynolds_number':r['reynolds_number'],'model':r['turbulence_model'],'accepted':r['numerically_accepted'],'mean_source_fraction':r['target']['mean_source_fraction'],'radius_m':a[:,0].tolist(),'source_fraction':a[:,1].tolist(),'numerically_accepted':r['numerically_accepted'],'model_validated':False}
 (OPT/'results/viewer-profiles.json').write_text(json.dumps(profiles,separators=(',',':')))
 # The plotted curves use only accepted, fully turbulent same-model cases.
 base=sorted([r for r in accepted if not r.get('internal_diffuser_modeled') and r['turbulence_model']=='kEpsilon' and r['mesh_scale']==1 and r['domain_scale']==1 and r['convection_order']==2 and abs(r['cold_mass_flow_kg_s']-.002)<1e-9 and r['reynolds_number']>=5000],key=lambda r:r['diameter_mm'])
 fig,axes=plt.subplots(1,2,figsize=(13,5.2),layout='constrained')
 for tc,col in [(5,'#146d91'),(10,'#e19031'),(15,'#8d4c9a')]:
  axes[0].plot([r['diameter_mm'] for r in base],[(35-tc)*r['target']['mean_source_fraction'] for r in base],'o-',color=col,label=f'{tc}°C source')
 axes[0].axhline(6,color='#b52d32',lw=1.6,label='Required >6°C');axes[0].axhline(7,color='#b52d32',ls=':',label='1°C design margin')
 axes[0].set(xlabel='Round exit diameter (mm)',ylabel='Mean temperature drop (°C)',title='Prescribed uniform outlet · accepted screens');axes[0].grid(alpha=.2);axes[0].legend(fontsize=8)
 internal=sorted([r for r in accepted if r.get('internal_diffuser_modeled') and r['turbulence_model']=='kOmegaSST' and r['mesh_scale']==1 and r['convection_order']==1],key=lambda r:r['diffuser']['half_angle_deg'])
 for tc,col in [(5,'#146d91'),(10,'#e19031'),(15,'#8d4c9a')]:
  axes[1].plot([r['diffuser']['half_angle_deg'] for r in internal],[(35-tc)*r['target']['mean_source_fraction'] for r in internal],'o-',color=col,label=f'{tc}°C source')
 axes[1].axhline(6,color='#b52d32',lw=1.6);axes[1].axhline(7,color='#b52d32',ls=':');axes[1].set(xlabel='Diffuser cone half angle (degrees)',ylabel='Mean temperature drop (°C)',title='Explicit 8 → 24 mm internal diffusers')
 if not internal:axes[1].text(.5,.5,'Internal cases still pending numerical checks',ha='center',transform=axes[1].transAxes)
 axes[1].grid(alpha=.2);axes[1].legend(fontsize=8)
 fig.suptitle('50 × 50 mm target, 200 mm from final outlet · 2 g/s · 35°C ambient\nStill air, constant-density RANS. Hardware unvalidated. Lines guide the eye.',fontsize=12)
 fig.savefig(OPT/'results/optimization-progress.png',dpi=170);plt.close(fig)
 # Numerical sensitivity compares like-for-like parameters only.
 parent=next((r for r in accepted if r['case']=='R02_D24'),None);sens=[]
 if parent:
  for name,label in [('R06_D24_fine','Finer mesh'),('R09_D24_SST','Turbulence model'),('R10_D24_domain','Larger domain'),('R04_D24_upwind','Convection order'),('R11_D24_lowflow','Lower source flow')]:
   r=next((r for r in records if r['case']==name),None)
   if r:sens.append({'case':name,'check':label,'numerically_accepted':r['numerically_accepted'],'mean_drop_c':r.get('target',{}).get('mean_drop_c'),'difference_from_parent_c':r.get('target',{}).get('mean_drop_c',0)-parent['target']['mean_drop_c'],'interpretation':'Use only if numerical checks pass; lower-flow case changes Reynolds number and may leave the fully turbulent regime.'})
 (OPT/'results/sensitivity.json').write_text(json.dumps(sens,indent=2))
 internal_sens=[]
 ip=next((r for r in accepted if r['case']=='R07_D24_diffuser_3deg_SST'),None)
 if ip:
  for name,label,tolerance in [('R12_D24_a3_second_order','Convection order',.5),('R13_D24_a3_fine','Finer internal mesh',.5),('R14_D24_a3_kEpsilon','Internal turbulence model',1.)]:
   r=next((r for r in records if r['case']==name),None)
   if r and r.get('target'):
    delta=r['target']['mean_drop_c']-ip['target']['mean_drop_c']
    internal_sens.append({'case':name,'check':label,'numerically_accepted':r['numerically_accepted'],'mean_drop_c':r['target']['mean_drop_c'],'difference_from_parent_c':delta,'acceptance_tolerance_c':tolerance,'sensitivity_within_tolerance':bool(r['numerically_accepted'] and abs(delta)<=tolerance)})
 (OPT/'results/internal-sensitivity.json').write_text(json.dumps(internal_sens,indent=2))

 summary={'target':json.loads((OPT/'config.json').read_text())['target'],'cases':len(records),'numerically_accepted_cases':len(accepted),'hardware_validated_cases':0,'numerically_accepted_above_6c_at_case_conditions':[{'case':r['case'],'mean_drop_c':r['target']['mean_drop_c']} for r in accepted if r['target']['mean_drop_c']>6],'search_decision':proposal,'sensitivity':sens,'internal_sensitivity':internal_sens,'status':'Conditional design search. No physically validated hardware optimum.','source_assumption':'2 g/s nominal; 5°C source and 35°C ambient. Paired real source measurements absent.','model_limits':'Still-air, constant-density prescribed source. No wind, buoyancy, wall warming or person model. Internal diffuser cases include passage flow but not source backpressure response.'}
 (OPT/'results/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['search_decision','sensitivity','target']},indent=2))
 # Render new, exact CAD surfaces. Full exterior with the measured design length.
 cadpath=OPT/'results/candidate-cad.json'
 if cadpath.exists():
  cad=json.loads(cadpath.read_text());fig=plt.figure(figsize=(14,8),facecolor='#f5f8fa')
  fig.text(.04,.95,'AA · Iterated diffuser concepts',fontsize=23,weight='bold',color='#173e51');fig.text(.04,.905,'Actual generated CAD. 8 mm inlet · 2 mm radial wall · 15 mm inlet and 10 mm exit lands.',fontsize=11,color='#526975')
  for i,c in enumerate(cad):
   ax=fig.add_axes([.02+(i%2)*.5,.49-(i//2)*.40,.46,.35],projection='3d',facecolor='#f5f8fa');mesh=trimesh.load_mesh(OPT/'designs'/c['name']/'wall.stl');verts=np.array(mesh.vertices)*1000
   light=np.array([.4,-.5,.8]);light/=np.linalg.norm(light);lum=.5+.5*np.maximum(mesh.face_normals@light,0);colors=np.column_stack((np.clip(np.array([.28,.58,.71])[None,:]*lum[:,None]+.12,0,1),np.ones(len(lum))));co=Poly3DCollection(verts[mesh.faces],facecolors=colors,edgecolors='none');ax.add_collection3d(co)
   length=c['total_length_mm'];ax.set_xlim(-length-3,5);ax.set_ylim(-18,18);ax.set_zlim(-18,18);ax.set_box_aspect((length+8,36,36),zoom=1.12);ax.view_init(elev=17,azim=-48);ax.set_proj_type('ortho');ax.set_axis_off()
   ax.text2D(.02,1.0,f"{c['name']} · {c['exit_bore_mm']:g} mm exit · {c['cone_half_angle_deg']:g}° half angle",transform=ax.transAxes,fontsize=13,weight='bold',color='#173e51');ax.text2D(.02,-.02,f"Total length {length:.1f} mm",transform=ax.transAxes,fontsize=11,color='#526975')
  fig.text(.04,.035,'Concepts require real fittings, insulation and mounting details. These are not manufacturing release drawings.',fontsize=10,color='#526975');fig.savefig(OPT/'results/iterated-designs.png',dpi=170);plt.close(fig)

if __name__=='__main__':report()
