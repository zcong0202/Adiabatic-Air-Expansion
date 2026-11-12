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

W,H,B,D,L=[P[k] for k in ['case_width','case_height','back_thickness','chamber_depth','lid_thickness']]
def rounded_rect(w,h,r,t,z):
    return union(box([w-2*r,h,t],[0,0,z]),box([w,h-2*r,t],[0,0,z]),*[cyl(r,t,[x,y,z],32) for x in [-w/2+r,w/2-r] for y in [-h/2+r,h/2-r]])
def slot(x,y,d,travel,h,z):
    return union(box([travel,d,h],[x,y,z]),cyl(d/2,h,[x-travel/2,y,z],24),cyl(d/2,h,[x+travel/2,y,z],24))
def web(x0,x1,y,thick,z0,z1):
    # Convex triangular gusset, broad foot on carrier deck.
    points=[[x,y+dy,z] for dy in [-thick/2,thick/2] for x,z in [(x0,z0),(x1,z0),(x1,z1)]]
    return tm.convex.convex_hull(points)
Z = P['rotor_plane']
# Recompute mounting positions from user-estimated OUTER tangents.
hole_d=P['motor_hole_opening_diameter']
upper_y=P['upper_hole_top_to_boss_bottom']-P['motor_boss_diameter']/2-hole_d/2
spacing=P['motor_holes_outer_span']-hole_d
mounts=[[0,upper_y],[0,upper_y-spacing]]
assert np.allclose(mounts,P['motor_mount_xy'])
closure=P['closure_xy']
def holes(points, diameter, height, z): return [cyl(diameter/2,height,[x,y,z],32) for x,y in points]
is_mounts=P['is_adapter_xy']
def profile(height,z,inset=0):
    return tm.convex.convex_hull(joined([cyl(P['case_main_radius']-inset,height,[0,0,z],96),cyl(P['case_pod_radius']-inset,height,[P['case_pod_offset'],0,z],64)]).vertices)
# One integrated cup. Circular gearcase with a smooth caliper bulge.
# Rear mounting face stays flat. All load ribs and brake lands are internal.
outer=profile(B+D-2,(B+D-2)/2)
edge=tm.convex.convex_hull(joined([profile(.1,B+D-1.95),profile(.1,B+D-.05,2)]).vertices)
housing=cut(union(outer,edge),profile(D+4,B+D/2+2,8))
# Central rear reinforcement, lands and a saddle merged into the cup.
ribs=[]
for angle in [-65,-25,25,65,130,230]:
    q=box([50,10,6],[50,0,B+3]);q.apply_transform(tm.transformations.rotation_matrix(math.radians(angle),[0,0,1]));ribs.append(q)
saddle=union(*[box([38,16,12],[103,y,16]) for y in [-25.5,25.5]],
             *[web(112,128,y,8,10,35) for y in [-25.5,25.5]])
housing=union(housing,ring(27,20,6,B+3),*ribs,saddle,
              *[cyl(12,6,[x,y,B+3],32) for x,y in mounts],
              *[cyl(9,D,[x,y,B+D/2],32) for x,y in closure])
# Nut pockets open from the back. Standard nut geometry is reference only.
housing=cut(housing,cyl(20,40,[0,0,10]),
            *holes(mounts,P['motor_mount_clearance_diameter'],30,10),
            *holes(closure,10.6,D+1,B+D/2+.5),
            *holes(closure,6.6,B+2,B/2),
            *[cyl(6.3,6,[x,y,2],6) for x,y in closure],
            *[slot(x,y,6.6,P['is_slot_travel'],40,12) for x,y in is_mounts])
# Cable access opens in the caliper bulge, along motor x axis.
cable=cyl(7,32,[0,0,0]);cable.apply_transform(tm.transformations.rotation_matrix(math.pi/2,[0,1,0]));cable.apply_translation([134,0,35])
housing=cut(housing,cable)
# Lid follows the smooth outline; recessed screw heads, circular face detail.
base=profile(L-2,B+D+(L-2)/2)
bevel=tm.convex.convex_hull(joined([profile(.1,B+D+L-1.95),profile(.1,B+D+L-.05,2)]).vertices)
lid=union(base,bevel)
lid=cut(lid,*holes(closure,6.6,L+4,B+D+L/2),
        *holes(closure,12.6,7,B+D+L-2),
        cyl(68,2,[0,0,B+D+L],96),
        *[slot(108,y,3,16,L+4,B+D+L/2) for y in [-12,-6,0,6,12]])
