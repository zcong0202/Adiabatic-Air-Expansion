"""Static layout geometry only. No powered coupling or pressure parts exported."""
from pathlib import Path
import json
import math
import zipfile
import numpy as np
import trimesh as tm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT=Path(__file__).resolve().parent


def box(size, at):
    m=tm.creation.box(size);m.apply_translation(at);return m


def cyl(radius, height, at, axis='z'):
    m=tm.creation.cylinder(radius=radius,height=height,sections=48)
    if axis=='x':m.apply_transform(tm.transformations.rotation_matrix(math.pi/2,[0,1,0]))
    m.apply_translation(at);return m


def union(meshes):return tm.boolean.union(meshes,engine='manifold')
def diff(a,b):return tm.boolean.difference([a,*b],engine='manifold')


def build():
    # All hardware dimensions here are placeholders, not AM0701 measurements.
    base=box([300,180,8],[150,0,-4])
    holes=[box([14,5.5,12],[x,y,-4]) for x in [30,100,190,275] for y in [-60,60]]
    base=diff(base,holes+[cyl(2.75,12,[x,60,-4]) for x in [225,245]])
    cradle=union([box([16,100,100],[0,0,50]),box([36,140,8],[0,0,4])])
    cradle=diff(cradle,[cyl(41,30,[0,0,100],'x'),*[cyl(2.75,12,[0,y,4]) for y in [-60,60]]])
    blank=union([box([12,70,100],[0,0,50]),box([36,140,8],[0,0,4])])
    blank=diff(blank,[cyl(2.75,12,[0,y,4]) for y in [-60,60]])
    adapter=union([box([12,34,110],[0,0,55]),box([36,60,8],[0,0,4])])
    adapter=diff(adapter,[cyl(2.75,12,[x,0,4]) for x in [-10,10]])
    parts={'01-base-FIT-ONLY':base,'02-cradle-EXAMPLE-80mm-body':cradle,
           '03-bearing-support-BLANK':blank,'04-brake-adapter-BLANK':adapter}
    checks=[]
    for name,m in parts.items():
        assert m.is_watertight and m.is_volume and m.volume>0,name
        m.export(OUT/(name+'.stl'))
        checks.append(dict(name=name,watertight=bool(m.is_watertight),volume_mm3=float(m.volume),bounds_mm=m.extents.tolist()))
    scene=[]
    def add(m,color,alpha=1):scene.append((m,color,alpha))
    add(base,'#c7cbd0')
    for x in [30,100]:
        m=cradle.copy();m.apply_translation([x,0,0]);add(m,'#718c9b')
    for x in [190,275]:
        m=blank.copy();m.apply_translation([x,0,0]);add(m,'#a5b8c1')
    m=adapter.copy();m.apply_translation([235,60,0]);add(m,'#a5b8c1')
    add(cyl(40,110,[68,0,100],'x'),'#7b8288',.18)
    add(cyl(6,48,[132,0,100],'x'),'#4b5055',.35)
    add(cyl(6,116,[229,0,100],'x'),'#4b5055',.35)
    add(cyl(18,34,[160,0,100],'x'),'#1a7899',.5) # envelope, no coupling STL
    add(cyl(80,3,[235,0,100],'x'),'#a97135',.22)
    fig=plt.figure(figsize=(13.5,7.5),facecolor='white');ax=fig.add_subplot(111,projection='3d')
    for m,c,a in scene:
        ax.add_collection3d(Poly3DCollection(m.triangles,facecolors=c,edgecolors='none',alpha=a))
    ax.set_xlim(-10,315);ax.set_ylim(-100,100);ax.set_zlim(-10,185)
    ax.set_box_aspect((325,200,195));ax.view_init(elev=22,azim=-58)
    ax.set_xlabel('Layout x (mm)');ax.set_ylabel('Layout y (mm)');ax.set_zlabel('Height (mm)')
    ax.text(64,0,151,'Motor envelope\nNOT MEASURED',ha='center',fontsize=9)
    fig.text(.5,.845,'Blue sleeve = spacing envelope only; no powered coupler supplied.',ha='center',fontsize=11,color='#12647d')
    ax.text(262,65,165,'160 mm disc envelope\nBrake not selected',ha='center',fontsize=9,color='#895b24')
    fig.suptitle('Motor + brake: static fit-check layout',fontsize=20,y=.96)
    fig.text(.5,.895,'Example dimensions. No pressure fittings. No powered-use rating.',ha='center',fontsize=12)
    fig.text(.5,.025,'Regulated supply required. Do not connect the AM0701 directly to a scuba cylinder.',ha='center',fontsize=12,color='#963c31')
    fig.savefig(OUT/'layout-preview.png',dpi=170,bbox_inches='tight');plt.close(fig)
    status={'date':'2026-11-11','status':'Static fit-check concept only; not fitted or powered-use CAD.',
            'actual_measurements':{'motor_body_diameter_mm':None,'motor_mount_pattern_mm':None,
                                   'motor_shaft_diameter_mm':None,'motor_shaft_usable_length_mm':None,
                                   'shaft_key_flat_thread':None,'brake_model':None,'bearing_dimensions':None},
            'example_geometry_only':{'base_mm':[300,180,8],'motor_body_diameter_mm':80,'shaft_axis_height_mm':100,
                                     'disc_diameter_mm':160,'coupler_envelope_diameter_mm':36,'coupler_envelope_length_mm':34},
            'files':checks,'coupler_stl_exported':False,
            'coupler_status':'Envelope shown for layout; no torque-transmitting coupler released without measured interfaces and mechanical/thermal validation.',
            'mesh_validation':'Closed positive-volume meshes only. Does not establish fit, strength, heat resistance, balance, speed rating or containment.',
            'pressure_source':'https://www.cosmostar.net/product/air-motor-and-agitator/255-am0701-0-9-hp-air-operated-vane-type-air-motor',
            'published_motor_pressure_bar':[1,7],'reference_tank_bar':200,
            'pressure_decision':'No regulator bypass. Use pressure control/protection and qualified full-flow supply within actual nameplate limits.',
            'open_items':['Exact measured hardware interfaces','Brake type and bearing geometry','Regulated inlet pressure/flow point','Printed load-path and coupler validation; hot brake isolation; guarding']}
    (OUT/'manifest.json').write_text(json.dumps(status,indent=2)+'\n')
    with zipfile.ZipFile(OUT/'static-fit-layout.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()):
            if p.suffix in ['.stl','.scad','.json','.md','.py','.png']:z.write(p,p.name)
    print(json.dumps(status,indent=2))


if __name__=='__main__':build()
