"""Deterministic faceted ruled-shell prototypes; exact matching STL and STEP solids."""
import json,math,sys
import numpy as np
import trimesh,gmsh
from build import STUDY,ROOT
sys.path.insert(0,str(ROOT/'scripts'))
from generate_designs import write_step_metres

def generate(width,height):
    wall=.0024;radius=.05;length=.205;cad=STUDY/'cad';name=f'outlet-{round(width*1000)}x{round(height*1000)}'
    # Include both inner/outer rectangle corners as well as the circular sampling angles.
    angles=list(np.linspace(0,2*math.pi,64,endpoint=False))
    for w,h in [(width,height),(width+2*wall,height+2*wall)]:
        a=math.atan2(h,w);angles.extend([a,math.pi-a,math.pi+a,2*math.pi-a])
    angles=sorted(set(round(a,12) for a in angles));N=len(angles);vertices=[]
    def ring(z,w,h,r=None):
        result=[]
        for a in angles:
            co,si=math.cos(a),math.sin(a);rr=r if r else min(w/(2*max(abs(co),1e-14)),h/(2*max(abs(si),1e-14)))
            result.append([rr*co,rr*si,z])
        return result
    for inner in [False,True]:
        R=radius-wall if inner else radius;w=width if inner else width+2*wall;h=height if inner else height+2*wall
        for z,circle in [(0,True),(.03,True),(.19,False),(length,False)]:vertices.extend(ring(z,w,h,R if circle else None))
    faces=[]
    for inner in [0,1]:
        offset=inner*4*N
        for j in range(3):
            for i in range(N):
                a=offset+j*N+i;b=offset+j*N+(i+1)%N;c=offset+(j+1)*N+(i+1)%N;d=offset+(j+1)*N+i
                tris=[[a,b,c],[a,c,d]];faces.extend([t[::-1] for t in tris] if inner else tris)
    for i in range(N):
        j=(i+1)%N;faces.extend([[i,4*N+i,4*N+j],[i,4*N+j,j],[3*N+i,3*N+j,7*N+j],[3*N+i,7*N+j,7*N+i]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True);mesh.fix_normals();assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume and len(mesh.split())==1
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',1);gmsh.model.add(name);occ=gmsh.model.occ
    points=[occ.addPoint(*v) for v in mesh.vertices];edges={};surfaces=[]
    for face in mesh.faces:
        es=[]
        for a,b in zip(face,np.roll(face,-1)):
            key=tuple(sorted((int(a),int(b))))
            if key not in edges:edges[key]=occ.addLine(points[key[0]],points[key[1]])
            es.append(edges[key] if a<b else -edges[key])
        surfaces.append(occ.addPlaneSurface([occ.addCurveLoop(es)]))
    solid=occ.addVolume([occ.addSurfaceLoop(surfaces)]);occ.synchronize();volume=occ.getMass(3,solid);assert abs(volume-mesh.volume)<1e-9
    step=cad/(name+'-metres.step');write_step_metres(step);gmsh.finalize()
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',1);gmsh.option.setString('Geometry.OCCTargetUnit','M');gmsh.open(str(step));entities=gmsh.model.getEntities(3);assert len(entities)==1
    box=np.array(gmsh.model.occ.getBoundingBox(*entities[0]));stepVolume=gmsh.model.occ.getMass(*entities[0]);gmsh.finalize();assert np.max(abs((box[3:]-box[:3])-mesh.extents))<.0002;assert abs(stepVolume-mesh.volume)<1e-9
    mm=mesh.copy();mm.apply_scale(1000);stl=cad/(name+'-print-mm.stl');mm.export(stl)
    info=dict(stl=str(stl.relative_to(STUDY)),step=str(step.relative_to(STUDY)),outlet_width_mm=width*1000,outlet_height_mm=height*1000,outlet_area_m2=width*height,spigot_od_mm=100,clear_inlet_mm=95.2,length_mm=205,nominal_wall_mm=2.4,watertight=bool(mesh.is_watertight),consistent_normals=bool(mesh.is_winding_consistent),components=1,step_units='metres; independently reimported closed BRep; dimensions and solid volume checked',stl_units='millimetres',bounds_mm=mm.bounds.tolist(),step_volume_m3=float(stepVolume),stl_volume_m3=float(mesh.volume),circular_faceting_max_radial_error_mm=radius*(1-math.cos(math.pi/64))*1000,geometry='Faceted ruled shell, 64 circle segments plus exact inner/outer rectangle corners. STEP and STL represent the same closed solid.',print='Bambu H2S / PLA / 0.4 mm nozzle; start 0.2 mm layers, 4–6 walls; inspect supports, bridging and fit. No G-code.',limits='Near-atmospheric unfitted outlet prototype, no pressure rating or stock motor fitting. External CFD shares the exact exit dimensions; interior flow and solar/wall heat are not resolved.')
    (cad/(name+'-verification.json')).write_text(json.dumps(info,indent=2));return info

if __name__=='__main__':generate(float(sys.argv[1]),float(sys.argv[2]))
