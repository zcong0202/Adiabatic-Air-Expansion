from pathlib import Path
import numpy as np,re,json,sys
from audit_seat import arr,internal
from boundary_balance import values,block
from seat_cfd import CFD

def vector_values(text,p,count):
 part=block(text[text.index('boundaryField'):],p);m=re.search(r'value\s+nonuniform\s+List<vector>\s+(\d+)\s*\((.*?)\)\s*;',part,re.S)
 if m:return np.fromstring(m.group(2).replace('(',' ').replace(')',' '),sep=' ').reshape(-1,3)
 m=re.search(r'value\s+uniform\s+\(([^)]+)\)',part)
 if m:return np.tile(np.fromstring(m.group(1),sep=' '),(count,1))
 raise ValueError(p)

def audit(name):
 c=CFD/'cases'/name;cfg=json.loads((c/'case.json').read_text());s=(c/'log.solver').read_text();last=max([p for p in c.iterdir() if p.name.isdigit() and (p/'U').exists()],key=lambda p:int(p.name));bt=(c/'constant/polyMesh/boundary').read_text();phi=(last/'phi').read_text();U=(last/'U').read_text();p=(last/'p').read_text();result={}
 for patch in ['inlet','outlet']:
  n=int(re.search(r'nFaces\s+(\d+)',block(bt,patch)).group(1));f=values(phi,patch,n)
  try:u=vector_values(U,patch,n)
  except ValueError:
   text=(c/'constant/polyMesh/owner').read_text();m=re.search(r'\n\d+\s*\(\s*(.*?)\)',text,re.S);owners=np.fromstring(m.group(1),sep=' ',dtype=int);start=int(re.search(r'startFace\s+(\d+)',block(bt,patch)).group(1));u=internal(last/'U',True)[owners[start:start+n]]
  # Outlet triangular areas are recovered from surface mesh geometry via native polyMesh points/faces.
  faces=(c/'constant/polyMesh/faces').read_text();start=int(re.search(r'startFace\s+(\d+)',block(bt,patch)).group(1));allfaces=re.findall(r'(\d+)\(([^()]*)\)',faces)
  points=(c/'constant/polyMesh/points').read_text();ps=points[points.index('\n(',points.index('}'))+2:];pointsarr=np.array([np.fromstring(v,sep=' ') for v in re.findall(r'\(([^()]*)\)',ps)])
  areas=[]
  for _,ids in allfaces[start:start+n]:
   vv=pointsarr[np.fromstring(ids,dtype=int,sep=' ')];areas.append(np.linalg.norm(np.cross(vv[1]-vv[0],vv[2]-vv[0]))/2)
  aa=np.array(areas);vel=u[:,2];mean=np.dot(aa,vel)/aa.sum();cv=math_sqrt=np.sqrt(np.dot(aa,(vel-mean)**2)/aa.sum())/max(abs(mean),1e-9)
  result[patch]=dict(volume_flux_m3_s=float(f.sum()),area_m2=float(aa.sum()),mean_axial_speed_m_s=float(mean),axial_speed_CV=float(cv),reverse_area_fraction=float(aa[vel<0].sum()/aa.sum()),transverse_rms_m_s=float(np.sqrt(np.dot(aa,np.sum(u[:,:2]**2,axis=1))/aa.sum())))
 # The field function object reports a true area average including zeroGradient inlet p.
 pressurefile=max((c/'postProcessing/pressure_in').glob('*/surfaceFieldValue.dat'),key=lambda p:float(p.parent.name))
 lines=[x for x in pressurefile.read_text().splitlines() if x.strip() and not x.startswith('#')];pin=float(lines[-1].split()[-1])*cfg['density_kg_m3']
 masserr=abs(result['inlet']['volume_flux_m3_s']+result['outlet']['volume_flux_m3_s'])/abs(result['inlet']['volume_flux_m3_s'])
 report=dict(case=cfg,iteration=int(last.name),mesh_ok='Mesh OK.' in (c/'log.checkMesh').read_text(),solver_ended='\nEnd\n'in s and 'FOAM FATAL'not in s,convergence_reported='SIMPLE solution converged' in s,patches=result,static_inlet_pressure_pa=pin,mass_relative_error=masserr,profile_uniform_assumption_supported=result['outlet']['axial_speed_CV']<=.25,note='Nozzle internal isothermal RANS, tetra mesh with wall functions. CV threshold .25 is an engineering screen, not a proved error bound. Field functions sample every 20 iterations.')
 (c/'audit.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 for n in sys.argv[1:]:print(json.dumps(audit(n),indent=2))
