"""Structured axisymmetric prescribed-exit jet screening; SI units.

This is a NEW solver setup, independent of the rejected earlier 3-D runs.
No internal diffuser/source coupling, buoyancy, wind, moisture or body model.
"""
import argparse,json,math,re,subprocess,time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OPT=ROOT/'optimization'
IMAGE='microfluidica/openfoam:2506@sha256:9ab54b92553d58a2e21adaf4ef98a8d0c118a09a1b388bd95480720ed7809b37'
PATCHES=['jet','ambient','far','outlet','wedgeFront','wedgeBack']

def write(case,rel,obj,body,cls='dictionary'):
 p=case/rel;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(f'FoamFile\n{{ version 2.0; format ascii; class {cls}; object {obj}; }}\n'+body+'\n')

def field(case,name,dims,value,bcs,vector=False):
 for p in ['wedgeFront','wedgeBack']:bcs[p]='type wedge;'
 text=f'dimensions [{dims}]; internalField uniform {value};\nboundaryField {{\n'
 text+='\n'.join(f'{p} {{ {bcs[p]} }}' for p in bcs)+'\n}'
 write(case,'0/'+name,name,text,'volVectorField' if vector else 'volScalarField')

def build(name,d=8,mass=.002,cold=5,ambient=35,scale=1,domain=1,model='kEpsilon',prt=.85,iterations=1600,order=2,diffuser=False,angle_deg=5,intensity=.05):
 if not (0<d<60 and mass>0 and 0.3<=scale<=2 and domain>=1 and 0<intensity<.3 and 0<angle_deg<15 and -273.15<cold<ambient):raise ValueError('Invalid geometry, source or mesh parameters')
 case=OPT/'cases'/name
 if case.exists():raise FileExistsError(case)
 case.mkdir(parents=True)
 radius=d/2000;rho=1.2;nu=1.5e-5;u=mass/(rho*math.pi*radius**2)
 if u/335>.25:raise ValueError('Prescribed jet exceeds low-Mach screening limit')
 xs=[0,.05,.2,.6*domain];rs=[0,radius,max(.032,2*radius),.08,.2*domain]
 nx=[max(12,round(45/scale)),max(20,round(85/scale)),max(15,round(75*domain/scale))]
 nr=[max(10,round(16/scale)),max(12,round(28/scale)),max(10,round(24/scale)),max(10,round(22/scale))]
 angle=math.radians(2.5);vertices=[];vmap={}
 def vert(i,j,k):
  r=rs[j];pt=(xs[i],r*math.cos(angle),r*math.sin(angle)*(1 if k else -1))
  key=tuple(round(a,12) for a in pt)
  if key not in vmap:vmap[key]=len(vertices);vertices.append(pt)
  return vmap[key]
 blocks=[];patch={p:[] for p in PATCHES}
 for i in range(len(xs)-1):
  for j in range(len(rs)-1):
   v=[vert(i,j,0),vert(i+1,j,0),vert(i+1,j+1,0),vert(i,j+1,0),vert(i,j,1),vert(i+1,j,1),vert(i+1,j+1,1),vert(i,j+1,1)]
   radialgrading=[1,2,1.5,2][j];axialgrading=[1,1,3][i]
   blocks.append('hex ('+' '.join(map(str,v))+f') ({nx[i]} {nr[j]} 1) simpleGrading ({axialgrading} {radialgrading} 1)')
   if i==0:patch['jet' if j==0 else 'ambient'].append([v[x] for x in [0,4,7,3]])
   if i==len(xs)-2:patch['outlet'].append([v[x] for x in [1,2,6,5]])
   if j==len(rs)-2:patch['far'].append([v[x] for x in [3,7,6,2]])
   patch['wedgeFront'].append([v[x] for x in [0,3,2,1]])
   patch['wedgeBack'].append([v[x] for x in [4,5,6,7]])
 if diffuser:
  # A 5 degree conical diffuser with 15 mm inlet and 10 mm exit lands.
  # Same exit nodes and radial cell count as the external jet block.
  patch['jet']=[];patch['walls']=[]
  cone=(radius-.004)/math.tan(math.radians(angle_deg))
  if cone<=0:raise ValueError('Diffuser exit must exceed 8 mm')
  cx=[-cone-.025,-cone-.010,-.010,0]
  cr=[.004,.004,radius,radius]
  def cv(x,r,k):
   pt=(x,r*math.cos(angle),r*math.sin(angle)*(1 if k else -1))
   key=tuple(round(a,12) for a in pt)
   if key not in vmap:vmap[key]=len(vertices);vertices.append(pt)
   return vmap[key]
  for j in range(3):
   v=[cv(cx[j],0,0),cv(cx[j+1],0,0),cv(cx[j+1],cr[j+1],0),cv(cx[j],cr[j],0),cv(cx[j],0,1),cv(cx[j+1],0,1),cv(cx[j+1],cr[j+1],1),cv(cx[j],cr[j],1)]
   nn=max(10,round((cx[j+1]-cx[j])/.001/scale))
   blocks.append('hex ('+' '.join(map(str,v))+f') ({nn} {nr[0]} 1) simpleGrading (1 1 1)')
   if j==0:patch['jet'].append([v[x] for x in [0,4,7,3]])
   patch['walls'].append([v[x] for x in [3,7,6,2]])
   patch['wedgeFront'].append([v[x] for x in [0,3,2,1]])
   patch['wedgeBack'].append([v[x] for x in [4,5,6,7]])
 text='convertToMeters 1;\nvertices (\n'+'\n'.join('('+' '.join(f'{a:.12g}' for a in v)+')' for v in vertices)+'\n);\nblocks (\n'+'\n'.join(blocks)+'\n);\nedges ();\nboundary (\n'
 for p,faces in patch.items():
  text+=p+' { type '+('wedge' if 'wedge' in p else 'wall' if p=='walls' else 'patch')+'; faces ('+' '.join('('+' '.join(map(str,f))+')' for f in faces)+'); }\n'
 text+='); mergePatchPairs ();'
 write(case,'system/blockMeshDict','blockMeshDict',text)
 inlet_u=mass/(rho*math.pi*.004**2) if diffuser else u
 ub={p:'type pressureInletOutletVelocity; value uniform (0 0 0);' for p in PATCHES};ub['jet']=f'type fixedValue; value uniform ({inlet_u} 0 0);'
 if diffuser:ub['walls']='type noSlip;'
 field(case,'U','0 1 -1 0 0 0 0','(0 0 0)',ub,True)
 pb={p:'type totalPressure; rho none; p0 uniform 0; value uniform 0;' for p in PATCHES};pb['jet']='type zeroGradient;'
 if diffuser:pb['walls']='type zeroGradient;'
 field(case,'p','0 2 -2 0 0 0 0','0',pb)
 kb=1.5*(intensity*inlet_u)**2;eps=.09**.75*kb**1.5/(.07*(8 if diffuser else d)/1000)
 for f,dim,val,jval in [('k','0 2 -2 0 0 0 0',1e-5,kb),('epsilon','0 2 -3 0 0 0 0',1e-5,eps),('omega','0 0 -1 0 0 0 0',1,math.sqrt(kb)/(.09**.25*.07*(8 if diffuser else d)/1000))]:
  bc={p:f'type inletOutlet; inletValue uniform {val}; value uniform {val};' for p in PATCHES};bc['jet']=f'type fixedValue; value uniform {jval};'
  if diffuser:bc['walls']={'k':'type kqRWallFunction; value uniform 0.001;','epsilon':'type epsilonWallFunction; value uniform 0.001;','omega':'type omegaWallFunction; value uniform 1;'}[f]
  field(case,f,dim,str(val),bc)
 nb={p:'type calculated; value uniform 0;' for p in PATCHES}
 if diffuser:nb['walls']='type nutUSpaldingWallFunction; value uniform 0;'
 field(case,'nut','0 2 -1 0 0 0 0','0',nb)
 tb={p:'type inletOutlet; inletValue uniform 0; value uniform 0;' for p in PATCHES};tb['jet']='type fixedValue; value uniform 1;'
 if diffuser:tb['walls']='type zeroGradient;'
 field(case,'theta','0 0 0 0 0 0 0','0',tb)
 write(case,'constant/transportProperties','transportProperties',f'transportModel Newtonian; nu {nu};')
 write(case,'constant/turbulenceProperties','turbulenceProperties',f'simulationType RAS; RAS {{ RASModel {model}; turbulence on; printCoeffs on; }}')
 uscheme='bounded Gauss linearUpwind grad(U)' if order==2 else 'bounded Gauss upwind'
 sscheme='bounded Gauss limitedLinear 1' if order==2 else 'bounded Gauss upwind'
 write(case,'system/fvSchemes','fvSchemes',f'''ddtSchemes {{ default steadyState; }}
gradSchemes {{ default Gauss linear; }}
divSchemes {{ default none; div(phi,U) {uscheme}; div(phi,k) bounded Gauss upwind; div(phi,epsilon) bounded Gauss upwind; div(phi,omega) bounded Gauss upwind; div(phi,theta) {sscheme}; div((nuEff*dev2(T(grad(U))))) Gauss linear; }}
laplacianSchemes {{ default Gauss linear corrected; }}
interpolationSchemes {{ default linear; }} snGradSchemes {{ default corrected; }} wallDist {{ method meshWave; }}''')
 write(case,'system/fvSolution','fvSolution','''solvers {
Phi { solver GAMG; tolerance 1e-9; relTol 0; smoother GaussSeidel; }
p { solver GAMG; tolerance 1e-12; relTol 0; smoother GaussSeidel; }
"(U|k|epsilon|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-11; relTol 0; }
theta { solver PBiCGStab; preconditioner DILU; tolerance 1e-10; relTol 0; }
}
SIMPLE { nNonOrthogonalCorrectors 1; consistent yes; pRefCell 0; pRefValue 0;
residualControl { p 1e-6; U 1e-6; "(k|epsilon|omega)" 1e-5; } }
relaxationFactors { fields { p .3; } equations { U .5; k .5; epsilon .5; omega .5; theta .7; } }
potentialFlow { nNonOrthogonalCorrectors 3; }''')
 functions=f'''sourceTracer {{ type scalarTransport; libs (solverFunctionObjects); field theta; phi phi; alphaD {1/.705}; alphaDt {1/prt}; nCorr 1; tolerance 1e-9; executeControl timeStep; executeInterval 1; writeControl writeTime; }}
ranges {{ type fieldMinMax; libs (fieldFunctionObjects); fields (U theta); executeControl timeStep; executeInterval 20; writeControl timeStep; writeInterval 20; }}
targetProfiles {{ type sets; libs (sampling); writeControl timeStep; writeInterval 50; setFormat raw; interpolationScheme cellPoint; fields (U theta); sets (
 target {{ type uniform; axis y; start (.2 0 0); end (.2 .1 0); nPoints 401; }}
 centerline {{ type uniform; axis x; start (.00001 0 0); end (.5 0 0); nPoints 401; }}
 ); }}
jetFlux {{ type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name jet; operation sum; fields (phi); writeFields false; writeControl timeStep; writeInterval 50; }}'''
 if diffuser:functions+='\nwallYPlus { type yPlus; libs (fieldFunctionObjects); writeControl writeTime; }\n'
 write(case,'system/controlDict','controlDict',f'''application simpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {iterations}; deltaT 1;
writeControl timeStep; writeInterval 100; purgeWrite 3; writeFormat ascii; writePrecision 12; writeCompression off; timeFormat general; timePrecision 9; runTimeModifiable true;
functions {{ {functions} }}''')
 info={'case':name,'diameter_mm':d,'cold_mass_flow_kg_s':mass,'cold_temperature_c':cold,'ambient_temperature_c':ambient,'density_reference_kg_m3':rho,'exit_speed_m_s':u,'mesh_scale':scale,'domain_scale':domain,'turbulence_model':model,'Prt':prt,'convection_order':order,'solver':'simpleFoam + passive thermal deficit','target':{'distance_m':.2,'width_m':.05,'height_m':.05,'objective':'area mean ambient minus air temperature > 6 C'},'assumptions':['Prescribed uniform exit; cold source flow independent of diameter','Constant density, dry air, passive temperature deficit','Axisymmetric still-air jet; wind and buoyancy excluded','No diffuser/source backpressure, wall warming, moisture or skin model'],'validation_status':'Not calibrated against AA measurements'}
 info['inlet_turbulence_intensity']=intensity
 info['internal_diffuser_modeled']=diffuser
 if diffuser:
  info['diffuser']={'inlet_bore_mm':8,'exit_bore_mm':d,'half_angle_deg':angle_deg,'inlet_land_mm':15,'exit_land_mm':10,'cone_length_mm':cone*1000,'total_length_mm':(cone+.025)*1000,'wall_temperature_model':'Adiabatic; heat pickup must be checked separately'}
  info['assumptions'][0]='Prescribed 8 mm source flow into an explicit internal diffuser'
  info['assumptions'][3]='No source backpressure response, wall warming, moisture or skin model'
  info['assumptions'].append('External body omitted; external lip idealized as zero thickness. CAD has a 2 mm wall.')
 (case/'case.json').write_text(json.dumps(info,indent=2));return case

