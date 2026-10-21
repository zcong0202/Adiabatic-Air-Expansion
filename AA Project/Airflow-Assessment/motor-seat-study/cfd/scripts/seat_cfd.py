"""Orthogonal 3D reference-seat CFD. All geometry is an engineering assumption.
OpenFOAM v2506 buoyantPimpleFoam, perfect gas, URANS k-epsilon.
"""
from pathlib import Path
import numpy as np,json,math,subprocess,time,argparse
ROOT=Path(__file__).resolve().parents[3];STUDY=ROOT/'motor-seat-study';CFD=STUDY/'cfd'
IMAGE='microfluidica/openfoam:2506@sha256:9ab54b92553d58a2e21adaf4ef98a8d0c118a09a1b388bd95480720ed7809b37'
CP=1006;R=287.05;PA=101325;TS=274.109275276178;TA=303.15;MASS=.0776

def put(case,rel,body,cls='dictionary',obj=None):
 p=case/rel;p.parent.mkdir(exist_ok=True,parents=True);obj=obj or p.name
 p.write_text(f'FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n'+body+'\n')
def in_box(q,b):return all(a-1e-9<=x<=z+1e-9 for x,(a,z) in zip(q,b))
def geometry():
 return [dict(name='back',box=[[-.04,0],[-.49,.49],[0,1.84]]),dict(name='left',box=[[0,.85],[-.49,-.45],[0,1.8]]),dict(name='right',box=[[0,.85],[.45,.49],[0,1.8]]),dict(name='roof',box=[[0,.85],[-.49,.49],[1.8,1.84]]),dict(name='seat',box=[[.16,.72],[-.33,.33],[.4,.48]]),dict(name='torso',box=[[.28,.42],[-.2,.2],[.48,1.2]]),dict(name='head',box=[[.28,.42],[-.14,.14],[1.2,1.44]]),dict(name='legL',box=[[.42,.56],[-.2,-.07],[.04,.4]]),dict(name='legR',box=[[.42,.56],[.07,.2],[.04,.4]])]

def axis(knots,h):
 return np.concatenate([np.linspace(a,b,max(2,math.ceil((b-a)/h))+1)[:-1] for a,b in zip(knots,knots[1:])]+[np.array([knots[-1]])])
