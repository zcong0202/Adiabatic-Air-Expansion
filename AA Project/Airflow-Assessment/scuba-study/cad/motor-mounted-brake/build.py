"""Motor-mounted brake, static fit prototype. mm. Generates the actual viewer meshes.
No rated brake, shaft hub, pressure component or fragment containment is provided.
Edit parameters.json and rebuild. All interfaces are provisional.
"""
from pathlib import Path
import json, math, zipfile
import numpy as np
import trimesh as tm

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / 'parameters.json').read_text())

def box(size, pos):
    a = tm.creation.box(size); a.apply_translation(pos); return a

def cyl(r, h, pos, sections=64):
    a = tm.creation.cylinder(radius=r, height=h, sections=sections)
    a.apply_translation(pos); return a

def union(*a): return tm.boolean.union(list(a), engine='manifold')
def cut(a, *b): return tm.boolean.difference([a, *b], engine='manifold')
def ring(ro, ri, h, z): return cut(cyl(ro,h,[0,0,z]),cyl(ri,h+2,[0,0,z]))
def joined(a): return tm.util.concatenate(a)

R, RI, B, D, L = [P[k] for k in ['case_outer_radius','case_inner_radius','back_thickness','chamber_depth','lid_thickness']]
Z = P['rotor_plane']
mounts = P['motor_mount_xy']
closure = [[P['closure_pitch_radius']*math.cos(math.radians(a)), P['closure_pitch_radius']*math.sin(math.radians(a))] for a in range(30,390,60)]
def holes(points, diameter, height, z): return [cyl(diameter/2,height,[x,y,z],32) for x,y in points]
rear = cut(cyl(R,B,[0,0,B/2]),
           cyl(P['motor_nose_clearance_diameter']/2,B+2,[0,0,B/2]),
           *holes(mounts,P['motor_mount_clearance_diameter'],B+2,B/2),
           *holes(closure,P['closure_clearance_diameter'],B+2,B/2),
           *holes(P['caliper_mount_xy'],P['caliper_mount_clearance_diameter'],B+2,B/2))
shell = cut(ring(R,RI,D,B+D/2),*holes(closure,P['closure_clearance_diameter'],D+2,B+D/2))
# Radial cable access. This is not a pressure enclosure.
cable = cyl(6,R-RI+6,[0,0,0]);cable.apply_transform(tm.transformations.rotation_matrix(math.pi/2,[0,1,0]));cable.apply_translation([(R+RI)/2,0,Z+8])
shell = cut(shell,cable)
lid = cut(cyl(R,L,[0,0,B+D+L/2]),*holes(closure,P['closure_clearance_diameter'],L+2,B+D+L/2),
          *[box([10,55,L+2],[x,0,B+D+L/2]) for x in [-72,-48,-24,0,24,48,72]])
# Caliper geometry is an envelope, NOT a manufacturer's drawing.
carrier = union(box([18,76,6],[94,0,9]),*[cyl(10,6,[x,y,15]) for x,y in P['caliper_mount_xy']])
carrier = cut(carrier,*holes(P['caliper_mount_xy'],P['caliper_mount_clearance_diameter'],16,12))
motor = joined([cyl(P['motor_body_diameter']/2,P['motor_body_length'],[0,0,-P['motor_body_length']/2-2]),cyl(19,4,[0,0,-2])])
shaft = cyl(P['shaft_diameter']/2,P['shaft_exposed_length'],[0,0,P['shaft_exposed_length']/2])
hub = union(ring(P['hub_outer_diameter']/2,P['shaft_diameter']/2+.2,P['hub_length'],P['hub_back_z']+P['hub_length']/2),ring(29,P['shaft_diameter']/2+.2,4,Z-2.9))
rotor_pattern = [[P['rotor_bolt_pitch_diameter']/2*math.cos(a*math.pi/3),P['rotor_bolt_pitch_diameter']/2*math.sin(a*math.pi/3)] for a in range(6)]
hub = cut(hub,*holes(rotor_pattern,P['rotor_bolt_clearance_diameter'],6,Z-2.9))
rotor = ring(P['rotor_diameter']/2,18.5,P['rotor_thickness'],Z)
windows = []
for i in range(6):
    a = i*math.pi/3
    m = box([30,23,6],[50,0,Z]);m.apply_transform(tm.transformations.rotation_matrix(a,[0,0,1]));windows.append(m)
