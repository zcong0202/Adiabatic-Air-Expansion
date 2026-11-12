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
anchors=P['carrier_anchor_xy'];is_mounts=P['is_adapter_xy']
# Broad base with a central stiffener ring and six radial ribs. Flat print underside.
ribs=[]
for angle in [-65,-25,25,65,130,230]:
    a=math.radians(angle)
    q=box([50,10,6],[50,0,B+3]);q.apply_transform(tm.transformations.rotation_matrix(a,[0,0,1]));ribs.append(q)
rear=union(rounded_rect(W,H,20,B,B/2),ring(27,20,6,B+3),*ribs,
           *[cyl(12,6,[x,y,B+3],32) for x,y in mounts])
rear=cut(rear,cyl(20,40,[0,0,10]),*holes(mounts,P['motor_mount_clearance_diameter'],30,10),
         *holes(closure,6.6,30,10),*holes(anchors,6.6,30,10),*[slot(x,y,6.6,P['is_slot_travel'],30,10) for x,y in is_mounts])
# Shell: thick corners and eight metal-sleeved closure stations.
shell=cut(rounded_rect(W,H,20,D,B+D/2),rounded_rect(W-12,H-12,14,D+2,B+D/2))
shell=union(shell,*[cyl(17 if abs(x)==112 else 10,D,[x,y,B+D/2],32) for x,y in closure])
shell=cut(shell,*holes(closure,10.6,D+2,B+D/2))
cable=cyl(8,30,[0,0,0]);cable.apply_transform(tm.transformations.rotation_matrix(math.pi/2,[0,1,0]));cable.apply_translation([W/2-3,0,Z+10])
shell=cut(shell,cable)
# Raised cover ribs. Vent slots are not a containment claim.
lid=union(rounded_rect(W,H,20,L,B+D+L/2),
          *[box([W-40,8,4],[0,y,B+D+L+2]) for y in [-72,72]],
          *[box([8,H-40,4],[x,0,B+D+L+2]) for x in [-72,72]])
lid=cut(lid,*holes(closure,6.6,20,B+D+6),*[box([8,70,20],[x,0,B+D+6]) for x in [-48,-24,0,24,48]])
# Wide saddle, four base bolts, large foot and integral gussets; not thin tabs.
# IS holes belong to the stock metal adapter, not the caliper's PM interface.
carrier=union(box([44,108,8],[102,0,14]),
              *[box([44,16,8],[102,y,18]) for y in [-25.5,25.5]],
              *[web(82,122,y,8,14,34) for y in [-40,40]],
              box([8,80,20],[120,0,24]))
carrier=cut(carrier,box([32,38,12],[96,0,20]),*holes(anchors,6.6,45,22),*holes(anchors,20,30,33),
            *[slot(x,y,6.6,P['is_slot_travel'],35,20) for x,y in is_mounts])
# Clarks adapter is a schematic envelope. Radial slots +/-4 mm do not guarantee alignment.
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
closure_bolts=joined([joined([cyl(3,B+D+L+10,[x,y,(B+D+L)/2],24),cyl(5.5,4,[x,y,B+D+L+3],6)]) for x,y in closure])
closure_nuts=joined([cut(cyl(5.7,5,[x,y,-3.5],6),cyl(3.1,7,[x,y,-3.5],24)) for x,y in closure])
caliper_bolts=joined([joined([cyl(3,36,[x,y,12],24),cyl(5.5,4,[x,y,32],6)]) for x,y in is_mounts])
anchor_bolts=joined([joined([cyl(3,24,[x,y,9],24),cyl(5.5,4,[x,y,21],6)]) for x,y in anchors])
# Wide metal washers distribute bearing loads; dimensions remain selection references.
washer_points=[(x,y,B+D+L+.5) for x,y in closure]+[(x,y,-.5) for x,y in closure+anchors]+[(x,y,18.5) for x,y in anchors]
washers=joined([cut(cyl(9,1,[x,y,z],32),cyl(3.3,3,[x,y,z],24)) for x,y,z in washer_points]+[cut(cyl(12,1,[x,y,16.5],32),cyl(3.75,3,[x,y,16.5],24)) for x,y in mounts])
rotor_bolts = joined([joined([cyl(2.4,7,[x,y,Z-1],24),cyl(4.3,2,[x,y,Z+2],24)]) for x,y in rotor_pattern])

