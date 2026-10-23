"""Cold air in the requested 20–50 cm band, from unchanged native fields."""
import json,zipfile,hashlib,sys
import numpy as np,trimesh
from build import STUDY,PA,GAS,CP
from extract import arr,overlap,voxel_mesh
OUT=STUDY/'results'

class NativeText:
    def __init__(self,text):self.text=text
    def read_text(self):return self.text

def boxes(info):
    if info['layout']=='overhead':return [[[-.8,.8],[-.2,.2],[1.6,1.9]]]
    result=[[[-.8,.8],[-.35,-.05],[1,1.7]]]
    if info['layout']=='opposed':result.append([[-.8,.8],[.05,.35],[1,1.7]])
    return result

def clipped_surface(mesh,cold,regions):
    native_idx=mesh['indices'];shape=tuple(len(mesh[k])-1 for k in ['z','y','x']);flag=np.zeros(shape,bool);flag[native_idx[:,2],native_idx[:,1],native_idx[:,0]]=cold;vertices=[];faces=[]
    for region in regions:
        axes=[np.r_[bounds[0],mesh[key][(mesh[key]>bounds[0]+1e-10)&(mesh[key]<bounds[1]-1e-10)],bounds[1]] for key,bounds in zip(['x','y','z'],region)]
        nx,ny,nz=[len(a)-1 for a in axes];idx=np.array([(i,j,k) for k in range(nz) for j in range(ny) for i in range(nx)],int);centers=np.column_stack([(a[ix]+a[ix+1])/2 for a,ix in zip(axes,idx.T)]);owner=[np.searchsorted(mesh[key],centers[:,i],side='right')-1 for i,key in enumerate(['x','y','z'])];inside=flag[owner[2],owner[1],owner[0]];sub=dict(zip(['x','y','z'],axes));sub['indices']=idx;v,f=voxel_mesh(sub,inside)
        faces.extend((f+len(vertices)).tolist());vertices.extend(v.tolist())
    return np.array(vertices,float).reshape(-1,3),np.array(faces,int).reshape(-1,3)

def update(name):
    file=OUT/(name+'.json');data=json.loads(file.read_text());
    if data.get('range_analysis_revision')=='native-band-v1' and (OUT/(name+'-range-volume.js')).exists():return data
    info=data['inputs'];case=STUDY/'cfd/cases'/name;mesh=np.load(case/'mesh-metadata.npz');regions=boxes(info);weight=sum((overlap(mesh,b) for b in regions),np.zeros(len(mesh['indices'])));n=len(weight);archive=STUDY/'archives'/(name+'.zip');z=zipfile.ZipFile(archive) if archive.exists() and not (case/'10/T').exists() else None
    def field(t,fld):
        nonlocal z
        if z:raw=z.read(f'{name}/{t}/{fld}')
        else:
            try:raw=(case/t/fld).read_bytes()
            except FileNotFoundError:
                z=zipfile.ZipFile(archive);raw=z.read(f'{name}/{t}/{fld}')
        assert hashlib.sha256(raw).hexdigest()==data['field_sha256'][t][fld]
        return arr(NativeText(raw.decode()),n)
    try:
        for row in data['history']:
            t=str(int(row['time_s']));T=field(t,'T');p=field(t,'p');o=field(t,'origin');rho=p/(GAS*T);drop=info['ambient_c']+273.15-T
            row['regions']['range20to50']={str(th):dict(volume_m3=float(weight[drop>=th].sum()),mass_kg=float((rho*weight)[drop>=th].sum()),source_mass_kg=float((o*rho*weight)[drop>=th].sum()),deficit_j=float((rho*weight*CP*drop)[drop>=th].sum())) for th in [2,6,10]}
        data['final']=data['history'][-1];data['range_region']=dict(boxes_m=regions,fluid_volume_m3=float(weight.sum()),scope='20–50 cm downstream. Side: upper-body-height slab; opposed: union of both slabs; overhead: horizontal-target slab. Sample volumes differ by layout; not equivalent body coverage.');v,f=clipped_surface(mesh,drop>=6,regions);model=trimesh.Trimesh(v,f,process=True) if len(f) else None;vol=abs(float(model.volume)) if model else 0.;target=data['final']['regions']['range20to50']['6']['volume_m3'];assert abs(vol-target)<1e-7,(vol,target)
        geo=dict(case=name,time_s=10,threshold_k=6,vertices=v.round(7).tolist(),faces=f.tolist(),nozzles=info['geometry'],volume_m3=target,region_boxes=regions,scope='Native cold-cell boundary clipped at the 20–50 cm analysis bands. Flat cut faces are analysis boundaries, not a physical limit of the jet.');(OUT/(name+'-range-volume.js')).write_text('window.AA_VOLUME='+json.dumps(geo,separators=(',',':'))+';')
        if model:model.export(OUT/(name+'-range-cold-air.glb'))
        data['range_analysis_revision']='native-band-v1';data['range_voxel_volume_check_m3']=vol;file.write_text(json.dumps(data,indent=2));return data
    finally:
        if z:z.close()

if __name__=='__main__':
    count=0
    for file in sorted(OUT.glob('*-sections.js')):update(file.name.removesuffix('-sections.js'));count+=1
    print('Range-band audits:',count)
