"""Isolated CAD builds avoid persistent OpenCASCADE STEP unit state."""
import sys,json,subprocess
from build import STUDY,spec
rows=[]
for design in ['base','wide','adaptive']:
    pairs=[(77,4)] if design!='adaptive' else [(m,n) for m in [2,27,52,77] for n in [1,2,4]]
    for mass,count in pairs:
        s=spec(mass,count,design);w,h=s['width_m'],s['height_m'];verification=STUDY/'cad'/f'outlet-{round(w*1000)}x{round(h*1000)}-verification.json'
        if not verification.exists():
            script='cad_compact.py' if design=='adaptive' else 'cad_original.py'
            with (STUDY/'results'/f'cad-{design}-{mass}-{count}.log').open('w') as log:subprocess.run([sys.executable,str(STUDY/'scripts'/script),str(w),str(h)],check=True,stdout=log,stderr=subprocess.STDOUT)
        info=json.loads(verification.read_text());info.update(design=design,applies_to_total_g_s=mass if design=='adaptive' else [2,27,52,77],outlet_count_for_area=count if design=='adaptive' else [1,2,4],exact_exit_width_m=w,exact_exit_height_m=h);rows.append(info);print('CAD verified',design,mass,count,flush=True)
(STUDY/'cad/manifest.json').write_text(json.dumps(rows,indent=2));print('Verified CAD models:',len(rows))
