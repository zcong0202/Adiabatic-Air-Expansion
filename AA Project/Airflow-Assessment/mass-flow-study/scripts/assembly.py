"""Place actual prototype STL bodies at the CFD exit faces. Geometry only."""
import json,hashlib
import numpy as np,trimesh
from build import STUDY
OUT=STUDY/'results';CAD=STUDY/'cad'

def main():
    manifest=json.loads((CAD/'manifest.json').read_text());assemblies={};models={}
    for file in OUT.glob('*.json'):
        d=json.loads(file.read_text())
        if not isinstance(d,dict) or 'final' not in d:continue
        c=d['inputs'];cad=next(m for m in manifest if abs(m['exact_exit_width_m']-c['width_m'])<1e-9 and abs(m['exact_exit_height_m']-c['height_m'])<1e-9);key=cad['stl']+':'+c['layout']+':'+str(c['outlets']);tag=hashlib.sha256(key.encode()).hexdigest()[:12]
        if tag not in assemblies:
            if cad['stl'] not in models:
                m=trimesh.load_mesh(STUDY/cad['stl'],process=True);m.apply_scale(.001);models[cad['stl']]=m
            scene=trimesh.Scene();placements=[]
            for n in c['geometry']:
                b=np.array(n['box']);center=b.mean(1);direction=n['direction'];rotation={3:[[1,0,0],[0,0,1],[0,-1,0]],2:[[1,0,0],[0,0,-1],[0,1,0]],4:[[1,0,0],[0,-1,0],[0,0,-1]]}[direction];R=np.array(rotation);end=center.copy()
                if direction==3:end[1]=b[1,1]
                elif direction==2:end[1]=b[1,0]
                else:end[2]=b[2,0]
                matrix=np.eye(4);matrix[:3,:3]=R;matrix[:3,3]=end-R@np.array([0,0,.205]);body=models[cad['stl']].copy();body.apply_transform(matrix);body.visual.face_colors=[62,91,105,255];scene.add_geometry(body,node_name=n['name']);placements.append(dict(name=n['name'],transform_m=matrix.tolist(),outlet_center_m=end.tolist()))
            name='assembly-'+tag+'.glb';scene.export(CAD/name);assemblies[tag]=dict(glb='cad/'+name,units='metres',outlets=c['outlets'],layout=c['layout'],prototype=cad['stl'],placements=placements,scope='Prototype bodies placed at CFD exit faces. The external CFD uses short blocks, not these full bodies. No manifold, mount, clamps or fitted stock interfaces are included.')
        d['cad_assembly']=assemblies[tag];file.write_text(json.dumps(d,indent=2))
    (CAD/'assemblies.json').write_text(json.dumps(list(assemblies.values()),indent=2));print('Unique assembled CAD layouts:',len(assemblies))
if __name__=='__main__':main()
