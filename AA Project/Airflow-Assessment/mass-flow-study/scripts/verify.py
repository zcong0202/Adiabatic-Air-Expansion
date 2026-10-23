"""Independent campaign consistency checks. Not physical validation or Lean proof."""
import json,hashlib,zipfile,sys
from pathlib import Path
import numpy as np
from build import STUDY,PA,GAS,CP,SOURCE_C
OUT=STUDY/'results'
checks=[]
def check(name,value):
    checks.append(dict(name=name,pass_=bool(value)))
    if not value:raise AssertionError(name)

def main():
    plan=json.loads((OUT/'campaign-plan.json').read_text());extra=json.loads((OUT/'refinement-plan.json').read_text()) if (OUT/'refinement-plan.json').exists() else {'cases':[]}
    names=[r['name'] for r in plan['cases']+extra['cases']];check('Every planned case has a unique ID',len(set(names))==len(names))
    status=json.loads((OUT/'campaign-status.json').read_text());check('All planned cases completed without failures',not status['failed'] and set(names)==set(status['completed']) and not status['running'])
    data=[]
    for name in names:
        d=json.loads((OUT/(name+'.json')).read_text());c=d['inputs'];data.append(d)
        check(name+': completed solver and every numerical gate',d['numerical_screens_pass'] and all(d['gates'].values()))
        check(name+': total flow split conserves mass',abs(c['per_outlet_g_s']*c['outlets']-c['total_g_s'])<1e-10)
        check(name+': fixed source, still air, gravity and 10 s',c['source_c']==SOURCE_C and c['ambient_c']==30 and c['wind_m_s']==0 and c['gravity_m_s2']==[0,0,-9.81] and c['spray_s']==10 and d['final']['time_s']==10)
        check(name+': actual exit areas equal declared CAD dimensions',abs(c['source_area_m2']-c['outlets']*c['width_m']*c['height_m'])<1e-9)
        check(name+': independent source energy equation',abs(d['source_cooling_w']-c['total_g_s']/1000*1006*(30-SOURCE_C))<1e-7)
        check(name+': source mass across full event',abs(d['source_mass_10s_kg']-c['total_g_s']/100)<1e-10)
        check(name+': native voxel volume independently matches rendered mesh',abs(d['voxel_mesh_volume_check_m3']-d['final']['regions']['domain']['6']['volume_m3'])<1e-7)
        check(name+': clipped range mesh conserves cold-cell overlap',abs(d['range_voxel_volume_check_m3']-d['final']['regions']['range20to50']['6']['volume_m3'])<1e-7)
        check(name+': all native saved times retained',len(d['history'])==11 and [r['time_s'] for r in d['history']]==list(range(11)))
        check(name+': physically bounded source/ambient temperature',all(r['min_c']>=SOURCE_C-.5 for r in d['history']))
        check(name+': every region and threshold has finite nonnegative metrics',all(np.isfinite(v) and v>=-1e-8 for r in d['history'] for region in r['regions'].values() for t in region.values() for v in t.values()))
        check(name+': cooled threshold volumes are nested',all(region['2']['volume_m3']+1e-9>=region['6']['volume_m3']>=region['10']['volume_m3']-1e-9 for r in d['history'] for region in r['regions'].values()))
        archive=json.loads((OUT/(name+'-archive.json')).read_text());path=STUDY/archive['archive'];check(name+': native ZIP hash verified',hashlib.sha256(path.read_bytes()).hexdigest()==archive['sha256'])
        with zipfile.ZipFile(path) as z:
            for fld,digest in d['field_sha256']['10'].items():check(name+': final native '+fld+' retained',hashlib.sha256(z.read(f'{name}/10/{fld}')).hexdigest()==digest)
    cad=json.loads((STUDY/'cad/manifest.json').read_text());check('14 dimension-checked CAD variants',len(cad)==14 and all(c['watertight'] and c['consistent_normals'] and c['components']==1 for c in cad))
    for d in data:
        c=d['inputs'];check(d['case']+': a verified CAD exit matches this CFD',any(abs(k['exact_exit_width_m']-c['width_m'])<1e-10 and abs(k['exact_exit_height_m']-c['height_m'])<1e-10 for k in cad))
    pairs=[]
    for r in extra['cases']:
        if 'parent' in r:
            coarse=next(d for d in data if d['case']==r['parent']);fine=next(d for d in data if d['case']==r['name']);a=coarse['final']['regions']['range20to50']['6']['volume_m3'];b=fine['final']['regions']['range20to50']['6']['volume_m3'];pairs.append(dict(coarse=coarse['case'],fine=fine['case'],region='range20to50',coarse_volume_m3=a,fine_volume_m3=b,relative_change=None if a==0 else b/a-1,coarse_cells=coarse['inputs']['cells'],fine_cells=fine['inputs']['cells'],coarse_best_5cm_drop_50_k=coarse['final']['sections'][2]['best_sampled_5cm_mean_drop_k'],fine_best_5cm_drop_50_k=fine['final']['sections'][2]['best_sampled_5cm_mean_drop_k']))
    result=dict(runtime_python=sys.version,numpy=np.__version__,checks=checks,passed=len(checks),failed=0,cases=len(data),native_snapshots=sum(len(d['history']) for d in data),cad_variants=len(cad),grid_pairs=pairs,hardware_validated=False,new_lean_proof=False,scope='Executed prescribed-source external CFD; numerical consistency checks only. Grid and closure sensitivity are not a physical uncertainty bound.')
    (OUT/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
if __name__=='__main__':main()
