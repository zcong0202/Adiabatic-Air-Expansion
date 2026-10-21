"""Audit solver logs and integrate actual sampled CFD fields.

Patch flux is advected cooling potential through a plane, not body heat removal.
"""
import base64
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.interpolate import LinearNDInterpolator

ROOT=Path(__file__).resolve().parents[1]
DTYPES={"Float32":"<f4","Float64":"<f8","Int32":"<i4","Int64":"<i8","UInt32":"<u4","UInt64":"<u8"}


def read_vtp(path):
    tree=ET.parse(path)
    def arr(node):
        if node.attrib.get("format")=="binary":
            raw=base64.b64decode(''.join((node.text or '').split()))
            header=8 if tree.getroot().attrib.get("header_type")=="UInt64" else 4
            out=np.frombuffer(raw[header:],dtype=DTYPES[node.attrib["type"]])
        else:out=np.fromstring(node.text,sep=" ")
        n=int(node.attrib.get("NumberOfComponents",1))
        return out.reshape(-1,n) if n>1 else out
    piece=tree.find(".//Piece")
    points=arr(piece.find("Points/DataArray")).astype(float)
    polys={n.attrib['Name']:arr(n).astype(int) for n in piece.findall("Polys/DataArray")}
    faces=[];start=0
    for end in polys['offsets']:
        ids=polys['connectivity'][start:end]
        faces.extend([[ids[0],ids[i],ids[i+1]] for i in range(1,len(ids)-1)])
        start=end
    data={n.attrib['Name']:arr(n).astype(float) for n in piece.findall("PointData/DataArray")}
    return points,np.asarray(faces),data


def metrics(path,ambient=35,rho_reference=None,total_temperature=False):
    pts,faces,d=read_vtp(path)
    q=pts[faces]
    area=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)/2
    centers=q.mean(axis=1)
    temp=d['T']-273.15;speed=np.linalg.norm(d['U'],axis=1)
    total=temp if total_temperature else temp+speed**2/(2*1005)
    rho=d['rho'][faces].mean(axis=1) if 'rho' in d else np.full(len(faces),rho_reference)
    ux=d['U'][faces,0].mean(axis=1)
    deficit=ambient-total[faces].mean(axis=1)
    # Exact sampling integration on generated cutting-plane triangles.
    flux=rho*ux*1005*deficit*area
    tracer=rho*ux*d['c'][faces].mean(axis=1)*area
    patch=(np.abs(centers[:,1])<=.025)&(np.abs(centers[:,2])<=.025)
    # Triangle-centroid patch integration is approximate at the square border.
    weights=area[patch]
    temp_cell=temp[faces].mean(axis=1)
    speed_cell=speed[faces].mean(axis=1)
    interpolator=LinearNDInterpolator(pts[:,1:3],np.column_stack([temp,speed,d['c']]))
    centre=np.asarray(interpolator([[0,0]])).ravel()
    return {"plane_x_m":float(np.mean(pts[:,0])),"centre_temperature_c":float(centre[0]),"centre_speed_m_s":float(centre[1]),"centre_source_fraction":float(centre[2]),"min_plane_temperature_c":float(np.min(temp)),"max_plane_speed_m_s":float(np.max(speed)),"source_fraction_min_max":[float(np.min(d['c'])),float(np.max(d['c']))],"full_plane_net_cooling_potential_w":float(flux.sum()),"full_plane_net_source_mass_flux_kg_s":float(tracer.sum()),"patch_size_mm":[50,50],"patch_integrated_area_m2":float(weights.sum()),"patch_area_mean_temperature_c":float(np.sum(temp_cell[patch]*weights)/weights.sum()),"patch_area_mean_speed_m_s":float(np.sum(speed_cell[patch]*weights)/weights.sum()),"patch_net_cooling_potential_w":float(flux[patch].sum()),"metric_limit":"Advected enthalpy deficit, not skin heat removal. Triangle-centroid square clipping introduces a small patch-area discretization error."}


def audit(case):
    info=json.loads((case/'case.json').read_text())
    s=(case/'log.solver').read_text() if (case/'log.solver').exists() else ''
    times=re.findall(r'^Time = (\S+)',s,re.M)
    residuals={}
    for name,initial,final in re.findall(r'Solving for (\w+), Initial residual = ([0-9.eE+-]+), Final residual = ([0-9.eE+-]+)',s):
        residuals[name]={'initial':float(initial),'linear_final':float(final)}
    result={**info,'last_iteration':float(times[-1]) if times else None,'solver_end_seen':'\nEnd\n' in s,'fatal_error':'FOAM FATAL' in s or '[stack trace]' in s,'convergence_reported':'SIMPLE solution converged' in s,'last_residuals':residuals,'mesh_ok':(case/'log.checkMesh').exists() and 'Mesh OK.' in (case/'log.checkMesh').read_text(),'samples':{}}
    for folder in sorted((case/'postProcessing/cuts').glob('*'),key=lambda p:float(p.name)) if (case/'postProcessing/cuts').exists() else []:
        if not folder.is_dir():continue
        entry={}
        for plane in ['target','clearance']:
            if (folder/f'{plane}.vtp').exists():entry[plane]=metrics(folder/f'{plane}.vtp',rho_reference=info.get('rho_reference_kg_m3'),total_temperature=info.get('solver')=='buoyantBoussinesqSimpleFoam')
        result['samples'][folder.name]=entry
    if result['samples']:
        latest=list(result['samples'])[-1];result['latest_sample']=latest
        result['latest_target']=result['samples'][latest]['target']
        result['latest_clearance']=result['samples'][latest]['clearance']
        result['source_flux_fraction']=result['latest_target']['full_plane_net_source_mass_flux_kg_s']/info['cold_mass_flow_kg_s']
        result['enthalpy_flux_fraction']=result['latest_target']['full_plane_net_cooling_potential_w']/info['nominal_source_sensible_capacity_w']
    result['interpretation']='No design ranking is accepted until convergence, conservation and sensitivity are assessed.'
    return result


if __name__=='__main__':
    output=[]
    for c in sorted((ROOT/'cases').glob('*')):
        if not (c/'case.json').exists():continue
        try:
            r=audit(c);(c/'audit.json').write_text(json.dumps(r,indent=2));output.append(r)
            print(c.name,'iteration',r['last_iteration'],'end',r['solver_end_seen'],'fatal',r['fatal_error'],'sample',r.get('latest_sample'), 'patchW',round(r['latest_target']['patch_net_cooling_potential_w'],2) if r.get('latest_target') else None,flush=True)
        except Exception as exc:
            print('AUDIT FAILED',c.name,str(exc),flush=True)
    (ROOT/'results/case-audits.json').write_text(json.dumps(output,indent=2))
