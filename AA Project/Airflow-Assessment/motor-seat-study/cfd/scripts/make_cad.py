"""Parametric low-pressure outlet prototype and assumed seat assembly.
No motor interface, pressure certification or supplier component CAD implied.
"""
from pathlib import Path
import numpy as np,math,json,sys
import gmsh,trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from seat_cfd import STUDY,geometry
CAD=STUDY/'cad';OUT=STUDY/'results';CAD.mkdir(exist_ok=True)
D=float(sys.argv[1]) if len(sys.argv)>1 else 100
wall=.0024;width=.14;height=.08;length=.205;radius=D/2000
sys.path.insert(0,str(STUDY.parent/'scripts'));from generate_designs import write_step_metres

def wire(z,w,h,r=None):
 o=gmsh.model.occ
 if r:
  angle=math.atan2(height,width);angles=[angle,math.pi-angle,math.pi+angle,2*math.pi-angle]
  pts=[o.addPoint(r*math.cos(a),r*math.sin(a),z) for a in angles];center=o.addPoint(0,0,z)
  return o.addWire([o.addCircleArc(pts[i],center,pts[(i+1)%4]) for i in range(4)])
 pts=[o.addPoint(x,y,z) for x,y in [(w/2,h/2),(-w/2,h/2),(-w/2,-h/2),(w/2,-h/2)]]
 return o.addWire([o.addLine(pts[i],pts[(i+1)%4]) for i in range(4)])
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('AA_140x80_low_pressure_outlet');o=gmsh.model.occ
outer=o.addThruSections([wire(0,0,0,radius),wire(.03,0,0,radius),wire(.19,width+2*wall,height+2*wall),wire(length,width+2*wall,height+2*wall)],makeSolid=True,makeRuled=True)
inner=o.addThruSections([wire(-.001,0,0,radius-wall),wire(.03,0,0,radius-wall),wire(.19,width,height),wire(length+.001,width,height)],makeSolid=True,makeRuled=True)
solid=o.cut(outer,inner)[0];o.synchronize()
keep=set(solid);front=solid
while front:
 front=[(d,abs(t)) for d,t in gmsh.model.getBoundary(front,combined=False,oriented=False)];front=list(set(front)-keep);keep.update(front)
o.remove(list(set(gmsh.model.getEntities())-keep),recursive=False);o.synchronize();write_step_metres(CAD/'side-slot-140x80-flow-body.step')
gmsh.option.setNumber('Mesh.MeshSizeMin',.001);gmsh.option.setNumber('Mesh.MeshSizeMax',.004);gmsh.model.mesh.generate(2);gmsh.write(str(CAD/'outlet-metres.stl'));gmsh.finalize()
m=trimesh.load_mesh(CAD/'outlet-metres.stl',process=True);m.fix_normals(multibody=True);m.apply_scale(1000);m.export(CAD/'side-slot-140x80-print-mm.stl')
assert m.is_watertight and m.is_winding_consistent
# Independent STEP import and SI bounding-box check.
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','M');gmsh.open(str(CAD/'side-slot-140x80-flow-body.step'));bounds=gmsh.model.getBoundingBox(-1,-1);gmsh.finalize();span=np.array(bounds[3:])-np.array(bounds[:3]);assert np.max(span)<.25 and np.max(span)>.2
verification=dict(watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),components=len(m.split()),stl_units='millimetres',step_units='metres',step_reimport_bounds_m=bounds,stl_bounds_mm=m.bounds.tolist(),volume_mm3=float(m.volume),mass_pla_g_at_1_24g_cm3=float(m.volume*.00124),exit_open_area_m2=width*height,inlet_clear_diameter_mm=D-4.8,inlet_spigot_od_mm=D,overall_length_mm=205,nominal_wall_mm=2.4,
 print_setup='PLA; 0.4 mm nozzle; 0.2 mm layers; 4-6 walls. Orient spigot down; inspect overhangs/supports in slicer. No G-code generated.',
 fit_status='Nominal 100 mm hose slip spigot. Fit, retention and hose/clamp interface require a coupon test. No threaded motor mounting is included.',
 cfd_scope='CFD resolves outlet patches and external flow only. Internal loft separation/loss/velocity uniformity not resolved.',pressure_scope='Atmospheric exhaust flow body only. Not a compressed-air pressure component.')
(CAD/'cad-verification.json').write_text(json.dumps(verification,indent=2))
# Editable parametric source as Python is the exact CAD generator; also supply a simple OpenSCAD shape.
(CAD/'side-slot-parametric.scad').write_text('''// Millimetres. Approximate hull representation; exact BRep/STL from make_cad.py.
wall=2.4; W=140; H=80; OD=100; L=205; $fn=96;
module shape(r,w,h) {
 cylinder(h=30,r=r);
 hull(){translate([0,0,29]) cylinder(h=1,r=r); translate([-w/2,-h/2,190]) cube([w,h,1]);}
 translate([-w/2,-h/2,190]) cube([w,h,15]);
}
difference(){shape(OD/2,W+2*wall,H+2*wall);translate([0,0,-0.1])shape(OD/2-wall,W,H);translate([-W/2,-H/2,204.8])cube([W,H,1]);}
''')
# Assembly CAD uses simplified solid envelopes for seat, body, source and collector.
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('AA_reference_seat_assembly');o=gmsh.model.occ
for item in geometry():
 b=item['box'];tag=o.addBox(b[0][0],b[1][0],b[2][0],b[0][1]-b[0][0],b[1][1]-b[1][0],b[2][1]-b[2][0])
 if item['name'] in ['left','right']:
  holes=[(3,o.addBox(.42,-.51 if item['name']=='left' else .43,z-.04,.14,.08,.08)) for z in [.84,1.24]]
  tag=o.cut([(3,tag)],holes)[0][0][1]
 o.synchronize();gmsh.model.setEntityName(3,tag,'REFERENCE_'+item['name'])