# Commercial adapter and caliper remain explicitly schematic hardware.
adapter=cut(box([22,68,4],[101,0,28]),*holes(is_mounts,6.6,8,28))
spacers=joined([cut(cyl(6,4,[x,y,24],32),cyl(3.3,6,[x,y,24],24)) for x,y in is_mounts])
closure_sleeves=joined([cut(cyl(5,D,[x,y,B+D/2],32),cyl(3.3,D+2,[x,y,B+D/2],24)) for x,y in closure])
# Main body thickness follows the user estimate; rear accessories are not modeled.
# Body shape remains a schematic envelope, not a dimensioned motor casting.
boss_h=P['motor_boss_projection']
body_length=P['motor_body_length']
motor = union(cyl(P['motor_body_diameter']/2,body_length,[0,0,-body_length/2]),cyl(P['motor_boss_diameter']/2,boss_h,[0,0,boss_h/2]))
# Shallow opening references. Actual bore depth/thread remains unknown.
motor = cut(motor,*holes(mounts,hole_d,9,-3.5))
shaft = cyl(P['shaft_diameter']/2,P['shaft_exposed_length'],[0,0,boss_h+P['shaft_exposed_length']/2])
hub = union(ring(P['hub_outer_diameter']/2,P['shaft_diameter']/2+.2,P['hub_length'],P['hub_back_z']+P['hub_length']/2),ring(29,P['shaft_diameter']/2+.2,4,Z-2.9))
rotor_pattern = [[P['rotor_bolt_pitch_diameter']/2*math.cos(a*math.pi/3),P['rotor_bolt_pitch_diameter']/2*math.sin(a*math.pi/3)] for a in range(6)]
hub = cut(hub,*holes(rotor_pattern,P['rotor_bolt_clearance_diameter'],6,Z-2.9))
rotor = ring(P['rotor_diameter']/2,18.5,P['rotor_thickness'],Z)
windows = []
for i in range(6):
    a = i*math.pi/3
    m = box([30,23,6],[50,0,Z]);m.apply_transform(tm.transformations.rotation_matrix(a,[0,0,1]));windows.append(m)
rotor = cut(rotor,*windows,*holes(rotor_pattern,P['rotor_bolt_clearance_diameter'],6,Z))
caliper=union(box([12,34,22],[95,0,Z]),box([24,34,6],[78,0,Z-8]),box([24,34,6],[78,0,Z+8]))
pads=joined([box([10,22,3],[74,0,Z-3]),box([10,22,3],[74,0,Z+3])])
motor_bolts=joined([joined([cyl(3,25,[x,y,4.5],24),cyl(6,4,[x,y,19],24)]) for x,y in mounts])
closure_bolts=joined([joined([cyl(3,52.5,[x,y,27.25],24),cyl(5.5,4,[x,y,55.5],6)]) for x,y in closure])
closure_nuts=joined([cut(cyl(5.7,5,[x,y,2.5],6),cyl(3.1,7,[x,y,2.5],24)) for x,y in closure])
caliper_bolts=joined([joined([cyl(3,36,[x,y,12],24),cyl(5.5,4,[x,y,32],6)]) for x,y in is_mounts])
washers=joined([cut(cyl(6,1,[x,y,53],32),cyl(3.3,3,[x,y,53],24)) for x,y in closure]+[cut(cyl(12,1,[x,y,16.5],32),cyl(3.75,3,[x,y,16.5],24)) for x,y in mounts])
rotor_bolts = joined([joined([cyl(2.4,7,[x,y,Z-1],24),cyl(4.3,2,[x,y,Z+2],24)]) for x,y in rotor_pattern])