items = [
 ('motor','Motor envelope',motor,'#6b7782','hardware',[0,0,-75],False,'User-estimated body Ø108 × 48 mm; boss Ø35 × 15; shaft Ø12 × 25. Front stack88 mm. Rear accessories not modeled. Casting outline, threads and fit tolerances unverified.'),
 ('shaft','Motor shaft',shaft,'#a3aab2','hardware',[0,0,-75],False,'User estimate Ø12 × 25 mm exposed from raised boss. Shaft spans z15–40 mm. Retention and bearing limits unknown.'),
 ('rear','01 · Motor adapter',rear,'#4c5a63','printed',[0,0,-30],True,'Two aligned holes at x0, y+44/-39 mm, derived from user outer-tangent estimates. Plate Ø7.5 clearance is provisional. No external base.'),
 ('motor-bolts','Motor screws × 2',motor_bolts,'#8e97a1','fastener',[0,0,0],False,'Two Ø6 screw envelopes only. An estimated Ø7 opening does not identify the thread. Actual screw size and engagement unknown.'),
 ('carrier','02 · Ribbed caliper saddle',carrier,'#c28b42','printed',[70,0,35],True,'44 × 108 mm deck; four M6 reference anchors; integral 8 mm gussets. IS51 slots have ±4 mm radial travel. Axial offset and fit remain provisional.'),
 ('adapter','Stock IS adapter · envelope',adapter,'#7d858b','hardware',[90,0,50],False,'Reuse the correct Clarks metal IS adapter and stock PM bolt/washer stack. This envelope is not its measured shape. IS51 mm interface; no invented PM geometry.'),
 ('spacers','Adapter spacers · reference',spacers,'#b2b8be','hardware',[70,0,45],False,'4 mm metal spacers shown only for layout. Select length after rotor alignment. Not thermal insulation or a qualified heat break.'),
 ('anchor-bolts','Saddle anchors × 4',anchor_bolts,'#8e97a1','fastener',[65,0,15],False,'M6 reference through-bolts and wide washers. Verify lengths, nuts and clearance with real hardware. No printed threads.'),
 ('sleeves','Closure sleeves × 8',closure_sleeves,'#9aa6ae','hardware',[0,0,100],False,'54 mm metal sleeve references, OD10 / ID6.6. Limit shell compression under closure preload; not a metal brake-torque skeleton.'),
 ('washers','Load-spreading washers',washers,'#aeb6bc','fastener',[0,0,5],False,'Illustrative Ø18 mm washers; Ø24 at motor lands. Select fasteners to match measured stack.'),
 ('hub','Direct shaft hub',hub,'#d89a58','hardware',[0,0,25],False,'Metal hub required for operation. Bore, key, clamping and axial retention unresolved; no functional hub STL released.'),
 ('rotor','160 mm brake disc',rotor,'#bec6cf','hardware',[0,0,65],False,'Selected Clarks size. Hole circle/thickness/window shape are provisional. Metal reference mesh only.'),
 ('rotor-bolts','Rotor screws × 6',rotor_bolts,'#7a8791','fastener',[0,0,85],False,'Metal screw envelopes; exact rotor interface and engagement unverified.'),
 ('caliper','Bike brake caliper',caliper,'#4a555f','hardware',[95,0,65],False,'Clarks CMD-23 reference envelope only. Not scanned or dimensioned. Cable actuation through side opening.'),
 ('pads','Brake pads',pads,'#514745','hardware',[95,0,65],False,'Friction parts remain metal-backed commercial pads. Shown with clearance, not compressed.'),
 ('caliper-bolts','IS adapter screws × 2',caliper_bolts,'#89949e','fastener',[70,0,85],False,'M6 reference screws through IS adapter and slotted saddle. Actual stock adapter, washer stack and clearances pending.'),
 ('shell','03 · Brake chamber',shell,'#424e57','printed',[0,0,140],True,'264 × 244 × 54 mm ring, 6 mm walls and eight reinforced sleeve stations. Cable access Ø16. Not a pressure vessel or rated fragment guard.'),
 ('lid','04 · Vented lid',lid,'#56646d','printed',[0,0,215],True,'6 mm plate with 4 mm outer ribs; eight closure bolts. Slots are unqualified vents, not a containment guard.'),
 ('closure-bolts','Closure screws × 8',closure_bolts,'#919ca5','fastener',[0,0,255],False,'Illustrative M6 through-bolts. Final length, washers and nuts must match measured stack.'),
 ('nuts','Closure nuts × 8',closure_nuts,'#919ca5','fastener',[0,0,-45],False,'Metal nuts, not printed threads.')
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
clearance_pairs=[('rotor','rear'),('rotor','carrier'),('rotor','caliper'),('rotor','shell'),('rotor','lid'),('hub','rear'),('hub','caliper'),('caliper','shell'),('caliper','lid'),('carrier','shell'),('motor','rear'),('motor','hub'),('motor','rotor'),('shaft','lid'),('carrier','caliper'),('carrier','rear'),('adapter','rotor'),('adapter','shell'),('sleeves','rotor'),('rear','shell'),('rear','lid'),('anchor-bolts','carrier'),('caliper-bolts','carrier'),('caliper-bolts','rear'),('motor-bolts','rotor')]
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
manifest=dict(load_screen='load-screen.json',brake_interface_audit='brake-interface-audit.json',carrier_export_withheld=False,revision='R04',mount_derivation=P['mount_derivation'],dimension_audit='dimension-audit.json',date='2026-11-12',status='STATIC FIT PROTOTYPE. Not fitted or released for powered operation.',
              architecture='Motor mounting holes support the enclosure. Rotor hub directly on motor shaft. No base, second shaft or coupling.',
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
        if f.is_file() and f.suffix in ['.stl','.json','.py','.html','.js','.md','.scad','.txt','.png','.jpg','.pdf','.svg'] and f.name!='assembly.json':z.write(f,f.relative_to(ROOT))
print(json.dumps({'parts':len(checks),'print_meshes':sum(1 for c in checks if c['export']),'clearance_pairs':len(intersections),'status':manifest['status']}))