def command(case,args):
 return ['docker','run','--rm','--entrypoint','/bin/bash','-v',f'{ROOT}:/work','-w',f'/work/optimization/cases/{case.name}',IMAGE,'/work/scripts/foam-entry.sh',*args]

def run(case):
 state={'status':'running','start_epoch':time.time(),'image':IMAGE};(case/'run-status.json').write_text(json.dumps(state,indent=2))
 try:
  for args,log in [(['blockMesh'],'log.blockMesh'),(['checkMesh'],'log.checkMesh'),(['potentialFoam','-initialiseUBCs'],'log.potentialFoam'),(['simpleFoam'],'log.solver')]:
   with (case/log).open('w') as out:code=subprocess.run(command(case,args),stdout=out,stderr=subprocess.STDOUT).returncode
   if code:raise RuntimeError(f'{args[0]} failed ({code}), see {log}')
   if args[0]=='checkMesh' and 'Mesh OK.' not in (case/log).read_text():raise RuntimeError('Mesh not accepted')
  state['status']='solver ended; audit required'
 except Exception as e:state.update(status='failed',error=str(e));raise
 finally:state['elapsed_s']=time.time()-state['start_epoch'];(case/'run-status.json').write_text(json.dumps(state,indent=2))
 print(json.dumps(state),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('name');p.add_argument('--diameter',type=float,default=8);p.add_argument('--mass',type=float,default=.002);p.add_argument('--cold',type=float,default=5);p.add_argument('--ambient',type=float,default=35);p.add_argument('--intensity',type=float,default=.05);p.add_argument('--scale',type=float,default=1);p.add_argument('--domain',type=float,default=1);p.add_argument('--model',default='kEpsilon');p.add_argument('--prt',type=float,default=.85);p.add_argument('--iterations',type=int,default=1600);p.add_argument('--order',type=int,default=2);p.add_argument('--angle',type=float,default=5);p.add_argument('--diffuser',action='store_true');p.add_argument('--run',action='store_true');a=p.parse_args()
 c=build(a.name,a.diameter,a.mass,a.cold,ambient=a.ambient,scale=a.scale,domain=a.domain,model=a.model,prt=a.prt,iterations=a.iterations,order=a.order,diffuser=a.diffuser,angle_deg=a.angle,intensity=a.intensity)
 print(c,flush=True)
 if a.run:run(c)


def resume(case,end=4000):
 """Continue an existing mesh and fields; retain the complete solver log."""
 p=case/'system/controlDict';s=p.read_text();s=re.sub(r'startFrom \w+;', 'startFrom latestTime;',s);s=re.sub(r'endTime [^;]+;',f'endTime {end};',s);s=re.sub(r'stopAt \w+;', 'stopAt endTime;',s);p.write_text(s)
 state={'status':'running continuation','start_epoch':time.time(),'image':IMAGE}
 (case/'run-status.json').write_text(json.dumps(state,indent=2))
 with (case/'log.solver').open('a') as out:
  out.write('\nContinuation using latest saved fields.\n');out.flush()
  code=subprocess.run(command(case,['simpleFoam']),stdout=out,stderr=subprocess.STDOUT).returncode
 state.update(status='solver ended; audit required' if code==0 else 'failed',elapsed_s=time.time()-state['start_epoch'],return_code=code)
 (case/'run-status.json').write_text(json.dumps(state,indent=2))
 if code:raise RuntimeError(state)
 print(json.dumps(state),flush=True)
