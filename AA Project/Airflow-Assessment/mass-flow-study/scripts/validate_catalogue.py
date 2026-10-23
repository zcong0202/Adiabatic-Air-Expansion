"""Check CAD/CFD identity, native replay hashes and sampled patch integrals."""
import hashlib,json,zipfile
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss
from validate_delivery import Links
STUDY=Path(__file__).resolve().parents[1];OUT=STUDY/'results';CAT=OUT/'nozzle-catalogue'

def main():
    checks=0
    def check(value):
        nonlocal checks
        assert value;checks+=1
    data=json.loads((CAT/'catalogue.json').read_text());check(data['count']==len(data['items'])==23)
    seen=[]
    for item in data['items']:
        stl=OUT/item['preview_stl'];check(hashlib.sha256(stl.read_bytes()).hexdigest()==item['stl_sha256']);check(item['watertight'] and not item['fit_verified'])
        check((OUT/item['stl']).exists() and (OUT/item['step']).exists() and (OUT/item['image']).exists())
        for row in item['runs']:
            r=json.loads((OUT/(row['case']+'.json')).read_text());c=r['inputs'];seen.append(r['case'])
            check(row['total_g_s']==c['total_g_s'] and row['outlets']==c['outlets'] and row['layout']==c['layout'])
            check(abs(row['drop20_k']-r['final']['sections'][0]['best_sampled_5cm_mean_drop_k'])<1e-12)
            check(abs(row['drop50_k']-r['final']['sections'][2]['best_sampled_5cm_mean_drop_k'])<1e-12)
        if item['group']=='early':check(not item['runs'] and 'unconverged' in item['limits'])
    check(len(seen)==len(set(seen))==55)
    q,w=leggauss(100);rr=np.hypot(q[:,None]*.025,q[None,:]*.025);ww=w[:,None]*w[None,:]/4
    for record in json.loads((CAT/'legacy-ranges.json').read_text()):
        archive=(CAT/record['archive']).resolve();check(hashlib.sha256(archive.read_bytes()).hexdigest()==record['archive_sha256'])
        with zipfile.ZipFile(archive) as z:
            check(z.testzip() is None)
            for field,digest in record['field_sha256'].items():check(hashlib.sha256(z.read(record['snapshot']+'/'+field)).hexdigest()==digest)
            for s in record['sections']:
                p=np.loadtxt(CAT/s['profile']);drop=float((record['ambient_c']-record['source_c'])*np.sum(np.interp(rr,p[:,0],p[:,1])*ww))
                check(abs(drop-s['mean_drop_k'])<1e-12)
                check(z.read(f'postProcessing/catalogueProfiles/{record["snapshot"]}/at{s["distance_cm"]}_theta_U.xy')==(CAT/s['profile']).read_bytes())
            check(abs(record['sections'][0]['mean_drop_k']-record['previous20_drop_k'])<.1)
    parser=Links();parser.feed((CAT/'catalogue.html').read_text())
    for link in parser.links:
        if not link.startswith('#'):check((OUT/link).exists())
    with zipfile.ZipFile(CAT/'all-nozzle-cad.zip') as z:
        check(z.testzip() is None)
        for name in z.namelist():
            if name=='CATALOGUE.json':check(z.read(name)==(CAT/'catalogue.json').read_bytes())
            elif name!='READ-FIRST.txt':check(z.read(name)==(STUDY.parent/name).read_bytes())
    result=dict(checks=checks,status='passed',designs=23,current_case_mappings=55,legacy_native_cases=5,limits='Integrity, identities and postprocessing. Hardware attachment and CFD physical accuracy not established.')
    (CAT/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
