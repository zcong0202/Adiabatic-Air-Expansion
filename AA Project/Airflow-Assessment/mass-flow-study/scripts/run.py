"""Run native OpenFOAM, then audit. Each invocation is one isolated case."""
import sys,json,time,subprocess
from build import ROOT,STUDY,IMAGE

def run(case,ranks=2):
    state=dict(status='running',started=time.time(),image=IMAGE,mpi_ranks=ranks,mpi_binding='none')
    (case/'run-status.json').write_text(json.dumps(state,indent=2))
    base_decomp=case/'system/decomposeParDict';base_decomp.write_text(f'FoamFile {{ version 2.0; format ascii; class dictionary; object decomposeParDict; }}\nnumberOfSubdomains {ranks}; method scotch;\n')
    mount=str(ROOT);work='/work/'+case.resolve().relative_to(ROOT.resolve()).as_posix()
    solver = f'decomposePar -force > log.decomposePar 2>&1\nmpirun --allow-run-as-root --bind-to none -np {ranks} buoyantPimpleFoam -parallel > log.solver 2>&1\nreconstructPar > log.reconstructPar 2>&1' if ranks > 1 else 'buoyantPimpleFoam > log.solver 2>&1'
    script=f'''source /usr/lib/openfoam/openfoam2506/etc/bashrc
set -e
checkMesh -allGeometry -allTopology > log.checkMesh 2>&1
grep -q 'Mesh OK.' log.checkMesh
{solver}
'''
    command=['docker','run','--rm','--cpus',str(ranks),'--memory','1500m','--name','aa-flow-'+case.name.lower().replace('_','-'),'--entrypoint','/bin/bash','-v',mount+':/work','-w',work,IMAGE,'-c',script]
    try:
        with (case/'log.container').open('w') as out:subprocess.run(command,check=True,stdout=out,stderr=subprocess.STDOUT)
        state['status']='solver ended; audit pending'
    except Exception as e:state.update(status='failed',error=str(e));raise
    finally:state['elapsed_s']=time.time()-state['started'];(case/'run-status.json').write_text(json.dumps(state,indent=2))
    try:
        sys.path.insert(0,str(ROOT/'pass-by-study/scripts'));from analyse import audit
        a=audit(case,False)
        # Tight source-flow screen across all written times, independent of the original absolute tolerance.
        a['gates']['source_mass_relative_0_5pct']=all(abs(row.get('source_mass_kg_s',a['case']['source_mass_kg_s'])/a['case']['source_mass_kg_s']-1)<.005 for row in a['history'])
        a['numerical_screens_pass']=all(a['gates'].values());(case/'audit.json').write_text(json.dumps(a,indent=2))
        state.update(status='audited',numerical_screens_pass=a['numerical_screens_pass']);(case/'run-status.json').write_text(json.dumps(state,indent=2))
        print(json.dumps(dict(case=case.name,elapsed_s=state['elapsed_s'],pass_=a['numerical_screens_pass'],gates=a['gates'],conservation=a['conservation'])),flush=True)
        if not a['numerical_screens_pass']:raise RuntimeError('Numerical screens failed')
    except Exception as error:
        state.update(status='failed',error=str(error));(case/'run-status.json').write_text(json.dumps(state,indent=2));raise

if __name__=='__main__':run(STUDY/'cfd/cases'/sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 2)