rotor = cut(rotor,*windows,*holes(rotor_pattern,P['rotor_bolt_clearance_diameter'],6,Z))
caliper = union(box([12,34,22],[95,0,Z]),box([24,34,6],[78,0,Z-8]),box([24,34,6],[78,0,Z+8]),
                *[cyl(9,4,[x,y,20]) for x,y in P['caliper_mount_xy']],box([10,64,4],[94,0,20]))
caliper = cut(caliper,*holes(P['caliper_mount_xy'],P['caliper_mount_clearance_diameter'],10,20))
pads = joined([box([10,22,3],[74,0,Z-3]),box([10,22,3],[74,0,Z+3])])
motor_bolts = joined([joined([cyl(3,15,[x,y,-.5],24),cyl(5,4,[x,y,8],24)]) for x,y in mounts])
closure_bolts = joined([joined([cyl(2.5,B+D+L+8,[x,y,(B+D+L)/2],24),cyl(4.5,4,[x,y,B+D+L+2],6)]) for x,y in closure])
closure_nuts = joined([cut(cyl(4.7,4,[x,y,-2],6),cyl(2.6,6,[x,y,-2],24)) for x,y in closure])
caliper_bolts = joined([joined([cyl(3,28,[x,y,10],24),cyl(5,4,[x,y,24],24)]) for x,y in P['caliper_mount_xy']])
rotor_bolts = joined([joined([cyl(2.4,7,[x,y,Z-1],24),cyl(4.3,2,[x,y,Z+2],24)]) for x,y in rotor_pattern])

items = [
 ('motor','Motor envelope',motor,'#6b7782','hardware',[0,0,-75],False,'AM0701 placeholder body. Mounting face and holes unmeasured.'),
 ('shaft','Motor shaft',shaft,'#a3aab2','hardware',[0,0,-75],False,'Example Ø12 × 32 mm, not measured. Bearing and shaft load limits unknown.'),
 ('rear','01 · Motor adapter',rear,'#b9d2d1','printed',[0,0,-30],True,'Bolts to four example motor holes. No external base. Hole pattern must be replaced with measurements.'),
 ('motor-bolts','Motor screws × 4',motor_bolts,'#8e97a1','fastener',[0,0,0],False,'Metal fasteners. Example M6 clearance; real motor thread and engagement unknown.'),
 ('carrier','02 · Caliper carrier',carrier,'#62a9a5','printed',[70,0,35],True,'Separate bolted carrier. Example mounting coordinates, not a Clarks drawing. Fit-only polymer part.'),
 ('hub','Direct shaft hub',hub,'#d89a58','hardware',[0,0,25],False,'Metal hub required for operation. Bore, key, clamping and axial retention unresolved; no functional hub STL released.'),
 ('rotor','160 mm brake disc',rotor,'#bec6cf','hardware',[0,0,65],False,'Selected Clarks size. Hole circle/thickness/window shape are provisional. Metal reference mesh only.'),
 ('rotor-bolts','Rotor screws × 6',rotor_bolts,'#7a8791','fastener',[0,0,85],False,'Metal screw envelopes; exact rotor interface and engagement unverified.'),
 ('caliper','Bike brake caliper',caliper,'#4a555f','hardware',[95,0,65],False,'Clarks CMD-23 reference envelope only. Not scanned or dimensioned. Cable actuation through side opening.'),
 ('pads','Brake pads',pads,'#514745','hardware',[95,0,65],False,'Friction parts remain metal-backed commercial pads. Shown with clearance, not compressed.'),
 ('caliper-bolts','Carrier screws × 2',caliper_bolts,'#89949e','fastener',[70,0,85],False,'Concept through-bolts pass through rear plate, carrier and caliper tabs. Actual mount orientation pending.'),
 ('shell','03 · Brake chamber',shell,'#d9e5e3','printed',[0,0,140],True,'Ø248 × 40 mm, cable opening Ø12. Non-pressure casing; not a rated fragment guard.'),
 ('lid','04 · Vented lid',lid,'#c5dad6','printed',[0,0,215],True,'Six closure bolts. Slots admit air; no heat-removal or containment rating.'),
 ('closure-bolts','Closure screws × 6',closure_bolts,'#919ca5','fastener',[0,0,255],False,'Illustrative M5 through-bolts. Final length, washers and nuts must match measured stack.'),
 ('nuts','Closure nuts × 6',closure_nuts,'#919ca5','fastener',[0,0,-45],False,'Metal nuts, not printed threads.')
]
out=[];checks=[]
for ident,label,m,col,kind,explode,export,note in items:
    assert m.is_watertight and m.is_volume,(ident,'invalid mesh')
    name=ident+'-FIT-ONLY.stl' if export else None
    if export:m.export(ROOT/name)
    out.append(dict(id=ident,label=label,color=col,kind=kind,explode=explode,file=name,note=note,
                    vertices=np.round(m.vertices,5).tolist(),faces=m.faces.tolist()))
    checks.append(dict(part=ident,watertight=bool(m.is_watertight),positive_volume=bool(m.is_volume),volume_mm3=round(float(m.volume),2),extents_mm=np.round(m.extents,3).tolist(),export=name))
