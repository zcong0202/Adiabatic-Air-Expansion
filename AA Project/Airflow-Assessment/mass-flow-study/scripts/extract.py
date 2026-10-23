"""Native-cell cold volumes, exact region overlap and downstream sections."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from build import ROOT,STUDY,PA,GAS,CP
sys.path.insert(0,str(ROOT/'motor-seat-study/cfd/scripts'))
from audit_seat import arr

REGIONS={'domain':[[-1.25,1.25],[-1.1,1.1],[0,2.7]],'walking_corridor':[[-.8,.8],[-.2,.2],[1,1.7]],'upper_body_band':[[-.8,.8],[-.4,.4],[1,1.7]]}

def overlap(mesh,bounds):
    idx=mesh['indices'];v=np.ones(len(idx))
    for k,key in enumerate(['x','y','z']):
        axis=mesh[key];i=idx[:,k];v*=np.maximum(0,np.minimum(axis[i+1],bounds[k][1])-np.maximum(axis[i],bounds[k][0]))
    return v

def section(mesh,grid,distance,info):
    if info['layout']=='overhead':
        normal=2;coord=2.1-distance;a,b='x','y';bounds=[[-.8,.8],[-.2,.2]];description=f'z={coord:.3f} m'
    else:
        normal=1;coord=-.55+distance;a,b='x','z';bounds=[[-.8,.8],[1,1.7]];description=f'y={coord:.3f} m'
    key=['x','y','z'][normal];index=int(np.clip(np.searchsorted(mesh[key],coord,side='right')-1,0,len(mesh[key])-2))
    values=grid[index,:,:] if normal==2 else grid[:,index,:]
    axes=[mesh[a],mesh[b]];da=np.maximum(0,np.minimum(axes[0][1:],bounds[0][1])-np.maximum(axes[0][:-1],bounds[0][0]));db=np.maximum(0,np.minimum(axes[1][1:],bounds[1][1])-np.maximum(axes[1][:-1],bounds[1][0]));area=db[:,None]*da[None,:];valid=np.isfinite(values);total=np.sum(area*valid);drop=info['ambient_c']-np.nan_to_num(values,nan=info['ambient_c'])
    return dict(distance_m=distance,normal_axis=key,coordinate_m=coord,description=description,axes=[a,b],area_m2=float(total),mean_drop_k=float(np.sum(area*drop)/total),area_ge6_m2=float(np.sum(area*(drop>=6))),area_ge2_m2=float(np.sum(area*(drop>=2))),area_ge10_m2=float(np.sum(area*(drop>=10))),peak_cell_drop_k=float(np.nanmax(drop[area>0])),values_c=values.tolist(),axis_a=axes[0].tolist(),axis_b=axes[1].tolist(),cell_containing_plane_index=index)

def voxel_mesh(mesh,cold):
    idx=mesh['indices'];nx,ny,nz=[len(mesh[k])-1 for k in ['x','y','z']];occupied=np.zeros((nz,ny,nx),bool);occupied[idx[:,2],idx[:,1],idx[:,0]]=cold
    # Faces use exact native cell edges. Mesh volume equals summed cold-cell volume.
    vertices=[];faces=[]
    offsets=[(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]
    corners=[[(0,0,0),(0,0,1),(0,1,1),(0,1,0)],[(1,0,0),(1,1,0),(1,1,1),(1,0,1)],[(0,0,0),(1,0,0),(1,0,1),(0,0,1)],[(0,1,0),(0,1,1),(1,1,1),(1,1,0)],[(0,0,0),(0,1,0),(1,1,0),(1,0,0)],[(0,0,1),(1,0,1),(1,1,1),(0,1,1)]]
    for i,j,k in idx[cold]:
        for n,(di,dj,dk) in enumerate(offsets):
            ni,nj,nk=i+di,j+dj,k+dk
            if 0<=ni<nx and 0<=nj<ny and 0<=nk<nz and occupied[nk,nj,ni]:continue
            start=len(vertices);vertices.extend([[float(mesh['x'][i+dx]),float(mesh['y'][j+dy]),float(mesh['z'][k+dz])] for dx,dy,dz in corners[n]]);faces.extend([[start,start+1,start+2],[start,start+2,start+3]])
    return np.array(vertices,float).reshape(-1,3),np.array(faces,int).reshape(-1,3)

def extract(case):
    audit=json.loads((case/'audit.json').read_text());assert audit['numerical_screens_pass'];info=audit['case'];mesh=np.load(case/'mesh-metadata.npz');idx=mesh['indices'];n=len(idx);vol=mesh['volumes'];regionVol={key:overlap(mesh,bounds) for key,bounds in REGIONS.items()};shape=tuple(len(mesh[k])-1 for k in ['z','y','x']);hist=[];hashes={};out=STUDY/'results';out.mkdir(exist_ok=True)
    times=sorted([p for p in case.iterdir() if p.is_dir() and p.name.replace('.','').isdigit() and (p/'T').exists()],key=lambda p:float(p.name))
    assert times and abs(float(times[-1].name)-10)<1e-8,'Native fields must be restored through 10 s before extraction'
    for p in times:
        T=arr(p/'T',n);pressure=arr(p/'p',n);rho=pressure/(GAS*T);origin=arr(p/'origin',n);U=arr(p/'U',n,True);Tc=T-273.15;drop=info['ambient_c']-Tc;grid=np.full(shape,np.nan);grid[idx[:,2],idx[:,1],idx[:,0]]=Tc
        regions={}
        for key,v in regionVol.items():
            regions[key]={str(th):dict(volume_m3=float(np.sum(v[drop>=th])),mass_kg=float(np.sum((rho*v)[drop>=th])),source_mass_kg=float(np.sum((origin*rho*v)[drop>=th])),deficit_j=float(np.sum((rho*v*CP*drop)[drop>=th]))) for th in [2,6,10]}
        sections=[section(mesh,grid,dist,info) for dist in [.2,.35,.5]]
        compact=[{key:val for key,val in s.items() if key not in ['values_c','axis_a','axis_b']} for s in sections]
        hist.append(dict(time_s=float(p.name),regions=regions,sections=compact,min_c=float(Tc.min()),max_speed_m_s=float(np.linalg.norm(U,axis=1).max()),cold_centroid_z_m=float(np.sum((rho*vol*mesh['centers'][:,2])[drop>=6])/np.sum((rho*vol)[drop>=6])) if (drop>=6).any() else None))
        hashes[p.name]={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ['T','p','U','origin']}
    # All pictures and 3D geometry refer to final native fields, not a budget rescaling.
    vv,ff=voxel_mesh(mesh,drop>=6)
    import trimesh
    model=trimesh.Trimesh(vertices=vv,faces=ff,process=True) if len(ff) else None
    represented=abs(float(model.volume)) if model is not None else 0
    native=hist[-1]['regions']['domain']['6']['volume_m3'];assert abs(represented-native)<1e-7,(represented,native)
    geometry=dict(case=case.name,time_s=10,threshold_k=6,vertices=vv.round(7).tolist(),faces=ff.tolist(),nozzles=info['geometry'],volume_m3=native,scope='Boundary of native cold cells; grid-stepped, not a smooth continuum isosurface. No body.')
    (out/(case.name+'-volume.js')).write_text('window.AA_VOLUME='+json.dumps(geometry,separators=(',',':'))+';')
    if model is not None:model.export(out/(case.name+'-cold-air.glb'))
    for s in sections:s['values_c']=[[None if not np.isfinite(v) else v for v in row] for row in s['values_c']]
    (out/(case.name+'-sections.js')).write_text('window.AA_SECTIONS='+json.dumps(dict(case=case.name,sections=sections),separators=(',',':'))+';')
    summary=dict(case=case.name,inputs=info,source_cooling_w=info['source_mass_kg_s']*CP*(info['ambient_c']-info['source_c']),source_mass_10s_kg=info['source_mass_kg_s']*10,history=hist,final=hist[-1],field_sha256=hashes,mesh_sha256=hashlib.sha256((case/'mesh-metadata.npz').read_bytes()).hexdigest(),gates=audit['gates'],conservation=audit['conservation'],numerical_screens_pass=True,voxel_mesh_volume_check_m3=represented,scope=info['scope'])
    (out/(case.name+'.json')).write_text(json.dumps(summary,indent=2));return summary

if __name__=='__main__':print(json.dumps(extract(STUDY/'cfd/cases'/sys.argv[1])['final'],indent=2))
