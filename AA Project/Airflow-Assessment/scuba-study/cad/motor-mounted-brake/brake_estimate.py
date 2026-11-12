"""CMD-23 image-based layout estimate. Not manufacturer CAD or fabrication geometry."""
from pathlib import Path
import math,json
import numpy as np
import trimesh as tm
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'brake-estimate';OUT.mkdir(exist_ok=True)
def box(s,p):
 m=tm.creation.box(s);m.apply_translation(p);return m
def cyl(r,h,p,axis='z',n=48):
 m=tm.creation.cylinder(radius=r,height=h,sections=n)
 if axis=='x':m.apply_transform(tm.transformations.rotation_matrix(math.pi/2,[0,1,0]))
 if axis=='y':m.apply_transform(tm.transformations.rotation_matrix(math.pi/2,[1,0,0]))
 m.apply_translation(p);return m
def union(*m):return tm.boolean.union(list(m),engine='manifold')
def cut(m,*b):return tm.boolean.difference([m,*b],engine='manifold')
def hull(*m):return tm.convex.convex_hull(tm.util.concatenate(m).vertices)
def ball(r,p):
 m=tm.creation.icosphere(subdivisions=2,radius=r);m.apply_translation(p);return m
def link(a,b,r):
 a,b=np.array(a),np.array(b);delta=b-a
 m=tm.creation.cylinder(radius=r,height=np.linalg.norm(delta),sections=24)
 m.apply_transform(tm.geometry.align_vectors([0,0,1],delta));m.apply_translation((a+b)/2);return m

def make_brake(rotor_z=28):
 # Pose in main model: x radial; y tangential; z shaft direction. Nominal disc plane z28.
 # Standard PM pitch is an anchor. Body contour and all offsets below are estimates.
 pm=74.17
 front=hull(cyl(18,16,[76,0,40]),*[cyl(12,12,[90,y,38]) for y in [-30,30]])
 back=hull(cyl(16,12,[80,0,16]),*[cyl(11,12,[95,y,16]) for y in [-29,29]])
 body=union(front,back,hull(*[ball(7.5,[104,y,z]) for y in [-17.5,17.5] for z in [21.5,36.5]]),*[cyl(8,18,[99,y,18],'x') for y in [-pm/2,pm/2]],
            link([95,-30,40],[104,-39,49],7))
 body=cut(body,*[cyl(3.3,30,[99,y,18],'x') for y in [-pm/2,pm/2]],box([100,140,4],[32,0,28]))
 arm=hull(cyl(10,6,[76,0,55]),cyl(6,6,[89,35,55]))
 arm=union(arm,cyl(4,8,[89,35,59]),cyl(7,8,[76,0,52]))
 barrel=cut(cyl(6,30,[104,-50,49],'y'),cyl(1.2,32,[104,-50,49],'y'))
 rear_adjust=cyl(10,6,[76,0,7])
 pivot=cyl(5,2,[76,0,59],n=6)
 # Frame IS holes axial; caliper PM holes radial. Stock adapter offsets are provisional.
 adapter=union(*[cyl(8,8,[101,y,3]) for y in [-25.5,25.5]],box([10,51,8],[101,0,3]),
               *[hull(cyl(8,8,[101,s*25.5,3]),cyl(8,12,[115,s*pm/2,18],'x')) for s in [-1,1]])
 adapter=cut(adapter,*[cyl(3.3,14,[101,y,3]) for y in [-25.5,25.5]],*[cyl(3.3,20,[115,y,18],'x') for y in [-pm/2,pm/2]])
 pm_bolts=tm.util.concatenate([union(cyl(3,35 if y<0 else 40,[101 if y<0 else 103.5,y,18],'x'),cyl(5,5,[81,y,18],'x')) for y in [-pm/2,pm/2]])
 pads=tm.util.concatenate([box([12,22,2],[74,0,z]) for z in [25,31]])
 wire=link([104,-36,49],[89,35,57],.7)
 cable=link([104,-65,49],[104,-110,49],2.5)
 parts={'caliper':body,'brake-arm':arm,'barrel-adjuster':barrel,'rear-adjuster':rear_adjust,'brake-pivot':pivot,'adapter':adapter,'pm-bolts':pm_bolts,'pads':pads,'brake-wire':wire,'cable-lead':cable}
 colors={'caliper':'#4a555f','brake-arm':'#354047','barrel-adjuster':'#59636b','rear-adjuster':'#59636b','brake-pivot':'#b94843','adapter':'#7d858b','pm-bolts':'#adb5bb','pads':'#514745','brake-wire':'#8e979b','cable-lead':'#343e45'}
 for k,m in parts.items():
  m.apply_translation([0,0,rotor_z-28]);m.visual.face_colors=[int(colors[k][i:i+2],16) for i in [1,3,5]]+[255]
 # Explicit assumed motion study, not a measured travel specification.
 sweeps=[]
 for degrees in np.linspace(0,30,7):
  q=arm.copy();q.apply_transform(tm.transformations.rotation_matrix(math.radians(degrees),[0,0,1],[76,0,rotor_z+27]));sweeps.append(q)
 sweep=union(*sweeps)
 physical=tm.util.concatenate([parts[k] for k in ['caliper','brake-arm','barrel-adjuster','rear-adjuster','brake-pivot']])
 return parts,sweep,physical

if __name__=='__main__':
 parts,sweep,physical=make_brake()
 checks=[]
 for k,m in parts.items():
  assert m.is_watertight and m.is_volume,k
  m.export(OUT/(k+'-ESTIMATE.stl'))
  checks.append({'part':k,'bounds_mm':np.round(m.bounds,2).tolist(),'watertight':bool(m.is_watertight),'volume_mm3':round(float(m.volume),2)})
 physical.export(OUT/'CMD23-caliper-assembly-ESTIMATE.stl');sweep.export(OUT/'arm-sweep-ASSUMED.stl')
 tm.Scene(parts).export(OUT/'CMD23-layout-ESTIMATE.glb')
 (OUT/'geometry-checks.json').write_text(json.dumps({'status':'Image-based reference geometry, not functional printable brake parts.','axis_order':'x radial, y tangential, z shaft','caliper_body_and_controls_extents_mm':np.round(physical.extents,2).tolist(),'arm_motion_assumed_deg':[0,30],'parts':checks},indent=2)+'\n')
 print(json.dumps({'caliper_extents_xyz_mm':np.round(physical.extents,2).tolist(),'parts':len(parts)}))
