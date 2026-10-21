"""Keep generated concepts and CFD status in the continuing AA overview."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT.parent/'project-overview.html'
s=p.read_text()
start='<!-- cfd-generated-start -->';end='<!-- cfd-generated-end -->'
if start in s:
    a=s.index(start);b=s.index(end,a)+len(end);s=s[:a]+s[b:]
models=json.loads((ROOT/'results/design-viewer-data.json').read_text())
checks=json.loads((ROOT/'evidence/geometry-checks.json').read_text())
rows=''
for name,model in models.items():
    info=json.loads((ROOT/'designs'/name/'design.json').read_text())
    topo=checks[name]
    rows+=f'<tr><td><strong>{name[:2]} · {model["label"]}</strong><br>{model["description"]}</td><td>{info["exit_area_mm2"]:.1f} mm²</td><td><a href="Airflow-Assessment/designs/{name}/concept.step">STEP</a> · <a href="Airflow-Assessment/designs/{name}/wall.stl">STL (m)</a> · <a href="Airflow-Assessment/designs/{name}/wall-mm.stl">STL (mm)</a> · <a href="Airflow-Assessment/designs/{name}/fluid-domain.step">Fluid STEP</a> · <a href="Airflow-Assessment/designs/{name}/mesh.msh">Fluid mesh</a><br>Watertight: {topo["stl_watertight"]}. Winding: {topo["winding_consistent"]}.</td></tr>'
buttons=''.join(f'<button type="button" data-cfd-model="{n}">{n[:2]} · {m["label"]}</button>' for n,m in models.items())
statefile=ROOT/'results/study-summary.json'
results='<p><strong>CFD in progress.</strong> Initial variable-density startup attempts failed and are excluded from ranking. Cases are being initialized from flow-only solutions, then solved with heat transfer and a source-air tracer. No design winner is established yet.</p>'
if statefile.exists():
    summary=json.loads(statefile.read_text())
    results=summary['overview_html']
block=f'''{start}
<section id="cfd-generated"><div class="eyebrow">Design generation · 15 Oct 2026</div><h2>Earlier concepts and 3-D CFD screening</h2><p>The iterative search above uses a separate structured model. This earlier batch remains diagnostic and is excluded from the optimization fit.</p>
<p><strong>Generated:</strong> STEP solids, watertight STL walls, conforming fluid meshes and reproducible OpenFOAM inputs. Dimensions are proposed assumptions. These are equivalents inspired by the references, not replicas of Milton or Jeanoko internals. Smooth adapter passages are included. Threads and shield mounting supports are omitted.</p>
<p><a href="Airflow-Assessment/AA-CFD-concepts-v1.zip">Download CAD package</a> · <a href="Airflow-Assessment/AA-CFD-study-v1.zip">Download CFD inputs and diagnostic results</a> · <a href="Airflow-Assessment/results/outlet-profiles.png">Outlet drawings</a></p>
<div class="tabs">{buttons}</div><p id="cfdModelDescription"></p>
<canvas id="cfdModelCanvas" width="1060" height="390" style="display:block;width:100%;height:390px;background:#edf4f7;border:1px solid #cedde3;touch-action:none" aria-label="Interactive concept model. Drag to rotate. Use half view to inspect the passage."></canvas>
<p><label><input type="checkbox" id="cfdHalf" checked> Longitudinal half view</label> · <button type="button" id="cfdReset">Reset view</button> <span class="sub">Drag to rotate. Coordinates and dimensions are in millimetres.</span></p>
<div class="scroll"><table><tr><th>Proposed design</th><th>Core outlet area</th><th>Downloads and topology</th></tr>{rows}</table></div>
<details><summary>Complete nozzle image · full walls</summary><img src="Airflow-Assessment/results/assembled-nozzles.png" style="width:100%" alt="Complete exterior views of the four generated nozzle concepts"><p><a href="Airflow-Assessment/results/assembled-nozzles.png">Download image</a>. Source tube, connection threads and shield supports are not modeled.</p></details>
<details><summary>Static engineering views</summary><img src="Airflow-Assessment/results/design-concepts.png" style="width:100%" alt="Four dimensioned concept half views"></details>
<h3>CFD result status</h3>{results}
<p><strong>Primary comparison:</strong> 2 g/s cold air, 15°C approximate total inlet temperature, 35°C ambient. Prescribed cold-branch flow, not 6.9 bar at the delivery inlet. The screening solver uses Boussinesq buoyancy, adiabatic walls and a passive source tracer. Failed ideal-gas attempts are retained as diagnostics. A 50 × 50 mm square at 200 mm is an assumed reporting region, not a body model.</p>
<p><strong>Shield distance:</strong> Its mouth projects 32 mm beyond the primary jet exit. Sample both 200 mm from the jet exit and 200 mm clear of the shield mouth (232 mm from the jet exit). Report the difference rather than hiding the extra travel distance.</p>
<p><strong>Limits:</strong> No internal vortex, condensation, radiation, human thermal model or compressor energy model. A prescribed source cannot predict how nozzle backpressure changes Jeanoko output. Catalogue data remain references. Thermal fields and pressure losses require solver and sensitivity checks before a ranking is accepted.</p>
<p><a href="Airflow-Assessment/evidence/geometry-checks.json">Geometry checks</a> · <a href="Airflow-Assessment/results/case-audits.json">CFD audit records</a> · <a href="Airflow-Assessment/scripts/generate_designs.py">Geometry generator</a> · <a href="Airflow-Assessment/scripts/build_case.py">Case generator</a> · <a href="Airflow-Assessment/cfd-brief.json">CFD scope</a></p>
<h3>Next technical steps</h3><p>Re-run clean cases with the final numerical settings. Check whether steady flow is attainable; use a time-dependent model if it is not. Then assess mesh, domain and numerical mixing sensitivity. Calibrate the baseline with measured cold-branch flow and temperature before ranking prototypes. Add a heated target surface to predict heat removed from a person.</p>
<h3>Open inputs</h3><p>Real bore and adapter geometry. Measured cold flow and temperature. Wind exposure. Patch size. Later calibration against the installed Jeanoko remains necessary.</p>
</section>
<script id="cfdModelData" type="application/json">{json.dumps(models,separators=(',',':'))}</script>
<script>
(()=>{{
const models=JSON.parse(document.getElementById('cfdModelData').textContent),canvas=document.getElementById('cfdModelCanvas'),ctx=canvas.getContext('2d'),half=document.getElementById('cfdHalf');let key=Object.keys(models)[0],yaw=-.65,pitch=.5,drag=null,pending=false;
function render(){{pending=false;const m=models[key],w=canvas.width,h=canvas.height,cx=Math.cos(yaw),sx=Math.sin(yaw),cy=Math.cos(pitch),sy=Math.sin(pitch);ctx.clearRect(0,0,w,h);const transformed=m.vertices_mm.map(v=>{{const x=v[0]+5,y=v[1],z=v[2],a=x*cx-y*sx,b=x*sx+y*cx;return[a,b*cy-z*sy,b*sy+z*cy]}}),faces=m.faces.filter(f=>!half.checked||f.reduce((a,i)=>a+m.vertices_mm[i][1],0)>=-1e-6).map(f=>({{f,z:f.reduce((a,i)=>a+transformed[i][2],0)/3}})).sort((a,b)=>a.z-b.z);for(const item of faces){{const t=item.f.map(i=>transformed[i]),u=t[1].map((x,i)=>x-t[0][i]),v=t[2].map((x,i)=>x-t[0][i]),n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],norm=Math.hypot(...n)||1,light=.55+.4*Math.abs((n[0]*.3+n[1]*.5+n[2]*.8)/norm);ctx.fillStyle=`rgb(${{Math.round(85*light+50)}},${{Math.round(130*light+60)}},${{Math.round(155*light+65)}})`;ctx.beginPath();t.forEach((p,i)=>ctx[i?'lineTo':'moveTo'](w/2+p[0]*8,h/2-p[1]*8));ctx.closePath();ctx.fill();ctx.strokeStyle='rgba(35,65,80,.11)';ctx.lineWidth=.3;ctx.stroke()}}ctx.fillStyle='#163342';ctx.font='17px system-ui';ctx.fillText(key+' · '+m.label,20,28);ctx.font='14px system-ui';ctx.fillText('Concept dimensions only. Threads and shield supports omitted.',20,h-18)}}
function schedule(){{if(!pending){{pending=true;requestAnimationFrame(render)}}}}function select(k){{key=k;document.getElementById('cfdModelDescription').textContent=models[k].description;document.querySelectorAll('[data-cfd-model]').forEach(b=>b.classList.toggle('active',b.dataset.cfdModel===k));schedule()}}document.querySelectorAll('[data-cfd-model]').forEach(b=>b.onclick=()=>select(b.dataset.cfdModel));half.onchange=schedule;document.getElementById('cfdReset').onclick=()=>{{yaw=-.65;pitch=.5;schedule()}};canvas.onpointerdown=e=>{{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)}};canvas.onpointermove=e=>{{if(!drag)return;yaw+=(e.clientX-drag[0])*.008;pitch+=(e.clientY-drag[1])*.008;drag=[e.clientX,e.clientY];schedule()}};canvas.onpointerup=()=>drag=null;canvas.onpointercancel=()=>drag=null;select(key);
}})();
</script>
{end}'''
marker='<section id="airflow">';assert marker in s;s=s.replace(marker,block+'\n'+marker,1)
if '<a href="#cfd-generated">' not in s:s=s.replace('<nav aria-label="Sections">','<nav aria-label="Sections"><a href="#cfd-generated">Designs & CFD</a>',1)
s=s.replace('<span class="status pending">CFD not run</span>','<span class="status pending">Earlier assessment · before CFD screening</span>')
p.write_text(s)
print('Updated',p)
