"""2D native sections and 3D threshold-cell volumes. Fixed scales, no inferred fields."""
import sys,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from build import STUDY

def read_js(path):return json.loads(path.read_text().split('=',1)[1].rstrip(';'))
def volume_figure(name,data,geo,is_range=False):
    out=STUDY/'results';cfg=data['inputs'];fig=plt.figure(figsize=(8.8,7));ax=fig.add_subplot(111,projection='3d');fig.subplots_adjust(left=.03,right=.95,bottom=.20,top=.87)
    vertices=np.array(geo['vertices']);faces=np.array(geo['faces'],int)
    if len(faces):ax.add_collection3d(Poly3DCollection(vertices[faces],facecolor='#26a8c4',edgecolor='none',alpha=.75))
    boxfaces=np.array([[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]])
    for nozzle in cfg['geometry']:
        x,y,z=nozzle['box'];v=np.array([[xx,yy,zz] for zz in z for yy in y for xx in x]);ax.add_collection3d(Poly3DCollection(v[boxfaces],facecolor='#354c58',edgecolor='#172f38',linewidth=.3))
    bounds=geo.get('region_boxes',[[[-.8,.8],[-.2,.2],[1,1.7]]])
    for box in bounds:
        v=np.array([[x,y,z] for z in box[2] for y in box[1] for x in box[0]])
        for a,b in [(0,1),(0,2),(1,3),(2,3),(4,5),(4,6),(5,7),(6,7),(0,4),(1,5),(2,6),(3,7)]:ax.plot(*v[[a,b]].T,color='#718691',ls='--',lw=.6)
    ax.set(xlim=(-1.25,1.25),ylim=(-1.1,1.1),zlim=(0,2.7),xlabel='x (m)',ylabel='y (m)',zlabel='Height z (m)',box_aspect=(2.5,2.2,2.7));ax.view_init(23,-55)
    f=data['final'];whole=f['regions']['domain']['6'];target=f['regions']['range20to50']['6'];roi='20–50 cm target band' if is_range else 'whole domain'
    fig.suptitle(f"{name} · {roi} · 10 s\nAir ≥6°C below ambient (T ≤24°C)",fontsize=12)
    fig.text(.5,.075,f"20–50 cm band: {target['volume_m3']:.4f} m³ / {target['mass_kg']*1000:.1f} g\nWhole domain: {whole['volume_m3']:.4f} m³ / {whole['mass_kg']*1000:.1f} g",ha='center',fontsize=11)
    fig.text(.5,.025,'Native cold cells. Dashed lines are analysis bounds, not walls. Disconnected regions possible. No person.',ha='center',fontsize=8)
    fig.savefig(out/(name+('-range-volume.png' if is_range else '-volume.png')),dpi=120);plt.close(fig)

def render(name):
    out=STUDY/'results';data=json.loads((out/(name+'.json')).read_text());cfg=data['inputs'];sections=read_js(out/(name+'-sections.js'))['sections']
    fig,axs=plt.subplots(1,3,figsize=(13.8,4.3),layout='constrained')
    for ax,s in zip(axs,sections):
        tt=np.array(s['values_c'],float);im=ax.pcolormesh(s['axis_a'],s['axis_b'],tt,shading='flat',vmin=1,vmax=30,cmap='coolwarm')
        ax.set(xlim=(-.8,.8),ylim=(-.2,.2) if cfg['layout']=='overhead' else (1,1.7),xlabel=s['axes'][0]+' (m)',ylabel=s['axes'][1]+' (m)',title=f"{s['distance_m']*100:g} cm · {s['description']}\narea ≥6 K drop: {s['area_ge6_m2']:.4f} m²\nbest sampled 5 cm mean: {s['best_sampled_5cm_mean_drop_k']:.2f} K drop",aspect='equal')
    fig.colorbar(im,ax=axs,label='Air temperature (°C)',shrink=.78)
    fig.suptitle(f"{name} · native 3D CFD sections at 10 s\n{cfg['total_g_s']:g} g/s total ÷ {cfg['outlets']} outlets = {cfg['per_outlet_g_s']:g} g/s each · {cfg['width_m']*1000:.1f} × {cfg['height_m']*1000:.1f} mm · {cfg['closure']}",fontsize=12)
    fig.supxlabel('Still air · gravity −9.81 m/s² · source 0.96°C · ambient 30°C · no person · native cell containing each plane',fontsize=9)
    fig.savefig(out/(name+'-sections.png'),dpi=120);plt.close(fig)
    volume_figure(name,data,read_js(out/(name+'-volume.js')),False);volume_figure(name,data,read_js(out/(name+'-range-volume.js')),True);return name
if __name__=='__main__':
    for name in sys.argv[1:]:print(render(name),flush=True)
