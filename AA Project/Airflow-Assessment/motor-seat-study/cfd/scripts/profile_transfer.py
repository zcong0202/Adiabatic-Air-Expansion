"""Transfer actual CAD-linked internal-nozzle mean exit profile to seat patches."""
from pathlib import Path
import numpy as np,json,re,sys,time
from scipy.interpolate import LinearNDInterpolator,NearestNDInterpolator
from audit_seat import internal,block
from seat_cfd import CFD

def source_profile():
 c=CFD/'cases/N02_D100_transient'
 while not json.loads((c/'run-status.json').read_text())['status'].startswith('solver ended'):time.sleep(5)
 bt=(c/'constant/polyMesh/boundary').read_text();b=block(bt,'outlet');n=int(re.search(r'nFaces\s+(\d+)',b).group(1));start=int(re.search(r'startFace\s+(\d+)',b).group(1))
 text=(c/'constant/polyMesh/owner').read_text();own=np.fromstring(re.search(r'\n\d+\s*\(\s*(.*?)\)',text,re.S).group(1),sep=' ',dtype=int)[start:start+n]
 text=(c/'constant/polyMesh/points').read_text();text=text[text.index('\n(',text.index('}'))+2:];pts=np.array([np.fromstring(x,sep=' ') for x in re.findall(r'\(([^()]*)\)',text)])
 faces=re.findall(r'(\d+)\(([^()]*)\)',(c/'constant/polyMesh/faces').read_text())[start:start+n];centres=[];areas=[]
 for _,f in faces:
  v=pts[np.fromstring(f,sep=' ',dtype=int)];centres.append(v.mean(axis=0));areas.append(np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))/2)
 centres=np.array(centres);areas=np.array(areas);paths=sorted([p for p in c.iterdir() if p.name.replace('.','').isdigit() and float(p.name)>=.1 and (p/'U').exists()],key=lambda p:float(p.name));vel=np.array([internal(p/'U',True)[own] for p in paths]);mean=vel.mean(axis=0);ks=np.array([internal(p/'k')[own] for p in paths]).mean(axis=0);om=np.array([internal(p/'omega')[own] for p in paths]).mean(axis=0)
 bulk=np.dot(areas,mean[:,2])/areas.sum();cv=np.sqrt(np.dot(areas,(mean[:,2]-bulk)**2)/areas.sum())/bulk
 cvs=[]
 for u in vel:
  b=np.dot(areas,u[:,2])/areas.sum();cvs.append(float(np.sqrt(np.dot(areas,(u[:,2]-b)**2)/areas.sum())/b))
 r=dict(case=c.name,times_s=[float(p.name) for p in paths],mean_axial_speed_m_s=float(bulk),axial_speed_CV=float(cv),CV_range=float(np.ptp(cvs)),maximum_profile_time_variation_m_s=float(np.max(np.linalg.norm(vel-mean[None,:,:],axis=2))),reverse_area_fraction=float(areas[mean[:,2]<0].sum()/areas.sum()),note='Short 0.3 s URANS follow-up from iteration1200; average of outputs at/after0.1s. This checks exit-profile stability, not long-duration validation or turbulence-model error.')
 assert r['reverse_area_fraction']<.01 and r['CV_range']<.03,r
 np.savez_compressed(c/'exit-profile.npz',centres=centres,areas=areas,U=mean,k=ks,omega=om)
 (c/'profile-audit.json').write_text(json.dumps(r,indent=2));return c/'exit-profile.npz'

def replace_patch(text,name,body):
 m=re.search(r'\b'+name+r'\s*\{',text[text.index('boundaryField'):]);offset=text.index('boundaryField');a=offset+m.end();i=a;depth=1
 while depth:
  if text[i]=='{':depth+=1
  if text[i]=='}':depth-=1
  i+=1
 return text[:a]+'\n'+body+'\n'+text[i-1:]

def apply(case):
 f=source_profile();pr=np.load(f);bc=np.load(case/'boundary-metadata.npz');cfg=json.loads((case/'case.json').read_text());rho=101325/(287.05*(cfg['source_c']+273.15));scale=cfg['source_mass_kg_s']/.0582;areas=cfg['patch_areas_m2'];total=sum(a for p,a in areas.items() if p.startswith('jet'))
 points=pr['centres'][:,:2];interps={n:(LinearNDInterpolator(points,pr[n]),NearestNDInterpolator(points,pr[n])) for n in ['U','k','omega']}
 for patch in bc.files:
  if not patch.startswith('jet'):continue
  xyz=bc[patch][:,1:4];left='Left'in patch;zc=.84 if 'Lower'in patch else 1.24
  xy=np.column_stack([xyz[:,0]-.49,(-1 if left else 1)*(xyz[:,2]-zc)])
  vals={}
  for name,(interp,near) in interps.items():
   a=interp(xy);bad=~np.isfinite(a);fallback=near(xy);a[bad]=fallback[bad];vals[name]=a
  local=vals['U'];u=np.column_stack([local[:,0],local[:,2] if left else -local[:,2],-local[:,1] if left else local[:,1]])
  # Normalize normal profile on the actual CFD patch to preserve prescribed source mass.
  weights=bc[patch][:,4];norm=np.dot(weights,np.abs(u[:,1]));target=cfg['source_mass_kg_s']*(areas[patch]/total)/rho;factor=target/norm;u*=factor
  k=np.maximum(vals['k']*factor**2,1e-8);eps=np.maximum(.09*k*vals['omega']*factor,1e-10)
  for name,values,vector in [('U',u,True),('k',k,False),('epsilon',eps,False)]:
   content=' '.join('('+' '.join(f'{x:.12g}' for x in v)+')' for v in values) if vector else ' '.join(f'{x:.12g}' for x in values)
   body=f'type fixedValue; value nonuniform List<{"vector" if vector else "scalar"}> {len(values)} ({content});'
   p=case/'0'/name;p.write_text(replace_patch(p.read_text(),patch,body))
 cfg['inlet_profile']=dict(source_case='N02_D100_transient',transfer='Mean internal CAD exit velocity and k/omega profile; rotated into four side outlets; flux-normalized to prescribed mass. epsilon=0.09*k*omega for outer k-epsilon closure.',flow_scaling_from_three_motor_profile=scale,limitation='Four-motor wind states scale the 3-motor exit shape; no independent 4-motor internal solve. Mesh interpolation and closure change introduce uncertainty.')
 (case/'case.json').write_text(json.dumps(cfg,indent=2))
if __name__=='__main__':print(source_profile())
