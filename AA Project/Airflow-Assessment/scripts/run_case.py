"""Run a generated case in a pinned ARM64 OpenFOAM container, preserving logs."""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IMAGE="microfluidica/openfoam:2506@sha256:9ab54b92553d58a2e21adaf4ef98a8d0c118a09a1b388bd95480720ed7809b37"


def command(case,args):
    return ["docker","run","--rm","--entrypoint","/bin/bash","-v",f"{ROOT}:/work","-w",f"/work/cases/{case.name}",IMAGE,"/work/scripts/foam-entry.sh",*args]


def execute(case,args,log):
    with (case/log).open("w") as output:
        result=subprocess.run(command(case,args),stdout=output,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed ({result.returncode}); see {case/log}")


def run(name,prepare=True):
    case=ROOT/"cases"/name
    started=time.time()
    state={"image":IMAGE,"case":name,"status":"running","started_epoch":started}
    (case/"run-status.json").write_text(json.dumps(state,indent=2))
    try:
        if prepare:
            execute(case,["gmshToFoam","mesh.msh"],"log.gmshToFoam")
            p=case/"constant/polyMesh/boundary"
            s,n=re.subn(r"(\bwalls\s*\{\s*type\s+)patch",r"\1wall",p.read_text())
            assert n==1,n
            p.write_text(s)
            execute(case,["checkMesh"],"log.checkMesh")
            if "Mesh OK." not in (case/"log.checkMesh").read_text():
                raise RuntimeError("checkMesh did not report Mesh OK")
            execute(case,["potentialFoam","-pName","pPotential","-initialiseUBCs"],"log.potentialFoam")
        info=json.loads((case/"case.json").read_text())
        execute(case,[info.get("solver","buoyantSimpleFoam")],"log.solver")
        state["status"]="solver_exited_successfully; convergence requires audit"
    except Exception as exc:
        state["status"]="failed"
        state["error"]=str(exc)
        raise
    finally:
        state["elapsed_s"]=round(time.time()-started,2)
        (case/"run-status.json").write_text(json.dumps(state,indent=2))
    print(json.dumps(state),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case")
    p.add_argument("--resume-prepared",action="store_true")
    args=p.parse_args();run(args.case,not args.resume_prepared)