items = [
 ('motor','Motor envelope',motor,'#6b7782','hardware',[0,0,-75],False,'User-estimated body Ø108 × 48 mm; boss Ø35 × 15; shaft Ø12 × 25. Front stack88 mm. Rear accessories not modeled. Casting outline, threads and fit tolerances unverified.'),
 ('shaft','Motor shaft',shaft,'#a3aab2','hardware',[0,0,-75],False,'User estimate Ø12 × 25 mm exposed from raised boss. Shaft spans z15–40 mm. Retention and bearing limits unknown.'),
 ('housing','01 · Integrated brake housing',housing,'#535e65','printed',[0,0,-35],True,'One-piece cup with internal caliper lands and gussets. Smooth circular case with a caliper bulge. 10 mm rear, 8 mm walls. Stock-adapter alignment remains provisional.'),
 ('motor-bolts','Motor screws × 2',motor_bolts,'#8e97a1','fastener',[0,0,0],False,'Ø6 reference screws only; actual motor thread and engagement remain unknown.'),
 ('adapter','Stock IS adapter · envelope',adapter,'#7d858b','hardware',[55,0,45],False,'Reuse the correct Clarks metal IS adapter. IS51 slots are internal to the case. Actual adapter shape, PM hardware and offset remain unverified.'),
 ('spacers','Adapter spacers · reference',spacers,'#b2b8be','hardware',[55,0,32],False,'4 mm metal spacer references; select after alignment. Not thermal insulation.'),
 ('sleeves','Closure sleeves × 8',closure_sleeves,'#9aa6ae','hardware',[0,0,45],False,'38 mm metal compression sleeves, OD10 / ID6.6 references. Not a qualified metal torque skeleton.'),
 ('washers','Metal washers',washers,'#aeb6bc','fastener',[0,0,110],False,'Ø12 at recessed closure heads; Ø24 at motor lands. Reference hardware.'),
 ('hub','Direct shaft hub',hub,'#d89a58','hardware',[0,0,25],False,'Metal hub required for operation. Bore, key, clamping and axial retention unresolved; no functional hub STL released.'),
 ('rotor','160 mm brake disc',rotor,'#bec6cf','hardware',[0,0,65],False,'Selected Clarks size. Hole circle/thickness/window shape are provisional. Metal reference mesh only.'),
 ('rotor-bolts','Rotor screws × 6',rotor_bolts,'#7a8791','fastener',[0,0,85],False,'Metal screw envelopes; exact rotor interface and engagement unverified.'),
 ('caliper','Bike brake caliper',caliper,'#4a555f','hardware',[95,0,65],False,'Clarks CMD-23 reference envelope only. Not scanned or dimensioned. Cable actuation through side opening.'),
 ('pads','Brake pads',pads,'#514745','hardware',[95,0,65],False,'Friction parts remain metal-backed commercial pads. Shown with clearance, not compressed.'),
 ('caliper-bolts','IS adapter screws × 2',caliper_bolts,'#89949e','fastener',[70,0,85],False,'M6 reference screws through IS adapter and slotted saddle. Actual stock adapter, washer stack and clearances pending.'),
 ('lid','02 · Recessed face cover',lid,'#a5afb3','printed',[0,0,140],True,'Matching chamfered lid, recessed screw heads, shallow circular face and small vents over the caliper. Cover is not a rated fragment guard.'),
 ('closure-bolts','Closure screws × 8',closure_bolts,'#919ca5','fastener',[0,0,180],False,'Illustrative M6 through-bolts. Final length, washers and nuts must match measured stack.'),
 ('nuts','Closure nuts × 8',closure_nuts,'#919ca5','fastener',[0,0,-55],False,'Metal nuts, not printed threads.')
]
out=[];checks=[]
for ident,label,m,col,kind,explode,export,note in items:
    assert m.is_watertight and m.is_volume,(ident,'invalid mesh')
    name=ident+'-FIT-ONLY.stl' if export else None
    if export:
        printable=m.copy();printable.apply_translation([0,0,-m.bounds[0,2]]);printable.export(ROOT/name)
        assert printable.extents[0]<340 and printable.extents[1]<320 and printable.extents[2]<340
        assert len(printable.split())==1,(ident,'disconnected print')
    out.append(dict(id=ident,label=label,color=col,kind=kind,explode=explode,file=name,note=note,
                    vertices=np.round(m.vertices,5).tolist(),faces=m.faces.tolist()))
    checks.append(dict(part=ident,watertight=bool(m.is_watertight),positive_volume=bool(m.is_volume),volume_mm3=round(float(m.volume),2),extents_mm=np.round(m.extents,3).tolist(),export=name,connected_print_solid=(len(m.split())==1 if export else None),fits_H2S_bed=(bool(m.extents[0]<340 and m.extents[1]<320 and m.extents[2]<340) if export else None)))
