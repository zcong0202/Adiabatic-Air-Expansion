"""Audit completed native CFD and sample moving 5 x 5 cm air patches.

The moving probes do not model a moving human obstacle or human heat removal.
"""
from pathlib import Path
import json, sys, re, hashlib
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from open_flow import ROOT, STUDY, CASES, CP, GAS, PA
from audit_seat import arr, patchvalue
from boundary_balance import values

def probes(case,field,n):
    paths=sorted((case/'postProcessing/airProbes').glob('*/'+field),key=lambda p:float(p.parent.name))
    assert len(paths)==1, paths
    lines=[line for line in paths[0].read_text().splitlines() if line.strip() and not line.startswith('#')]
    flat=np.fromstring(' '.join(lines).replace('(',' ').replace(')',' '),sep=' ')
    cols=1+n*(3 if field=='U' else 1)
    assert len(flat)%cols==0
    mat=flat.reshape(-1,cols); assert (np.diff(mat[:,0])>0).all()
    return mat[:,0],mat[:,1:].reshape(len(mat),n,3) if field=='U' else mat[:,1:]

def threshold_lengths(times,deficit,threshold=6.):
    total=0.;longest=0.;current=0.
    for i in range(len(times)-1):
        dt=times[i+1]-times[i];a=deficit[i]-threshold;b=deficit[i+1]-threshold
        if a>0 and b>0: total+=dt;current+=dt;longest=max(longest,current)
        elif a<=0 and b>0:
            length=dt*b/(b-a);total+=length;current=length;longest=max(longest,current)
        elif a>0 and b<=0:
            length=dt*a/(a-b);total+=length;current+=length;longest=max(longest,current);current=0.
        else: current=0.
    return float(total),float(longest)

def sample_passages(case,ta):
    meta=json.loads((case/'probe-metadata.json').read_text());n=meta['points']
    times,T=probes(case,'T',n);utimes,U=probes(case,'U',n);assert np.array_equal(times,utimes)
    assert np.isfinite(T).all() and np.isfinite(U).all()
    assert 250<T.min()<400 and T.max()<400
    gap=float(np.diff(times).max());assert gap<.08
    # Native probes first write after t=0. Add the known initial rest atmosphere.
    if times[0]>0:
        times=np.r_[0,times];T=np.vstack([np.full(n,ta+273.15),T]);U=np.concatenate([np.zeros((1,n,3)),U])
    speed=np.linalg.norm(U,axis=2);x=np.array(meta['x']);weights=np.array(meta['quadrature_weights']);offsets=np.array(meta['quadrature_offsets_m'])
    lines={}
    for line in meta['lines']:
        temperatures=[];velocities=[]
        for inds in line['indices']:
            temperatures.append(RegularGridInterpolator((times,x),T[:,inds]-273.15,bounds_error=True))
            velocities.append(RegularGridInterpolator((times,x),speed[:,inds],bounds_error=True))
        lines[line['name']]=(temperatures,velocities)
    result=[];traces={}
    arrivals=[1.5,5.,8.5] if times[-1]<=10.001 else [1.5,5.,15.,28.5]
    for v in [.6,1.2,1.8]:
        for center in arrivals:
            begin=center-.8/v;end=center+.8/v
            t=np.linspace(begin,end,max(2,int(np.ceil((end-begin)/.005))+1));xx=(t-center)*v
            assert begin>=times[0] and end<=times[-1], (begin,end,times[-1])
            for name,(temp,vel) in lines.items():
                tt=np.zeros(len(t));uu=np.zeros(len(t))
                for j,wz in enumerate(weights):
                    for dx,wx in zip(offsets,weights):
                        points=np.column_stack([t,xx+dx]);tt+=wz*wx*temp[j](points);uu+=wz*wx*vel[j](points)
                deficit=ta-tt;above,longest=threshold_lengths(t,deficit)
                error_sensitivity={str(e):dict(zip(['total_s','longest_s'],threshold_lengths(t,deficit,6+e))) for e in [0,1,2,3]}
                key=f'{name}_v{v}_t{center}'
                traces[key]={'time_s':t.tolist(),'path_x_m':xx.tolist(),'area_temperature_c':tt.tolist(),'area_speed_m_s':uu.tolist()}
                result.append(dict(patch=name,walking_speed_m_s=v,center_crossing_s=center,
                                   complete_path_window_s=[begin,end],patch_side_m=.05,
                                   peak_area_deficit_k=float(deficit.max()),minimum_area_temperature_c=float(tt.min()),
                                   time_above_delta6_s=above,longest_continuous_above_delta6_s=longest,
                                   assumed_upward_temperature_error_k_sensitivity=error_sensitivity,
                                   positive_deficit_dose_k_s=float(np.trapezoid(np.maximum(deficit,0),t)),
                                   peak_area_mean_speed_m_s=float(uu.max()),mean_area_temperature_c=float(np.trapezoid(tt,t)/(end-begin))))
    (case/'moving-probe-traces.json').write_text(json.dumps(traces,separators=(',',':')))
    return result,dict(native_probe_interval_max_s=gap,native_probe_count=n,probe_interpolation='OpenFOAM cellPoint; linear time and along-path interpolation; 3x3 Gauss quadrature over moving 5 cm square',walking_trace_step_max_s=.005,body_blockage_included=False)

