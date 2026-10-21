"""Create reproducible OpenFOAM v2506 conceptual cold-jet cases."""
import argparse
import json
import math
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCHES=["coldInlet","walls","upstream","downstream","windIn","windOut","top","bottom"]


def header(obj, cls="dictionary"):
    return f"FoamFile\n{{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def write(case, rel, obj, text, cls="dictionary"):
    p=case/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(header(obj,cls)+text+"\n")


def field(case,name,dim,internal,bcs,vector=False):
    text=f"dimensions [{dim}];\ninternalField uniform {internal};\nboundaryField\n{{\n"
    for patch in PATCHES:
        text+=f"{patch}\n{{ {bcs[patch]} }}\n"
    text+="}\n"
    write(case,"0/"+name,name,text,"volVectorField" if vector else "volScalarField")


def build(design,wind=0.0,mass=.002,cold=15.,iterations=1200,tag=None,mesh_scale=1.,domain_scale=1.,model="realizableKE",prt=.85):
    label=tag or f"{design}_w{wind:g}_m{mass*1000:g}_T{cold:g}"
    case=ROOT/"cases"/label
    if case.exists():
        raise FileExistsError(f"Refusing to replace existing case {case}")
    case.mkdir(parents=True)
    meshdir=ROOT/"designs"/design
    if mesh_scale!=1 or domain_scale!=1:
        meshdir/=f"mesh_s{mesh_scale:g}_d{domain_scale:g}"
    shutil.copyfile(meshdir/"mesh.msh",case/"mesh.msh")
    info=json.loads((ROOT/"designs"/design/"design.json").read_text())
    ambient=308.15
    tc=cold+273.15
    rho=101325/(287.05*tc)
    u=mass/(rho*math.pi*.004**2)
    k=1.5*(.05*u)**2
    eps=.09**.75*k**1.5/.00056
    windvec=f"(0 {wind} 0)"
    openpatches=PATCHES[2:]
    inletwall={"coldInlet":f"type flowRateInletVelocity; massFlowRate constant {mass}; rho rho; rhoInlet {rho}; value uniform ({u} 0 0);", "walls":"type noSlip;"}
    ubc={**inletwall,**{p:f"type pressureInletOutletVelocity; tangentialVelocity uniform {windvec}; value uniform {windvec};" for p in openpatches}}
    if wind>0:
        ubc["windIn"]=f"type fixedValue; value uniform {windvec};"
    field(case,"U","0 1 -1 0 0 0 0",windvec,ubc,True)
    pbc={p:"type calculated; value uniform 101325;" for p in PATCHES}
    field(case,"p","1 -1 -2 0 0 0 0","101325",pbc)
    potentialbc={p:("type zeroGradient;" if p in ["coldInlet","walls"] else "type fixedValue; value uniform 0;") for p in PATCHES}
    field(case,"pPotential","0 2 -2 0 0 0 0","0",potentialbc)
    pbc={p:"type prghPressure; p uniform 101325; rho rho; value uniform 101325;" for p in openpatches}
    pbc.update({"coldInlet":"type fixedFluxPressure; value uniform 101325;","walls":"type fixedFluxPressure; value uniform 101325;"})
    if wind>0:pbc["windIn"]="type fixedFluxPressure; value uniform 101325;"
    field(case,"p_rgh","1 -1 -2 0 0 0 0","101325",pbc)
    tbc={p:f"type inletOutlet; inletValue uniform {ambient}; value uniform {ambient};" for p in openpatches}
    tbc.update({"coldInlet":f"type totalTemperature; U U; phi phi; psi thermo:psi; gamma 1.4; T0 uniform {tc}; value uniform {tc};","walls":"type zeroGradient;"})
    field(case,"T","0 0 0 1 0 0 0",str(ambient),tbc)
    kbc={p:"type inletOutlet; inletValue uniform 0.001; value uniform 0.001;" for p in openpatches}
    kbc.update({"coldInlet":f"type fixedValue; value uniform {k};","walls":"type kqRWallFunction; value uniform 0.001;"})
    field(case,"k","0 2 -2 0 0 0 0","0.001",kbc)
    ebc={p:"type inletOutlet; inletValue uniform 0.001; value uniform 0.001;" for p in openpatches}
    ebc.update({"coldInlet":f"type fixedValue; value uniform {eps};","walls":"type epsilonWallFunction; value uniform 0.001;"})
    field(case,"epsilon","0 2 -3 0 0 0 0","0.001",ebc)
    obc={p:"type inletOutlet; inletValue uniform 1; value uniform 1;" for p in openpatches}
    obc.update({"coldInlet":f"type fixedValue; value uniform {math.sqrt(k)/(.09**.25*.00056)};","walls":"type omegaWallFunction; value uniform 1;"})
    field(case,"omega","0 0 -1 0 0 0 0","1",obc)
    nbc={p:"type calculated; value uniform 0;" for p in PATCHES}
    nbc["walls"]="type nutkWallFunction; value uniform 0;"
    field(case,"nut","0 2 -1 0 0 0 0","0",nbc)
    abc={p:"type calculated; value uniform 0;" for p in PATCHES}
    abc["walls"]=f"type compressible::alphatWallFunction; Prt {prt}; value uniform 0;"
    field(case,"alphat","1 -1 -1 0 0 0 0","0",abc)
    cbc={p:"type inletOutlet; inletValue uniform 0; value uniform 0;" for p in openpatches}
    cbc.update({"coldInlet":"type fixedValue; value uniform 1;","walls":"type zeroGradient;"})
    field(case,"c","0 0 0 0 0 0 0","0",cbc)
    write(case,"constant/thermophysicalProperties","thermophysicalProperties",f"""
thermoType {{ type heRhoThermo; mixture pureMixture; transport const; thermo hConst; equationOfState perfectGas; specie specie; energy sensibleEnthalpy; }}
mixture {{ specie {{ molWeight 28.96; }} thermodynamics {{ Cp 1005; Hf 0; }} transport {{ mu 1.831e-05; Pr 0.705; }} }}
""")
    write(case,"constant/turbulenceProperties","turbulenceProperties",f"simulationType RAS;\nRAS {{ RASModel {model}; turbulence on; printCoeffs on; {model}Coeffs {{ Prt {prt}; }} }}")
    write(case,"constant/g","g","dimensions [0 1 -2 0 0 0 0]; value (0 0 -9.81);","uniformDimensionedVectorField")
    write(case,"constant/radiationProperties","radiationProperties","radiationModel none;")
    write(case,"system/fvSchemes","fvSchemes","""
ddtSchemes { default steadyState; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes {
 default none;
 div(phi,U) bounded Gauss upwind;
 div(phi,h) bounded Gauss upwind;
 div(phi,K) bounded Gauss upwind;
 div(phi,k) bounded Gauss upwind;
 div(phi,epsilon) bounded Gauss upwind;
 div(phi,omega) bounded Gauss upwind;
 div(phi,c) bounded Gauss upwind;
 div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
""")
    write(case,"system/fvSolution","fvSolution","""
solvers {
 T { solver PBiCGStab; preconditioner DILU; tolerance 1e-10; relTol 0; }
 c { solver PBiCGStab; preconditioner DILU; tolerance 1e-10; relTol 0; }
 Phi { solver GAMG; tolerance 1e-9; relTol 0.001; smoother DICGaussSeidel; }
 p_rgh { solver GAMG; tolerance 1e-9; relTol 0; smoother DICGaussSeidel; }
 "(U|h|k|epsilon|omega|c)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-9; relTol 0.05; }
}
SIMPLE { momentumPredictor yes; nNonOrthogonalCorrectors 2;
 residualControl { p_rgh 1e-5; U 1e-5; h 1e-5; "(k|epsilon|omega)" 1e-4; }
}
relaxationFactors { fields { rho 0.5; p_rgh 0.25; } equations { U 0.5; h 0.6; k 0.5; epsilon 0.5; omega 0.5; c 1; } }
potentialFlow { PhiRefCell 0; PhiRefValue 0; nNonOrthogonalCorrectors 5; }
""")
    clearx=.2+info["front_x_m"]
    functions=f"""
sourceTracer {{ type scalarTransport; libs (solverFunctionObjects); field c; phi phi; rho rho; alphaD {1/.705}; alphaDt {1/prt}; nCorr 1; tolerance 1e-7; executeControl timeStep; executeInterval 1; writeControl writeTime; }}
range {{ type fieldMinMax; libs (fieldFunctionObjects); fields (T U c); executeControl timeStep; executeInterval 50; writeControl writeTime; }}
inletFlux {{ type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name coldInlet; operation sum; fields (phi); writeFields false; writeControl timeStep; writeInterval 50; }}
inletPressure {{ type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name coldInlet; operation areaAverage; fields (p T); writeFields false; writeControl timeStep; writeInterval 50; }}
wallYPlus {{ type yPlus; libs (fieldFunctionObjects); writeControl writeTime; }}
cuts {{ type surfaces; libs (sampling); writeControl writeTime; surfaceFormat vtk; interpolationScheme cellPoint; fields (T U c p rho);
 surfaces {{
  target {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (.2 0 0); normal (1 0 0); }} interpolate true; }}
  clearance {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point ({clearx} 0 0); normal (1 0 0); }} interpolate true; }}
  midplane {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 0); normal (0 0 1); }} interpolate true; }}
 }}
}}
"""
    write(case,"system/controlDict","controlDict",f"""
application buoyantSimpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime {iterations}; deltaT 1;
writeControl timeStep; writeInterval 200; purgeWrite 1; writeFormat ascii; writePrecision 10; writeCompression off; timeFormat general; timePrecision 8; runTimeModifiable true;
functions {{ {functions} }}
""")
    write(case,"system/decomposeParDict","decomposeParDict","numberOfSubdomains 4; method scotch;")
    manifest={"design":design,"case":label,"cold_mass_flow_kg_s":mass,"cold_total_temperature_c":cold,"ambient_temperature_c":35,"crosswind_m_s":wind,"inlet_turbulence_intensity":.05,"model":model,"Prt":prt,"mesh_scale":mesh_scale,"domain_scale":domain_scale,"iterations_requested":iterations,"source_static_pressure_estimate_pa":101325,"source_turbulence_initial_speed_m_s":u,"target_primary_exit_x_m":.2,"target_clearance_x_m":clearx,"nominal_source_sensible_capacity_w":mass*1005*(35-cold),"wall_heat_transfer":"Adiabatic; no condensation, radiation, skin or internal vortex modeled.","status":"Conceptual assumptions; no measured AA boundary conditions."}
    (case/"case.json").write_text(json.dumps(manifest,indent=2))
    (case/"case.foam").touch()
    print(case)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("design")
    p.add_argument("--wind",type=float,default=0)
    p.add_argument("--mass",type=float,default=.002)
    p.add_argument("--cold",type=float,default=15)
    p.add_argument("--iterations",type=int,default=1200)
    p.add_argument("--tag")
    p.add_argument("--mesh-scale",type=float,default=1)
    p.add_argument("--domain-scale",type=float,default=1)
    p.add_argument("--model",default="realizableKE")
    p.add_argument("--prt",type=float,default=.85)
    a=p.parse_args();build(a.design,a.wind,a.mass,a.cold,a.iterations,a.tag,a.mesh_scale,a.domain_scale,a.model,a.prt)
