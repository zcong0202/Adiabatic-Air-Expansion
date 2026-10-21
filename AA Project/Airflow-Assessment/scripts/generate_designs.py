"""Parametric concept solids and conforming Gmsh fluid meshes (SI units).

These are proposed geometries, not reverse-engineered Milton/Jeanoko parts.
Threads and mounting supports are deliberately omitted from the flow geometry.
"""
import argparse
import json
import math
from pathlib import Path

import gmsh
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DESIGNS = {
    "D0_round": {"label": "Round baseline", "description": "8 mm bore, 40 mm straight passage", "bore_mm": 8, "exit_area_mm2": math.pi * 4**2, "front_x_m": 0},
    "D1_compact": {"label": "Compact smooth outlet", "description": "8 to 6 mm convergence over final 15 mm", "bore_mm": 8, "exit_area_mm2": math.pi * 3**2, "front_x_m": 0},
    "D2_slot": {"label": "Rounded slot", "description": "8 mm round inlet to 16 x 3 mm capsule outlet", "bore_mm": 8, "exit_area_mm2": 13*3 + math.pi*1.5**2, "front_x_m": 0},
    "D3_shield": {"label": "Open shield", "description": "8 mm baseline plus 26 mm ID / 30 mm OD, 30 mm long open shield; 2 mm gap", "bore_mm": 8, "exit_area_mm2": math.pi * 4**2, "front_x_m": 0.032},
}


def write_step_metres(path):
    """Gmsh exports SI model numbers with a default mm STEP unit tag.
    Declare metres explicitly, then verify independently on import."""
    gmsh.write(str(path))
    text=path.read_text()
    assert 'SI_UNIT(.MILLI.,.METRE.)' in text
    path.write_text(text.replace('SI_UNIT(.MILLI.,.METRE.)','SI_UNIT($,.METRE.)'))


def ring(x, width, height):
    """Single closed spline through a capsule boundary, consistent seam."""
    a, radius = (width-height)/2, height/2
    pts = []
    # Radial intersection with a capsule aligned along y.
    for theta in np.linspace(0, 2*math.pi, 64, endpoint=False):
        cy, sz = math.cos(theta), math.sin(theta)
        if abs(sz) > 1e-12 and radius/abs(sz)*abs(cy) <= a:
            rad = radius/abs(sz)
        else:
            rad = a*abs(cy) + math.sqrt(max(0, radius*radius-a*a*sz*sz))
        pts.append(gmsh.model.occ.addPoint(x, rad*cy, rad*sz))
    curve = gmsh.model.occ.addSpline(pts+[pts[0]])
    return gmsh.model.occ.addWire([curve])


def loft(width, height):
    sections = [ring(-0.04, 0.008, 0.008), ring(-0.026, 0.008, 0.008), ring(-0.012, (0.008+width)/2, (0.008+height)/2), ring(0, width, height)]
    return gmsh.model.occ.addThruSections(sections, makeSolid=True, makeRuled=False)[0][1]


def channel_and_outer(name):
    occ = gmsh.model.occ
    if name == "D1_compact":
        upstream = occ.addCylinder(-0.04, 0, 0, 0.025, 0, 0, 0.004)
        tip = occ.addCone(-0.015, 0, 0, 0.015, 0, 0, 0.004, 0.003)
        inner = occ.fuse([(3,upstream)], [(3,tip)])[0][0][1]
        outer_up = occ.addCylinder(-0.04, 0, 0, 0.025, 0, 0, 0.006)
        outer_tip = occ.addCone(-0.015, 0, 0, 0.015, 0, 0, 0.006, 0.005)
        outer = occ.fuse([(3,outer_up)], [(3,outer_tip)])[0][0][1]
    elif name == "D2_slot":
        inner = loft(0.016, 0.003)
        # The solid uses a separate outer loft with minimum nominal 2 mm wall.
        outer_sections = [ring(-0.04, .012, .012), ring(-.026, .012, .012), ring(-.012, .016, .0095), ring(0,.020,.007)]
        outer = occ.addThruSections(outer_sections, makeSolid=True, makeRuled=False)[0][1]
    else:
        inner = occ.addCylinder(-0.04, 0, 0, 0.04, 0, 0, 0.004)
        outer = occ.addCylinder(-0.04, 0, 0, 0.04, 0, 0, 0.006)
    return inner, outer


def initialize(name):
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add(name)


def solid(name, out):
    initialize(name)
    occ = gmsh.model.occ
    inner, outer = channel_and_outer(name)
    pieces = occ.cut([(3,outer)],[(3,inner)])[0]
    if name == "D3_shield":
        outer_shield = occ.addCylinder(.002,0,0,.03,0,0,.015)
        inner_shield = occ.addCylinder(.002,0,0,.03,0,0,.013)
        pieces += occ.cut([(3,outer_shield)],[(3,inner_shield)])[0]
    occ.synchronize()
    write_step_metres(out / "concept.step")
    gmsh.option.setNumber("Mesh.MeshSizeMin", .0006)
    gmsh.option.setNumber("Mesh.MeshSizeMax", .002)
    gmsh.model.mesh.generate(2)
    gmsh.write(str(out / "wall.stl"))
    gmsh.finalize()


