"""Exact native-cell area average over sampled 5x5 cm patches at t=10 s."""
import json
import numpy as np
from build import STUDY
OUT=STUDY/'results'

def patch_metric(section,ambient=30):
    a=np.array(section['axis_a']);b=np.array(section['axis_b']);temp=np.array(section['values_c'],float);drop=np.nan_to_num(ambient-temp,nan=0)
    ca=np.arange(-.775,.775+1e-8,.01);lo,hi=(1,1.7) if section['axes'][1]=='z' else (-.2,.2);cb=np.arange(lo+.025,hi-.025+1e-8,.01)
    wa=np.maximum(0,np.minimum(ca[:,None]+.025,a[None,1:])-np.maximum(ca[:,None]-.025,a[None,:-1]))/.05
    wb=np.maximum(0,np.minimum(cb[:,None]+.025,b[None,1:])-np.maximum(cb[:,None]-.025,b[None,:-1]))/.05
    average=wb@drop@wa.T;j,i=np.unravel_index(np.argmax(average),average.shape)
    return dict(best_sampled_5cm_mean_drop_k=float(average[j,i]),best_sampled_5cm_mean_c=float(ambient-average[j,i]),best_sampled_5cm_center_m=[float(ca[i]),float(cb[j])],patch_side_m=.05,patch_center_step_m=.01,patch_scope='Best among sampled patch centres inside the section bounds at 10 s. Exact cell/patch area overlap; not a body or a continuous-position optimum.')

def update(name):
    file=OUT/(name+'-sections.js');sections=json.loads(file.read_text().split('=',1)[1].rstrip(';'));summary=json.loads((OUT/(name+'.json')).read_text())
    for k,s in enumerate(sections['sections']):
        metrics=patch_metric(s,summary['inputs']['ambient_c']);s.update(metrics);summary['final']['sections'][k].update(metrics);summary['history'][-1]['sections'][k].update(metrics)
    file.write_text('window.AA_SECTIONS='+json.dumps(sections,separators=(',',':'))+';');(OUT/(name+'.json')).write_text(json.dumps(summary,indent=2));return summary

if __name__=='__main__':
    count=0
    for file in OUT.glob('*-sections.js'):update(file.name.removesuffix('-sections.js'));count+=1
    print('Section patch audits:',count)
