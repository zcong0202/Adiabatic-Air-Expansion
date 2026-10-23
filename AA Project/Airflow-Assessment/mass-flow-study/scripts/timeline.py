"""Native 0–10 s dashboard frames. No new CFD, interpolation or field rescaling."""
import io,json,hashlib,zipfile,concurrent.futures,os
import numpy as np,trimesh
from build import STUDY
from extract import arr,voxel_mesh,section
from range_metrics import boxes,clipped_surface,NativeText
from patch import patch_metric
OUT=STUDY/'results'

def geometry(mesh,cold,regions,expected):
    v,f=clipped_surface(mesh,cold,regions) if regions else voxel_mesh(mesh,cold)
    if len(f):
        model=trimesh.Trimesh(v,f,process=True)
        assert abs(abs(model.volume)-expected)<1e-7,(model.volume,expected)
        v,f=model.vertices,model.faces
    else:assert expected<1e-12
    return dict(vertices=np.round(v,7).tolist(),faces=f.tolist(),volume_m3=expected,**({'region_boxes':regions} if regions else {}))

def create(name):
    data=json.loads((OUT/(name+'.json')).read_text());path=OUT/(name+'-timeline.js');record=OUT/(name+'-timeline-audit.json')
    signature=hashlib.sha256(json.dumps(data['field_sha256'],sort_keys=True).encode()).hexdigest()
    if path.exists() and record.exists():
        old=json.loads(record.read_text())
        if old.get('field_signature')==signature and old.get('file_sha256')==hashlib.sha256(path.read_bytes()).hexdigest():return name
    with zipfile.ZipFile(STUDY/'archives'/(name+'.zip')) as z:
        raw=z.read(name+'/mesh-metadata.npz');assert hashlib.sha256(raw).hexdigest()==data['mesh_sha256']
        mesh=np.load(io.BytesIO(raw));idx=mesh['indices'];n=len(idx);shape=tuple(len(mesh[k])-1 for k in ['z','y','x']);regions=boxes(data['inputs']);frames=[]
        for row in data['history']:
            time=int(row['time_s']);raw=z.read(f'{name}/{time}/T');assert hashlib.sha256(raw).hexdigest()==data['field_sha256'][str(time)]['T']
            temp=arr(NativeText(raw.decode()),n)-273.15;cold=data['inputs']['ambient_c']-temp>=6;grid=np.full(shape,np.nan);grid[idx[:,2],idx[:,1],idx[:,0]]=temp
            sections=[]
            for distance in [.2,.35,.5]:
                s=section(mesh,grid,distance,data['inputs']);s.update(patch_metric(s));s['values_c']=[[None if not np.isfinite(t) else t for t in line] for line in s['values_c']];sections.append(s)
            frames.append(dict(time_s=time,range=geometry(mesh,cold,regions,row['regions']['range20to50']['6']['volume_m3']),whole=geometry(mesh,cold,None,row['regions']['domain']['6']['volume_m3']),sections=sections))
    result=dict(case=name,threshold_k=6,source_c=data['inputs']['source_c'],ambient_c=data['inputs']['ambient_c'],nozzles=data['inputs']['geometry'],frames=frames,scope='Native saved temperature fields at integer seconds 0–10. No temporal interpolation; spray ON only. Mesh volume checked against original native regional metrics.')
    path.write_text('window.AA_TIMELINE='+json.dumps(result,separators=(',',':'))+';')
    record.write_text(json.dumps(dict(case=name,frames=len(frames),times_s=[f['time_s'] for f in frames],field_signature=signature,file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,native_temperature_hashes_verified=11,mesh_hash_verified=True,volume_checks=22,scope=result['scope']),indent=2));print('FRAMES '+name,flush=True);return name
if __name__=='__main__':
    names=json.loads((OUT/'campaign-status.json').read_text())['completed']
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:done=list(pool.map(create,names))
    (OUT/'timeline-validation.json').write_text(json.dumps(dict(cases=len(done),native_frames=len(done)*11,native_temperature_hashes_verified=len(done)*11,volume_checks=len(done)*22,temporal_interpolation=False,new_cfd_runs=False,scope='Native archive re-extraction only; source, CFD fields and physical uncertainty unchanged.'),indent=2))