def fluid(name, out, scale=1.0, domain_scale=1.0):
    initialize(name)
    occ = gmsh.model.occ
    inner, unused_outer = channel_and_outer(name)
    occ.remove([(3,unused_outer)], recursive=True)
    ext = occ.addBox(0,-.12*domain_scale,-.12*domain_scale,.4*domain_scale,.24*domain_scale,.24*domain_scale)
    if name == "D3_shield":
        so = occ.addCylinder(.002,0,0,.03,0,0,.015)
        si = occ.addCylinder(.002,0,0,.03,0,0,.013)
        shell = occ.cut([(3,so)],[(3,si)])[0]
        ext = occ.cut([(3,ext)],shell)[0][0][1]
    vols = occ.fuse([(3,inner)],[(3,ext)])[0]
    occ.synchronize()
    assert len(vols)==1, vols
    walls, inlet, ambient, downstream, windin, windout, top, bottom = [], [], [], [], [], [], [], []
    for _, tag in gmsh.model.getBoundary(vols, oriented=False):
        x,y,z = occ.getCenterOfMass(2,tag)
        box = gmsh.model.getBoundingBox(2,tag)
        if abs(x+.04)<1e-7 and box[3]-box[0]<1e-6:
            inlet.append(tag)
        elif x < -1e-8:
            walls.append(tag)
        elif abs(x)<1e-7 and box[3]-box[0]<1e-6:
            ambient.append(tag)
        elif abs(x-.4*domain_scale)<1e-7:
            downstream.append(tag)
        elif abs(y+.12*domain_scale)<1e-7:
            windin.append(tag)
        elif abs(y-.12*domain_scale)<1e-7:
            windout.append(tag)
        elif abs(z+.12*domain_scale)<1e-7:
            bottom.append(tag)
        elif abs(z-.12*domain_scale)<1e-7:
            top.append(tag)
        else:
            walls.append(tag)
    groups={"coldInlet":inlet,"walls":walls,"upstream":ambient,"downstream":downstream,"windIn":windin,"windOut":windout,"top":top,"bottom":bottom}
    assert all(groups.values()), groups
    for name_,tags in groups.items():
        pg=gmsh.model.addPhysicalGroup(2,tags)
        gmsh.model.setPhysicalName(2,pg,name_)
    pg=gmsh.model.addPhysicalGroup(3,[v[1] for v in vols])
    gmsh.model.setPhysicalName(3,pg,"fluid")
    write_step_metres(out / "fluid-domain.step")
    # Smoothly graded jet refinement; mesh scale is explicitly recorded.
    field=gmsh.model.mesh.field.add("MathEval")
    size=f"{scale}*Min(0.018,0.0008+0.018*Max(x,0)+0.5*Max(Sqrt(y*y+z*z)-(0.006+0.10*Max(x,0)),0))"
    gmsh.model.mesh.field.setString(field,"F",size)
    gmsh.model.mesh.field.setAsBackgroundMesh(field)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary",0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints",0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature",0)
    gmsh.option.setNumber("Mesh.Algorithm3D",10)
    gmsh.option.setNumber("Mesh.Optimize",1)
    gmsh.option.setNumber("Mesh.MshFileVersion",2.2)
    gmsh.option.setNumber("Mesh.Binary",0)
    gmsh.model.mesh.generate(3)
    gmsh.write(str(out / "mesh.msh"))
    counts={gmsh.model.mesh.getElementProperties(int(typ))[0]:len(tags) for typ,tags in zip(*gmsh.model.mesh.getElements(3)[:2])}
    metadata={"length_unit":"metre","mesh_scale":scale,"domain_scale":domain_scale,"patches":groups,"element_counts":counts,"nodes":len(gmsh.model.mesh.getNodes()[0]),"target_primary_exit_x_m":.2,"target_clearance_x_m":.2+DESIGNS[name]["front_x_m"],"boundary_layer_prisms":False,"status":"Unstructured tetrahedral screening mesh; wall functions required. Not a validated mesh."}
    (out/"mesh-metadata.json").write_text(json.dumps(metadata,indent=2))
    gmsh.finalize()


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design",choices=list(DESIGNS),action="append")
    parser.add_argument("--mesh-scale",type=float,default=1.0)
    parser.add_argument("--domain-scale",type=float,default=1.0)
    parser.add_argument("--mesh-only",action="store_true")
    args=parser.parse_args()
    for name in args.design or DESIGNS:
        out=ROOT/"designs"/name
        if args.mesh_scale!=1 or args.domain_scale!=1:
            out=out/f"mesh_s{args.mesh_scale:g}_d{args.domain_scale:g}"
        out.mkdir(parents=True,exist_ok=True)
        if not args.mesh_only:
            solid(name,out)
        fluid(name,out,args.mesh_scale,args.domain_scale)
        (out/"design.json").write_text(json.dumps({**DESIGNS[name],"name":name,"length_unit":"metre","common_source_bore_mm":8,"channel_length_mm":40,"threads":"Omitted, adapter flow passage included as assumed 8 mm bore; not ready for manufacturing.","geometry_basis":"Proposed design parameters, not measured product dimensions."},indent=2))
        print("COMPLETE",name,flush=True)
