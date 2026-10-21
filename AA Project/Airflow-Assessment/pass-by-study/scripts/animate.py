"""Actual transient open-jet fields plus virtual moving-square air sampling."""
import json,sys,subprocess,hashlib
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import FFMpegWriter
from open_flow import STUDY,CASES
from audit_seat import arr

def render(name):
    case=CASES/name;a=json.loads((case/'audit.json').read_text());cfg=a['case']
    assert a['numerical_screens_pass']
    mesh=np.load(case/'mesh-metadata.npz');idx=mesh['indices'];n=len(idx)
    axes=[(mesh[k][:-1]+mesh[k][1:])/2 for k in ['x','y','z']]
    x,y=np.meshgrid(np.linspace(-.85,.85,180),np.linspace(-.9,.55,155));planes=[];times=[];hashes={}
    paths=sorted([p for p in case.iterdir() if p.is_dir() and (p/'T').exists() and p.name.replace('.','').isdigit() and float(p.name)<=10],key=lambda p:float(p.name))
    for path in paths:
        grid=np.full((len(axes[2]),len(axes[1]),len(axes[0])),np.nan);grid[idx[:,2],idx[:,1],idx[:,0]]=arr(path/'T',n)-273.15
        sample=RegularGridInterpolator((axes[2],axes[1],axes[0]),grid,bounds_error=False,fill_value=np.nan)
        planes.append(sample(np.column_stack([np.full(x.size,1.15),y.ravel(),x.ravel()])).reshape(x.shape));times.append(float(path.name));hashes[path.name]=hashlib.sha256((path/'T').read_bytes()).hexdigest()
    planes=np.array(planes);times=np.array(times)
    trace=json.loads((case/'moving-probe-traces.json').read_text())['left1.15_v1.2_t5.0']
    ttrace=np.array(trace['time_s']);deficit=30-np.array(trace['area_temperature_c'])
    p=next(p for p in a['passages'] if p['patch']=='left1.15' and p['walking_speed_m_s']==1.2 and p['center_crossing_s']==5)
    fig,ax=plt.subplots(1,2,figsize=(12,6.6),dpi=100);fig.subplots_adjust(left=.065,right=.94,top=.78,bottom=.24,wspace=.36)
    im=ax[0].pcolormesh(x,y,planes[0],vmin=1,vmax=30,cmap='coolwarm',shading='nearest')
    fig.colorbar(im,ax=ax[0],fraction=.045,pad=.02,label='Air temperature (°C)')
    for nozzle in cfg['geometry']:
        box=np.array(nozzle['box'])
        if box[2,0]<=1.15<=box[2,1]:ax[0].add_patch(Rectangle((box[0,0],box[1,0]),np.diff(box[0])[0],np.diff(box[1])[0],fc='#00bdcf',ec='#075968'))
    ax[0].plot([-.8,.8],[-.2,-.2],'--',color='#e6bf41',lw=1.2)
    marker,=ax[0].plot([-.025,.025],[-.2,-.2],color='#12191f',lw=3)
    ax[0].set(xlabel='Walking direction x (m)',ylabel='Lateral y (m)',title='Actual CFD air plane at z = 1.15 m',xlim=(-.85,.85),ylim=(-.9,.55),aspect='equal')
    ax[1].plot(ttrace-5,deficit,color='#167d93',lw=2,label='Moving 5 × 5 cm air square')
    ax[1].axhline(6,color='#b2631a',ls='--',label='6 K target');line=ax[1].axvline(0,color='#152b37',lw=1)
    dot,=ax[1].plot([],[],'o',color='#152b37')
    ax[1].set(xlabel='Time relative to passage centre (s)',ylabel='Air-area temperature deficit (K)',xlim=(ttrace[0]-5,ttrace[-1]-5),ylim=(0,max(8,float(deficit.max())*1.1)),title='Virtual passage at 1.2 m/s; centre at 5 s');ax[1].grid(alpha=.2);ax[1].legend(fontsize=8,loc='upper right')
    fig.suptitle('Outdoor nozzle CFD / virtual air exposure / NO HUMAN BODY',fontsize=16,y=.97)
    fig.text(.5,.89,f'{cfg["layout"]} · {cfg["nominal_standoff_m"]*100:g} cm · {cfg.get("outlet_width_m",.14)*1000:g} × {cfg.get("outlet_height_m",.08)*1000:g} mm · pitch {cfg.get("pitch_deg",0):g}° · {cfg["source_mass_kg_s"]*1000:.1f} g/s at {cfg["source_c"]:.2f}°C',ha='center',fontsize=10)
    label=fig.text(.5,.105,'',ha='center',fontsize=11)
    fig.text(.5,.045,'Black line is the vertical 5 cm air patch in plan view. No body, wake, skin heat transfer or upstream startup is simulated.',ha='center',fontsize=9)
    fig.text(.5,.018,'Display: linear interpolation of 1 s native temperature fields. Trace: about 25 ms probes. No synthetic turbulent motion.',ha='center',fontsize=8)
    def draw(t):
        j=max(0,min(np.searchsorted(times,t,side='right')-1,len(times)-2));f=np.clip((t-times[j])/(times[j+1]-times[j]),0,1)
        im.set_array((planes[j]*(1-f)+planes[j+1]*f).ravel());active=ttrace[0]<=t<=ttrace[-1]
        marker.set_visible(active);marker.set_data([(t-5)*1.2-.025,(t-5)*1.2+.025],[-.2,-.2]);line.set_xdata([t-5,t-5])
        if active:
            drop=np.interp(t,ttrace,deficit);dot.set_data([t-5],[drop]);label.set_text(f'Solver time {t:.2f} s | moving-area deficit {drop:.1f} K | total >6 K during this passage: {p["time_above_delta6_s"]:.3f} s')
        else:dot.set_data([],[]);label.set_text(f'Solver time {t:.2f} s | virtual patch crosses this path from {ttrace[0]:.2f} to {ttrace[-1]:.2f} s')
    draw(5);out=STUDY/'results';fig.savefig(out/(name+'-air-field.png'),dpi=150)
    movie=out/(name+'-air-exposure.mp4');writer=FFMpegWriter(fps=12,codec='libx264',extra_args=['-pix_fmt','yuv420p','-crf','21','-movflags','+faststart'])
    with writer.saving(fig,str(movie),dpi=100):
        for t in np.linspace(0,10,121):draw(t);writer.grab_frame()
    plt.close(fig)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(movie),'-filter_complex','fps=8,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse',str(out/(name+'-air-exposure.gif'))],check=True)
    meta=dict(case=name,source='Native transient CFD temperature fields, not particles in a steady field',native_field_times_s=times.tolist(),temperature_field_sha256=hashes,
              display='Trilinear spatial and linear 1-second temporal interpolation',probe_trace='Native approx.25ms cellPoint probes; virtual 5cm square, no human',frames=121,fps=12,simulated_interval_s=[0,10],body_included=False)
    (out/(name+'-animation-provenance.json')).write_text(json.dumps(meta,indent=2));print(movie)
if __name__=='__main__':render(sys.argv[1])
