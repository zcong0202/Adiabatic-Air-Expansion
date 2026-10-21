"""Provisional Milton-style male NPT print variants; NOT a measured Jeanoko fit.

The thread envelope/profile is an approximate printable construction informed
by the published BOSL2 NPT module. No ASME thread-gauge compliance is claimed.
Only the exterior changes. Keep the R07 8-to-24 mm internal contour.
"""
from pathlib import Path
import json, math, zipfile, hashlib
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
try:
 from round_jet import OPT, ROOT
except ModuleNotFoundError:
 ROOT=Path(__file__).resolve().parent
 OPT=ROOT

OUT=OPT/'deliverables/C24-3deg-Milton-mount-reference'
OUT.mkdir(parents=True,exist_ok=True)
BASE={'total_length_mm':25+8/math.tan(math.radians(3)),
      'cone_length_mm':8/math.tan(math.radians(3))}
L=BASE['total_length_mm'];CONE=BASE['cone_length_mm']
PITCH=25.4/18
THREAD_LENGTH=.6006*25.4
THREAD_BASE_MAJOR=.668*25.4
DEPTH=PITCH*math.cos(math.radians(30))*5/8
HEX_AF=22.
HEX_END=THREAD_LENGTH+4
BLEND_END=HEX_END+10
THETA=np.linspace(0,2*np.pi,240,endpoint=False)

def bore(s):
 return np.where(s<15,4,np.where(s<L-10,4+(s-15)*math.tan(math.radians(3)),12))

def outer_radius(s,theta,undersize):
 s,theta=np.broadcast_arrays(s,theta)
 original=bore(s)+2
 # Radial hex contour has 22 mm across flats; grow into it over 10 mm.
 sector=(theta+np.pi/6)%(np.pi/3)-np.pi/6
 hexr=(HEX_AF/2)/np.cos(sector)
 blend=np.clip((BLEND_END-s)/(BLEND_END-HEX_END),0,1)
 collar=original+(hexr-original)*blend
 # Printed Z rises toward the male free end, as in BOSL2 external NPT.
 z=THREAD_LENGTH-s
 major=(THREAD_BASE_MAJOR-undersize)/2-z/32
 phase=(z/PITCH-theta/(2*np.pi)+.5)%1-.5
 shape=np.interp(phase,[-.5,-7/16,-6/16,-1/16,1/16,6/16,7/16,.5],
                 [-DEPTH*1.07,-DEPTH*1.07,-DEPTH,0,0,-DEPTH,-DEPTH*1.07,-DEPTH*1.07])
 thread=major+shape
 # A short entry chamfer helps the fit coupon start without forcing it.
 thread-=np.clip((.6-s)/.6,0,1)*.25
 # Smoothly end the thread into the shoulder over 0.05 mm.
 transition=np.clip((s-THREAD_LENGTH)/.05,0,1)
 shoulder=thread*(1-transition)+hexr*transition
 return np.where(s<=THREAD_LENGTH,thread,np.where(s<THREAD_LENGTH+.05,shoulder,collar))

def make(undersize=0,coupon=False):
 length=BLEND_END+2 if coupon else L
 ss=np.unique(np.r_[np.linspace(0,THREAD_LENGTH,310),
                      THREAD_LENGTH+.025,THREAD_LENGTH+.05,
                      np.linspace(THREAD_LENGTH+.06,HEX_END,10),
                      np.linspace(HEX_END,BLEND_END,30),
                      np.linspace(BLEND_END,length,max(3,int((length-BLEND_END)/.7)+1)),
                      [15,length]])
 ss=ss[(ss>=0)&(ss<=length)]
 outer=outer_radius(ss[:,None],THETA[None,:],undersize)
 inner=np.broadcast_to(bore(ss)[:,None],outer.shape)
 assert np.min(outer-inner)>1.9
 vertices=[]
 for radius in [outer,inner]:
  vertices.append(np.stack([radius*np.cos(THETA),radius*np.sin(THETA),
                           np.broadcast_to(length-ss[:,None],radius.shape)],axis=2).reshape(-1,3))
 vertices=np.concatenate(vertices)
 n=len(THETA); nr=len(ss); offset=nr*n
 faces=[]
 for base in [0,offset]:
  for j in range(nr-1):
   a=base+j*n+np.arange(n);b=base+j*n+(np.arange(n)+1)%n;c=b+n;d=a+n
   faces.extend(np.column_stack([a,b,c]));faces.extend(np.column_stack([a,c,d]))
 for j in [0,nr-1]:
  a=j*n+np.arange(n);b=j*n+(np.arange(n)+1)%n;c=b+offset;d=a+offset
  faces.extend(np.column_stack([a,b,c]));faces.extend(np.column_stack([a,c,d]))
 mesh=trimesh.Trimesh(vertices=vertices,faces=np.array(faces),process=True)
 mesh.fix_normals()
 assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
 assert mesh.volume>0
 mesh.units='mm'
 return mesh,{'minimum_radial_wall_mm':float((outer-inner).min()),'size_mm':mesh.extents.tolist(),
              'watertight':True,'connected_components':1,'diameter_undersize_mm':undersize,
              'coupon_only':coupon,'hardware_fit_verified':False}

