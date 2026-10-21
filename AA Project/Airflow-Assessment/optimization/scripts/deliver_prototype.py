"""Export unchanged CFD geometry in print orientation, plus a fit/print guide."""
import json, math, shutil, hashlib, zipfile
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from round_jet import ROOT, OPT

dest=OPT/'deliverables/C24-3deg-print-prototype'
dest.mkdir(parents=True,exist_ok=True)
src=OPT/'designs/C24_a3'
d=json.loads((src/'design.json').read_text())
m=trimesh.load(src/'wall-mm.stl',force='mesh')
original=m.copy()
rotation=trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0])
m.apply_transform(rotation)
m.apply_translation([0,0,-m.bounds[0,2]])
stl=dest/'AA_C24_3deg_PRINT_mm.stl'
m.export(stl)
check=trimesh.load(stl,force='mesh')
assert check.is_watertight and check.is_winding_consistent and len(check.split())==1
assert np.allclose(check.extents,[28,28,d['total_length_mm']],atol=.001)
assert abs(check.volume-original.volume)/original.volume<1e-5
m.units='mm'
geometry_3mf=dest/'AA_C24_3deg_GEOMETRY_mm.3mf'
m.export(geometry_3mf)
roundtrip=trimesh.load(geometry_3mf,force='mesh')
assert roundtrip.is_watertight and np.allclose(roundtrip.extents,check.extents,atol=.001)
with zipfile.ZipFile(geometry_3mf) as z:
 assert any(b'unit="millimeter"' in z.read(n) for n in z.namelist() if n.endswith('.model'))
shutil.copy2(src/'concept.step',dest/'AA_C24_3deg_EDITABLE.step')
shutil.copy2(src/'design.json',dest/'source-design.json')
report={
 'case':'R07_D24_diffuser_3deg_SST','geometry_changed_from_CFD':False,
 'transformation':'Rigid rotation only; wide outlet on Z=0, inlet at top',
 'stl_units':'millimetres','step_units':'metres, declared within STEP',
 'bounds_mm':check.bounds.tolist(),'extents_mm':check.extents.tolist(),
 'watertight':bool(check.is_watertight),'consistent_winding':bool(check.is_winding_consistent),
 'connected_components':len(check.split()),'faces':len(check.faces),
 'solid_volume_mm3':float(check.volume),
 'nominal_radial_wall_mm':2,'minimum_analytic_cone_normal_wall_mm':2*math.cos(math.radians(3)),
 'stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest(),
 'hardware_fit_verified':False,'physically_tested':False,
 'printer_user_supplied':'Bambu H2S, PLA, 0.4 mm nozzle',
 'slicer_completed':(dest/'slice-verification.json').exists(),
 'printer_toolpath_verified':False,'connector':'Straight inlet land: 12 mm OD, 8 mm ID, 15 mm long. No inferred thread.'}
(dest/'mesh-verification.json').write_text(json.dumps(report,indent=2))
guide='''AA C24 / 3-degree diffuser: PRINTABLE BENCH-TEST PROTOTYPE

PRINT FILE: AA_C24_3deg_PRINT_mm.stl (MILLIMETRES).
ALTERNATIVE: AA_C24_3deg_GEOMETRY_mm.3mf (geometry only; millimetres).
EDIT FILE: AA_C24_3deg_EDITABLE.step (units declared as METRES).
Keep STL scale at 100%. Expected slicer size: 28 x 28 x 177.65 mm.
This is the same flow geometry as CFD case R07, rotated for printing.
Mesh checks: closed solid, correct winding, one connected component.

BAMBU H2S / PLA / 0.4 mm NOZZLE
Import STL into Bambu Studio. Select your installed H2S 0.4 mm profile
and the profile for your actual PLA. Use 0.20 mm layers as a starting point.
The supplied orientation puts the 24 mm bore outlet on the bed.
Do not auto-orient onto its side. Keep the full 2 mm wall in the slice.
Start with 5 wall loops; inspect the preview for continuous solid walls.
Keep the bore and both ends OPEN. Do not add internal supports.
The cone is 3 degrees from vertical, so geometry does not require supports.
Use an outside-only brim if needed for adhesion. Remove it before testing.
Use filament-maker temperature and cooling settings.
If included, AA_C24_H2S_PLA_0p4_sliced.3mf is a Bambu Studio project from
a completed H2S slice using installed manufacturer presets. It uses Generic
PLA and the default Cool Plate. Select your ACTUAL PLA and plate in Studio,
then RE-SLICE. It has not been printed or verified on your printer.
The CLI reports T65535 as invalid during G-code analysis. That exact command
comes from the unchanged installed H2S end template for AMS unloading.
The CLI still returns success. Keep the native manufacturer templates and
re-slice in Studio; do not hand-edit machine commands or print this blindly.
See slice-verification.json for the record and estimated time/material.

DIMENSIONS
Inlet: 8 mm bore; 12 mm outside diameter; 15 mm straight land.
Cone: 152.649 mm long; 3 degree half angle.
Outlet: 24 mm bore; 28 mm outside diameter; 10 mm straight land.
Total length: 177.649 mm. Radial wall: 2 mm.
Allow for your printer's actual hole-size error. Measure the finished part.

CONNECTION IS STILL OPEN
The Amazon Jeanoko listing does not establish a verified mating geometry.
This file includes NO assumed Jeanoko thread or snap fit.
Measure cold-outlet OD, ID, usable straight length, and any thread.
A separate measured adapter or flexible sleeve must preserve the 8 mm bore
and avoid cold-air leaks. Support the long body independently.
Do not force an interference fit on the vortex assembly.
Connect only downstream of the vortex cold outlet; no supply-pressure rating.
Keep the PLA body and mount away from the hot exhaust.

WHAT THE COMPUTATION DOES AND DOES NOT ESTABLISH
Dry, adiabatic, steady axisymmetric SST CFD: prescribed 2 g/s cold air at
5 C, ambient 35 C, still air. Predicted mean temperature drop: 9.44 C
over a 50 x 50 mm target 200 mm FROM THE FINAL OUTLET.
Source response to this attachment, printed roughness, wall heat pickup,
hot exhaust, fit, and hardware performance are not validated.
The video animates tracers in the saved steady mean flow. It is not a
transient CFD solution and does not resolve turbulence in time.

FIRST BENCH CHECK
Confirm clear bore and sound walls. Mount without loading the cold port.
With the attachment installed, measure cold-flow rate and inlet temperature.
Place the 50 x 50 mm sampling plane 200 mm after the final outlet.
Compare its area-average air temperature against nearby ambient, with hot
exhaust routed away. More than 6 C drop remains a physical test target.
'''
(dest/'PRINT-AND-FIT.txt').write_text(guide)

