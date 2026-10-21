"""Unconfined four-outlet CFD screen. Virtual moving probes; no human body.

The old solver setup is reused, never its seat mesh or seat temperature results.
"""
from pathlib import Path
import sys, json, math, time, subprocess, argparse
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'motor-seat-study/cfd/scripts'))
import seat_cfd as base

STUDY = ROOT/'pass-by-study'
CASES = STUDY/'cfd/cases'
IMAGE = base.IMAGE
PA, GAS, CP = 101325., 8314.46261815324/28.965, 1006.
OUTLET_WIDTH, OUTLET_HEIGHT = .14, .08

def outlets(layout, distance):
    """Distances refer to nominal near-side sampling plane, not measured reach."""
    result=[]
    w,h=OUTLET_WIDTH,OUTLET_HEIGHT
    if layout=='one-row':
        for x in [-.60,-.20,.20,.60]:
            y=-.20-distance;z=1.15
            result.append(dict(box=[[x-w/2,x+w/2],[y-.04,y],[z-h/2,z+h/2]],direction=3))
    elif layout=='one-side':
        for x in [-.20,.20]:
            for z in [1.15,1.55]:
                y=-.20-distance
                result.append(dict(box=[[x-w/2,x+w/2],[y-.04,y],[z-h/2,z+h/2]],direction=3))
    elif layout=='two-side':
        for sign in [-1,1]:
            for z in [1.15,1.55]:
                y=sign*(.20+distance)
                result.append(dict(box=[[-w/2,w/2],[y-.04,y] if sign<0 else [y,y+.04],[z-h/2,z+h/2]],direction=3 if sign<0 else 2))
    elif layout=='overhead':
        for x in [-.20,.20]:
            for y in [-.06,.06]:
                z=1.75+distance
                result.append(dict(box=[[x-w/2,x+w/2],[y-h/2,y+h/2],[z,z+.04]],direction=4))
    else: raise ValueError(layout)
    for i,row in enumerate(result): row['name']='jet'+str(i)
    return result

def axis(bounds, fine_interval, h, extra):
    knots=sorted(set([*bounds,*fine_interval,*extra]))
    coords=[]
    for a,b in zip(knots,knots[1:]):
        step=h if fine_interval[0]-1e-9 <= (a+b)/2 <= fine_interval[1]+1e-9 else h*2
        # At least two cells span each outlet edge, even in the coarse screen.
        if any(abs(b-a-w)<1e-8 for w in [.04,.08,.14]): step=min(step,(b-a)/2)
        coords.extend(np.linspace(a,b,max(1,math.ceil((b-a)/step))+1)[:-1])
    return np.array(coords+[knots[-1]])

