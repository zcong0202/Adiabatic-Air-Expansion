"""Export candidate diffuser CAD corresponding to the internal CFD geometry."""
from pathlib import Path
import json,math,sys
import gmsh,trimesh
import numpy as np
from round_jet import OPT,ROOT
sys.path.insert(0,str(ROOT/'scripts'))
from generate_designs import write_step_metres


def generate(d=24,angle=5):
 name=f'C{d:g}_a{angle:g}';out=OPT/'designs'/name;out.mkdir(parents=True,exist_ok=True)
 r=d/2000;cone=(r-.004)/math.tan(math.radians(angle));length=cone+.025
 gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add(name);occ=gmsh.model.occ
 def solid(radius0,radius1):
  a=occ.addCylinder(-length,0,0,.015,0,0,radius0)
  b=occ.addCone(-cone-.010,0,0,cone,0,0,radius0,radius1)
  c=occ.addCylinder(-.010,0,0,.010,0,0,radius1)
  tags=occ.fuse([(3,a)],[(3,b),(3,c)])[0];return tags
 inner=solid(.004,r);outer=solid(.006,r+.002)
 occ.cut(outer,inner);occ.synchronize();write_step_metres(out/'concept.step')
 gmsh.option.setNumber('Mesh.MeshSizeMin',.0007);gmsh.option.setNumber('Mesh.MeshSizeMax',.002);gmsh.model.mesh.generate(2);gmsh.write(str(out/'wall.stl'));gmsh.finalize()
 mesh=trimesh.load_mesh(out/'wall.stl',process=True);mesh.fix_normals(multibody=True);mesh.export(out/'wall.stl');mm=mesh.copy();mm.apply_scale(1000);mm.export(out/'wall-mm.stl')
 info={'name':name,'inlet_bore_mm':8,'exit_bore_mm':d,'cone_half_angle_deg':angle,'cone_length_mm':cone*1000,'total_length_mm':length*1000,'wall_thickness_radial_mm':2,'inlet_land_mm':15,'outlet_land_mm':10,'watertight':bool(mesh.is_watertight),'winding_consistent':bool(mesh.is_winding_consistent),'step_units':'metre','stl_units':'wall.stl metres; wall-mm.stl millimetres','status':'Flow concept. Real source connector, insulation, mounts and manufacturing tolerances remain undefined.'}
 assert mesh.is_watertight and mesh.is_winding_consistent
 (out/'design.json').write_text(json.dumps(info,indent=2));return info

if __name__=='__main__':
 results=[generate(16,5),generate(24,3),generate(24,5),generate(24,7)]
 (OPT/'results/candidate-cad.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
