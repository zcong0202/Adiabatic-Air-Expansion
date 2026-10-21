"""CAD-linked isothermal internal-nozzle RANS comparison, 3-motor shared flow."""
from pathlib import Path
import json,sys,math,subprocess,time
import numpy as np,gmsh
from seat_cfd import CFD,put,docker
D=float(sys.argv[1]);name='N'+('00' if D==50 else '01')+'_D'+str(int(D));case=CFD/'cases'/name
if case.exists():raise FileExistsError(case)
case.mkdir(parents=True);meshdir=case/'mesh';meshdir.mkdir()
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add(name);o=gmsh.model.occ
# Identical circle-to-rectangle flow shape as the CAD generator, without wall material.
def ring(z,r=None):
 if r:
  a=math.atan2(.08,.14);angles=[a,math.pi-a,math.pi+a,2*math.pi-a];pts=[o.addPoint(r*math.cos(v),r*math.sin(v),z) for v in angles];center=o.addPoint(0,0,z);curves=[o.addCircleArc(pts[i],center,pts[(i+1)%4]) for i in range(4)]
 else:
  pts=[o.addPoint(x,y,z) for x,y in [(.07,.04),(-.07,.04),(-.07,-.04),(.07,-.04)]];curves=[o.addLine(pts[i],pts[(i+1)%4]) for i in range(4)]
 return o.addWire(curves)
r=(D/1000-2*.0024)/2
vol=o.addThruSections([ring(0,r),ring(.03,r),ring(.19),ring(.205)],makeSolid=True,makeRuled=True);o.synchronize();vtag=vol[0][1]
surfs=gmsh.model.getBoundary([(3,vtag)],oriented=False);groups={'inlet':[],'outlet':[],'walls':[]}
for _,tag in surfs:
 bb=o.getBoundingBox(2,tag)
 key='inlet' if abs(bb[2])<1e-6 and abs(bb[5])<1e-6 else 'outlet' if abs(bb[2]-.205)<1e-6 and abs(bb[5]-.205)<1e-6 else 'walls'
 groups[key].append(tag)
for p,tags in groups.items():pg=gmsh.model.addPhysicalGroup(2,tags);gmsh.model.setPhysicalName(2,pg,p)
pg=gmsh.model.addPhysicalGroup(3,[vtag]);gmsh.model.setPhysicalName(3,pg,'fluid')
gmsh.option.setNumber('Mesh.MeshSizeMin',.0035);gmsh.option.setNumber('Mesh.MeshSizeMax',.006);gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.option.setNumber('Mesh.Binary',0);gmsh.model.mesh.generate(3);gmsh.model.mesh.optimize('Netgen');gmsh.write(str(meshdir/'fluid.msh'));gmsh.finalize()
rho=1.288;mass=.0194*3/4;uin=mass/(rho*math.pi*r*r);k=1.5*(.05*uin)**2;omega=math.sqrt(k)/(.09**.25*.07*2*r)
patches=['inlet','outlet','walls']
def field(name,dims,iv,bc,vec=False):put(case,'0/'+name,f'dimensions [{dims}]; internalField uniform {iv}; boundaryField {{ '+' '.join(p+' { '+bc[p]+' }' for p in patches)+' }','volVectorField' if vec else 'volScalarField')
field('U','0 1 -1 0 0 0 0','(0 0 0)',dict(inlet=f'type fixedValue; value uniform (0 0 {uin});',outlet='type zeroGradient;',walls='type noSlip;'),True)
field('p','0 2 -2 0 0 0 0','0',dict(inlet='type zeroGradient;',outlet='type fixedValue; value uniform 0;',walls='type zeroGradient;'))
field('k','0 2 -2 0 0 0 0',str(k),dict(inlet=f'type fixedValue; value uniform {k};',outlet='type zeroGradient;',walls='type kqRWallFunction; value uniform 1e-5;'))
field('omega','0 0 -1 0 0 0 0',str(omega),dict(inlet=f'type fixedValue; value uniform {omega};',outlet='type zeroGradient;',walls='type omegaWallFunction; value uniform 1;'))
field('nut','0 2 -1 0 0 0 0','0',dict(inlet='type calculated; value uniform 0;',outlet='type calculated; value uniform 0;',walls='type nutUSpaldingWallFunction; value uniform 0;'))
put(case,'constant/transportProperties','transportModel Newtonian; nu 1.4e-5;');put(case,'constant/turbulenceProperties','simulationType RAS; RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }')
put(case,'system/fvSchemes','''ddtSchemes { default steadyState; } gradSchemes { default cellLimited Gauss linear 1; }
divSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,k) bounded Gauss upwind; div(phi,omega) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear limited .5; } interpolationSchemes { default linear; } snGradSchemes { default limited .5; } wallDist { method meshWave; }''')
put(case,'system/fvSolution','''solvers { p { solver GAMG; tolerance 1e-9; relTol .01; smoother GaussSeidel; } "(U|k|omega)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-9; relTol .02; } }
SIMPLE { nNonOrthogonalCorrectors 2; consistent yes; residualControl { p 1e-5; U 1e-5; k 1e-5; omega 1e-5; } }
relaxationFactors { fields { p .3; } equations { U .5; k .5; omega .5; } }''')
put(case,'system/controlDict','''application simpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime 1200; deltaT 1; writeControl timeStep; writeInterval 100; purgeWrite 2; writeFormat ascii; writePrecision 10; writeCompression off; runTimeModifiable true;
functions { pressure_in { type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name inlet; operation areaAverage; fields (p); writeFields false; writeControl timeStep; writeInterval 20; }
pressure_out { type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name outlet; operation areaAverage; fields (p); writeFields false; writeControl timeStep; writeInterval 20; } }
''')
put(case,'system/decomposeParDict','numberOfSubdomains 4; method scotch;')
info=dict(case=name,spigot_od_mm=D,inlet_clear_mm=2*r*1000,outlet_mm=[140,80],length_mm=205,nominal_wall_mm=2.4,mass_per_nozzle_kg_s=mass,density_kg_m3=rho,inlet_mean_speed=uin,source='3 active motors feeding a shared collector and four equal branches',status='Internal isothermal CFD; thermal/pressure source response not coupled; no hardware validation')
(case/'case.json').write_text(json.dumps(info,indent=2))
state=dict(status='running',started=time.time());(case/'run-status.json').write_text(json.dumps(state))
for args,log in [(['gmshToFoam','mesh/fluid.msh'],'log.gmshToFoam'),(['checkMesh'],'log.checkMesh'),(['decomposePar','-force'],'log.decomposePar'),(['mpirun','--allow-run-as-root','-np','4','simpleFoam','-parallel'],'log.solver'),(['reconstructPar','-latestTime'],'log.reconstructPar')]:
 with (case/log).open('w') as f:rc=subprocess.run(docker(case,args),stdout=f,stderr=subprocess.STDOUT).returncode
 if rc:state.update(status='failed',error=log);break
 if args[0]=='gmshToFoam':
  import re
  bp=case/'constant/polyMesh/boundary';txt=bp.read_text();txt=re.sub(r'(walls\s*\{\s*type\s+)patch',r'\1wall',txt);bp.write_text(txt)
else:state['status']='solver ended; audit pending'
state['elapsed_s']=time.time()-state['started'];(case/'run-status.json').write_text(json.dumps(state,indent=2));print(state)