# Check actual mesh intersections for the assembly. Intended contact faces are zero-volume.
clearance_pairs=[('rotor','housing'),('rotor','caliper'),('rotor','lid'),('hub','housing'),('hub','caliper'),('caliper','housing'),('caliper','lid'),('motor','housing'),('motor','hub'),('motor','rotor'),('shaft','lid'),('adapter','rotor'),('adapter','housing'),('sleeves','rotor'),('housing','lid'),('caliper-bolts','housing'),('motor-bolts','rotor'),('closure-bolts','housing'),('closure-bolts','lid'),('nuts','housing'),('washers','lid')]
meshes={i[0]:i[2] for i in items}
intersections=[]
for a,b in clearance_pairs:
    overlap=tm.boolean.intersection([meshes[a],meshes[b]],engine='manifold')
    v=float(overlap.volume) if not overlap.is_empty else 0
    intersections.append(dict(parts=[a,b],overlap_mm3=round(v,6)))
    assert v<.01,(a,b,v)
assert abs((mounts[0][1]+hole_d/2)-(mounts[1][1]-hole_d/2)-P['motor_holes_outer_span'])<1e-6
assert abs(mounts[0][1]+hole_d/2+P['motor_boss_diameter']/2-P['upper_hole_top_to_boss_bottom'])<1e-6
assert P['hub_back_z']>=boss_h
assert P['hub_back_z']+P['hub_length']<=boss_h+P['shaft_exposed_length']
assert abs(joined([motor,shaft]).extents[2]-P['motor_overall_length'])<1e-6
manifest=dict(load_screen='load-screen.json',brake_interface_audit='brake-interface-audit.json',carrier_export_withheld=True,revision='R05',mount_derivation=P['mount_derivation'],dimension_audit='dimension-audit.json',date='2026-11-12',status='STATIC FIT PROTOTYPE. Not fitted or released for powered operation.',
              architecture='Two printed pieces: integrated brake cup and matching cover. Internal IS adapter support is part of the cup. Motor-mounted; no separate carrier, base or coupling.',
              parameters=P,checks=checks,clearance_checks=intersections,
              scope='Mesh closure and listed interference checks only. Not structural, thermal, balance, bearing-load, rotor-speed or containment validation.',
              open_items=['Verify user-estimated dimensions/tolerances; determine thread and safe engagement','Verify shaft fit, key/flat/pin and axial retention','Clarks caliper dimensions and mounting orientation','Rotor thickness and bolt pattern','Motor overhung-load and mounting-load ratings','Brake speed/thermal rating; metal load path and guard for powered tests'],
              excluded='No pressure components; no functional rotor or hub STL. Use regulated motor supply within confirmed rating.')
(ROOT/'assembly.json').write_text(json.dumps(out,separators=(',',':')))
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Embed geometry so the viewer also works with file:// and no network.
template=(ROOT/'viewer.template.html').read_text()
(ROOT/'index.html').write_text(template.replace('__ASSEMBLY__',json.dumps(out,separators=(',',':'))).replace('__PARAMETERS__',json.dumps(P)))
with zipfile.ZipFile(ROOT/'motor-mounted-brake-fit.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(ROOT.rglob('*')):
        if f.is_file() and (f.suffix!='.stl' or f.name in [c['export'] for c in checks if c['export']]) and f.suffix in ['.stl','.json','.py','.html','.js','.md','.scad','.txt','.png','.jpg','.pdf','.svg'] and f.name!='assembly.json':z.write(f,f.relative_to(ROOT))
print(json.dumps({'parts':len(checks),'print_meshes':sum(1 for c in checks if c['export']),'clearance_pairs':len(intersections),'status':manifest['status']}))
