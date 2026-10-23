"""Sample saved conical-nozzle CFD. No flow solve or new boundary conditions.

Run with --native-root pointing to the original Airflow-Assessment folder.
Preserve the small replay case in LFS; never modify the original fields.
"""
import argparse, hashlib, json, shutil, subprocess, zipfile
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

STUDY=Path(__file__).resolve().parents[1]
ASSESS=STUDY.parent
IMAGE='microfluidica/openfoam:2506@sha256:9ab54b92553d58a2e21adaf4ef98a8d0c118a09a1b388bd95480720ed7809b37'
CASES={'C16_a5':'R01_D16','C24_a3':'R13_D24_a3_fine','C24_a5':'R05_D24_diffuser_SST','C24_a7':'R08_D24_diffuser_7deg_SST','stock_D28_a5':'S03_stock_b60_D28_a5_lowflow_fine'}

def main(root):
    out=STUDY/'results/nozzle-catalogue';out.mkdir(exist_ok=True)
    records=[]
    for design,name in CASES.items():
        source=root/'optimization/cases'/name
        audit=json.loads((source/'audit.json').read_text())
        assert audit['numerically_accepted']
        snap=audit['native_balance']['snapshot'];case=STUDY/'cfd/cases'/('catalogue_'+name)
        if not case.exists():
            case.mkdir(parents=True)
            for part in ['constant','system',snap]:shutil.copytree(source/part,case/part)
            for part in ['case.json','audit.json','log.solver','log.checkMesh','run-status.json']:shutil.copyfile(source/part,case/part)
        sample='''FoamFile { version 2.0; format ascii; class dictionary; object catalogueSamples; }
functions { catalogueProfiles { type sets; libs (sampling); writeControl timeStep; writeInterval 1;
setFormat raw; interpolationScheme cellPoint; fields (theta U);
sets (
 at20 { type uniform; axis y; start (.2 0 0); end (.2 .1 0); nPoints 401; }
 at50 { type uniform; axis y; start (.5 0 0); end (.5 .1 0); nPoints 401; }
); } }
'''
        (case/'system/catalogueSamples').write_text(sample)
        cmd=['docker','run','--rm','--entrypoint','/bin/bash','-v',f'{ASSESS}:/work','-w',f'/work/mass-flow-study/cfd/cases/{case.name}',IMAGE,'/work/scripts/foam-entry.sh','postProcess','-dict','system/catalogueSamples','-fields','(theta U)','-time',snap]
        done=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (case/'log.catalogue-sample').write_text(done.stdout)
        if done.returncode:raise RuntimeError(done.stdout[-3000:])
        sections=[];profiles={}
        q,w=leggauss(100);rr=np.hypot(q[:,None]*.025,q[None,:]*.025);ww=w[:,None]*w[None,:]/4
        ta=audit['ambient_temperature_c'];tc=audit['cold_temperature_c']
        fig,axes=plt.subplots(1,2,figsize=(8,3.8),layout='constrained')
        for ax,distance in zip(axes,[20,50]):
            path=next((case/f'postProcessing/catalogueProfiles/{snap}').glob(f'at{distance}_*.xy'))
            a=np.loadtxt(path)
            # raw sets use field order in the requested list: scalar theta, vector U.
            assert a.shape==(401,5) and np.all(np.diff(a[:,0])>0)
            theta=a[:,1];assert theta.min()>-1e-4 and theta.max()<1.0001
            drop=float((ta-tc)*np.sum(np.interp(rr,a[:,0],theta)*ww))
            section=dict(distance_cm=distance,mean_drop_k=drop,mean_air_c=ta-drop,metric='Fixed centred 50 x 50 mm area mean; steady passive scalar',profile=f'{name}-at{distance}.xy')
            shutil.copyfile(path,out/section['profile']);sections.append(section)
            profiles[str(distance)]={'radius_m':a[:,0].tolist(),'theta':theta.tolist()}
            xy=np.linspace(-.025,.025,101);r=np.hypot(xy[:,None],xy[None,:]);t=ta-(ta-tc)*np.interp(r,a[:,0],theta)
            im=ax.imshow(t,origin='lower',extent=[-25,25,-25,25],vmin=tc,vmax=ta,cmap='coolwarm');ax.set(title=f'{distance} cm · Δ {drop:.2f}°C',xlabel='y (mm)',ylabel='z (mm)')
        fig.colorbar(im,ax=axes,label='Air temperature (°C)',shrink=.8)
        fig.suptitle(f'{design} · {audit["cold_mass_flow_kg_s"]*1000:.2f} g/s · {tc:.2f}°C supply / {ta:g}°C ambient\nSaved steady CFD · axisymmetric · gravity excluded',fontsize=11)
        fig.savefig(out/f'{name}-ranges.png',dpi=150);plt.close(fig)
        # Check the new 20 cm extraction against the earlier accepted target record.
        old=audit['target']['mean_drop_c'];error=abs(sections[0]['mean_drop_k']-old)
        assert error<.1,(name,error)
        archive=STUDY/'archives'/f'catalogue-{name}.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for f in case.rglob('*'):
                if f.is_file():z.write(f,f.relative_to(case))
        with zipfile.ZipFile(archive) as z:assert z.testzip() is None
        record=dict(design=design,case=name,sections=sections,profiles=profiles,image=f'{name}-ranges.png',source_c=tc,ambient_c=ta,total_g_s=audit['cold_mass_flow_kg_s']*1000,accepted=True,internal_diffuser=bool(audit.get('internal_diffuser_modeled')),snapshot=snap,previous20_drop_k=old,previous20_difference_k=error,field_sha256={f:hashlib.sha256((case/snap/f).read_bytes()).hexdigest() for f in ['theta','U']},archive=f'../../archives/{archive.name}',archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),limits='Steady axisymmetric dry passive-scalar screen. Gravity, wind, wall heat, real source coupling and human heat transfer excluded. No spray duration predicted.')
        records.append(record);print(name,[(s['distance_cm'],round(s['mean_drop_k'],3)) for s in sections],flush=True)
    (out/'legacy-ranges.json').write_text(json.dumps(records,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native-root',required=True,type=Path);main(p.parse_args().native_root)
