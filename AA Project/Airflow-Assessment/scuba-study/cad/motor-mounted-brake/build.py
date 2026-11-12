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
# R07: rear case floor sits behind the motor face, outside a motor recess.
# A separate flat adapter plate keeps the motor face and rotor at their original datums.
BACK=P['rear_case_z'];FLOOR=BACK+B;FRONT=B+D;TOP=FRONT+L
plate_points=P['plate_bolt_xy']
outer=profile(FRONT-BACK-2,(FRONT+BACK-2)/2)
edge=tm.convex.convex_hull(joined([profile(.1,FRONT-1.95),profile(.1,FRONT-.05,2)]).vertices)
housing=cut(union(outer,edge),profile(FRONT-FLOOR+4,(FRONT+FLOOR)/2+2,P['shell_wall']),
            cyl(P['motor_recess_radius'],B+2,[0,0,BACK+B/2]))
# Two short lands place the assumed IS adapter at z=-1. No free-standing long bracket.
lands=[cyl(12,P['adapter_mount_plane']-FLOOR,[x,y,(P['adapter_mount_plane']+FLOOR)/2],48) for x,y in is_mounts]
# Motor adapter supports surround the central rear recess; closure pillars stay clear of disc.
plate_posts=[cyl(10,-FLOOR,[x,y,FLOOR/2],40) for x,y in plate_points]
housing=union(housing,*lands,*plate_posts,*[cyl(9,FRONT-FLOOR,[x,y,(FRONT+FLOOR)/2],40) for x,y in closure])
housing=cut(housing,
            *holes(closure,10.6,FRONT-FLOOR+1,(FRONT+FLOOR)/2+.5),
            *holes(closure,6.6,B+2,BACK+B/2),
            *[cyl(6.3,6,[x,y,BACK+2],6) for x,y in closure],
            *holes(plate_points,8.5,-FLOOR+1,FLOOR/2+.5),
            *holes(plate_points,5.6,B+2,BACK+B/2),
            *[cyl(5.2,5,[x,y,BACK+1.5],6) for x,y in plate_points],
            *[slot(x,y,6.6,P['is_slot_travel'],35,-5) for x,y in is_mounts],
            *[slot(x,y,11.6,P['is_slot_travel'],8,BACK+3) for x,y in is_mounts])
# Cable entry follows the estimated barrel direction. Rear pad adjustment has tool access.
cable=cyl(8,150,[0,0,0]);cable.apply_transform(tm.transformations.rotation_matrix(math.pi/2,[1,0,0]));cable.apply_translation([104,-85,49])
housing=cut(housing,cable,cyl(7,40,[76,0,-20]))
# D-shaped motor plate: right-hand relief clears the estimated rear pad adjuster.
motor_plate=cut(cyl(P['motor_plate_radius'],B,[0,0,B/2]),box([100,200,40],[110,0,5]),
                cyl(20,B+2,[0,0,B/2]),*holes(mounts,P['motor_mount_clearance_diameter'],B+2,B/2),
                *holes(plate_points,5.6,B+2,B/2),*holes(plate_points,10.6,6,9))
# Matching cover. Its inner face is z75: 12 mm beyond the nominal control envelope.
lid=union(profile(L-2,FRONT+(L-2)/2),tm.convex.convex_hull(joined([profile(.1,TOP-1.95),profile(.1,TOP-.05,2)]).vertices))
lid=cut(lid,*holes(closure,6.6,L+4,FRONT+L/2),*holes(closure,12.6,7,TOP-2),cyl(68,2,[0,0,TOP],96),
        *[slot(126,y,3,20,L+4,FRONT+L/2) for y in [-12,-6,0,6,12]])
