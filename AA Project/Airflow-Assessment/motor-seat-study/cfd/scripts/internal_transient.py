from pathlib import Path
import shutil,re,json,subprocess,time
from seat_cfd import CFD,put,docker
from audit_seat import block
src=CFD/'cases/N01_D100';c=CFD/'cases/N02_D100_transient'
if c.exists():raise FileExistsError(c)
c.mkdir();shutil.copytree(src/'constant',c/'constant');shutil.copytree(src/'1200',c/'0');shutil.copytree(src/'system',c/'system');shutil.copyfile(src/'log.checkMesh',c/'log.checkMesh')
p=c/'0/U';s=p.read_text();old=block(s[s.index('boundaryField'):],'inlet');s=s.replace(old,'\n type flowRateInletVelocity; volumetricFlowRate 0.011296583850931677; value uniform (0 0 1.5870234799);\n',1);p.write_text(s)
for f in ['U','p','k','omega','nut']:
 p=c/'0'/f;s=p.read_text();s=re.sub(r'location\s+"1200"','location "0"',s);p.write_text(s)
p=c/'system/fvSchemes';p.write_text(p.read_text().replace('default steadyState','default Euler'))
put(c,'system/fvSolution','''solvers {
p { solver GAMG; smoother GaussSeidel; tolerance 1e-9; relTol .01; }
pFinal { $p; relTol 0; }
"(U|k|omega)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-9; relTol .01; }
"(U|k|omega)Final" { $U; relTol 0; }
}
PIMPLE { momentumPredictor yes; nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 1; }
relaxationFactors { equations { U 1; k 1; omega 1; } }''')
put(c,'system/controlDict','''application pimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime 1; deltaT .001;
writeControl adjustableRunTime; writeInterval .1; purgeWrite 0; writeFormat ascii; writePrecision 10; writeCompression off; timePrecision 8; runTimeModifiable true; adjustTimeStep yes; maxCo 1; maxDeltaT .01;
functions { pressure_in { type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name inlet; operation areaAverage; fields (p); writeFields false; writeControl writeTime; } }
''')
info=json.loads((src/'case.json').read_text());info.update(case=c.name,solver='pimpleFoam',source_case=src.name,initialization='SST steady candidate at iteration1200; not accepted as converged. 1 s time-dependent follow-up.');(c/'case.json').write_text(json.dumps(info,indent=2))
state=dict(status='running',started=time.time());(c/'run-status.json').write_text(json.dumps(state))
for args,log in [(['decomposePar','-force'],'log.decomposePar'),(['mpirun','--allow-run-as-root','-np','4','pimpleFoam','-parallel'],'log.solver'),(['reconstructPar'],'log.reconstructPar')]:
 with (c/log).open('w') as f:rc=subprocess.run(docker(c,args),stdout=f,stderr=subprocess.STDOUT).returncode
 if rc:state.update(status='failed',error=log);break
else:state['status']='solver ended; audit pending'
state['elapsed_s']=time.time()-state['started'];(c/'run-status.json').write_text(json.dumps(state,indent=2));print(state)
