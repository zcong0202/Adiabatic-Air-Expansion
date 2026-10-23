"""Prescribed source DOE. Real 3D buoyant CFD; no motor-map extrapolation."""
from pathlib import Path
import json,sys,re,argparse,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
STUDY=ROOT/'mass-flow-study'
sys.path.insert(0,str(ROOT/'pass-by-study/scripts'))
import open_flow as flow
base=flow.base
PA,GAS,CP=flow.PA,flow.GAS,flow.CP
SOURCE_C=.9592752761779835
AMBIENT_C=30.
IMAGE=base.IMAGE

def spec(mass_g=77,count=4,design='wide',layout='side',h=.065,closure='auto',pitch=0):
    assert math.isfinite(mass_g) and 0<mass_g<=1000 and count in [1,2,4]
    assert design in ['base','wide','adaptive'] and layout in ['side','opposed','overhead']
    assert closure in ['auto','laminar','kEpsilon'] and .01<h<=.1
    width,height={'base':(.14,.08),'wide':(.28,.04)}.get(design,(.28,.04))
    if design=='adaptive':
        # Hold target exit speed at 1.5 m/s, fixed 2:1 aspect ratio.
        rho=PA/(GAS*(SOURCE_C+273.15));area=mass_g/1000/count/(rho*1.5)
        width=math.sqrt(2*area);height=area/width
    dh=2*width*height/(width+height)
    speed=mass_g/1000/count/(PA/(GAS*(SOURCE_C+273.15))*width*height)
    Re=mass_g/1000/count*dh/(width*height*1.8e-5)
    selected=('laminar' if Re<2300 else 'kEpsilon') if closure=='auto' else closure
    return dict(total_g_s=mass_g,outlets=count,per_outlet_g_s=mass_g/count,design=design,layout=layout,width_m=width,height_m=height,exit_speed_m_s=speed,hydraulic_reynolds=Re,closure=selected,transition=2300<=Re<=4000,h_m=h,pitch_deg=pitch)

def geometry(s):
    w,h=s['width_m'],s['height_m'];layout=s['layout'];count=s['outlets'];rows=[]
    if layout=='side':
        coords={1:[(0,1.35)],2:[(-.2,1.35),(.2,1.35)],4:[(-.2,1.15),(.2,1.15),(-.2,1.55),(.2,1.55)]}[count]
        for x,z in coords:rows.append(dict(box=[[x-w/2,x+w/2],[-.59,-.55],[z-h/2,z+h/2]],direction=3))
    elif layout=='opposed':
        assert count==4
        for sign in [-1,1]:
            for z in [1.15,1.55]:
                y=sign*.55;rows.append(dict(box=[[-w/2,w/2],[y-.04,y] if sign<0 else [y,y+.04],[z-h/2,z+h/2]],direction=3 if sign<0 else 2))
    elif layout=='overhead':
        assert count==4
        for x in [-.2,.2]:
            for y in [-.08,.08]:rows.append(dict(box=[[x-w/2,x+w/2],[y-h/2,y+h/2],[2.1,2.14]],direction=4))
    else:raise ValueError(layout)
    for i,n in enumerate(rows):n['name']='jet'+str(i)
    return rows

