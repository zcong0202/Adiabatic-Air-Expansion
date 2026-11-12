"""Single-piece open motor/brake mount variant. Static fit geometry; no wall, cover or guard."""
from pathlib import Path
import json,math,zipfile,shutil
import numpy as np
import trimesh as tm
ROOT=Path(__file__).resolve().parent;PARENT=ROOT.parent
snapshot=ROOT/'reference-inputs.json'
if not snapshot.exists():snapshot.write_text(json.dumps({'parameters':json.loads((PARENT/'parameters.json').read_text()),'assembly':json.loads((PARENT/'assembly.json').read_text())},separators=(',',':')))
frozen=json.loads(snapshot.read_text());P=frozen['parameters'];source=frozen['assembly']
if not (ROOT/'brake_reference.py').exists():shutil.copyfile(PARENT/'brake_estimate.py',ROOT/'brake_reference.py')
from brake_reference import make_brake
exact_brake,_,_=make_brake(P['rotor_plane'])
for d in source:
 if d['id'] in exact_brake:
  d['vertices']=exact_brake[d['id']].vertices.tolist();d['faces']=exact_brake[d['id']].faces.tolist()
lookup={d['id']:d for d in source}
def mesh(ident):
 d=lookup[ident];return tm.Trimesh(d['vertices'],d['faces'],process=True)
def cyl(r,h,p,n=64):
 m=tm.creation.cylinder(radius=r,height=h,sections=n);m.apply_translation(p);return m
def box(size,p):
 m=tm.creation.box(size);m.apply_translation(p);return m
def union(*m):return tm.boolean.union(list(m),engine='manifold')
def cut(m,*b):return tm.boolean.difference([m,*b],engine='manifold')
def hull(*m):return tm.convex.convex_hull(tm.util.concatenate(m).vertices)
def holes(points,d,h,z):return [cyl(d/2,h,[x,y,z],32) for x,y in points]
def slot(x,y,d,travel,h,z):return union(box([travel,d,h],[x,y,z]),cyl(d/2,h,[x-travel/2,y,z],32),cyl(d/2,h,[x+travel/2,y,z],32))
plate_points=P['plate_bolt_xy'];mounts=P['is_adapter_xy']
# Open ring with two broad arms; flat rear printing face. All case walls are removed.
ring=cut(cyl(76,10,[0,0,-13]),cyl(62,12,[0,0,-13]))
arms=[hull(cyl(12,10,[33,s*57.16,-13]),cyl(12,10,[101,s*25.5,-13])) for s in [-1,1]]
bridge=hull(*[cyl(12,10,[101,y,-13]) for y in [-25.5,25.5]])
frame=union(ring,*arms,bridge,*[cyl(10,9,[x,y,-3.5]) for x,y in plate_points],*[cyl(12,7,[x,y,-4.5]) for x,y in mounts])
frame=cut(frame,cyl(62,30,[0,0,-15]),
          *[slot(x,y,6.6,8,30,-8) for x,y in mounts],*[slot(x,y,11.6,8,8,-15) for x,y in mounts],cyl(7,30,[76,0,-15]))
# Preserve motor interface. Remove all five obsolete plate-to-frame bolt holes.
plate=cut(cyl(76,10,[0,0,5]),box([100,200,40],[110,0,5]),
          cyl(20,12,[0,0,5]),*holes(P['motor_mount_xy'],7.5,12,5))
# Posts overlap the plate by 1 mm; Boolean union produces one connected solid.
mount=union(frame,plate)
# Merge coincident union vertices and remove collapsed triangles before STL export.
mount.process(validate=False)
mount.update_faces(mount.nondegenerate_faces())
mount.update_faces(mount.unique_faces());mount.remove_unreferenced_vertices()
collar=mesh('hub')
printed={'single-piece-mount':mount}
records=[]
for ident,m in printed.items():
 assert m.is_volume and m.is_watertight and len(m.split())==1,ident
 assert np.all(m.extents<np.array([340,320,340]))
 q=m.copy();q.apply_transform(tm.transformations.rotation_matrix(math.pi,[1,0,0]));q.apply_translation([0,0,-q.bounds[0,2]]);q.export(ROOT/(ident+'-FIT-ONLY.stl'))
 reloaded=tm.load(ROOT/(ident+'-FIT-ONLY.stl'));assert reloaded.is_volume and len(reloaded.split())==1
 records.append({'part':ident,'extents_mm':np.round(m.extents,3).tolist(),'single_closed_solid':True,'H2S_bed_fit':True})
