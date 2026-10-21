"""Show convergence and thermal stress alongside the cooling objective."""
import json,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from round_jet import OPT
records=json.loads((OPT/'results/cfd-records.json').read_text());thermal=json.loads((OPT/'results/thermal-sensitivity.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(13,9),layout='constrained');colors=['#166e91','#e39431','#4d8a59','#8f56a0','#b94b4b']
names=['R00_D8','R01_D16','R07_D24_diffuser_3deg_SST','R05_D24_diffuser_SST','R08_D24_diffuser_7deg_SST']
for name,color in zip(names,colors):
 r=next((r for r in records if r['case']==name),None)
 if not r:continue
 label=name.replace('R00_D8','8 mm exit').replace('R01_D16','16 mm exit').replace('R07_D24_diffuser_3deg_SST','24 mm / 3° diffuser').replace('R05_D24_diffuser_SST','24 mm / 5° diffuser').replace('R08_D24_diffuser_7deg_SST','24 mm / 7° diffuser')
 axes[0,0].plot([v['iteration'] for v in r['history']],[v['mean_drop_c'] for v in r['history']],label=label,color=color)
 s=(OPT/'cases'/name/'log.solver').read_text();xx=[];yy=[]
 for part in re.split(r'\nTime = ',s)[1:]:
  t=float(part.splitlines()[0]);v={}
  for field,value in re.findall(r'Solving for (\w+), Initial residual = ([^,]+)',part):
   if field not in v:v[field]=float(value)
  if 'Ux' in v and 'Uy' in v:xx.append(t);yy.append(max(v['Ux'],v['Uy']))
 axes[0,1].semilogy(xx,yy,label=label,color=color,lw=.8)
axes[0,0].axhline(6,color='black',ls='--');axes[0,0].set(title='Mean cooling settles as iterations continue',xlabel='Solver iteration',ylabel='Mean drop across target (°C)');axes[0,0].legend(fontsize=8)
axes[0,1].axhline(1e-5,color='black',ls='--',label='Fixed momentum threshold');axes[0,1].set(title='Relevant momentum residuals',xlabel='Solver iteration',ylabel='Maximum initial Ux / Uy residual',ylim=(1e-8,1));axes[0,1].legend(fontsize=7)
internal=[r for r in records if r.get('numerically_accepted') and r.get('internal_diffuser_modeled') and r['convection_order']==1 and r['mesh_scale']==1 and r['turbulence_model']=='kOmegaSST']
internal=sorted(internal,key=lambda r:r['diffuser']['half_angle_deg']);labels=[f"{r['diffuser']['half_angle_deg']:g}°" for r in internal];x=np.arange(len(internal));width=.25
for j,typ in enumerate(['dry','combined5','combined10']):
 values=[]
 for r in internal:
  t=next(t for t in thermal if t['case']==r['case'])
  values.append(r['target']['mean_drop_c'] if typ=='dry' else next(v['mean_drop_c'] for v in t['combined_heat_and_humidity'] if v['source_temperature_c']==(5 if typ=='combined5' else 10)))
 axes[1,0].bar(x+(j-1)*width,values,width,label=['Dry CFD, 5°C source','Heat + humidity, 5°C source','Heat + humidity, 10°C source'][j])
axes[1,0].axhline(6,color='black',ls='--');axes[1,0].axhline(7,color='black',ls=':');axes[1,0].set(xticks=x,xticklabels=labels,xlabel='24 mm diffuser cone half angle',ylabel='Mean drop (°C)',title='Assumed thermal stress reduces available margin');axes[1,0].legend(fontsize=7)
checks=[]
for r in internal:
 b=r['native_balance'];checks.append([abs(b['mass_imbalance_relative_to_source'])*100,abs(b['scalar_advective_imbalance_relative_to_source'])*100])
if checks:
 a=np.array(checks);axes[1,1].bar(x-.15,a[:,0],.3,label='Mass imbalance');axes[1,1].bar(x+.15,a[:,1],.3,label='Scalar advective imbalance')
axes[1,1].set(xticks=x,xticklabels=labels,xlabel='Diffuser half angle',ylabel='Absolute imbalance (% of cold source)',title='Native finite-volume balance checks');axes[1,1].legend(fontsize=8)
for a in axes.flat:a.grid(alpha=.18)
fig.suptitle('Numerical checks and one-way thermal sensitivity\n2 g/s, 35°C ambient, 50 × 50 mm target at 20 cm. Heat stress U=20 W/m²/K, ambient RH80%. Hardware unvalidated.',fontsize=12)
fig.savefig(OPT/'results/verification-and-margin.png',dpi=160);plt.close(fig)