closure_sleeves=joined([cut(cyl(5,FRONT-FLOOR,[x,y,(FRONT+FLOOR)/2],32),cyl(3.3,FRONT-FLOOR+2,[x,y,(FRONT+FLOOR)/2],24)) for x,y in closure])
plate_sleeves=joined([cut(cyl(4,-FLOOR,[x,y,FLOOR/2],32),cyl(2.8,-FLOOR+2,[x,y,FLOOR/2],24)) for x,y in plate_points])
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
motor_bolts=joined([joined([cyl(3,18,[x,y,2],24),cyl(6,4,[x,y,13],24)]) for x,y in mounts])
closure_bolts=joined([joined([cyl(3,TOP-4.5-(BACK+1),[x,y,((TOP-4.5)+(BACK+1))/2],24),cyl(5.5,4,[x,y,TOP-2.5],6)]) for x,y in closure])
closure_nuts=joined([cut(cyl(5.7,5,[x,y,BACK+2.5],6),cyl(3.1,7,[x,y,BACK+2.5],24)) for x,y in closure])
plate_bolts=joined([joined([cyl(2.5,25,[x,y,-5.5],24),cyl(4.5,3,[x,y,8.5],6)]) for x,y in plate_points])
plate_nuts=joined([cut(cyl(4.7,4,[x,y,BACK+2],6),cyl(2.6,6,[x,y,BACK+2],24)) for x,y in plate_points])
# IS M6x18 reference screws insert from the rear into the stock metal adapter.
is_bolts=joined([joined([cyl(3,18,[x,y,-2],24),cyl(5,6,[x,y,-14],24)]) for x,y in is_mounts])
washers=joined([cut(cyl(6,1,[x,y,TOP-5],32),cyl(3.3,3,[x,y,TOP-5],24)) for x,y in closure]+[cut(cyl(12,1,[x,y,10.5],32),cyl(3.75,3,[x,y,10.5],24)) for x,y in mounts]+[cut(cyl(5,1,[x,y,6.5],32),cyl(2.8,3,[x,y,6.5],24)) for x,y in plate_points])
rotor_bolts = joined([joined([cyl(2.4,7,[x,y,Z-1],24),cyl(4.3,2,[x,y,Z+2],24)]) for x,y in rotor_pattern])

# Replace the old box placeholder with the source-based estimate.
from brake_estimate import make_brake
brake_parts,arm_sweep,brake_physical=make_brake(Z)
caliper=brake_parts['caliper'];adapter=brake_parts['adapter'];pads=brake_parts['pads']
# Brake estimate is unchanged; the new housing is checked against it and its assumed arm sweep.