def generate_mesh(case,variant='back',h=.075,large_domain=False):
 # Include every candidate source edge in every mesh. This keeps variants comparable.
 xs=axis(([-1.3,-.5] if large_domain else [-.5])+[-.04,0,.16,.28,.42,.56,.72,.85,1.2,1.65]+([2.5] if large_domain else []),h)
 ys=axis(([-1.8,-1] if large_domain else [-1])+[-.49,-.45,-.33,-.2,-.14,-.07,.07,.14,.2,.33,.45,.49,1]+([1.8] if large_domain else []),h)
 zs=axis([0,.04,.4,.48,.72,.8,.84,.88,1.12,1.2,1.28,1.44,1.8,1.84,2.2]+([3.0] if large_domain else []),h)
 nx,ny,nz=len(xs)-1,len(ys)-1,len(zs)-1; solids=geometry(); cells={};centers=[];vol=[]
 for k in range(nz):
  for j in range(ny):
   for i in range(nx):
    q=((xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2,(zs[k]+zs[k+1])/2)
    if any(in_box(q,b['box']) for b in solids):continue
    cells[i,j,k]=len(centers);centers.append(q);vol.append((xs[i+1]-xs[i])*(ys[j+1]-ys[j])*(zs[k+1]-zs[k]))
 def vid(i,j,k):return (k*(ny+1)+j)*(nx+1)+i
 points=[(x,y,z) for z in zs for y in ys for x in xs]
 def face(i,j,k,d):
  # Outward orientation from current cell.
  return [[vid(i,j,k),vid(i,j,k+1),vid(i,j+1,k+1),vid(i,j+1,k)],
   [vid(i+1,j,k),vid(i+1,j+1,k),vid(i+1,j+1,k+1),vid(i+1,j,k+1)],
   [vid(i,j,k),vid(i+1,j,k),vid(i+1,j,k+1),vid(i,j,k+1)],
   [vid(i,j+1,k),vid(i,j+1,k+1),vid(i+1,j+1,k+1),vid(i+1,j+1,k)],
   [vid(i,j,k),vid(i,j+1,k),vid(i+1,j+1,k),vid(i+1,j,k)],
   [vid(i,j,k+1),vid(i+1,j,k+1),vid(i+1,j+1,k+1),vid(i,j+1,k+1)]][d]
 directions=[(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]
 interior=[];patches={p:[] for p in ['xmin','xmax','ymin','ymax','top','ground','panels','seat','person','jetBack','jetLeftLower','jetRightLower','jetLeftUpper','jetRightUpper']};areas={p:0 for p in patches}
 for (i,j,k),c in cells.items():
  for d,(di,dj,dk) in enumerate(directions):
   neighbour=cells.get((i+di,j+dj,k+dk));f=face(i,j,k,d)
   if neighbour is not None:
    if c<neighbour:interior.append((f,c,neighbour))
    continue
   q=np.mean(np.array([points[v] for v in f]),axis=0);x,y,z=q
   if k==0 and d==4:p='ground'
   elif i==0 and d==0:p='xmin'
   elif i==nx-1 and d==1:p='xmax'
   elif j==0 and d==2:p='ymin'
   elif j==ny-1 and d==3:p='ymax'
   elif k==nz-1 and d==5:p='top'
   else:
    nq=np.array(centers[c])+np.array([di,dj,dk])*1e-4
    # Boundary lies on an obstacle; classify by face location with a small step into obstacle.
    nq=q+np.array([di,dj,dk])*1e-5
    ob=next((b['name'] for b in solids if in_box(nq,b['box'])),'panels')
    p='person' if ob in ['torso','head','legL','legR'] else 'seat' if ob=='seat' else 'panels'
    if variant=='back' and abs(x)<1e-7 and -.07<y<.07 and .72<z<.84:p='jetBack'
    if variant in ['side','upper'] and abs(abs(y)-.45)<1e-7 and .42<x<.56:
     side='Left' if y<0 else 'Right'
     if variant=='side' and .8<z<.88:p='jet'+side+'Lower'
     if 1.2<z<1.28:p='jet'+side+'Upper'
   pp=np.array([points[v] for v in f]);a=float(np.linalg.norm(np.cross(pp[1]-pp[0],pp[3]-pp[0])))
   patches[p].append((f,c));areas[p]+=a
 patches={p:v for p,v in patches.items() if v};areas={p:areas[p] for p in patches}
 allfaces=[v[0] for v in interior];owners=[v[1] for v in interior];neighbours=[v[2] for v in interior];boundary=[]
 for p,rows in patches.items():
  start=len(allfaces);allfaces += [v[0] for v in rows];owners += [v[1] for v in rows]
  typ='patch' if p in ['xmin','xmax','ymin','ymax','top'] or p.startswith('jet') else 'wall'
  boundary.append(f'{p} {{ type {typ}; nFaces {len(rows)}; startFace {start}; }}')
 # Remove unused points so checkMesh catches real problems only.
 used=sorted(set(v for f in allfaces for v in f));remap={v:i for i,v in enumerate(used)}
 put(case,'constant/polyMesh/points',str(len(used))+'\n(\n'+'\n'.join('('+' '.join(f'{x:.12g}' for x in points[v])+')' for v in used)+'\n)','vectorField')
 put(case,'constant/polyMesh/faces',str(len(allfaces))+'\n(\n'+'\n'.join('4('+' '.join(str(remap[v]) for v in f)+')' for f in allfaces)+'\n)','faceList')
 for name,arr in [('owner',owners),('neighbour',neighbours)]:put(case,'constant/polyMesh/'+name,str(len(arr))+'\n(\n'+'\n'.join(map(str,arr))+'\n)','labelList')
 put(case,'constant/polyMesh/boundary',str(len(boundary))+'\n(\n'+'\n'.join(boundary)+'\n)','polyBoundaryMesh')
 np.savez_compressed(case/'mesh-metadata.npz',centers=centers,volumes=vol,x=xs,y=ys,z=zs,indices=np.array(list(cells)))
 # Save native boundary geometry for independent flux audit and skin-area averaging.
 np.savez_compressed(case/'boundary-metadata.npz',**{p:np.array([[v[1],*np.mean([points[n] for n in v[0]],axis=0),float(np.linalg.norm(np.cross(np.array(points[v[0][1]])-points[v[0][0]],np.array(points[v[0][3]])-points[v[0][0]])))] for v in rows]) for p,rows in patches.items()})
 return patches,areas,len(centers)

def build(name,variant='back',h=.075,end=30,wind=0,direction='front',source_c=TS-273.15,ambient_c=30,heat=100,panel_heat=0,large_domain=False,freestream_tangent=False):
 case=CFD/'cases'/name
 if case.exists():raise FileExistsError(case)
 case.mkdir(parents=True);patches,areas,n=generate_mesh(case,variant,h,large_domain);jets=[p for p in patches if p.startswith('jet')];opens=['xmin','xmax','ymin','ymax','top'];walls=[p for p in patches if p not in opens+jets]
 ta=ambient_c+273.15;ts=source_c+273.15;rhoc=PA/(R*ts)
 velocity=(-wind,0,0) if direction=='front' else (0,wind,0)
 uvec='('+' '.join(map(str,velocity))+')';totalarea=sum(areas[p] for p in jets);uin=MASS/(rhoc*totalarea)
 def field(name,dims,val,bc,vec=False):put(case,'0/'+name,f'dimensions [{dims}]; internalField uniform {val};\nboundaryField {{\n'+'\n'.join(p+' { '+bc(p)+' }' for p in patches)+'\n}','volVectorField' if vec else 'volScalarField')
 # Open boundaries: fixed wind only on upstream side; pressure/velocity mixed elsewhere.
 upstream='xmax' if direction=='front' else 'ymin'
 def ubc(p):
  if p in jets:return f'type flowRateInletVelocity; massFlowRate {MASS*areas[p]/totalarea}; rho rho; rhoInlet {rhoc}; value uniform (0 0 0);'
  if p in walls:return 'type noSlip;'
  if wind and p==upstream:return f'type fixedValue; value uniform {uvec};'
  return f'type pressureInletOutletVelocity; '+(f'tangentialVelocity uniform {uvec}; ' if freestream_tangent else '')+f'value uniform {uvec};'
 field('U','0 1 -1 0 0 0 0',uvec,ubc,True)
 field('p','1 -1 -2 0 0 0 0','101325',lambda p:'type calculated; value uniform 101325;')
 def pbc(p):
  if p in walls+jets or (wind and p==upstream):return 'type fixedFluxPressure; value uniform 101325;'
  b=np.load(case/'boundary-metadata.npz')[p]; zz=b[:,3]; pp=PA*np.exp(-9.81*zz/(8314.46261815324/28.965*ta)); vals=' '.join(f'{v:.12g}' for v in pp)
  return f'type prghPressure; rho rho; p nonuniform List<scalar> {len(pp)} ({vals}); value uniform 101325;'
 field('p_rgh','1 -1 -2 0 0 0 0','101325',pbc)
 # Initialise the exact isothermal ideal-gas hydrostatic atmosphere.
 zz=np.load(case/'mesh-metadata.npz')['centers'][:,2]; gas=8314.46261815324/28.965; pp=PA*np.exp(-9.81*zz/(gas*ta)); prgh=pp*(1+9.81*zz/(gas*ta))
 for fld,a in [('p',pp),('p_rgh',prgh)]:
  fp=case/'0'/fld;txt=fp.read_text();txt=txt.replace('internalField uniform 101325;',f'internalField nonuniform List<scalar> {len(a)} ('+' '.join(f'{v:.12g}' for v in a)+');');fp.write_text(txt)
 def tbc(p):
  if p in jets:return f'type fixedValue; value uniform {ts};'
  if p=='panels' and panel_heat>0:return f'type externalWallHeatFluxTemperature; mode power; Q {panel_heat}; kappaMethod fluidThermo; value uniform {ta};'
  if p=='person':return f'type externalWallHeatFluxTemperature; mode power; Q {heat}; kappaMethod fluidThermo; value uniform {ta};'
  if p in walls:return 'type zeroGradient;'
  return f'type inletOutlet; inletValue uniform {ta}; value uniform {ta};'
 field('T','0 0 0 1 0 0 0',str(ta),tbc)
 intensity=.05;kjet=max(1e-8,1.5*(intensity*uin)**2);kamb=max(1e-5,1.5*(.05*max(wind,.05))**2);epsjet=max(1e-10,.09**.75*kjet**1.5/(.07*.08))
 for f,dims,initial,jet,wall in [('k','0 2 -2 0 0 0 0',kamb,kjet,'type kqRWallFunction; value uniform 1e-5;'),('epsilon','0 2 -3 0 0 0 0',max(1e-6,.09**.75*kamb**1.5/.05),epsjet,'type epsilonWallFunction; value uniform 1e-5;')]:
  field(f,dims,str(initial),lambda p,iv=initial,jv=jet,w=wall: w if p in walls else f'type fixedValue; value uniform {jv};' if p in jets else f'type inletOutlet; inletValue uniform {iv}; value uniform {iv};')
 field('nut','0 2 -1 0 0 0 0','0',lambda p:'type nutkWallFunction; value uniform 0;' if p in walls else 'type calculated; value uniform 0;')
 field('alphat','1 -1 -1 0 0 0 0','0',lambda p:'type compressible::alphatWallFunction; Prt 0.85; value uniform 0;' if p in walls else 'type calculated; value uniform 0;')
 # The compressible scalarTransport uses rho and mass flux; D = dynamic diffusivity.
 field('origin','0 0 0 0 0 0 0','0',lambda p:'type fixedValue; value uniform 1;' if p in jets else 'type zeroGradient;' if p in walls else 'type inletOutlet; inletValue uniform 0; value uniform 0;')
 put(case,'constant/g','dimensions [0 1 -2 0 0 0 0]; value (0 0 -9.81);','uniformDimensionedVectorField')
 put(case,'constant/thermophysicalProperties',f'''thermoType {{ type heRhoThermo; mixture pureMixture; transport const; thermo hConst; equationOfState perfectGas; specie specie; energy sensibleEnthalpy; }}
pRef 101325; mixture {{ specie {{ molWeight 28.965; }} thermodynamics {{ Cp 1006; Hf 0; }} transport {{ mu 1.8e-5; Pr 0.71; }} }}''')
 put(case,'constant/turbulenceProperties','simulationType RAS; RAS { RASModel kEpsilon; turbulence on; printCoeffs on; }')
 put(case,'system/fvSchemes','''ddtSchemes { default Euler; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes { default none; div(phi,U) Gauss linearUpwind grad(U); div(phi,h) Gauss limitedLinear 1; div(phi,e) Gauss limitedLinear 1; div(phi,K) Gauss upwind; div(phi,Ekp) Gauss upwind; div(phi,k) Gauss upwind; div(phi,epsilon) Gauss upwind; div(phi,origin) Gauss limitedLinear 1; div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; } snGradSchemes { default corrected; } wallDist { method meshWave; }''')
 put(case,'system/fvSolution','''solvers {
"rho.*" { solver PCG; preconditioner DIC; tolerance 1e-10; relTol 0; }
p_rgh { solver GAMG; smoother GaussSeidel; tolerance 1e-7; relTol .02; }
p_rghFinal { $p_rgh; relTol 0; }
"(U|h|e|k|epsilon|origin)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol .02; }
"(U|h|e|k|epsilon|origin)Final" { $U; relTol 0; }
}
PIMPLE { momentumPredictor yes; nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 101325; }
relaxationFactors { equations { "(U|h|k|epsilon)" 1; } }''')
 functions='''ranges { type fieldMinMax; libs (fieldFunctionObjects); fields (T U origin); executeControl timeStep; executeInterval 20; writeControl writeTime; }
sourceOrigin { type scalarTransport; libs (solverFunctionObjects); field origin; rho rho; phi phi; schemesField origin; alphaD 1.40845; alphaDt 1.17647; nCorr 1; tolerance 1e-8; executeControl timeStep; executeInterval 1; writeControl writeTime; }
wallHeat { type wallHeatFlux; libs (fieldFunctionObjects); patches (person panels seat ground); writeControl writeTime; }
'''
 for p in patches:
  if p in opens+jets:functions+=f'flux_{p} {{ type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name {p}; operation sum; fields (phi); writeFields false; writeControl writeTime; }}\n'
 put(case,'system/controlDict',f'''application buoyantPimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT .005;
writeControl adjustableRunTime; writeInterval 1; purgeWrite 0; writeFormat ascii; writePrecision 10; writeCompression off; timeFormat general; timePrecision 8; runTimeModifiable true; adjustTimeStep yes; maxCo 1; maxDeltaT .04;
functions {{ {functions} }}''')
 put(case,'system/decomposeParDict','numberOfSubdomains 4; method scotch;')
 info=dict(large_domain=large_domain,freestream_tangent=freestream_tangent,pressure_boundary_revision='Hydrostatic ambient pressure profile with prghPressure; exact hydrostatic initial p and p_rgh',case=name,variant=variant,cells=n,grid_max_h_m=h,source_mass_kg_s=MASS,source_c=source_c,ambient_c=ambient_c,source_mean_speed_m_s=uin,source_area_m2=totalarea,patch_areas_m2=areas,wind_m_s=wind,wind_direction=direction,person_heat_w=heat,additional_panel_heat_w=panel_heat,solver='buoyantPimpleFoam',model='Perfect-gas variable-density transient URANS k-epsilon; dry; adiabatic panels; fixed 100 W person heat input',geometry=geometry(),source_thermal_status='Conditional loaded-motor catalogue pair; not measured',scope='Reference geometry; exact user seat dimensions unknown',body_regions=dict(torso=[[.42,.62],[-.22,.22],[.72,1.16]],neck=[[.42,.62],[-.16,.16],[1.2,1.4]],occupied=[[0,.85],[-.45,.45],[.48,1.6]]),limitations=['Block manikin and enclosure geometry assumed','No radiation, solar, moisture, motor internals or resolved collector/nozzle interior','Fixed source mass/temperature; actual backpressure coupling still needs supplier map','Square/slot boundary representations; not literal round control B geometry','100 W all enters air as convection; no prescribed skin temperature','Grid-averaged temperature regions, not skin heat removal or comfort'])
 (case/'case.json').write_text(json.dumps(info,indent=2));return case

def docker(case,args):return ['docker','run','--rm','--name','aa-seat-'+case.name.lower().replace('_','-'),'--entrypoint','/bin/bash','-v',f'{ROOT}:/work','-w',f'/work/motor-seat-study/cfd/cases/{case.name}',IMAGE,'/work/scripts/foam-entry.sh',*args]
def run(case,parallel=True):
 state=dict(status='running',started=time.time(),image=IMAGE);(case/'run-status.json').write_text(json.dumps(state,indent=2))
 jobs=[(['checkMesh','-allGeometry','-allTopology'],'log.checkMesh')]
 if parallel:jobs += [(['decomposePar','-force'],'log.decomposePar'),(['mpirun','--allow-run-as-root','-np','4','buoyantPimpleFoam','-parallel'],'log.solver'),(['reconstructPar'],'log.reconstructPar')]
 else:jobs += [(['buoyantPimpleFoam'],'log.solver')]
 try:
  for args,log in jobs:
   with (case/log).open('w') as f:rc=subprocess.run(docker(case,args),stdout=f,stderr=subprocess.STDOUT).returncode
   if rc:raise RuntimeError(f'{args[0]} failed: {log}')
   if args[0]=='checkMesh' and 'Mesh OK.' not in (case/log).read_text():raise RuntimeError('Mesh not accepted')
  state['status']='solver ended; audit pending'
 except Exception as e:state.update(status='failed',error=str(e));raise
 finally:state['elapsed_s']=time.time()-state['started'];(case/'run-status.json').write_text(json.dumps(state,indent=2))
 print(json.dumps(state),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--variant',default='back');p.add_argument('--h',type=float,default=.075);p.add_argument('--end',type=float,default=30);p.add_argument('--wind',type=float,default=0);p.add_argument('--direction',default='front');p.add_argument('--source',type=float,default=TS-273.15);p.add_argument('--run',action='store_true');p.add_argument('--serial',action='store_true');a=p.parse_args();c=build(a.name,a.variant,a.h,a.end,a.wind,a.direction,a.source);print(c,flush=True)
 if a.run:run(c,not a.serial)