L=d['total_length_mm']; cone=d['cone_length_mm']; xs=np.array([0,15,15+cone,L]); ri=np.array([4,4,12,12])
fig=plt.figure(figsize=(12,6),layout='constrained')
gs=fig.add_gridspec(1,2,width_ratios=[1.6,1])
a=fig.add_subplot(gs[0]);
for sign in [-1,1]:
 a.add_patch(Polygon(np.column_stack([np.r_[xs,xs[::-1]],sign*np.r_[ri,(ri+2)[::-1]]]),facecolor='#708b9b',edgecolor='#2d4552'))
a.plot([0,L],[0,0],':',color='#87979f',lw=.8)
a.annotate('',(0,-23),(L,-23),arrowprops=dict(arrowstyle='<->',color='#26495f'))
a.text(L/2,-28,f'{L:.2f} mm total',ha='center',color='#26495f')
a.annotate('8 mm ID\n12 mm OD\n15 mm land',(2,6),(15,37),arrowprops=dict(arrowstyle='->'),ha='center')
a.annotate('24 mm ID\n28 mm OD\n10 mm land',(L-3,14),(L-18,37),arrowprops=dict(arrowstyle='->'),ha='center')
a.text(90,18,'3° half angle  |  2 mm radial wall',ha='center',fontsize=10)
a.set(xlim=(-8,L+8),ylim=(-36,53),xlabel='Axial distance from inlet (mm)',ylabel='Radius (mm)',title='Section through the actual CAD')
a.set_aspect('equal');a.spines[['top','right']].set_visible(False)
b=fig.add_subplot(gs[1],projection='3d')
# Surface plot comes from the same analytic geometry, in print orientation.
angle=np.linspace(0,2*np.pi,90); axials=np.array([0,10,10+cone,L]);outer=np.array([14,14,6,6]);inner=outer-2
aa,zz=np.meshgrid(angle,axials)
for rr,color in [(outer,'#438eac'),(inner,'#a5cfdb')]:
 r=rr[:,None];b.plot_surface(r*np.cos(aa),r*np.sin(aa),zz,color=color,alpha=.94,linewidth=0,shade=True)
for z,r0 in [(0,12),(L,4)]:
 r,ang=np.meshgrid([r0,r0+2],angle);b.plot_surface(r*np.cos(ang),r*np.sin(ang),np.full_like(r,z),color='#39758c',shade=True)
b.set(xlim=(-20,20),ylim=(-20,20),zlim=(0,L),xlabel='X (mm)',ylabel='Y (mm)',zlabel='Z (mm)',title='Supplied print orientation')
b.set_xticks([-14,0,14]);b.set_yticks([-14,0,14]);b.set_xlabel('');b.set_ylabel('')
b.set_box_aspect([40,40,L]);b.view_init(elev=16,azim=35)
fig.suptitle('AA printable prototype · wide outlet on bed\nFit and cooling performance require bench validation',fontsize=15)
fig.savefig(dest/'dimensions-and-print-orientation.png',dpi=160);plt.close(fig)
archive=ROOT/'AA-C24-3deg-print-prototype.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(dest.iterdir()):z.write(f,arcname=dest.name+'/'+f.name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'package':str(archive),'stl':str(stl),'verification':report},indent=2))
