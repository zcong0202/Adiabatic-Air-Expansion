"""Generate scientific figures and low-pressure flow-body CAD from results."""
from pathlib import Path
import sys,json,math,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch,Rectangle
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'optimization/scripts'))
from campaign import source,CFG
OUT=HERE/'results';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})

fig,ax=plt.subplots(figsize=(12,4),layout='constrained');ax.set(xlim=(0,12),ylim=(0,4));ax.axis('off')
boxes=[(.1,2.1,2.0,'Remote stock supply\ncompressor + receiver\ndryer + filter'),(2.7,2.1,2.0,'~10 m compressed\nair feed hose\nregulator + valve'),(5.3,2.1,2.0,'Stock vortex\nnear the outlet\npaired flow / cold map'),(7.9,2.1,1.8,'Custom nozzle\nshort cold path\nCAD + CFD'),(10.1,2.1,1.8,'Target\n5 × 5 cm\nat 20 cm')]
for x,y,w,t in boxes:
 ax.add_patch(FancyBboxPatch((x,y),w,1.15,boxstyle='round,pad=.06',fc='#e9f3f5',ec='#2c6778'));ax.text(x+w/2,y+.57,t,ha='center',va='center',fontsize=10)
for a,b in zip(boxes,boxes[1:]):ax.add_patch(FancyArrowPatch((a[0]+a[2]+.05,2.65),(b[0]-.1,2.65),arrowstyle='-|>',mutation_scale=15,color='#2c6778'))
ax.add_patch(FancyArrowPatch((6.3,2.05),(6.3,.95),arrowstyle='-|>',mutation_scale=15,color='#b66827'));ax.text(6.3,.7,'Hot exhaust away from target\nStock muffler; local noise remains',ha='center',color='#8a4a20')
ax.text(.1,3.7,'Proposed stock-component architecture',fontsize=18,weight='bold',color='#183947');ax.text(.1,.1,'System diagram. Commercial part envelopes and fitted adapter are not verified CAD.',fontsize=10,color='#536773')
fig.savefig(OUT/'system-architecture.png',dpi=170);fig.savefig(OUT/'system-architecture.svg');plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
betas=np.array(CFG['source']['cold_fractions']);temps=np.array([source(float(b))['cold_c'] for b in betas]);mass=np.array([source(float(b))['mass_kg_s']*1000 for b in betas])
axes[0].plot(betas*100,temps,'o-',color='#24738b',label='Approximate manufacturer curve');axes[0].plot(betas*100,38-.8*(34-temps),'s--',color='#ae612f',label='Declared inlet / source stress');axes[0].set(xlabel='Vortex cold fraction beta (%)',ylabel='Cold-source temperature (°C)',title='Source flow and temperature are coupled');axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
axes[1].plot(betas*100,mass,'o-',color='#24738b');axes[1].plot(betas*100,.9*mass,'s--',color='#ae612f');axes[1].set(xlabel='Vortex cold fraction beta (%)',ylabel='Cold branch (g/s)',title='227 reference L/min total inlet');axes[1].grid(alpha=.2)
fig.suptitle('EXAIR reference candidate · 100 psig · inlet 34°C\nFamily curve is approximate; mass conversion assumes 20°C and 1 atm',fontsize=12)
fig.savefig(OUT/'source-operating-map.png',dpi=170);plt.close(fig)

report=json.loads((OUT/'campaign.json').read_text());rows=report['cases']
if not rows:raise SystemExit('No completed CFD cases to plot.')
fig,ax=plt.subplots(figsize=(11,4.5),layout='constrained');xx=np.arange(len(rows));ax.bar(xx-.2,[r['nominal_dry_drop_c'] for r in rows],width=.38,label='Nominal dry CFD scalar',color='#287d94');ax.bar(xx+.2,[r['stress_min_drop_c'] for r in rows],width=.38,label='Declared stress screen, min(dry, moist)',color='#d69b4b');ax.axhline(6,color='#aa4136',ls='--',label='Strict 6°C target');ax.axhline(7,color='#376544',ls=':',label='7°C design margin');ax.set_xticks(xx,[(r['case'].split('_')[0]+('f' if r['case'].endswith('_fine') else ''))+'\n'+f"β={r['beta']:.1f}, D={r['diameter_mm']:g} mm"+('\n90% flow' if 'lowflow' in r['case'] else '') for r in rows],fontsize=8);ax.set(ylabel='Area-average temperature drop (°C)',title='Executed recursive campaign · still-air, constant-density screen');ax.legend(fontsize=8);ax.grid(axis='y',alpha=.15);fig.savefig(OUT/'iteration-history.png',dpi=170);plt.close(fig)

