"""Render intact concept CAD. No cutaway, added fittings or mounting hardware."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
DESIGNS=['D0_round','D1_compact','D2_slot','D3_shield']
LABELS=['Round baseline','Compact outlet','Rounded slot','Open shield']
CAPTIONS=['8 mm bore · 40 mm long','8 mm inlet → 6 mm exit · 40 mm long','8 mm inlet → 16 × 3 mm slot · 40 mm long','8 mm core · 26 mm shield bore · 2 mm gap']
fig=plt.figure(figsize=(15,9),facecolor='#f5f8fa')
fig.text(.045,.95,'AA • Complete nozzle views',fontsize=25,weight='bold',color='#173e51')
fig.text(.045,.912,'Actual concept geometry • Full walls shown • Dimensions in millimetres',fontsize=12,color='#526975')
for i,name in enumerate(DESIGNS):
    ax=fig.add_axes([.025+(i%2)*.5,.49-(i//2)*.405,.45,.36],projection='3d',facecolor='#f5f8fa')
    mesh=trimesh.load_mesh(ROOT/'designs'/name/'wall.stl',process=True)
    verts=np.array(mesh.vertices)*1000
    tris=verts[mesh.faces]
    normals=mesh.face_normals
    light=np.array([.5,-.6,.8]);light/=np.linalg.norm(light)
    lum=.50+.50*np.maximum(normals@light,0)
    base=np.array([.25,.56,.70])
    colors=np.column_stack((np.clip(base[None,:]*lum[:,None]+.13,0,1),np.ones(len(lum))))
    if name=='D3_shield':
        shield=tris[:,:,0].mean(axis=1)>1
        colors[shield,:3]=np.clip(np.array([.53,.65,.71])[None,:]*lum[shield,None]+.12,0,1)
    poly=Poly3DCollection(tris,facecolors=colors,edgecolors='none',zsort='average')
    ax.add_collection3d(poly)
    # Positive x view exposes each outlet. Shield view uses a wider frame.
    ax.set_xlim(-43,35);ax.set_ylim(-18,18);ax.set_zlim(-18,18)
    ax.set_box_aspect((78,36,36),zoom=1.2 if name=='D3_shield' else 1.7);ax.view_init(elev=22,azim=-42)
    ax.set_axis_off();ax.set_proj_type('ortho')
    ax.text2D(.06,1.0,f'D{i}  {LABELS[i]}',transform=ax.transAxes,fontsize=15,weight='bold',color='#173e51')
    ax.text2D(.06,-.025,CAPTIONS[i],transform=ax.transAxes,fontsize=11,color='#526975')
fig.text(.045,.055,'Concept CAD only. Source tube, connection threads and shield mounting supports are not modeled.',fontsize=11,color='#526975')
fig.savefig(ROOT/'results/assembled-nozzles.png',dpi=190,facecolor=fig.get_facecolor())
plt.close(fig)
print(ROOT/'results/assembled-nozzles.png')