gmsh.option.setString('Geometry.OCCTargetUnit','M')
for side in [-1,1]:
 for z in [.84,1.24]:
  body=o.importShapes(str(CAD/'side-slot-140x80-flow-body.step'))
  o.rotate(body,0,0,0,1,0,0,side*math.pi/2)
  o.translate(body,.49,side*(.45+length),z)
  o.synchronize()
  for d,t in body:gmsh.model.setEntityName(d,t,'CUSTOM_140x80_OUTLET')
# Off-the-shelf source and collector represented by labelled envelopes only.
for i in range(4):
 tag=o.addCylinder(-.25,-.30+i*.20,.20,0,0,.30,.035);o.synchronize();gmsh.model.setEntityName(3,tag,'STOCK_MOTOR_ENVELOPE_'+str(i+1))
tag=o.addCylinder(-.25,-.4,.12,0,.8,0,.075);o.synchronize();gmsh.model.setEntityName(3,tag,'STOCK_COLLECTOR_ENVELOPE')
o.synchronize();write_step_metres(CAD/'reference-seat-assembly-envelopes.step');gmsh.finalize()
# Assembly visualization from the same scene boxes and actual nozzle mesh placement.
fig=plt.figure(figsize=(11,8));ax=fig.add_subplot(111,projection='3d')
for item in geometry():
 b=np.array(item['box']);box=trimesh.creation.box(extents=b[:,1]-b[:,0],transform=trimesh.transformations.translation_matrix(b.mean(axis=1)))
 isbody=item['name'] in ['torso','head','legL','legR'];color='#e6b77a' if isbody else '#547a8b' if item['name']=='seat' else '#a5bac4'
 ax.add_collection3d(Poly3DCollection(box.triangles,facecolors=color,edgecolors='#6b8793',linewidths=.2,alpha=.8 if isbody else .16))
for side in [-1,1]:
 for z in [.84,1.24]:
  nm=m.copy();nm.apply_scale(.001);verts=nm.vertices.copy();# model local x,y = aperture horizontal, vertical; local z = flow-axis length
  nm.vertices=np.column_stack([.49+verts[:,0],side*(.45+length-verts[:,2]),z+verts[:,1]])
  ax.add_collection3d(Poly3DCollection(nm.triangles,facecolors='#168e9d',edgecolors='none',alpha=.95))
  ax.quiver(.49,side*.43,z,0,-side*.20,0,color='#0b657c',arrow_length_ratio=.25,lw=2)
ax.set(xlim=(-.4,1),ylim=(-.85,.85),zlim=(0,1.9),xlabel='Front direction x (m)',ylabel='Width y (m)',zlabel='Height z (m)');ax.set_box_aspect((1.4,1.7,1.9));ax.view_init(elev=20,azim=32)
fig.suptitle('Reference seat + four custom side outlets',fontsize=18);fig.text(.5,.06,'0.9 m × 0.85 m × 1.8 m enclosure; block manikin; geometry assumed and user accepted.',ha='center',fontsize=10);fig.text(.5,.03,'Nozzles are generated CAD. Seat/source envelopes and mounting interfaces are not manufacturing drawings.',ha='center',fontsize=9)
fig.savefig(OUT/'seat-assembly.png',dpi=160,bbox_inches='tight');plt.close(fig)
# Actual standalone nozzle view.
fig=plt.figure(figsize=(8,6));ax=fig.add_subplot(111,projection='3d');ax.add_collection3d(Poly3DCollection(m.triangles,facecolors=np.clip(np.array([.12,.53,.64])[None,:]*(.40+.60*np.maximum(m.face_normals@np.array([.3,-.5,.8]),0))[:,None]+.08,0,1),edgecolors='none',alpha=1));bb=m.bounds;ax.set(xlim=bb[:,0],ylim=bb[:,1],zlim=bb[:,2]);ax.set_box_aspect(m.extents.copy());ax.view_init(20,-50);ax.set_axis_off();fig.suptitle(f'Custom outlet: {D:g} mm nominal spigot → 140 × 80 mm slot');fig.text(.5,.05,'205 mm long · 2.4 mm nominal wall · low-pressure exhaust prototype · fit unverified',ha='center',fontsize=9);fig.savefig(OUT/'slot-cad.png',dpi=160,bbox_inches='tight');plt.close(fig)
print(json.dumps(verification,indent=2))
