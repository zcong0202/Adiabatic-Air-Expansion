"""Exact parametric outlet prototypes. Units checked; not fitted or pressure-rated."""
from pathlib import Path
import sys,json,math,argparse
import numpy as np
import gmsh,trimesh
from open_flow import ROOT,STUDY,outlets
sys.path.insert(0,str(ROOT/'scripts'))
from generate_designs import write_step_metres

def generate(width=.14,height=.08):
    cad=STUDY/'cad';cad.mkdir(exist_ok=True)
    name=f'outlet-{round(width*1000)}x{round(height*1000)}';wall=.0024;length=.205;radius=.05
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add(name);occ=gmsh.model.occ
    def wire(z,w,h,r=None):
        if r:
            a=math.atan2(height,width);angles=[a,math.pi-a,math.pi+a,2*math.pi-a]
            pts=[occ.addPoint(r*math.cos(b),r*math.sin(b),z) for b in angles];center=occ.addPoint(0,0,z)
            return occ.addWire([occ.addCircleArc(pts[i],center,pts[(i+1)%4]) for i in range(4)])
        pts=[occ.addPoint(x,y,z) for x,y in [(w/2,h/2),(-w/2,h/2),(-w/2,-h/2),(w/2,-h/2)]]
        return occ.addWire([occ.addLine(pts[i],pts[(i+1)%4]) for i in range(4)])
    outer=occ.addThruSections([wire(0,0,0,radius),wire(.03,0,0,radius),wire(.19,width+2*wall,height+2*wall),wire(length,width+2*wall,height+2*wall)],makeSolid=True,makeRuled=True)
    inner=occ.addThruSections([wire(-.001,0,0,radius-wall),wire(.03,0,0,radius-wall),wire(.19,width,height),wire(length+.001,width,height)],makeSolid=True,makeRuled=True)
    solid=occ.cut(outer,inner)[0];occ.synchronize();keep=set(solid);front=solid
    while front:
        front=[(d,abs(t)) for d,t in gmsh.model.getBoundary(front,combined=False,oriented=False)];front=list(set(front)-keep);keep.update(front)
    occ.remove(list(set(gmsh.model.getEntities())-keep),recursive=False);occ.synchronize()
    step=cad/(name+'-metres.step');write_step_metres(step)
    gmsh.option.setNumber('Mesh.MeshSizeMin',.001);gmsh.option.setNumber('Mesh.MeshSizeMax',.004);gmsh.model.mesh.generate(2)
    raw=cad/(name+'-metres.stl');gmsh.write(str(raw));gmsh.finalize()
    mesh=trimesh.load_mesh(raw,process=True);mesh.fix_normals(multibody=True);mesh.apply_scale(1000)
    stl=cad/(name+'-print-mm.stl');mesh.export(stl)
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','M');gmsh.open(str(step))
    gmsh.option.setNumber('Mesh.MeshSizeMin',.001);gmsh.option.setNumber('Mesh.MeshSizeMax',.004);gmsh.model.mesh.generate(2)
    xyz=gmsh.model.mesh.getNodes()[1].reshape(-1,3);bounds=np.r_[xyz.min(axis=0),xyz.max(axis=0)];gmsh.finalize()
    assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
    # OCC analytic BBoxes can enclose loft control points outside the surface.
    # Compare reimported, independently remeshed surface dimensions instead.
    assert np.max(abs(np.array(bounds[3:])-np.array(bounds[:3])-mesh.extents*.001))<.0002
    info=dict(stl=str(stl.relative_to(STUDY)),step=str(step.relative_to(STUDY)),outlet_width_mm=width*1000,outlet_height_mm=height*1000,
              outlet_area_m2=width*height,spigot_od_mm=100,clear_inlet_mm=95.2,length_mm=205,nominal_wall_mm=2.4,
              watertight=bool(mesh.is_watertight),consistent_normals=bool(mesh.is_winding_consistent),components=len(mesh.split()),
              step_units='metres; independently reimported and surface-remeshed; dimensions checked within 0.2 mm',stl_units='millimetres',bounds_mm=mesh.bounds.tolist(),
              print='Bambu H2S; PLA; 0.4 mm nozzle; start 0.2 mm layers and 4-6 walls. Check supports and fit coupon; no G-code.',
              limits='Unfitted near-atmospheric exhaust prototype. Hose/clamps and stock distribution not selected. No pressure rating. External CFD slot dimensions shared; actual internal loft and backpressure not yet validated for pass-by use.')
    (cad/(name+'-verification.json')).write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
    raw.unlink()
    return mesh,info

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--width',type=float,default=.14);p.add_argument('--height',type=float,default=.08);a=p.parse_args();generate(a.width,a.height)