def build(name,**kwargs):
    s=spec(**kwargs);nozzles=geometry(s)
    flow.OUTLET_WIDTH=s['width_m'];flow.OUTLET_HEIGHT=s['height_m'];flow.outlets=lambda *args:nozzles
    base.MASS=s['total_g_s']/1000;base.CFD=STUDY/'cfd';base.STUDY=STUDY
    base.geometry=lambda:nozzles
    if s['design']=='adaptive' or s['h_m']<.06:
        # Resolve each custom exit height/width with >=2 cells; >=3 in fine checks.
        def adaptive_axis(bounds,fine_interval,h,extra):
            knots=sorted(set([*bounds,*fine_interval,*extra]));coords=[];mincells=3 if h<.06 else 2
            for a,b in zip(knots,knots[1:]):
                step=h if fine_interval[0]-1e-9<=(a+b)/2<=fine_interval[1]+1e-9 else h*2
                if min(s['width_m'],s['height_m'])/mincells<.01:
                    inside=fine_interval[0]-1e-9<=(a+b)/2<=fine_interval[1]+1e-9
                    step=min(step,(.04 if inside else .035) if h<.06 else .055)
                if any(abs(b-a-d)<1e-8 for d in [.04,s['width_m'],s['height_m']]):step=min(step,(b-a)/mincells)
                coords.extend(np.linspace(a,b,max(1,math.ceil((b-a)/step))+1)[:-1])
            return np.array(coords+[knots[-1]])
        flow.axis=adaptive_axis
    base.generate_mesh=lambda case,*args,**kw:flow.generate_mesh(case,'unused',.35,s['h_m'])
    case=base.build(name,'outdoor-mass-sweep',s['h_m'],10,0,'front',SOURCE_C,AMBIENT_C,0,0,False,True)
    # External nozzle blocks are solid; the internal loft is not resolved.
    ctrl=case/'system/controlDict';text=ctrl.read_text().replace('patches (person panels seat ground)','patches (nozzleWalls ground)').replace('maxCo 1;','maxCo .7;').replace('maxDeltaT .04;','maxDeltaT .025;')
    # Saving whole-domain integrated mass/tracer/energy each write supplements native audits.
    ctrl.write_text(text)
    if s['closure']=='laminar':base.put(case,'constant/turbulenceProperties','simulationType laminar;')
    # A source-origin passive scalar still needs diffusivity in laminar mode.
    if s['pitch_deg']:
        u=(case/'0/U').read_text();normal=s['exit_speed_m_s'];vertical=normal*math.tan(math.radians(s['pitch_deg']))
        for n in nozzles:
            assert n['direction'] in [2,3]
            sign=1 if n['direction']==3 else -1
            u=re.sub(r'\b'+n['name']+r'\s*\{[^}]*\}',n['name']+f' {{ type fixedValue; value uniform (0 {sign*normal:.12g} {vertical:.12g}); }}',u)
        (case/'0/U').write_text(u)
    info=json.loads((case/'case.json').read_text());info.update(s,mesh_quality_revision='Compact exit axes cap far-field spacing when an outlet-aligned cell edge is below 10 mm; fine exit faces have at least 3 cells.',source_c=SOURCE_C,ambient_c=AMBIENT_C,gravity_m_s2=[0,0,-9.81],wind_m_s=0,spray_s=10,source_mass_kg_s=s['total_g_s']/1000,
      scope='Prescribed cold-air source; total flow split equally across outlets. No person, enclosure, motor internals or measured source qualification.',
      model='Perfect-gas variable-density buoyant transient '+s['closure'],
      source_thermal_status='Fixed at previous CFD 0.959275 C. Changing mass flow does not predict the motor/vortex state.',
      sampling_distances_m=[.2,.35,.5],body_regions={},person_heat_w=0,domain_m=[[-1.25,1.25],[-1.1,1.1],[0,2.7]],
      limitations=['No internal CAD flow or commercial manifold coupling','No human heat transfer or wake','Cold-air volume may be disconnected','Laminar/URANS regime screen; outlet disturbances and transition are unknown','10 seconds ON only; no post-shutoff decay claim','Uniform prescribed boundary; valve startup and pipe cooldown absent'])
    (case/'case.json').write_text(json.dumps(info,indent=2));return case

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--mass',type=float,default=77);p.add_argument('--count',type=int,default=4);p.add_argument('--design',default='wide');p.add_argument('--layout',default='side');p.add_argument('--h',type=float,default=.065);p.add_argument('--closure',default='auto');p.add_argument('--pitch',type=float,default=0);a=p.parse_args();print(build(a.name,mass_g=a.mass,count=a.count,design=a.design,layout=a.layout,h=a.h,closure=a.closure,pitch=a.pitch),flush=True)
