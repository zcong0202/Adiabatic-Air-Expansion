"""Verified native archive. Remove only newly generated redundant fields after verification."""
import json,zipfile,hashlib,shutil,sys,time
from build import STUDY

def archive(name):
    case=STUDY/'cfd/cases'/name;out=STUDY/'archives';out.mkdir(exist_ok=True);dest=out/(name+'.zip');info=case/'archive.json'
    if info.exists() and dest.exists():return
    result=json.loads((STUDY/'results'/(name+'.json')).read_text());assert result['numerical_screens_pass']
    temp=dest.with_suffix('.tmp')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as z:
        for path in sorted(case.rglob('*')):
            rel=path.relative_to(case)
            if path.is_file() and not rel.parts[0].startswith('processor') and path.name!='archive.json':z.write(path,str(path.relative_to(case.parent)))
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        for t,fields in result['field_sha256'].items():
            for fld,digest in fields.items():assert hashlib.sha256(z.read(f'{name}/{t}/{fld}')).hexdigest()==digest
    temp.replace(dest);record=dict(archive=str(dest.relative_to(STUDY)),bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),native_fields_checked=sum(map(len,result['field_sha256'].values())),processor_subdomains_excluded='Redundant; complete reconstructed native fields retained',restore=f'Unzip this archive into {STUDY.name}/cfd/cases; it contains {name}/.',scope='Native OpenFOAM replay inputs, mesh, reconstructed fields, solver logs and audit. Original pre-existing studies untouched.')
    info.write_text(json.dumps(record,indent=2));(STUDY/'results'/(name+'-archive.json')).write_text(json.dumps(record,indent=2))
    for p in list(case.iterdir()):
        if p.is_dir() and (p.name.startswith('processor') or (p.name.replace('.','').isdigit() and float(p.name)>0)):shutil.rmtree(p)
    print('ARCHIVED '+name,flush=True)

if __name__=='__main__':
    if len(sys.argv)>1:
        for name in sys.argv[1:]:archive(name)
    else:
        while True:
            status=json.loads((STUDY/'results/campaign-status.json').read_text())
            for name in status['completed']:archive(name)
            if 'ended_utc' in status:break
            time.sleep(15)