items = [
 ('motor','Motor envelope',motor,'#6b7782','hardware',[0,0,-75],False,'User-estimated body Ø108 × 48 mm; boss Ø35 × 15; shaft Ø12 × 25. Front stack88 mm. Rear accessories not modeled. Casting outline, threads and fit tolerances unverified.'),
 ('shaft','Motor shaft',shaft,'#a3aab2','hardware',[0,0,-75],False,'User estimate Ø12 × 25 mm exposed from raised boss. Shaft spans z15–40 mm. Retention and bearing limits unknown.'),
 ('housing','01 · Integrated brake housing',housing,'#535e65','printed',[0,0,-35],True,'R07 deeper cup, rear brake pocket, internal IS lands, cable entry and rear adjustment access. Nominal image model and3 mm local allowances checked. Fit remains estimate-based.'),
 ('motor-plate','02 · Motor adapter plate',motor_plate,'#6c7b82','printed',[0,0,-65],True,'Flat D-shaped plate, two estimated motor holes. Five M5 reference bolts attach the case. Right-hand relief clears rear brake controls.'),
 ('plate-bolts','Adapter screws × 5',plate_bolts,'#929fa8','fastener',[0,0,-85],False,'M5 reference screws, recessed heads. Verify actual lengths and motor mounting loads.'),
 ('plate-nuts','Adapter nuts × 5',plate_nuts,'#929fa8','fastener',[0,0,-100],False,'Metal nut references recessed in case rear.'),
 ('plate-sleeves','Adapter sleeves × 5',plate_sleeves,'#a2afb7','hardware',[0,0,-45],False,'8 mm metal sleeve references; OD8/ID5.6. Printed posts are not qualified for powered duty.'),
 ('is-bolts','IS mount screws × 2',is_bolts,'#929fa8','fastener',[30,0,-70],False,'M6x18 reference, inserted from rear. Estimated adapter thread/engagement must be verified; no printed threads.'),
 ('motor-bolts','Motor screws × 2',motor_bolts,'#8e97a1','fastener',[0,0,0],False,'Ø6 reference screws only; actual motor thread and engagement remain unknown.'),
 ('adapter','Stock IS adapter · envelope',adapter,'#7d858b','hardware',[55,0,45],False,'Estimated stepped IS-to-PM bracket. IS51 axes along shaft; PM74.17 axes radial. Casting offsets and pose inferred, not certified. R07 lands follow this assumed pose; actual bracket offset still needs confirmation.'),
 ('sleeves','Closure sleeves × 8',closure_sleeves,'#9aa6ae','hardware',[0,0,45],False,'83 mm metal compression sleeves, OD10 / ID6.6 references. Not a qualified metal torque skeleton.'),
 ('washers','Metal washers',washers,'#aeb6bc','fastener',[0,0,110],False,'Ø12 at recessed closure heads; Ø24 at motor lands. Reference hardware.'),
 ('hub','Direct shaft hub',hub,'#d89a58','hardware',[0,0,25],False,'Metal hub required for operation. Bore, key, clamping and axial retention unresolved; no functional hub STL released.'),
 ('rotor','160 mm brake disc',rotor,'#bec6cf','hardware',[0,0,65],False,'Selected Clarks size. Hole circle/thickness/window shape are provisional. Metal reference mesh only.'),
 ('rotor-bolts','Rotor screws × 6',rotor_bolts,'#7a8791','fastener',[0,0,85],False,'Metal screw envelopes; exact rotor interface and engagement unverified.'),
 ('caliper','Bike brake caliper',caliper,'#4a555f','hardware',[95,0,65],False,'CMD-23 image-based body estimate. Overall body and controls about55 ×110 ×60 mm (radial/tangential/axial). Not measured manufacturer CAD; see source and uncertainty report.'),
 ('pads','Brake pads',pads,'#514745','hardware',[95,0,65],False,'Friction parts remain metal-backed commercial pads. Shown with clearance, not compressed.'),
 ('lid','03 · Recessed face cover',lid,'#a5afb3','printed',[0,0,140],True,'R07 cover; inner face z75 clears the estimated controls. Removable for servicing. Not a rated fragment guard.'),
 ('closure-bolts','Closure screws × 8',closure_bolts,'#919ca5','fastener',[0,0,180],False,'Illustrative M6 through-bolts. Final length, washers and nuts must match measured stack.'),
 ('nuts','Closure nuts × 8',closure_nuts,'#919ca5','fastener',[0,0,-55],False,'Metal nuts, not printed threads.')
]
for ident,label,color,note in [
 ('brake-arm','Cable actuation arm','#354047','Shape estimated from photos. Travel unmeasured; separate sweep assumes 0–30 degrees.'),
 ('barrel-adjuster','Cable barrel adjuster','#59636b','Estimated30 mm long, Ø12 reference. Thread and cable bend radius unverified.'),
 ('rear-adjuster','Rear pad adjuster','#59636b','Estimated projection behind the rotor; needs tool access.'),
 ('brake-pivot','Arm pivot screw','#b94843','Illustrative pivot cap, not a functional fastener design.'),
 ('pm-bolts','PM fastener references','#adb5bb','35/40 mm lengths shown by Clarks fitting sheet. Actual stack and installation still unverified.'),
 ('brake-wire','Brake inner cable','#8e979b','Illustrative cable line. Routing and actuation clearance not validated.'),
 ('cable-lead','Cable entry allowance','#343e45','45 mm straight lead reference only. Not a specified bend radius.')]:
 items.append((ident,label,brake_parts[ident],color,'hardware',[55,0,65],False,note))