def generate_mesh(case,layout,distance,h=.065):
    nozzles=outlets(layout,distance)
    fine_x=max(.65,max(abs(v) for n in nozzles for v in n['box'][0])+.08)
    xs=axis([-1.25,1.25],[-fine_x,fine_x],h,[v for n in nozzles for v in n['box'][0]])
    ys=axis([-1.1,1.1],[-.8,.8],h,[-.2,.2]+[v for n in nozzles for v in n['box'][1]])
    # Keep the artificial fine/coarse transition away from nozzle-top faces.
    # A 1 cm gap at z=2.29..2.30 created small-determinant cells in the 50 cm overhead pilot.
    fine_top=max(2.3,max(n['box'][2][1] for n in nozzles)+.1)
    zs=axis([0,2.7],[1.0,fine_top],h,[v for n in nozzles for v in n['box'][2]])
    nx,ny,nz=[len(a)-1 for a in [xs,ys,zs]]
    X,Y,Z=np.meshgrid((xs[:-1]+xs[1:])/2,(ys[:-1]+ys[1:])/2,(zs[:-1]+zs[1:])/2,indexing='ij')
    occupied=np.zeros(X.shape,bool)
    for n in nozzles:
        b=n['box']; occupied|=(X>b[0][0]-1e-10)&(X<b[0][1]+1e-10)&(Y>b[1][0]-1e-10)&(Y<b[1][1]+1e-10)&(Z>b[2][0]-1e-10)&(Z<b[2][1]+1e-10)
    # z/y/x loop ordering matches global field indices and visualization reshaping.
    indices=np.array([(i,j,k) for k in range(nz) for j in range(ny) for i in range(nx) if not occupied[i,j,k]],int)
    cells={tuple(v):i for i,v in enumerate(indices)}
    centers=np.column_stack([a[idx]+np.diff(a)[idx]/2 for a,idx in zip([xs,ys,zs],indices.T)])
    volumes=np.prod(np.column_stack([np.diff(a)[idx] for a,idx in zip([xs,ys,zs],indices.T)]),axis=1)
    points=np.array([(x,y,z) for z in zs for y in ys for x in xs])
    def vid(i,j,k): return (k*(ny+1)+j)*(nx+1)+i
    def face(i,j,k,d):
        return [[vid(i,j,k),vid(i,j,k+1),vid(i,j+1,k+1),vid(i,j+1,k)],
                [vid(i+1,j,k),vid(i+1,j+1,k),vid(i+1,j+1,k+1),vid(i+1,j,k+1)],
                [vid(i,j,k),vid(i+1,j,k),vid(i+1,j,k+1),vid(i,j,k+1)],
                [vid(i,j+1,k),vid(i,j+1,k+1),vid(i+1,j+1,k+1),vid(i+1,j+1,k)],
                [vid(i,j,k),vid(i,j+1,k),vid(i+1,j+1,k),vid(i+1,j,k)],
                [vid(i,j,k+1),vid(i+1,j,k+1),vid(i+1,j+1,k+1),vid(i,j+1,k+1)]][d]
    directions=[(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]
    patches={p:[] for p in ['xmin','xmax','ymin','ymax','top','ground','nozzleWalls']+[n['name'] for n in nozzles]}
    interior=[]
    for (i,j,k),owner in cells.items():
        for d,(di,dj,dk) in enumerate(directions):
            neighbor=cells.get((i+di,j+dj,k+dk)); f=face(i,j,k,d)
            if neighbor is not None:
                if owner<neighbor: interior.append((f,owner,neighbor))
                continue
            if d==0 and i==0: patch='xmin'
            elif d==1 and i==nx-1: patch='xmax'
            elif d==2 and j==0: patch='ymin'
            elif d==3 and j==ny-1: patch='ymax'
            elif d==4 and k==0: patch='ground'
            elif d==5 and k==nz-1: patch='top'
            else:
                q=points[f].mean(axis=0)+np.array([di,dj,dk])*1e-6
                n=next(n for n in nozzles if base.in_box(q,n['box']))
                # Face outward normal from FLUID is opposite the nozzle outlet direction.
                patch=n['name'] if d==(n['direction']^1) else 'nozzleWalls'
            patches[patch].append((f,owner))
    patches={p:v for p,v in patches.items() if v}
    allfaces=[v[0] for v in interior];owners=[v[1] for v in interior];neighbors=[v[2] for v in interior]
    boundary=[];metadata={};areas={}
    for patch,rows in patches.items():
        start=len(allfaces);allfaces.extend(r[0] for r in rows);owners.extend(r[1] for r in rows)
        typ='wall' if patch in ['ground','nozzleWalls'] else 'patch'
        boundary.append(f'{patch} {{ type {typ}; nFaces {len(rows)}; startFace {start}; }}')
        data=[]
        for f,owner in rows:
            pts=points[f];area=np.linalg.norm(np.cross(pts[1]-pts[0],pts[3]-pts[0]));data.append([owner,*pts.mean(axis=0),area])
        metadata[patch]=np.array(data);areas[patch]=float(metadata[patch][:,-1].sum())
    used=sorted(set(v for f in allfaces for v in f));remap={v:i for i,v in enumerate(used)}
    put=base.put
    put(case,'constant/polyMesh/points',str(len(used))+'\n(\n'+'\n'.join('('+' '.join(f'{x:.12g}' for x in points[v])+')' for v in used)+'\n)','vectorField')
    put(case,'constant/polyMesh/faces',str(len(allfaces))+'\n(\n'+'\n'.join('4('+' '.join(str(remap[v]) for v in f)+')' for f in allfaces)+'\n)','faceList')
    for name,arr in [('owner',owners),('neighbour',neighbors)]: put(case,'constant/polyMesh/'+name,str(len(arr))+'\n(\n'+'\n'.join(map(str,arr))+'\n)','labelList')
    put(case,'constant/polyMesh/boundary',str(len(boundary))+'\n(\n'+'\n'.join(boundary)+'\n)','polyBoundaryMesh')
    np.savez_compressed(case/'mesh-metadata.npz',centers=centers,volumes=volumes,x=xs,y=ys,z=zs,indices=indices)
    np.savez_compressed(case/'boundary-metadata.npz',**metadata)
    assert all(abs(areas[n['name']]-OUTLET_WIDTH*OUTLET_HEIGHT)<1e-9 for n in nozzles)
    return patches,areas,len(indices)

def probe_points(case):
    """Fixed world-space lines support quadrature over moving 5 cm squares."""
    x=np.linspace(-.825,.825,166)
    g,w=np.polynomial.legendre.leggauss(3);offset=g*.025
    lines=[];points=[]
    for sign in [-1,1]:
        for height in [1.15,1.55]:
            row=dict(name=('left' if sign<0 else 'right')+str(height),plane='xz',y=sign*.2,z=height,indices=[])
            for off in offset:
                row['indices'].append(list(range(len(points),len(points)+len(x))))
                points.extend([[float(xx),sign*.2,height+off] for xx in x])
            lines.append(row)
    row=dict(name='top1.75',plane='xy',y=0,z=1.75,indices=[])
    for off in offset:
        row['indices'].append(list(range(len(points),len(points)+len(x))))
        points.extend([[float(xx),float(off),1.75] for xx in x])
    lines.append(row)
    (case/'probe-metadata.json').write_text(json.dumps(dict(x=x.tolist(),quadrature_offsets_m=offset.tolist(),quadrature_weights=(w/2).tolist(),lines=lines,points=len(points)),indent=2))
    return points

def build(name,layout='one-side',distance=.2,h=.065,end=30,wind=0,source_c=None,rest=False,width=.14,height=.08,wind_direction='front',pitch_deg=0):
    global OUTLET_WIDTH,OUTLET_HEIGHT
    OUTLET_WIDTH,OUTLET_HEIGHT=width,height
    base.CFD=STUDY/'cfd';base.STUDY=STUDY
    budget=json.loads((STUDY/'results/timing-and-energy.json').read_text())['source_budget']
    base.MASS=budget['mass_kg_s']
    base.geometry=lambda: outlets(layout,distance)
    base.generate_mesh=lambda case,*a,**k: generate_mesh(case,layout,distance,h)
    if source_c is None:
        source_c=budget['supply_c']
    direction='side' if wind_direction in ['cross','opposed'] else 'front'
    case=base.build(name,'open-jets',h,end,wind,direction,source_c,30,0,0,False,True)
    if wind and wind_direction=='opposed':
        # Reverse the ambient wind and swap the upwind far-field velocity/pressure patches.
        for fld in ['U','p_rgh']:
            fp=case/'0'/fld;t=fp.read_text();t=t.replace(f'(0,{wind},0)',f'(0,{-wind},0)')
            t=t.replace(f'(0 {wind} 0)',f'(0 {-wind} 0)').replace(f'(0 {wind:g} 0)',f'(0 {-wind:g} 0)')
            t=t.replace('ymin {','__swap__ {').replace('ymax {','ymin {').replace('__swap__ {','ymax {');fp.write_text(t)
    info=json.loads((case/'case.json').read_text())
    if pitch_deg:
        assert layout in ['one-side','one-row','two-side']
        import re
        u=(case/'0/U').read_text();normal=info['source_mean_speed_m_s'];vertical=normal*math.tan(math.radians(pitch_deg))
        for nozzle in outlets(layout,distance):
            sign=1 if nozzle['direction']==3 else -1
            u=re.sub(r'\b'+nozzle['name']+r'\s*\{[^}]*\}',nozzle['name']+f' {{ type fixedValue; value uniform (0 {sign*normal:.12g} {vertical:.12g}); }}',u)
        (case/'0/U').write_text(u)
        info['source_mean_speed_m_s']=normal/math.cos(math.radians(pitch_deg))
        info['pitch_test_note']='Oblique prescribed velocity on vertical slot patches; not resolved tilted-CAD faces. Same nominal normal mass flux; actual mass checked. Total velocity increases by 1/cos(pitch).'
    info.update(layout=layout,nominal_standoff_m=distance,outlet_width_m=width,outlet_height_m=height,wind_direction=wind_direction,pitch_deg=pitch_deg,
                implied_total_motor_plus_path_heat_w=budget['shaft_work_w']-budget['mass_kg_s']*CP*(budget['inlet_c']-source_c),
                source_reference_distance='Side: nozzle to y=+/-0.2 m plane; overhead: nozzle to z=1.75 m plane.',
                scope='Unconfined pulsed-jet screen with virtual walking air probes. No person, seat, walls, enclosure or human cooling claim.',
                model='Dry ideal-gas buoyant URANS k-epsilon; ground and short nozzle blocks only; no body heat or body obstruction.',
                body_regions={},person_heat_w=0,domain_m=[[-1.25,1.25],[-1.1,1.1],[0,2.7]],
                valve_model=f'Ideal constant nominal cold outlet flow from t=0 to end={end:g} s, within the 30 s activation limit. Upstream valve delay, line cooling and motor spin-up NOT resolved.',
                limitations=['No human blockage, wake or heat transfer','No actual nozzle interior/profile or stock flow-network coupling','Coarse Cartesian jet screen; grid/domain/turbulence sensitivity needed','Uniform 5% inlet turbulence hypothesis','Mounting heights and nominal path are engineering assumptions','Different layouts target different incident body regions; air-probe results are not body comfort scores'])
    # Fix the wall-function boundary for a nozzle wall: its name must not begin with jet.
    ctrl=case/'system/controlDict';s=ctrl.read_text().replace('patches (person panels seat ground)','patches (nozzleWalls ground)')
    s=s.replace('maxCo 1;','maxCo .7;').replace('maxDeltaT .04;','maxDeltaT .025;')
    pts=probe_points(case)
    block='airProbes { type probes; libs (sampling); interpolationScheme cellPoint; fixedLocations yes; fields (T U); writeControl runTime; writeInterval .025; probeLocations (\n'+'\n'.join('('+' '.join(f'{a:.8g}' for a in q)+')' for q in pts)+'\n); }\n'
    # controlDict's final brace closes functions.
    at=s.rfind('}');s=s[:at]+block+s[at:];ctrl.write_text(s)
    if rest:
        info.update(source_mass_kg_s=0,source_c=30,source_mean_speed_m_s=0,scope='Hydrostatic rest validation; no source, body, wind or heat.')
        for name in ['U','T','origin']:
            fp=case/'0'/name;t=fp.read_text()
            if name=='U':
                import re
                t=re.sub(r'massFlowRate [^;]+;','massFlowRate 0;',t)
            elif name=='T': t=t.replace(f'value uniform {source_c+273.15};','value uniform 303.15;')
            else: t=t.replace('type fixedValue; value uniform 1;','type fixedValue; value uniform 0;')
            fp.write_text(t)
    (case/'case.json').write_text(json.dumps(info,indent=2));return case

def docker(case,args):
    return ['docker','run','--rm','--name','aa-passby-'+case.name.lower().replace('_','-'),'--entrypoint','/bin/bash','-v',f'{ROOT}:/work','-w',f'/work/pass-by-study/cfd/cases/{case.name}',IMAGE,'/work/scripts/foam-entry.sh',*args]

def run(case):
    state=dict(status='running',started=time.time(),image=IMAGE)
    (case/'run-status.json').write_text(json.dumps(state,indent=2))
    jobs=[(['checkMesh','-allGeometry','-allTopology'],'log.checkMesh'),(['decomposePar','-force'],'log.decomposePar'),(['mpirun','--allow-run-as-root','-np','4','buoyantPimpleFoam','-parallel'],'log.solver'),(['reconstructPar'],'log.reconstructPar')]
    try:
        for args,log in jobs:
            with (case/log).open('w') as out: rc=subprocess.run(docker(case,args),stdout=out,stderr=subprocess.STDOUT).returncode
            if rc: raise RuntimeError(f'{args[0]} failed: {case/log}')
            if args[0]=='checkMesh' and 'Mesh OK.' not in (case/log).read_text(): raise RuntimeError('Mesh not accepted')
        state['status']='solver ended; audit pending'
    except Exception as e: state.update(status='failed',error=str(e));raise
    finally:
        state['elapsed_s']=time.time()-state['started'];(case/'run-status.json').write_text(json.dumps(state,indent=2))
    print(json.dumps(state),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--layout',default='one-side',choices=['one-side','two-side','overhead','one-row']);p.add_argument('--distance',type=float,default=.2);p.add_argument('--h',type=float,default=.065);p.add_argument('--end',type=float,default=10);p.add_argument('--wind',type=float,default=0);p.add_argument('--source',type=float);p.add_argument('--pitch',type=float,default=0);p.add_argument('--wind-direction',choices=['front','cross','opposed'],default='front');p.add_argument('--width',type=float,default=.14);p.add_argument('--height',type=float,default=.08);p.add_argument('--rest',action='store_true');p.add_argument('--run',action='store_true');a=p.parse_args()
    case=build(a.name,a.layout,a.distance,a.h,a.end,a.wind,source_c=a.source,rest=a.rest,width=a.width,height=a.height,wind_direction=a.wind_direction,pitch_deg=a.pitch);print(case,flush=True)
    if a.run: run(case)