selected=report['selected_case'] or rows[-1];case=ROOT/'optimization/cases'/selected['case'];info=json.loads((case/'case.json').read_text());a=json.loads((case/'audit.json').read_text());f=case/'postProcessing/targetProfiles'/f"{a['target']['iteration']:g}"/'target_theta_U.xy';profile=np.loadtxt(f)
y=np.linspace(-.04,.04,241);yy,zz=np.meshgrid(y,y);theta=np.interp(np.hypot(yy,zz),profile[:,0],profile[:,1]);temp=34-(34-selected['nominal_source_c'])*theta
fig,ax=plt.subplots(figsize=(6,5),layout='constrained');im=ax.pcolormesh(yy*1000,zz*1000,temp,shading='auto',cmap='coolwarm',vmin=min(20,temp.min()),vmax=34);ax.add_patch(Rectangle((-25,-25),50,50,fill=False,ls='--',lw=2,ec='#163d32'));ax.set(xlabel='y (mm)',ylabel='z (mm)',title=selected['case']+'\nNominal dry scalar-derived temperature at 20 cm');ax.set_aspect('equal');fig.colorbar(im,ax=ax,label='Air temperature (°C)');fig.savefig(OUT/'target-field.png',dpi=170);plt.close(fig)

cad=HERE/'cad';cad.mkdir(exist_ok=True);d=selected['diameter_mm'];angle=selected['half_angle_deg'];cone=(d/2-4)/math.tan(math.radians(angle));length=cone+25
(cad/'nozzle-parametric.scad').write_text(f'''// Flow body only. Millimetres. No fitted source connector or pressure rating.
D={d:g}; halfAngle={angle:g}; inlet=8; wall=2; inletLand=15; outletLand=10;
cone=(D-inlet)/2/tan(halfAngle); $fn=180;
module body(w) {{
 cylinder(h=inletLand,r=inlet/2+w);
 translate([0,0,inletLand]) cylinder(h=cone,r1=inlet/2+w,r2=D/2+w);
 translate([0,0,inletLand+cone]) cylinder(h=outletLand,r=D/2+w);
}}
difference() {{ body(wall); translate([0,0,-0.01]) cylinder(h=inletLand+.02,r=inlet/2);
 translate([0,0,inletLand]) cylinder(h=cone,r1=inlet/2,r2=D/2);
 translate([0,0,inletLand+cone-.01]) cylinder(h=outletLand+.02,r=D/2); }}
''')
import gmsh,trimesh
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('AA_stock_source_nozzle');occ=gmsh.model.occ
def solid(extra):
 r0=.004+extra;r1=d/2000+extra;c0=occ.addCylinder(0,0,0,0,0,.015,r0);c1=occ.addCone(0,0,.015,0,0,cone/1000,r0,r1);c2=occ.addCylinder(0,0,(cone+15)/1000,0,0,.01,r1);return occ.fuse([(3,c0)],[(3,c1),(3,c2)])[0]
outer=solid(.002);inner=solid(0);occ.cut(outer,inner);occ.synchronize()
sys.path.insert(0,str(ROOT/'scripts'));from generate_designs import write_step_metres
write_step_metres(cad/'nozzle-flow-body.step');gmsh.option.setNumber('Mesh.MeshSizeMin',.0007);gmsh.option.setNumber('Mesh.MeshSizeMax',.002);gmsh.model.mesh.generate(2);gmsh.write(str(cad/'nozzle-metres.stl'));gmsh.finalize();mesh=trimesh.load_mesh(cad/'nozzle-metres.stl',process=True);mesh.fix_normals(multibody=True);mesh.apply_scale(1000);mesh.export(cad/'nozzle-print-mm.stl')
assert mesh.is_watertight and mesh.is_winding_consistent
metadata={'selected_case':selected['case'],'inlet_bore_mm':8,'outlet_bore_mm':d,'half_angle_deg':angle,'total_length_mm':length,'wall_radial_mm':2,'STL_units':'millimetres','STEP_units':'metres','watertight':bool(mesh.is_watertight),'winding_consistent':bool(mesh.is_winding_consistent),'connected_components':len(mesh.split()),'volume_mm3':float(mesh.volume),'fitted_adapter_verified':False,'pressure_rating_established':False,'status':'Printable low-pressure flow body. Confirm actual stock source bore/thread, adapter and installation. Not a complete fitted assembly.'};(cad/'cad-verification.json').write_text(json.dumps(metadata,indent=2))
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig=plt.figure(figsize=(10,4.8));ax=fig.add_subplot(111,projection='3d');tris=mesh.vertices[mesh.faces];normals=mesh.face_normals;light=np.array([.7,-.5,.6]);light/=np.linalg.norm(light);lum=.5+.5*np.maximum(normals@light,0);colors=np.clip(np.array([.25,.56,.70])[None,:]*lum[:,None]+.12,0,1);ax.add_collection3d(Poly3DCollection(tris,facecolors=colors,edgecolors='none'));ax.set(xlim=(-d,d),ylim=(-d,d),zlim=(0,length));ax.set_box_aspect((2*d,2*d,length));ax.view_init(elev=16,azim=-45);ax.set_axis_off();fig.suptitle(f'Custom flow body · 8 → {d:g} mm · {angle:g}° half angle · {length:.1f} mm long',fontsize=14);fig.text(.5,.035,'Actual generated CAD. Stock source, fitted adapter and mounting hardware remain separate.',ha='center',fontsize=10);fig.savefig(OUT/'nozzle-cad.png',dpi=170);plt.close(fig)
print(json.dumps(metadata,indent=2))