arm_offsets=np.array([[x,y,z] for x in [-3,3] for y in [-3,3] for z in [-3,3]])
arm_envelope=tm.convex.convex_hull(np.concatenate([arm_sweep.vertices+v for v in arm_offsets]))
items.append(('arm-envelope','Assumed arm clearance',arm_envelope,'#d5a54b','clearance',[55,0,65],False,'0–30 degree assumed arm travel, with3 mm box allowance. Not a measured travel limit or complete cable-motion model.'))
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
case_parts=['housing','motor-plate','lid']
clearance_pairs=[(a,b) for a in ['rotor','hub','motor','shaft','caliper','adapter','pads','brake-arm','barrel-adjuster','rear-adjuster','brake-pivot','pm-bolts','brake-wire','cable-lead'] for b in case_parts]
clearance_pairs += [('housing','motor-plate'),('housing','lid'),('motor-plate','lid'),('motor','hub'),('motor','rotor'),('hub','caliper'),('rotor','caliper'),('rotor','sleeves'),('motor-bolts','rotor')]
clearance_pairs += [(a,b) for a in ['closure-bolts','nuts','washers','plate-bolts','plate-nuts','plate-sleeves','is-bolts'] for b in case_parts]
meshes={i[0]:i[2] for i in items}
intersections=[]
for a,b in clearance_pairs:
    overlap=tm.boolean.intersection([meshes[a],meshes[b]],engine='manifold')
    v=float(overlap.volume) if not overlap.is_empty else 0
    intersections.append(dict(parts=[a,b],overlap_mm3=round(v,6)))
    assert np.isfinite(v) and v<.01,(a,b,v)
# Check assumed full arm sweep and conservative convex3 mm envelopes around controls/body.
allowance_checks=[]
for name,shape,margin in [('arm-sweep',arm_sweep,3)]+[(key,brake_parts[key],3) for key in ['caliper','barrel-adjuster','rear-adjuster','brake-pivot']]:
    offsets=np.array([[x,y,z] for x in [-margin,margin] for y in [-margin,margin] for z in [-margin,margin]])
    keepout=tm.convex.convex_hull(np.concatenate([shape.vertices+v for v in offsets]))
    for target in case_parts:
        overlap=tm.boolean.intersection([keepout,meshes[target]],engine='manifold')
        volume=0 if overlap.is_empty else float(overlap.volume)
        allowance_checks.append(dict(envelope=name,margin_mm=margin,target=target,overlap_mm3=round(volume,6)))
        assert np.isfinite(volume) and volume<.01,(name,target,volume)
# Straight rear tool access; it terminates at the rear pad adjuster, not a claimed wrench size.
service=cyl(6,44,[76,0,-18])
for target in case_parts:
    overlap=tm.boolean.intersection([service,meshes[target]],engine='manifold')
    volume=0 if overlap.is_empty else float(overlap.volume)
    allowance_checks.append(dict(envelope='rear-tool-access',margin_mm=0,target=target,overlap_mm3=round(volume,6)))
    assert np.isfinite(volume) and volume<.01,('rear-tool-access',target,volume)
assert abs((mounts[0][1]+hole_d/2)-(mounts[1][1]-hole_d/2)-P['motor_holes_outer_span'])<1e-6
assert abs(mounts[0][1]+hole_d/2+P['motor_boss_diameter']/2-P['upper_hole_top_to_boss_bottom'])<1e-6
assert P['hub_back_z']>=boss_h
assert P['hub_back_z']+P['hub_length']<=boss_h+P['shaft_exposed_length']
assert abs(joined([motor,shaft]).extents[2]-P['motor_overall_length'])<1e-6
manifest=dict(load_screen='load-screen.json',brake_interface_audit='brake-interface-audit.json',carrier_export_withheld=True,revision='R07',mount_derivation=P['mount_derivation'],dimension_audit='dimension-audit.json',date='2026-11-12',status='STATIC FIT PROTOTYPE. Checked against nominal R06 brake estimate and declared allowances; real fit and powered use unverified.',
              architecture='Three flat-print parts: recessed cup, D-shaped motor adapter plate and cover. Motor face/shaft/rotor datums unchanged; no external base or second shaft.',
              parameters=P,checks=checks,clearance_checks=intersections,allowance_checks=allowance_checks,nominal_geometry_pass=True,fit_pass=None,brake_estimate_report='brake-estimate/estimate-report.html',
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
        if f.is_file() and (f.suffix!='.stl' or f.parent.name=='brake-estimate' or f.name in [c['export'] for c in checks if c['export']]) and f.suffix in ['.stl','.json','.py','.html','.js','.md','.scad','.txt','.png','.jpg','.pdf','.svg','.glb'] and f.name!='assembly.json':z.write(f,f.relative_to(ROOT))
print(json.dumps({'parts':len(checks),'print_meshes':sum(1 for c in checks if c['export']),'clearance_pairs':len(intersections),'allowance_checks':len(allowance_checks),'status':manifest['status']}))
