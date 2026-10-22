"""Independent EOS checks and native-field provenance checks for the computation panel."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from CoolProp.CoolProp import PropsSI
root=Path(__file__).resolve().parents[1]
points=[]
for p,t,pout in [(1.2,290,1.01325),(7.31325,313.15,1.0142),(11.71325,313.15,1.015),(201.01325,313.15,7.31325),(9.45,325.3,1.15),(5.66,298.4,1.05),(330.4,310.7,10.9)]:
 h=PropsSI('Hmass','T',t,'P',p*1e5,'Air');s=PropsSI('Smass','T',t,'P',p*1e5,'Air')
 ts=PropsSI('T','Smass',s,'P',pout*1e5,'Air')
 points.append({'p_bar':p,'T_k':t,'pout_bar':pout,'h':h,'s':s,'rho':PropsSI('Dmass','T',t,'P',p*1e5,'Air'),'throttle_T':PropsSI('T','Hmass',h,'P',pout*1e5,'Air'),'isentropic_T':ts if ts>=160 else None})
(root/'panel/data/eos-checks.json').write_text(json.dumps(points,indent=2)+'\n')
parser=argparse.ArgumentParser();parser.add_argument('--native',required=True,type=Path);native=parser.parse_args().native
data=json.loads((root/'panel/data/cfd.json').read_text());checks=[]
for case in data['cases']:
 audit=json.loads((native/case['id']/'audit.json').read_text())
 hashes=audit['temperature_field_sha256'];checked=0
 for snap in case['snapshots']:
  key=str(int(snap['time_s']))
  if key in hashes:
   assert hashes[key]==snap['T_sha256'],(case['id'],key)
   checked+=1
 assert checked>=len(case['snapshots'])-1
 checks.append({'case':case['id'],'native_audit_temperature_hashes_matched':checked,'extracted_snapshots':len(case['snapshots']),'recorded_numerical_screens_pass':audit['numerical_screens_pass']})
out={'date':'2026-10-22','scope':'Numerical validation, not hardware validation. New panel is not Lean-verified.','native_cfd_provenance':checks,'total_saved_snapshots':sum(len(c['snapshots']) for c in data['cases']),'native_integration_method':'ASCII cell fields, exact rectilinear cell/region intersection, rho=p/RT. Threshold classifies cell-constant T.','formal_coverage':'Existing conditional algebraic Lean proofs; no claim for new JS/ODE/interpolation.','hardware_validated':False}
(root/'panel/data/validation.json').write_text(json.dumps(out,indent=2)+'\n')
print('Saved independent EOS checks and',len(checks),'native CFD provenance checks')
