"""Extract Eulerian cooled mass/volume from native OpenFOAM fields. No new CFD run."""
import argparse, hashlib, json, re
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT/'AA Project/Airflow-Assessment/pass-by-study/results/cfd-summary.json'
REGIONS = {
 'domain': {'name':'Whole simulated domain', 'bounds':[[-1.25,1.25],[-1.1,1.1],[0,2.7]]},
 'corridor': {'name':'Walking corridor · 1.6 × 0.4 × 0.7 m', 'bounds':[[-.8,.8],[-.2,.2],[1,1.7]]},
}

def field(path,n):
 s=path.read_text()
 m=re.search(r'internalField\s+nonuniform\s+List<\w+>\s+(\d+)\s*\((.*?)\)\s*;',s,re.S)
 if m:
  a=np.fromstring(m.group(2),sep=' ')
  assert len(a)==n==int(m.group(1)),path
  return a
 m=re.search(r'internalField\s+uniform\s+([^;]+)',s)
 return np.full(n,float(m.group(1)))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rounded(a):return np.round(a,8).tolist()

def build(native):
 summary=json.loads(SUMMARY.read_text());out={'schema':1,'description':'Native field integration; no rerun; cell-constant temperature threshold, exact cell/region intersection volumes.','thresholds_k':np.arange(.5,30.01,.5).tolist(),'regions':REGIONS,'cases':[],'limitations':['URANS dry ideal gas, k-epsilon. Numerical screening, not hardware validation.','No human, body wake, solar load, humidity, valve shutoff, source transient or nozzle interior.','Threshold volume is sensitive to grid and turbulence. No continuum error bound.','Source mass is passive origin tracer times density. No parcel lifetime inferred.','Pressure and T give rho=p/(R T), consistent with the perfect-gas solver.','Corridor bounds are a new analysis choice, not an original design requirement.']}
 for row in summary['cases']:
  name=row['case'];case=native/name;info=json.loads((case/'case.json').read_text());audit=json.loads((case/'audit.json').read_text())
  mesh=np.load(case/'mesh-metadata.npz');ind=mesh['indices'];n=len(ind)
  lo=np.column_stack([mesh[a][ind[:,j]] for j,a in enumerate(['x','y','z'])]);hi=np.column_stack([mesh[a][ind[:,j]+1] for j,a in enumerate(['x','y','z'])])
  weights={key:np.prod(np.maximum(0,np.minimum(hi,np.array(r['bounds'])[:,1])-np.maximum(lo,np.array(r['bounds'])[:,0])),axis=1) for key,r in REGIONS.items()}
  assert np.allclose(weights['domain'],mesh['volumes'])
  snaps=sorted([p for p in case.iterdir() if p.is_dir() and re.fullmatch(r'\d+(\.\d+)?',p.name) and (p/'T').exists()],key=lambda p:float(p.name))
  result={'id':name,'layout':info['layout'],'distance_m':info['nominal_standoff_m'],'width_m':info.get('outlet_width_m',row['width_m']),'height_m':info.get('outlet_height_m',row['height_m']),'wind_m_s':info['wind_m_s'],'wind_direction':info.get('wind_direction','front'),'pitch_deg':info.get('pitch_deg',0),'source_kg_s':info['source_mass_kg_s'],'source_c':info['source_c'],'ambient_c':info['ambient_c'],'cells':n,'numerical_screens_pass':audit.get('numerical_screens_pass',False),'reference_patch':row.get('reference'),'mesh_sha256':sha(case/'mesh-metadata.npz'),'times':[],'snapshots':[]}
  # Keep all audit gates, independent of our extraction.
  result['audit_gates']=audit.get('gates',audit.get('numerical_gates',{}))
  for snap in snaps:
   T=field(snap/'T',n);p=field(snap/'p',n);rho=p/((8314.46261815324/28.965)*T);origin=field(snap/'origin',n)
   assert np.isfinite(T).all() and (T>100).all() and (rho>0).all()
   # Preserve unmodified tracer; bounded diagnostics expose excursions.
   drop=info['ambient_c']+273.15-T
   sample={'time_s':float(snap.name),'T_sha256':sha(snap/'T'),'p_sha256':sha(snap/'p'),'origin_sha256':sha(snap/'origin'),'origin_bounds':[float(origin.min()),float(origin.max())],'regions':{}}
   for key,w in weights.items():
    mass=rho*w;region={'fluid_volume_m3':float(w.sum()),'total_mass_kg':float(mass.sum())}
    metrics=[]
    for d in out['thresholds_k']:
     sel=drop>=d;v=float(w[sel].sum());m=float(mass[sel].sum());ms=float((mass*origin)[sel].sum());e=float((mass*1006*drop)[sel].sum())
     metrics.append([v,m,ms,e])
    region['columns']=['cooled_volume_m3','cooled_mass_kg','source_mass_kg','sensible_deficit_j'];region['values']=rounded(np.array(metrics));sample['regions'][key]=region
   result['times'].append(float(snap.name));result['snapshots'].append(sample)
  out['cases'].append(result);print(name,n,len(snaps),flush=True)
 out['provenance']={'summary_sha256':sha(SUMMARY),'extractor_sha256':sha(Path(__file__)),'native_root_name':'pass-by-study/cfd/cases','density_R_j_kg_k':8314.46261815324/28.965,'cp_j_kg_k':1006,'hardware_validated':False}
 dest=ROOT/'panel/data/cfd.json';dest.write_text(json.dumps(out,separators=(',',':'))+'\n');dest.with_suffix('.js').write_text('globalThis.AA_CFD = '+json.dumps(out,separators=(',',':'))+';\n')
 print('saved',dest,flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('native',type=Path);build(parser.parse_args().native)