def audit(case,do_probes=True):
    info=json.loads((case/'case.json').read_text());state=json.loads((case/'run-status.json').read_text())
    assert state['status'].startswith('solver ended'),state
    ctrl=(case/'system/controlDict').read_text();end=float(re.search(r'\bendTime\s+([^;]+)',ctrl).group(1))
    dirs=sorted([p for p in case.iterdir() if p.is_dir() and re.fullmatch(r'[0-9.]+',p.name) and (p/'T').exists()],key=lambda p:float(p.name))
    assert abs(float(dirs[-1].name)-end)<1e-6
    mesh=np.load(case/'mesh-metadata.npz');centers=mesh['centers'];vol=mesh['volumes'];n=len(vol);boundary=np.load(case/'boundary-metadata.npz');rows=[]
    hashes={}
    for path in dirs:
        T=arr(path/'T',n);U=arr(path/'U',n,True);p=arr(path/'p',n)
        rho=arr(path/'rho',n) if (path/'rho').exists() else p/(GAS*T)
        origin=arr(path/'origin',n) if (path/'origin').exists() else np.zeros(n)
        h=arr(path/'h',n) if (path/'h').exists() else CP*T
        assert all(np.isfinite(a).all() for a in [T,U,rho,origin,p,h])
        row=dict(time_s=float(path.name),temperature_min_c=float(T.min()-273.15),temperature_max_c=float(T.max()-273.15),
                 speed_max_m_s=float(np.linalg.norm(U,axis=1).max()),origin_min=float(origin.min()),origin_max=float(origin.max()),
                 mass_kg=float(np.dot(rho,vol)),origin_kg=float(np.dot(rho*origin,vol)),
                 energy_j=float(np.dot(rho*(h+.5*np.sum(U**2,axis=1)+9.81*centers[:,2])-p,vol)))
        if (path/'phi').exists():
            ff=(path/'phi').read_text();ht=(path/'h').read_text() if (path/'h').exists() else None;ot=(path/'origin').read_text();flux={}
            for patch in boundary.files:
                if patch in ['nozzleWalls','ground']: continue
                b=boundary[patch];owners=b[:,0].astype(int);phi=values(ff,patch,len(b));hh=patchvalue(ht,patch,owners,h) if ht else CP*patchvalue((path/'T').read_text(),patch,owners,T)
                oo=patchvalue(ot,patch,owners,origin);kin=.5*np.sum(U[owners]**2,axis=1)
                if patch.startswith('jet'): kin[:]=.5*info['source_mean_speed_m_s']**2
                flux[patch]=dict(mass_kg_s=float(phi.sum()),origin_kg_s=float(np.dot(phi,oo)),energy_w=float(np.dot(phi,hh+kin+9.81*b[:,3])))
            row['flux']=flux;row['source_mass_kg_s']=-sum(f['mass_kg_s'] for patch,f in flux.items() if patch.startswith('jet'))
        rows.append(row);hashes[path.name]=hashlib.sha256((path/'T').read_bytes()).hexdigest()
    valid=[r for r in rows if 'flux' in r and r['time_s']>=max(1,end-5)]
    times=np.array([r['time_s'] for r in valid]);duration=times[-1]-times[0];mass=info['source_mass_kg_s'];cooling=mass*CP*(info['ambient_c']-info['source_c']);balances={}
    for inventory,flux,key,norm in [('mass_kg','mass_kg_s','mass',mass*duration),('origin_kg','origin_kg_s','origin',mass*duration),('energy_j','energy_w','energy',cooling*duration)]:
        residual=valid[-1][inventory]-valid[0][inventory]+np.trapezoid([sum(f[flux] for f in r['flux'].values()) for r in valid],times)
        balances[key+'_relative_error']=float(residual/max(norm,1e-12))
    gates=dict(mesh_ok='Mesh OK.' in (case/'log.checkMesh').read_text(),solver_complete='\nEnd\n' in (case/'log.solver').read_text() and 'FOAM FATAL' not in (case/'log.solver').read_text(),
               finite_fields=True,temperature_bounds=all(r['temperature_min_c']>-23.15 and r['temperature_max_c']<126.85 for r in rows),
               origin_bounds=all(r['origin_min']>-.005 and r['origin_max']<1.005 for r in rows),
               source_mass=all(abs(r.get('source_mass_kg_s',mass)-mass)<max(.0001,.005*mass) for r in rows),
               mass_closure=abs(balances['mass_relative_error'])<.03,origin_closure=abs(balances['origin_relative_error'])<.05,energy_closure=abs(balances['energy_relative_error'])<.08)
    passages,metadata=sample_passages(case,info['ambient_c']) if do_probes else ([],{})
    # A fixed upper-body-height air band prevents optimising only one narrow spot.
    native=case/'5';band={}
    if (native/'T').exists():
        idx=mesh['indices'];axes=[(mesh[k][:-1]+mesh[k][1:])/2 for k in ['x','y','z']]
        grid=np.full((len(axes[2]),len(axes[1]),len(axes[0])),np.nan)
        tt=arr(native/'T',n)-273.15;grid[idx[:,2],idx[:,1],idx[:,0]]=tt
        interpolate=RegularGridInterpolator((axes[2],axes[1],axes[0]),grid,bounds_error=True)
        x=-.8+(np.arange(320)+.5)*1.6/320;z=1.+(np.arange(140)+.5)*.7/140;xx,zz=np.meshgrid(x,z)
        samples=interpolate(np.column_stack([zz.ravel(),np.full(xx.size,-.2),xx.ravel()]))
        deficit=info['ambient_c']-samples;cellarea=(1.6/320)*(.7/140)
        band=dict(time_s=5,plane='y=-0.2 m; x=-0.8..0.8 m; z=1.0..1.7 m; no body',
                  area_m2=1.12,mean_air_c=float(samples.mean()),
                  area_above_delta6_m2=float((deficit>6).sum()*cellarea),
                  positive_deficit_area_k_m2=float(np.maximum(deficit,0).sum()*cellarea))
    data=dict(case=info,gates=gates,numerical_screens_pass=all(gates.values()),conservation=balances,
              conservation_note='Trapezoid of 1 s native fields over last 5 s. Includes pressure work and gravity. Open-boundary diffusion and exact boundary kinetic face interpolation omitted; engineering screen, not rigorous error bound.',
              history=rows,passages=passages,sampling=metadata,temperature_field_sha256=hashes,incident_air_band_snapshot=band,
              performance_scope='Virtual air sampling only. No moving human, wake, skin heat transfer, comfort or proven physical error bound.')
    (case/'audit.json').write_text(json.dumps(data,indent=2));return data

if __name__=='__main__':
    for name in sys.argv[1:]:
        d=audit(CASES/name);print(json.dumps(dict(case=name,gates=d['gates'],conservation=d['conservation'],passages=len(d['passages']))),flush=True)
        if not d['numerical_screens_pass']:raise SystemExit(1)
