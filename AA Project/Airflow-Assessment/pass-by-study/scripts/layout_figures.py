"""Scientific geometry views. Arrows show prescribed direction, not CFD vectors."""
import json,math
import numpy as np,trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from open_flow import STUDY,outlets

OUT=STUDY/'results'
def draw():
    fig,axes=plt.subplots(2,3,figsize=(14,8),layout='constrained')
    for j,layout in enumerate(['one-side','two-side','overhead']):
        nozzles=outlets(layout,.35);ax=axes[0,j];side=axes[1,j]
        for n in nozzles:
            b=np.array(n['box']);q=b.mean(axis=1)
            ax.add_patch(Rectangle((b[0,0],b[1,0]),np.diff(b[0])[0],np.diff(b[1])[0],fc='#078da1'))
            side.add_patch(Rectangle((b[1,0],b[2,0]),np.diff(b[1])[0],np.diff(b[2])[0],fc='#078da1'))
            if layout=='overhead': side.annotate('',(q[1],1.75),xytext=(q[1],b[2,0]),arrowprops={'arrowstyle':'->','color':'#078da1'})
            else:
                target=-.2 if q[1]<0 else .2
                ax.annotate('',(q[0],target),xytext=(q[0],q[1]),arrowprops={'arrowstyle':'->','color':'#078da1'})
                side.annotate('',(target,q[2]),xytext=(q[1],q[2]),arrowprops={'arrowstyle':'->','color':'#078da1'})
        ax.plot([-.9,.9],[0,0],'--',color='#a35a13');ax.annotate('Walking path',(.6,0),xytext=(-.9,.13),arrowprops={'arrowstyle':'->','color':'#a35a13'},color='#a35a13')
        ax.add_patch(Rectangle((-.12,-.2),.24,.4,fill=False,ec='#657580',ls='--'))
        side.add_patch(Rectangle((-.2,0),.4,1.75,fill=False,ec='#657580',ls='--'))
        for z in [1.15,1.55]:side.plot([-.2,.2],[z,z],'.',color='#a35a13',ms=6)
        side.plot(0,1.75,'.',color='#a35a13',ms=6)
        ax.set(title=layout.replace('-',' ').title()+' / plan',xlabel='Walking direction x (m)',ylabel='Lateral y (m)',xlim=(-1,1),ylim=(-.85,.85),aspect='equal')
        side.set(title='Front elevation',xlabel='Lateral y (m)',ylabel='Height z (m)',xlim=(-.85,.85),ylim=(0,2.5),aspect='equal')
        for a in [ax,side]:a.grid(alpha=.15)
    fig.suptitle('Outdoor pass-by candidates / 35 cm nominal nearest target distance',fontsize=17)
    fig.supxlabel('Dashed person envelope is a reference only. No person or enclosure in this CFD stage. Arrows are prescribed directions.',fontsize=10)
    fig.savefig(OUT/'outdoor-layouts.png',dpi=150);plt.close(fig)
    mesh=trimesh.load_mesh(STUDY/'cad/outlet-140x80-print-mm.stl');mesh.apply_scale(.001)
    fig=plt.figure(figsize=(10,8));ax=fig.add_subplot(111,projection='3d')
    for n in outlets('one-side',.35):
        b=np.array(n['box']);q=b.mean(axis=1);v=mesh.vertices
        # Local x is along path, local y vertical; local z is the flow axis.
        points=np.column_stack([q[0]+v[:,0],b[1,1]-.205+v[:,2],q[2]+v[:,1]])
        ax.add_collection3d(Poly3DCollection(points[mesh.faces],facecolors='#148a9a',edgecolors='none',alpha=.96))
        ax.quiver(q[0],b[1,1],q[2],0,.25,0,color='#148a9a',arrow_length_ratio=.2)
    ax.plot([-.95,.95],[0,0],[.01,.01],'--',color='#ad671a',lw=2)
    ax.quiver(.65,0,.01,.25,0,0,color='#ad671a',arrow_length_ratio=.3)
    # Upright envelope only, never a seated body or simulated flow obstacle.
    for z in [0,1.75]:ax.plot([-.12,.12,.12,-.12,-.12],[-.2,-.2,.2,.2,-.2],[z]*5,'--',color='#697d87',alpha=.65)
    for x in [-.12,.12]:
        for y in [-.2,.2]:ax.plot([x,x],[y,y],[0,1.75],'--',color='#697d87',alpha=.65)
    ax.text(.2,.25,1.45,'Reference envelope\nabsent from CFD',fontsize=9,color='#526c78')
    ax.set(xlim=(-1,1),ylim=(-.85,.45),zlim=(0,2),xlabel='Walking direction x (m)',ylabel='Lateral y (m)',zlabel='Height z (m)');ax.set_box_aspect((2,1.3,2));ax.view_init(24,-55)
    fig.suptitle('Four free-standing outlets beside a walking path',fontsize=17)
    fig.text(.5,.04,'Generated nozzle CAD shown. Stands, motor/load, stock hoses and connections are not designed here.',ha='center',fontsize=10)
    fig.savefig(OUT/'outdoor-nozzle-assembly.png',dpi=150,bbox_inches='tight');plt.close(fig)
if __name__=='__main__':draw()
