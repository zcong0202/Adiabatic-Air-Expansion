"""Orthographic CPU depth-buffer render of the exact viewer triangles. No AI geometry."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent
parts=json.loads((R/'assembly.json').read_text())
W,H=1500,1100
forward=np.array([.85,.42,1.]);forward/=np.linalg.norm(forward)
right=np.cross([0,1,0],forward);right/=np.linalg.norm(right)
up=np.cross(forward,right)
light=np.array([-.5,.8,1]);light/=np.linalg.norm(light)
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(fontpath,24);small=ImageFont.truetype(fontpath,18)
def render(explosion,path):
    arrays=[]
    for d in parts:
        v=np.array(d['vertices'])+np.array(d['explode'])*explosion
        arrays.append((d,v))
    points=np.concatenate([v for d,v in arrays]);xy=np.column_stack([points@right,points@up]);lo,hi=xy.min(0),xy.max(0)
    scale=min((W-160)/(hi[0]-lo[0]),(H-200)/(hi[1]-lo[1]));centre=(lo+hi)/2
    depth=np.full((H,W),-np.inf);pixels=np.full((H,W,3),246,dtype=np.uint8)
    for d,v in arrays:
        project=np.column_stack([(v@right-centre[0])*scale+W/2,H/2-(v@up-centre[1])*scale,v@forward])
        color=np.array([int(d['color'][i:i+2],16) for i in (1,3,5)])
        for inds in d['faces']:
            vv=v[inds];normal=np.cross(vv[1]-vv[0],vv[2]-vv[0]);nn=np.linalg.norm(normal)
            if nn<1e-12:continue
            normal/=nn
            if normal@forward<=0:continue
            p=project[inds];x0=max(0,int(np.floor(p[:,0].min())));x1=min(W-1,int(np.ceil(p[:,0].max())))
            y0=max(0,int(np.floor(p[:,1].min())));y1=min(H-1,int(np.ceil(p[:,1].max())))
            if x1<x0 or y1<y0:continue
            x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
            if abs(den)<1e-12:continue
            a=((p[1,1]-p[2,1])*(x-p[2,0])+(p[2,0]-p[1,0])*(y-p[2,1]))/den
            b=((p[2,1]-p[0,1])*(x-p[2,0])+(p[0,0]-p[2,0])*(y-p[2,1]))/den
            c=1-a-b;z=a*p[0,2]+b*p[1,2]+c*p[2,2]
            patch=depth[y0:y1+1,x0:x1+1];mask=(a>=-1e-8)&(b>=-1e-8)&(c>=-1e-8)&(z>patch)
            patch[mask]=z[mask]
            brightness=.43+.57*max(0,float(normal@light))
            pixels[y0:y1+1,x0:x1+1][mask]=np.clip(color*brightness,0,255).astype(np.uint8)
    im=Image.fromarray(pixels);draw=ImageDraw.Draw(im)
    draw.text((48,30),'CMD-23  /  IMAGE-BASED ESTIMATE',font=font,fill='#263139')
    draw.text((48,H-70),'Exploded arrangement' if explosion else 'About 55 × 110 × 60 mm  ·  radial / tangential / axial',font=font,fill='#263139')
    draw.text((48,H-35),'Reference reconstruction. Body dimensions and mounting offsets are not verified.',font=small,fill='#627077')
    im.save(R/path)
render(0,'estimate-preview.png')
render(.8,'estimate-exploded.png')
print('Rendered current CAD with a depth buffer.')
