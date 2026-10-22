"""Generate bounded real-air property table for offline browser calculations."""
import json, hashlib
from pathlib import Path
import numpy as np
import CoolProp
from CoolProp.CoolProp import PropsSI
root=Path(__file__).resolve().parents[1]
P=np.unique(np.r_[1.01325,np.linspace(1.05,12,100),np.geomspace(12,331.1,80)])
T=np.arange(160.,502.,2.)
out={'fluid':'Air','backend':'HEOS','CoolProp_version':CoolProp.__version__,'p_bar':P.tolist(),'t_k':T.tolist(),'h':[],'s':[],'rho':[],'scope':'Dry pseudo-pure air. Bilinear p,T table. Inverse T from monotonic h or s. No humidity/icing. No hardware performance prediction.'}
for p in P:
 for key,prop in [('h','Hmass'),('s','Smass'),('rho','Dmass')]:
  values=PropsSI(prop,'P',np.full(len(T),p*1e5),'T',T,'Air')
  assert np.isfinite(values).all()
  out[key].append(np.round(values,7).tolist())
assert np.all(np.diff(np.array(out['h']),axis=1)>0)
assert np.all(np.diff(np.array(out['s']),axis=1)>0)
out['generator_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
s=json.dumps(out,separators=(',',':'))
(root/'panel/data/air.json').write_text(s+'\n');(root/'panel/data/air.js').write_text('globalThis.AA_AIR = '+s+';\n')
print('Real-air grid',len(P),'×',len(T),'states',len(s),'bytes')
