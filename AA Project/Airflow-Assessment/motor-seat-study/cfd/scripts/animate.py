"""Render saved transient temperature fields, with labelled temporal interpolation."""
from pathlib import Path
import numpy as np,json,sys,hashlib,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import FFMpegWriter
from scipy.interpolate import RegularGridInterpolator
from audit_seat import arr,audit
from seat_cfd import CFD,STUDY
OUT=STUDY/'results'
def data(case):
 a=audit(case);mesh=np.load(case/'mesh-metadata.npz');idx=mesh['indices'];x,y,z=[(mesh[k][:-1]+mesh[k][1:])/2 for k in ['x','y','z']];shape=(len(z),len(y),len(x));front=[];side=[];times=[];hashes={}
 yy,zz=np.meshgrid(np.linspace(-.49,.49,150),np.linspace(.02,1.8,230));xx,zs=np.meshgrid(np.linspace(-.04,.98,150),np.linspace(.02,1.8,230))
 paths=sorted([p for p in case.iterdir() if p.is_dir() and (p/'T').exists() and p.name.replace('.','').isdigit()],key=lambda p:float(p.name))
 for p in paths:
  t=arr(p/'T',len(idx));g=np.full(shape,np.nan);g[idx[:,2],idx[:,1],idx[:,0]]=t-273.15
  interp=RegularGridInterpolator((z,y,x),g,bounds_error=False,fill_value=np.nan)
  front.append(interp(np.column_stack([zz.ravel(),yy.ravel(),np.full(yy.size,.49)])).reshape(yy.shape))
  side.append(interp(np.column_stack([zs.ravel(),np.zeros(zs.size),xx.ravel()])).reshape(xx.shape))
  times.append(float(p.name));hashes[p.name]=hashlib.sha256((p/'T').read_bytes()).hexdigest()
 return a,np.array(times),np.array(front),np.array(side),yy,zz,xx,zs,hashes

def render(name):
 case=CFD/'cases'/name;a,times,front,side,yy,zz,xx,zs,hashes=data(case);info=a['case']
 fig,axes=plt.subplots(1,2,figsize=(11.5,7),dpi=100);fig.subplots_adjust(left=.07,right=.9,bottom=.16,top=.82,wspace=.25)
 im=axes[0].pcolormesh(yy,zz,front[0],cmap='coolwarm',vmin=1,vmax=35,shading='nearest');ims=axes[1].pcolormesh(xx,zs,side[0],cmap='coolwarm',vmin=1,vmax=35,shading='nearest')
 for ax in axes:ax.set_ylim(0,1.85);ax.set_facecolor('#e1e6e8')
 axes[0].set(xlabel='Width y (m)',ylabel='Height z (m)',title='Air plane in front of body: x = 0.49 m',xlim=(-.5,.5))
 for z0,z1,y0,y1 in [(.48,1.2,-.2,.2),(1.2,1.44,-.14,.14)]:axes[0].add_patch(Rectangle((y0,z0),y1-y0,z1-z0,fill=False,ec='#4c5960',lw=1,ls=':'))
 for y0 in [-.45,.45]:
  for z0 in [.8,1.2]:axes[0].plot([y0,y0],[z0,z0+.08],color='#00c9e0',lw=4)
 for key,col in [('torso','#25613e'),('neck','#25613e')]:
  box=np.array(info['body_regions'][key]);axes[0].add_patch(Rectangle((box[1,0],box[2,0]),box[1,1]-box[1,0],box[2,1]-box[2,0],fill=False,ec=col,lw=1,ls='--'))
 axes[1].set(xlabel='Front direction x (m)',ylabel='Height z (m)',title='Centre plane: y = 0',xlim=(-.05,1))
 for b in info['geometry']:
  box=np.array(b['box'])
  if box[1,0]<=0<=box[1,1]:axes[1].add_patch(Rectangle((box[0,0],box[2,0]),box[0,1]-box[0,0],box[2,1]-box[2,0],fc='#9aa9b1',ec='#758a95',lw=.5))
 fig.colorbar(im,ax=axes,location='right',fraction=.035,pad=.04,label='Air temperature (°C)')
 fig.suptitle('AA reference seat · transient 3D CFD cooling',fontsize=17,y=.96)
 active=info.get('active_motors',round(info['source_mass_kg_s']/.0194))
 fig.text(.5,.9,f'{active} loaded motors · {info["source_mass_kg_s"]*1000:.1f} g/s · {info["source_c"]:.2f}°C supply · 30°C ambient · still air',ha='center',fontsize=11)
 label=fig.text(.5,.07,'',ha='center',fontsize=11)
 fig.text(.5,.025,'Perfect-gas buoyant URANS. Assumed reference geometry; 100 W body. Hardware unvalidated.',ha='center',fontsize=9)
 def draw(t):
  j=min(np.searchsorted(times,t,side='right')-1,len(times)-2);j=max(j,0);f=(t-times[j])/(times[j+1]-times[j]);f=np.clip(f,0,1)
  im.set_array((front[j]*(1-f)+front[j+1]*f).ravel());ims.set_array((side[j]*(1-f)+side[j+1]*f).ravel())
  means={k:np.interp(t,[r['time_s'] for r in a['history']],[r['regions'][k]['mean_c'] for r in a['history']]) for k in ['torso','neck']}
  label.set_text(f'Simulated time {t:4.1f} s  |  Torso-region mean {means["torso"]:.1f}°C  |  Neck-region mean {means["neck"]:.1f}°C')
 draw(times[-1]);fig.savefig(OUT/(name+'-temperature.png'),dpi=150)
 fps=12;frames=121;movie=OUT/(name+'-cooling.mp4')
 writer=FFMpegWriter(fps=fps,codec='libx264',extra_args=['-pix_fmt','yuv420p','-crf','21','-movflags','+faststart'])
 with writer.saving(fig,str(movie),dpi=100):
  for t in np.linspace(times[0],times[-1],frames):draw(t);writer.grab_frame()
 plt.close(fig)
 subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(movie),'-filter_complex','fps=8,scale=760:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse',str(OUT/(name+'-cooling.gif'))],check=True)
 provenance=dict(case=name,type='Time-dependent CFD temperature fields, not particles in a frozen field',saved_times_s=times.tolist(),temporal_interpolation='Linear interpolation between 1-second CFD outputs; not added solver time steps',simulated_duration_s=float(times[-1]-times[0]),video_duration_s=frames/fps,frames=frames,fps=fps,spatial_display='Trilinear interpolation of native Cartesian cell centres; solid cells masked',temperature_field_sha256=hashes,hardware_validated=False)
 (OUT/(name+'-animation-provenance.json')).write_text(json.dumps(provenance,indent=2));print(movie)
if __name__=='__main__':render(sys.argv[1])
