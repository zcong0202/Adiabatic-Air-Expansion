"""Consistent low-Mach screening model; independent of ideal-gas attempts.

T is transported as an approximate total temperature. Buoyancy uses this
temperature with a linear density law. Kinetic-energy recovery is omitted
from the temperature PDE. This is stated explicitly in the case manifest.
"""
import json
import re
import shutil
import sys
import numpy as np
from build_case import ROOT, build, field, write, PATCHES
from restart_thermal import internal, replace_internal


def build_bouss(design,source_name,wind=0.0,tag=None,iterations=800):
    name=tag or design+f'_bouss_w{wind:g}'
    source=ROOT/'cases'/source_name
    latest=max([p for p in source.iterdir() if p.is_dir() and p.name.isdigit()],key=lambda p:int(p.name))
    build(design,wind,.002,15,iterations,name,model='kEpsilon')
    case=ROOT/'cases'/name
    shutil.copytree(source/'constant/polyMesh',case/'constant/polyMesh')
    shutil.copyfile(source/'log.checkMesh',case/'log.checkMesh')
    rho=101325/(287.05*288.15)
    for f in ['U','k','epsilon','nut']:
        replace_internal(case/'0'/f,internal(latest/f))
    # Enforce the prescribed volume rate corresponding to the cold mass rate.
    p=case/'0/U';s=p.read_text();s=re.sub(r'massFlowRate constant [^;]+; rho rho; rhoInlet [^;]+;',f'volumetricFlowRate constant {0.002/rho};',s);p.write_text(s)
    pbcs={p:('type zeroGradient;' if p in ['coldInlet','walls'] else 'type fixedValue; value uniform 0;') for p in PATCHES}
    if wind>0:pbcs['windIn']='type zeroGradient;'
    field(case,'p','0 2 -2 0 0 0 0','0',pbcs)
    pbcs={p:'type fixedValue; value uniform 0;' for p in PATCHES[2:]};pbcs.update({'coldInlet':'type fixedFluxPressure; value uniform 0;','walls':'type fixedFluxPressure; value uniform 0;'})
    if wind>0:pbcs['windIn']='type fixedFluxPressure; value uniform 0;'
    field(case,'p_rgh','0 2 -2 0 0 0 0','0',pbcs)
    tbc={p:'type inletOutlet; inletValue uniform 308.15; value uniform 308.15;' for p in PATCHES[2:]};tbc.update({'coldInlet':'type fixedValue; value uniform 288.15;','walls':'type zeroGradient;'})
    field(case,'T','0 0 0 1 0 0 0','308.15',tbc)
    abc={p:'type calculated; value uniform 0;' for p in PATCHES};abc['walls']='type alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;'
    field(case,'alphat','0 2 -1 0 0 0 0','0',abc)
    # Initialize consistently from an existing scalar where available.
    if (latest/'c').exists():
        c=np.clip(internal(latest/'c'),0,1)
    else:
        c=np.zeros(len(internal(latest/'k')))
    replace_internal(case/'0/c',c);replace_internal(case/'0/T',308.15-20*c)
    write(case,'constant/transportProperties','transportProperties',f'transportModel Newtonian; nu {1.831e-5/rho}; beta {1/298.15}; TRef 298.15; Pr 0.705; Prt 0.85;')
    p=case/'system/fvSchemes';s=p.read_text();s=s.replace('divSchemes {','divSchemes {\n div(phi,T) bounded Gauss upwind;\n div((nuEff*dev2(T(grad(U))))) Gauss linear;');p.write_text(s)
    p=case/'system/fvSolution';s=p.read_text().replace('(U|h|k|epsilon|omega|c)','(U|T|h|k|epsilon|omega|c)').replace(' h 1e-5;',' T 1e-5;').replace('rho 0.5; p_rgh 0.25','rho 0.5; p_rgh 0.3').replace('U 0.5; h 0.6;','U 0.4; T 1; h 0.6;');s=s.replace('nNonOrthogonalCorrectors 2;','nNonOrthogonalCorrectors 2; pRefCell 0; pRefValue 0;');p.write_text(s)
    p=case/'system/controlDict';s=p.read_text().replace('application buoyantSimpleFoam;','application buoyantBoussinesqSimpleFoam;').replace('writeInterval 200;','writeInterval 100;').replace('fields (T U c p rho);','fields (T U c p);').replace('writeControl timeStep; writeInterval 50;','writeControl timeStep; writeInterval 50;');p.write_text(s)
    info=json.loads((case/'case.json').read_text())
    info.update({'solver':'buoyantBoussinesqSimpleFoam','density_model':'Boussinesq; constant density in continuity, linear variation for buoyancy','rho_reference_kg_m3':rho,'temperature_interpretation':'Approximate total temperature; kinetic-energy recovery omitted from PDE. At target speeds this correction is small; near compact outlet it can approach 2 K.','buoyancy_density_approximation':'20 K range / 298.15 K = 6.7%; source uncertainty larger. Not calibrated.','initialization_source':source_name,'initialization_iteration':int(latest.name),'model':'kEpsilon','convection_scheme':'Bounded first order for screening; mesh sensitivity required','nominal_source_sensible_capacity_w':40.2})
    (case/'case.json').write_text(json.dumps(info,indent=2))
    print(name)


if __name__=='__main__':
    build_bouss(sys.argv[1],sys.argv[2],float(sys.argv[3]) if len(sys.argv)>3 else 0)