q=collar.copy();q.apply_translation([0,0,-q.bounds[0,2]]);q.export(ROOT/'shaft-collar-REFERENCE.stl')
items=[]
frame_d=dict(id='single-piece-mount',label='01 · One-piece motor / brake mount',color='#536871',kind='printed',explode=[0,0,-40],file='single-piece-mount-FIT-ONLY.stl',note='Motor plate and open brake support form one connected solid. Five integral solid posts replace joint bolts and sleeves. Motor and IS holes retained. Static fit only.',vertices=mount.vertices.tolist(),faces=mount.faces.tolist())
items.append(frame_d)
keep=['hub','motor','shaft','motor-bolts','is-bolts','adapter','rotor','rotor-bolts','caliper','pads','brake-arm','barrel-adjuster','rear-adjuster','brake-pivot','pm-bolts','brake-wire','cable-lead','arm-envelope']
for ident in keep:
 d=dict(lookup[ident])
 if ident=='hub':d.update(label='Shaft collar / disc hub · reference',file='shaft-collar-REFERENCE.stl',reference=True,note='Reference shape only. Plain disc holes and bore; no working threads, clamp, key or axial retention. Metal functional hub still required. Not for powered use.')
 if ident in ['motor','shaft']:d['explode']=[0,0,-110]
 items.append(d)
washers=tm.util.concatenate([cut(cyl(12,1,[x,y,10.5],32),cyl(3.75,3,[x,y,10.5],24)) for x,y in P['motor_mount_xy']])
items.append(dict(id='washers',label='Motor washers',color='#aeb6bc',kind='fastener',explode=[0,0,-20],file=None,note='Metal washer references; motor threads and fastener stack remain unverified.',vertices=washers.vertices.tolist(),faces=washers.faces.tolist()))
allmeshes={d['id']:tm.Trimesh(d['vertices'],d['faces'],process=True) for d in items}
assert all(m.is_volume for m in allmeshes.values()), [(k,m.is_volume) for k,m in allmeshes.items() if not m.is_volume]
checks=[]
for part in [d['id'] for d in items if d['id'] not in ['single-piece-mount','arm-envelope']]:
 for target in ['single-piece-mount']:
  overlap=tm.boolean.intersection([allmeshes[part],allmeshes[target]],engine='manifold');v=0 if overlap.is_empty else float(overlap.volume)
  assert math.isfinite(v) and v<.01,(part,target,v)
  checks.append({'parts':[part,target],'overlap_mm3':round(v,6)})
allowances=[]
for part in ['caliper','barrel-adjuster','rear-adjuster','brake-pivot','arm-envelope']:
 m=allmeshes[part]
 if part!='arm-envelope':m=tm.convex.convex_hull(np.concatenate([m.vertices+np.array([x,y,z]) for x in [-3,3] for y in [-3,3] for z in [-3,3]]))
 for target in ['single-piece-mount']:
  overlap=tm.boolean.intersection([m,allmeshes[target]],engine='manifold');v=0 if overlap.is_empty else float(overlap.volume)
  assert math.isfinite(v) and v<.01,(part,target,v)
  allowances.append({'envelope':part,'target':target,'overlap_mm3':round(v,6)})
manifest={'variant':'OPEN-02-SINGLE','basis':'R07 motor datums and R06 image-estimated CMD23. Two-piece OPEN-01 and enclosed R07 retained separately.','status':'Static fit prototype; no powered-use or containment rating.','prints':records,'collar':'Reference only; not a functioning torque/retention design.','selected_interference_checks':checks,'allowance_checks':allowances,'nominal_geometry_pass':True,'real_fit_verified':False,'shaft_z_mm':[15,40],'hub_z_mm':[18,38],'rotor_z_mm':28,'motor_mount_xy_mm':P['motor_mount_xy'],'IS_pitch_mm':51,'print_orientation':'Motor plate front face on bed. Local supports required below offset brake arms/ring. No support-free claim.','integral_connections':5,'plate_joint_hardware_removed':True,'open_items':['Actual motor threads and ports','Actual brake/adapter dimensions and cable motion','Functional metal shaft hub and disc bolt retention','Hot strength, bearings, speed, brake duty and guard for powered tests']}
(ROOT/'assembly.json').write_text(json.dumps(items,separators=(',',':')))
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'prints':records,'interference_checks':len(checks),'allowance_checks':len(allowances)}))
# The viewer/template are kept local to this variant, so R07 is untouched.
if (ROOT/'viewer.template.html').exists():
 (ROOT/'index.html').write_text((ROOT/'viewer.template.html').read_text().replace('__ASSEMBLY__',json.dumps(items,separators=(',',':'))))
with zipfile.ZipFile(ROOT/'single-piece-mount-fit.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in ROOT.iterdir():
  if f.is_file() and f.suffix in ['.stl','.json','.html','.js','.py','.md','.png','.txt']:z.write(f,f.name)