# Check actual mesh intersections for the assembly. Intended contact faces are zero-volume.
clearance_pairs=[('rotor','rear'),('rotor','carrier'),('rotor','caliper'),('rotor','shell'),('rotor','lid'),('hub','rear'),('hub','caliper'),('caliper','shell'),('caliper','lid'),('carrier','shell')]
meshes={i[0]:i[2] for i in items}
intersections=[]
for a,b in clearance_pairs:
    overlap=tm.boolean.intersection([meshes[a],meshes[b]],engine='manifold')
    v=float(overlap.volume) if not overlap.is_empty else 0
    intersections.append(dict(parts=[a,b],overlap_mm3=round(v,6)))
    assert v<.01,(a,b,v)
manifest=dict(date='2026-11-12',status='STATIC FIT PROTOTYPE. Not fitted or released for powered operation.',
              architecture='Motor mounting holes support the enclosure. Rotor hub directly on motor shaft. No base, second shaft or coupling.',
              parameters=P,checks=checks,clearance_checks=intersections,
              scope='Mesh closure and listed interference checks only. Not structural, thermal, balance, bearing-load, rotor-speed or containment validation.',
              open_items=['Motor mounting face, hole coordinates, thread and safe engagement','Shaft diameter, exposed length, key/flat and axial retention','Clarks caliper dimensions and mounting orientation','Rotor thickness and bolt pattern','Motor overhung-load and mounting-load ratings','Brake speed/thermal rating; metal load path and guard for powered tests'],
              excluded='No pressure components; no functional rotor or hub STL. Use regulated motor supply within confirmed rating.')
(ROOT/'assembly.json').write_text(json.dumps(out,separators=(',',':')))
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Embed geometry so the viewer also works with file:// and no network.
template=(ROOT/'viewer.template.html').read_text()
(ROOT/'index.html').write_text(template.replace('__ASSEMBLY__',json.dumps(out,separators=(',',':'))).replace('__PARAMETERS__',json.dumps(P)))
with zipfile.ZipFile(ROOT/'motor-mounted-brake-fit.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(ROOT.iterdir()):
        if f.suffix in ['.stl','.json','.py','.html','.js','.md','.scad','.txt','.png'] and f.name!='assembly.json':z.write(f,f.name)
print(json.dumps({'parts':len(checks),'print_meshes':4,'clearance_pairs':len(intersections),'status':manifest['status']}))
