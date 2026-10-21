"""Animate mean-flow advection in a saved STEADY field. No transient CFD claim."""
import json, math, hashlib, subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.patches import Polygon, Rectangle
from matplotlib.animation import FFMpegWriter
from audit_round import internal
from round_jet import OPT

case=OPT/'cases/R07_D24_diffuser_3deg_SST'
data=case/'5124';out=OPT/'results';out.mkdir(exist_ok=True)
info=json.loads((case/'case.json').read_text());d=info['diffuser']
c=internal(data/'C',True);theta=internal(data/'theta');u=internal(data/'U',True)
x=np.r_[c[:,0],c[:,0]];y=np.r_[c[:,1],-c[:,1]]
tri=mtri.Triangulation(x,y)
centx=x[tri.triangles].mean(axis=1);centy=y[tri.triangles].mean(axis=1)
cone=d['cone_length_mm']/1000;L=d['total_length_mm']/1000
def radius(x):
 return np.where(x<-cone-.010,.004,np.where(x<-.010,.004+(x+cone+.010)*math.tan(math.radians(3)),.012))
tri.set_mask((centx<0)&(np.abs(centy)>radius(centx)))
ux=mtri.LinearTriInterpolator(tri,np.r_[u[:,0],u[:,0]])
uy=mtri.LinearTriInterpolator(tri,np.r_[u[:,1],-u[:,1]])
def velocity(p):
 return np.column_stack([ux(p[:,0],p[:,1]).filled(np.nan),uy(p[:,0],p[:,1]).filled(np.nan)])
# Integrate deterministic mean-flow pathlines. No synthetic turbulent motion.
dt=0.00002
p=np.column_stack([np.full(17,-L+.002),np.linspace(-.0033,.0033,17)])
paths=[p.copy()]
for k in range(12000):
 active=np.isfinite(p).all(axis=1)&(p[:,0]<.265)
 if not active.any():break
 q=p[active];v=velocity(q);mid=q+.5*dt*v;v2=velocity(mid)
 p[active]=q+dt*v2
 p[~active]=np.nan
 paths.append(p.copy())
paths=np.array(paths)
lifetimes=[]
for j in range(paths.shape[1]):
 valid=np.isfinite(paths[:,j]).all(axis=1);ids=np.flatnonzero(valid)
 lifetimes.append(float(ids[-1]*dt) if len(ids) else 0)
assert min(lifetimes)>.01
assert all(np.nanmax(paths[:,j,0])>.20 for j in range(paths.shape[1]))
print('Pathlines reach target; physical travel times:',lifetimes,flush=True)

fig=plt.figure(figsize=(12.8,7.2),dpi=100)
gs=fig.add_gridspec(2,2,height_ratios=[1,.12],width_ratios=[2.4,1],left=.07,right=.95,top=.78,bottom=.15,wspace=.25)
a=fig.add_subplot(gs[0,0]);b=fig.add_subplot(gs[0,1])
temp=35-30*np.r_[theta,theta]
im=a.tripcolor(tri,temp,shading='gouraud',cmap='coolwarm',vmin=5,vmax=35,rasterized=True)
for sign in [-1,1]:
 xx=np.array([-L,-cone-.010,-.010,0]);rr=np.array([.004,.004,.012,.012])
 a.add_patch(Polygon(np.column_stack([np.r_[xx,xx[::-1]],sign*np.r_[rr,(rr+.002)[::-1]]]),facecolor='#657884',edgecolor='#344652',lw=.7,zorder=4))