if __name__=='__main__':
 files={};nominal=None
 for undersize,label in [(0,'nominal'),(.2,'diameter-minus-0p2'),(.4,'diameter-minus-0p4')]:
  for coupon,prefix in [(False,'NOZZLE'),(True,'FIT-COUPON')]:
   mesh,report=make(undersize,coupon);name=f'{prefix}_3-8-MNPT_{label}_mm.stl';path=OUT/name
   mesh.export(path)
   loaded=trimesh.load(path,force='mesh')
   assert loaded.is_watertight and np.allclose(loaded.extents,mesh.extents,atol=.001)
   report['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();files[name]=report
   if not coupon and undersize==0:
    nominal=mesh
    mesh.export(OUT/'NOZZLE_3-8-MNPT_nominal_GEOMETRY_mm.3mf')
 # Independent check of the mathematical internal profile against the case CAD.
 sample=np.linspace(0,L,1001)
 reference=np.interp(sample,[0,15,15+CONE,L],[4,4,12,12])
 assert np.max(np.abs(bore(sample)-reference))<1e-10
 report={'status':'Provisional mounting reference; print coupons before a full nozzle',
  'reference_product':'Milton S-183, Amazon B00KT9OUD0',
  'manufacturer_url':'https://miltonindustries.com/products/miltonr-s-183-turbo-blow-gun-nozzle-kit-3-piece-s-183',
  'manufacturer_thread_statement':'3/8 NPT for S-181 and S-182 guns',
  'male_gender_basis':'External thread visible in manufacturer product photo',
  'manufacturer_photo':'https://miltonindustries.com/cdn/shop/products/s-183_fanspraytip_down.jpg?v=1686310893',
  'thread_construction_reference':'https://github.com/BelfrySCAD/BOSL2/blob/master/threading.scad#pipe-threading',
  'thread':'Provisional 3/8-18 NPT male, right hand',
  'thread_pitch_mm':PITCH,'thread_length_mm':THREAD_LENGTH,'diametral_taper':'1:16',
  'approx_base_crest_envelope_diameter_mm':THREAD_BASE_MAJOR,
  'thread_is_gauge_verified':False,'thread_is_exact_Milton_replica':False,
  'hex_across_flats_mm':HEX_AF,'coupon_height_mm':BLEND_END+2,
  'nozzle_length_mm':L,'internal_contour_matches_R07':True,
  'maximum_internal_profile_difference_mm':float(np.max(np.abs(bore(sample)-reference))),
  'CFD_status':'R07 internal geometry unchanged. No new CFD was run; port fit, source response, wall heat transfer and installation remain unvalidated.',
  'Jeanoko_fit':'User confirmed on 2026-10-15: a Milton S-183 tip screws directly onto the Jeanoko cold outlet. Printed prototype fit remains untested.',
  'reference_tip_fit_user_confirmed':True,
  'printed_thread_fit_verified':False,
  'files':files}
 (OUT/'mount-reference.json').write_text(json.dumps(report,indent=2))
 guide='''AA / MILTON-STYLE DIRECT MOUNT / PROVISIONAL PRINT PACKAGE

This revision replaces the smooth inlet exterior with a male 3/8-18 NPT
prototype. Milton specifies 3/8 NPT; its product photo shows an external
male thread. On 2026-10-15 the user confirmed that a Milton S-183 tip screws
directly onto the Jeanoko cold outlet. The reference interface is therefore
confirmed by a user fit test. Printed prototype thread fit remains untested.
No nominal thread diameter is treated as an actual flow-bore measurement.

PRINT THE FIT COUPONS FIRST
Three short, hollow coupons reproduce the same thread, shoulder and lead-in
used on the full nozzle. The labels describe EXTERNAL DIAMETER reductions:
nominal = no reduction; minus-0p2 = 0.20 mm smaller; minus-0p4 = 0.40 mm smaller.
They are approximate printable profiles, not gauged ASME threads.
Use H2S / 0.4 mm / actual PLA, 0.20 mm layers, 5 walls, no supports.
Import at 100% in MILLIMETRES. The broad collar/base is down; male thread up.
An outside brim may help. Keep the central passage open.

Offer each finished coupon to the COLD outlet by hand. Start with the
nominal coupon. Do not force, use a wrench, or use the coupon as a tap.
Choose a variant only if it starts and seats without cross-threading.
If none starts cleanly, stop: the port may be another size or BSP thread.
The confirmed commercial-tip fit does not establish printed thread tolerance.
Check available thread depth and clearance from the vortex body.

AFTER A COUPON FITS
Print the matching NOZZLE STL. Broad 24 mm ID outlet goes on the bed;
male inlet thread is at the top. Overall size remains 28 x 28 x 177.65 mm.
The 22 mm hex shoulder has a sloped exterior to avoid a large unsupported
ledge in this orientation. Do not use the hex to tighten a PLA pipe joint.
Support the nozzle independently. This printed part has no pressure rating.
Fit only to the downstream cold-delivery outlet, away from hot exhaust.
Use your actual filament and bed profile; re-slice in Bambu Studio.

GEOMETRY AND CFD STATUS
The internal contour is unchanged: 8 mm ID inlet, 15 mm inlet land,
152.649 mm 3-degree half-angle cone, 24 mm ID outlet with 10 mm land.
The new exterior adds the thread, hex shoulder, and a support-friendly ramp.
The saved animation still represents the original R07 prescribed-flow CFD.
It does not simulate a real threaded source junction or certify this mount.
Printed thread fit, leaks, actual cold flow/temperature, changed wall heat
pickup and the >6 C target all require a physical test.

Editable generator: optimization/scripts/milton_mount_reference.py.
Reference and verification record: mount-reference.json.
'''
 (OUT/'PRINT-COUPONS-FIRST.txt').write_text(guide)
 # Inspectable engineering view, rendered from the actual output meshes.
 fig=plt.figure(figsize=(12,6.5),layout='constrained')
 for i,(part,title) in enumerate([(nominal,'Full nozzle · thread at top'),(make(0,True)[0],'Fit coupon · nominal')]):
  ax=fig.add_subplot(1,2,i+1,projection='3d')
  # Keep exact thread facets; a cropped view reveals the external helix.
  triangles=part.triangles
  keep=np.ones(len(triangles),bool)
  normal=part.face_normals[keep];lighting=.45+.5*np.abs(normal@np.array([.3,-.4,.8]))
  colors=np.column_stack([.2+.13*lighting,.35+.25*lighting,.45+.28*lighting,np.ones(len(lighting))])
  ax.add_collection3d(Poly3DCollection(triangles[keep],facecolors=colors,edgecolors='none',rasterized=True))
  height=part.extents[2];ax.set(xlim=(-15,15),ylim=(-15,15),zlim=(0,height),title=title)
  ax.set_box_aspect([30,30,height]);ax.view_init(elev=20,azim=35)
  ax.set_xticks([-14,0,14]);ax.set_yticks([-14,0,14]);ax.set_zlabel('mm')
 fig.suptitle('Milton-style 3/8-18 NPT male mount · prototype\nCommercial tip fit user-confirmed; printed thread needs coupon check',fontsize=15)
 fig.savefig(OUT/'mount-and-coupon.png',dpi=150);plt.close(fig)
 archive=ROOT/'AA-C24-Milton-mount-reference.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for path in OUT.iterdir():z.write(path,arcname=OUT.name+'/'+path.name)
  z.write(Path(__file__),arcname=OUT.name+'/milton_mount_reference.py')
 with zipfile.ZipFile(archive) as z:assert z.testzip() is None
 print(json.dumps({'package':str(archive),'files':files,'unchanged_internal_contour':True},indent=2))
