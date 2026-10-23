"""GIF of integer-second native temperature sections and cold-cell volumes."""
from pathlib import Path
import sys,json,io
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
OUT=Path(__file__).resolve().parents[1]/'results'
def animate(name):
    data=json.loads((OUT/(name+'-timeline.js')).read_text().split('=',1)[1].rstrip(';'));images=[]
    for f in data['frames']:
        fig=plt.figure(figsize=(13.5,4.8));axes=[fig.add_subplot(131),fig.add_subplot(132)];ax=fig.add_subplot(133,projection='3d');fig.subplots_adjust(left=.055,right=.93,bottom=.24,top=.8,wspace=.3)
        for a,s in zip(axes,[f['sections'][0],f['sections'][2]]):
            im=a.pcolormesh(s['axis_a'],s['axis_b'],np.array(s['values_c'],float),cmap='coolwarm',vmin=1,vmax=30,shading='flat');a.set(xlim=(-.5,.5),ylim=(1,1.7),xlabel='Width x (m)',ylabel='Height z (m)',title=f"{s['distance_m']*100:.0f} cm · best 5 cm ΔT {s['best_sampled_5cm_mean_drop_k']:.1f} K",aspect='equal')
        geo=f['range'];v=np.array(geo['vertices']);faces=np.array(geo['faces'],int)
        if len(faces):ax.add_collection3d(Poly3DCollection(v[faces],facecolor='#2da9bf',edgecolor='none',alpha=.85))
        for n in data['nozzles']:
            x,y,z=n['box'];ax.plot([x[0],x[1]],[y[1],y[1]],[sum(z)/2]*2,color='#253b46',lw=5)
        ax.set(xlim=(-.5,.5),ylim=(-.6,.02),zlim=(1,1.7),xlabel='x (m)',ylabel='y (m)',zlabel='Height (m)',box_aspect=(1,.62,.7),title=f"20–50 cm air ≥6 K colder\n{geo['volume_m3']*1000:.2f} L");ax.view_init(22,-60)
        fig.suptitle(f"Scuba source · one loaded motor / one nozzle · {f['time_s']} s\n19.4 g/s · {data['source_c']:.2f}°C assumed source · 30°C ambient · gravity / still air",fontsize=13)
        cb=fig.add_axes([.25,.14,.32,.035]);fig.colorbar(im,cax=cb,orientation='horizontal',label='Air temperature (°C)')
        fig.text(.5,.025,'Native 3D CFD cells at saved integer seconds. No source-off decay, person, wind or hardware validation.',ha='center',fontsize=9)
        b=io.BytesIO();fig.savefig(b,format='png',dpi=100);plt.close(fig);b.seek(0);images.append(Image.open(b).convert('RGB').copy())
    dest=OUT/(name+'-cooling.gif');images[0].save(dest,save_all=True,append_images=images[1:],duration=1000,loop=0);return dest
if __name__=='__main__':print(animate(sys.argv[1]))