a.plot([.2,.2],[-.025,.025],'--',color='#063e28',lw=2,zorder=5)
a.text(.2,.034,'Target at 200 mm',ha='center',fontsize=10,color='#063e28')
a.axvline(0,color='#5c6772',lw=.6,ls=':');a.text(0,-.044,'Final outlet',ha='center',fontsize=9)
a.set(xlim=(-L-.012,.255),ylim=(-.057,.057),xlabel='Distance from final outlet (m)',ylabel='Radial position (m)',title='Temperature field and moving mean-flow tracers')
a.set_aspect('equal',adjustable='box')
profile=max((case/'postProcessing/targetProfiles').glob('*/target_theta_U.xy'),key=lambda p:float(p.parent.name))
pr=np.loadtxt(profile);v=np.linspace(-40,40,161);yy,zz=np.meshgrid(v,v)
target=35-30*np.interp(np.hypot(yy,zz)/1000,pr[:,0],pr[:,1])
b.pcolormesh(yy,zz,target,shading='auto',cmap='coolwarm',vmin=5,vmax=35)
b.add_patch(Rectangle((-25,-25),50,50,fill=False,ls='--',lw=2,edgecolor='#063e28'))
b.set(xlabel='y (mm)',ylabel='z (mm)',title='Target plane · steady');b.set_aspect('equal')
fig.colorbar(im,ax=[a,b],orientation='horizontal',fraction=.045,pad=.22,label='Air temperature (°C)')
fig.suptitle('AA · 8 → 24 mm diffuser · 3° half angle\nSTEADY CFD FIELD · animated tracers · NOT transient CFD',fontsize=16,y=.965)
fig.text(.5,.825,'Assumed 2 g/s · 5°C source · 35°C ambient · still air · adiabatic walls',ha='center',fontsize=11)
fig.text(.5,.065,'Predicted mean drop: 9.44°C across 50 × 50 mm at 200 mm. Hardware performance unverified.',ha='center',fontsize=11)
fig.text(.5,.025,'Tracers follow the saved mean velocity, slowed ~42×. Turbulent fluctuations are not resolved in this animation.',ha='center',fontsize=10,color='#475969')
points=a.scatter([],[],s=12,c='white',edgecolors='#183c52',linewidths=.4,zorder=6)
trail=a.scatter([],[],s=4,c='white',alpha=.38,linewidths=0,zorder=5)
fps=24;frames=192;physical_step=.001
offsets=np.linspace(0,1,12,endpoint=False)
def positions(t,lag=0):
 result=[]
 for j,life in enumerate(lifetimes):
  phase=((t-lag)/life+offsets+j*.137)%1
  ids=np.minimum((phase*life/dt).astype(int),len(paths)-1)
  result.extend(paths[ids,j,:])
 return np.array(result)
writer=FFMpegWriter(fps=fps,codec='libx264',metadata={'title':'AA steady CFD with mean-flow tracer animation','comment':'Not transient CFD; prescribed 2 g/s source; hardware unvalidated'},extra_args=['-pix_fmt','yuv420p','-crf','20','-movflags','+faststart'])
movie=out/'AA-C24-steady-CFD-tracers.mp4'
with writer.saving(fig,str(movie),dpi=100):
 for frame in range(frames):
  time=frame*physical_step
  points.set_offsets(positions(time));trail.set_offsets(np.concatenate([positions(time,k*.00015) for k in range(1,6)]))
  if frame==0:fig.savefig(out/'AA-C24-animation-poster.png',dpi=100)
  writer.grab_frame()
  if frame%48==0:print(f'Encoded {frame}/{frames}',flush=True)
plt.close(fig)
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(movie),'-filter_complex','fps=12,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',str(out/'AA-C24-steady-CFD-preview.gif')],check=True)
provenance={'visualization':'Animated deterministic tracer advection through a frozen steady RANS velocity field','not_transient_cfd':True,'source_case':str(case),'saved_iteration':'5124 (solver iteration, not seconds)','frames':frames,'fps':fps,'playback_duration_s':frames/fps,'mean_flow_time_per_video_second_s':physical_step*fps,'path_integration':'Explicit midpoint RK2, 20 microsecond step, linear cell-centre interpolation, mirrored axisymmetric midplane','temperature_field':'35 - 30*theta in degrees C; unchanged saved passive scalar','flow_geometry_changed':False,'physical_validation':False,'input_sha256':{n:hashlib.sha256((data/n).read_bytes()).hexdigest() for n in ['C','U','theta']},'mp4_sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'path_time_to_display_exit_s':lifetimes}
(out/'AA-C24-animation-provenance.json').write_text(json.dumps(provenance,indent=2))
print(movie,flush=True)
