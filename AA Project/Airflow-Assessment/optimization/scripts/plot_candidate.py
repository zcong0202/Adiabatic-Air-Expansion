"""Plot actual saved candidate CFD fields, not an image-generated plume."""
import json,re,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.patches import Polygon,Rectangle
from audit_round import internal
from round_jet import OPT
case=OPT/'cases/R07_D24_diffuser_3deg_SST';info=json.loads((case/'case.json').read_text());d=info['diffuser']
latest=max([p for p in case.iterdir() if p.is_dir() and p.name.isdigit() and (p/'C').exists()],key=lambda p:int(p.name))
c=internal(latest/'C',True);t=internal(latest/'theta');u=internal(latest/'U',True)
x=np.r_[c[:,0],c[:,0]];y=np.r_[c[:,1],-c[:,1]];theta=np.r_[t,t]
tri=mtri.Triangulation(x,y);cen=np.column_stack([x[tri.triangles].mean(axis=1),y[tri.triangles].mean(axis=1)])
cone=d['cone_length_mm']/1000;L=d['total_length_mm']/1000
rr=np.where(cen[:,0]<-cone-.010,.004,np.where(cen[:,0]<-.010,.004+(cen[:,0]+cone+.010)*math.tan(math.radians(d['half_angle_deg'])),.012))
tri.set_mask((cen[:,0]<0)&(np.abs(cen[:,1])>rr))
fig,axes=plt.subplots(1,2,figsize=(14,5.2),gridspec_kw={'width_ratios':[1.9,1]},layout='constrained')
a=axes[0];im=a.tripcolor(tri,35-30*theta,shading='gouraud',cmap='coolwarm',vmin=5,vmax=35)
for sign in [-1,1]:
 xx=np.array([-L,-cone-.010,-.010,0]);rr=np.array([.004,.004,.012,.012]);poly=np.column_stack([np.r_[xx,xx[::-1]],sign*np.r_[rr,(rr+.002)[::-1]]]);a.add_patch(Polygon(poly,facecolor='#7e8990',edgecolor='#4e5c65',lw=.6))
a.plot([.2,.2],[-.025,.025],color='#126b44',ls='--',lw=2);a.set(xlim=(-L-.01,.25),ylim=(-.055,.055),xlabel='Distance from final outlet (m)',ylabel='Radial position (m)',title='Saved axisymmetric CFD midplane')
a.set_aspect('equal',adjustable='box');a.text(.2,.03,'20 cm target',ha='center',fontsize=9,color='#126b44')
p=case/'postProcessing/targetProfiles'/f'{int(latest.name)}'/'target_theta_U.xy'
if not p.exists():p=max((case/'postProcessing/targetProfiles').glob('*/target_theta_U.xy'),key=lambda p:float(p.parent.name))
profile=np.loadtxt(p);v=np.linspace(-.04,.04,241);yy,zz=np.meshgrid(v,v);temp=35-30*np.interp(np.hypot(yy,zz),profile[:,0],profile[:,1]);axes[1].pcolormesh(yy*1000,zz*1000,temp,cmap='coolwarm',vmin=5,vmax=35,shading='auto');axes[1].add_patch(Rectangle((-25,-25),50,50,fill=False,edgecolor='#126b44',ls='--',lw=2));axes[1].set(xlabel='y (mm)',ylabel='z (mm)',title='Temperature at 20 cm');axes[1].set_aspect('equal')
fig.colorbar(im,ax=axes,label='Air temperature (°C), dry constant-property approximation',shrink=.78)
fig.suptitle(f'8 → 24 mm diffuser · 3° half angle · {d["total_length_mm"]:.1f} mm long\nAssumed 2 g/s, 5°C source, 35°C ambient. Still air. No wall warming in this CFD field.',fontsize=13)
fig.savefig(OPT/'results/candidate-cfd.png',dpi=175);plt.close(fig)
print(OPT/'results/candidate-cfd.png')
