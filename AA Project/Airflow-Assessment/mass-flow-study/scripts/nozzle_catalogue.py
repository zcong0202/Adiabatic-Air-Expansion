"""Publish every designed nozzle, exact CAD links, fitting status and CFD scope."""
import hashlib, json, os, zipfile
from pathlib import Path
from html import escape as h
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

STUDY=Path(__file__).resolve().parents[1];ASSESS=STUDY.parent;OUT=STUDY/'results';DEST=OUT/'nozzle-catalogue'
def read(p):return json.loads(p.read_text())
def url(p):return Path(os.path.relpath(p,OUT)).as_posix()
def link(label,p,download=False):return f'<a href="{h(url(p))}"'+(' download' if download else '')+f'>{h(label)}</a>'

def preview(stl,name):
    target=DEST/f'{name}-cad.png'
    cache=DEST/f'{name}-cad-source.sha256';digest=hashlib.sha256(stl.read_bytes()).hexdigest()
    mesh=trimesh.load(stl,force='mesh');assert mesh.is_watertight and mesh.is_winding_consistent
    if not target.exists() or (cache.exists() and cache.read_text()!=digest):
        mesh.apply_translation(-mesh.bounds.mean(axis=0))
        # Only the view is rotated; downloadable CAD stays unchanged.
        longest=int(np.argmax(mesh.extents))
        if longest!=2:
            mat=np.eye(4);mat[[longest,2],:]=mat[[2,longest],:];mesh.apply_transform(mat)
        fig=plt.figure(figsize=(5,3.5));ax=fig.add_subplot(projection='3d')
        light=np.clip(.55+.4*(mesh.face_normals@np.array([.3,-.5,.8])),.15,.95)
        colors=np.column_stack([.15+.12*light,.40+.25*light,.43+.25*light,np.ones(len(light))])
        ax.add_collection3d(Poly3DCollection(mesh.triangles,facecolors=colors,edgecolors='none',rasterized=True))
        ext=mesh.extents;span=max(ext);half=np.maximum(ext*.6,span*.13)
        ax.set(xlim=(-half[0],half[0]),ylim=(-half[1],half[1]),zlim=(-half[2],half[2]));ax.set_box_aspect(half);ax.view_init(25,40);ax.set_axis_off();fig.patch.set_facecolor('#f1f7f6');ax.set_facecolor('#f1f7f6')
        fig.subplots_adjust(0,0,1,1);fig.savefig(target,dpi=100);plt.close(fig)
    cache.write_text(digest)
    return dict(image=url(target),watertight=True,components=len(mesh.split()),bounds_mm=trimesh.load(stl,force='mesh').extents.tolist(),stl_sha256=digest)

def build():
    DEST.mkdir(exist_ok=True);items=[]
    runs=[]
    for f in OUT.glob('*.json'):
        d=read(f)
        if isinstance(d,dict) and d.get('numerical_screens_pass') and 'final' in d and 'range20to50' in d['final']['regions']:runs.append(d)
    # Current nozzle variants. Each run must match the exact outlet dimensions.
    for i,cad in enumerate(read(STUDY/'cad/manifest.json')):
        name=Path(cad['stl']).stem.replace('-print-mm','');matched=[]
        for r in runs:
            c=r['inputs']
            if c['design']==cad['design'] and abs(c['width_m']-cad['exact_exit_width_m'])<1e-10 and abs(c['height_m']-cad['exact_exit_height_m'])<1e-10:
                matched.append(dict(case=r['case'],total_g_s=c['total_g_s'],outlets=c['outlets'],per_outlet_g_s=c['per_outlet_g_s'],layout=c['layout'],drop20_k=r['final']['sections'][0]['best_sampled_5cm_mean_drop_k'],drop50_k=r['final']['sections'][2]['best_sampled_5cm_mean_drop_k'],area20_m2=r['final']['sections'][0]['area_ge6_m2'],area50_m2=r['final']['sections'][2]['area_ge6_m2'],fine=r['case'].endswith('_fine'),closure=c['closure']))
        assert matched,name
        item=dict(id=name,group='current',label=f'{cad["design"].capitalize()} · {cad["outlet_width_mm"]:.2f} × {cad["outlet_height_mm"]:.2f} mm',description='Current outdoor slot. Exact CFD exit size; nozzle interior not solved.',mount='100 mm OD hose spigot · 95.2 mm clear bore',fit='Unfitted hose prototype',fit_verified=False,flow_condition='2 / 27 / 52 / 77 g/s total where listed · 0.96°C supply · 30°C ambient · 10 s · gravity on',metric='Best sampled 5 × 5 cm mean temperature drop. Scan spacing 10 mm. A20/A50: area at least 6°C below ambient.',stl=STUDY/cad['stl'],step=STUDY/cad['step'],runs=sorted(matched,key=lambda r:(r['total_g_s'],r['outlets'],r['layout'],r['case'])),evidence=STUDY/'cad/manifest.json',limits=cad['limits'])
        items.append(item)
    # The original four bodies remain available. Their CFD never converged.
    labels={'D0_round':'D0 · Round baseline','D1_compact':'D1 · Compact smooth outlet','D2_slot':'D2 · Rounded slot','D3_shield':'D3 · Open shield'}
    for name,label in labels.items():
        folder=ASSESS/'designs'/name;d=read(folder/'design.json')
        items.append(dict(id=name,group='early',label=label,description=d['description'],mount='Assumed 8 mm inlet bore · connector omitted',fit='Flow body only',fit_verified=False,flow_condition='Earlier 2 g/s · 15°C source · 35°C ambient · steady diagnostic · still air',metric='Original fixed 5 × 5 cm patch at 20 cm from core exit. Not the current best-patch scan.',stl=folder/'wall-mm.stl',step=folder/'concept.step',runs=[],evidence=ASSESS/'results/study-summary.json',limits='20 cm: unconverged diagnostic, values withheld for design selection. 50 cm: no accepted result. Requires a new CFD solve before comparison with current slots. D3 shield projects beyond the core exit.'))
    legacy={r['design']:r for r in read(DEST/'legacy-ranges.json')}
    for cad in read(ASSESS/'optimization/results/candidate-cad.json'):
        name=cad['name'];folder=ASSESS/'optimization/designs'/name;r=legacy[name]
        items.append(dict(id=name,group='cone',label=f'{name} · {cad["exit_bore_mm"]} mm / {cad["cone_half_angle_deg"]}°',description=f'8 mm inlet → {cad["exit_bore_mm"]} mm outlet. Length {cad["total_length_mm"]:.2f} mm. Half angle stated.',mount='3/8-18 NPT male reference' if name=='C24_a3' else 'Assumed 8 mm inlet bore · connector omitted',fit='Threaded prototype · coupon required' if name=='C24_a3' else 'Flow body only',fit_verified=False,flow_condition=f'{r["total_g_s"]:.2f} g/s · {r["source_c"]:.2f}°C source · {r["ambient_c"]:g}°C ambient · steady · gravity excluded',metric='Fixed centred 5 × 5 cm area mean. Native cellPoint sections at 20 / 50 cm. Solver iterations are not seconds.',stl=folder/'wall-mm.stl',step=folder/'concept.step',runs=[],legacy=r,evidence=DEST/'legacy-ranges.json',limits=r['limits']+(' C16 result is a 16 mm prescribed uniform-exit proxy; its internal 5° cone was not solved.' if name=='C16_a5' else ' Internal conical passage included.')))
    r=legacy['stock_D28_a5'];folder=ASSESS/'system-study/cad'
    items.append(dict(id='stock_D28_a5',group='cone',label='Stock-source cone · 28 mm / 5°',description='EXAIR reference-source design. 8 → 28 mm bore. Length 139.30 mm. Separate source from Jeanoko and motors.',mount='EXAIR port/adapter not specified',fit='Flow body only',fit_verified=False,flow_condition=f'{r["total_g_s"]:.2f} g/s · {r["source_c"]:.2f}°C source · {r["ambient_c"]:g}°C ambient · steady · gravity excluded',metric='Fixed centred 5 × 5 cm area mean. Nominal dry fields, without one-way wall/moisture stress corrections.',stl=folder/'nozzle-print-mm.stl',step=folder/'nozzle-flow-body.step',runs=[],legacy=r,evidence=ASSESS/'system-study/results/campaign.json',limits=r['limits']+' Fitted EXAIR adapter remains undefined.'))
    mount=ASSESS/'optimization/deliverables/C24-3deg-Milton-mount-reference'
    cards=[];manifest=[];files=set()
    for item in items:
        # Render C24 with its actual threaded exterior; preserve smooth STEP label.
        display_stl=mount/'NOZZLE_3-8-MNPT_nominal_mm.stl' if item['id']=='C24_a3' else item['stl']
        item.update(preview(display_stl,item['id']));item['preview_stl']=url(display_stl)
        downloads=[link('STL · mm'+(' · smooth body' if item['id']=='C24_a3' else ''),item['stl'],True),link('STEP · metres · flow body',item['step'],True)]
        files.update([item['stl'],item['step']])
        if item['id']=='C24_a3':
            for tolerance in ['nominal','diameter-minus-0p2','diameter-minus-0p4']:
                for prefix,title in [('NOZZLE','Threaded STL'),('FIT-COUPON','Fit coupon')]:
                    f=mount/f'{prefix}_3-8-MNPT_{tolerance}_mm.stl';downloads.append(link(f'{title} · {tolerance}',f,True));files.add(f)
            for label,f in [('Threaded 3MF · geometry',mount/'NOZZLE_3-8-MNPT_nominal_GEOMETRY_mm.3mf'),('Print and fit guide',mount/'PRINT-COUPONS-FIRST.txt'),('Mount verification',mount/'mount-reference.json')]:downloads.append(link(label,f));files.add(f)
        if item['group']=='current':
            coupon=ASSESS/'pass-by-study/cad/hose-fit-coupon-OD100-mm.stl';downloads.append(link('100 mm hose fit coupon',coupon,True));files.add(coupon)
        rows=[]
        if item['runs']:
            for r in item['runs']:
                rows.append(f'<tr data-catalogue-case="{r["case"]}"><td>{r["total_g_s"]}</td><td>{r["outlets"]} × {r["per_outlet_g_s"]:g}</td><td>{h(r["layout"])}<small>{"fine" if r["fine"] else r["closure"]}</small></td><td>{r["drop20_k"]:.2f}°C</td><td>{r["drop50_k"]:.2f}°C</td><td><button class="pick catalogue-load" data-cfd="{r["case"]}" data-range="0">20 cm</button> / <button class="pick catalogue-load" data-cfd="{r["case"]}" data-range="2">50 cm</button></td></tr>')
            results='<div class="table nozzle-results"><table><thead><tr><th>Total g/s</th><th>Nozzles × g/s</th><th>Layout/model</th><th>Δ20</th><th>Δ50</th><th>Open CFD</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
        elif item.get('legacy'):
            r=item['legacy'];a,b=r['sections'];isproxy=not r['internal_diffuser']
            results=f'<div class="nozzle-deltas"><div><small>20 cm mean Δ</small><strong>{a["mean_drop_k"]:.2f}°C</strong></div><div><small>50 cm mean Δ</small><strong>{b["mean_drop_k"]:.2f}°C</strong></div></div>'
            if isproxy:results+='<p class="banner warn">Exit-only proxy. This CFD did not include this nozzle’s internal cone.</p>'
            results+=f'<a href="nozzle-catalogue/{h(r["image"])}"><img class="range-preview" loading="lazy" src="nozzle-catalogue/{h(r["image"])}" alt="{h(item["label"])} saved temperature sections at 20 and 50 cm"></a><div class="links">'+link('Native sampled profiles',DEST/'legacy-ranges.json')+link('CFD replay archive',STUDY/'archives'/f'catalogue-{r["case"]}.zip')+'</div>'
        else:results='<div class="nozzle-deltas unavailable"><div><small>20 cm</small><strong>Unconverged</strong></div><div><small>50 cm</small><strong>Not available</strong></div></div>'
        cards.append(f'<article class="nozzle-card" data-nozzle="{h(item["id"])}" data-group="{item["group"]}" data-threaded="{str(item["id"]=="C24_a3").lower()}"><img class="cad-preview" loading="lazy" src="{item["image"]}" alt="Actual CAD mesh of {h(item["label"])}"><div class="nozzle-content"><p class="eyebrow">{h(item["group"])} · {h(item["fit"])}</p><h3>{h(item["label"])}</h3><p>{h(item["description"])}</p><p class="mount-label">{h(item["mount"])}</p><div class="links">'+''.join(downloads)+f'</div><details class="nozzle-evidence" open><summary>CFD at 20 and 50 cm'+(f' · {len(item["runs"])} runs' if item['runs'] else '')+f'</summary><p class="note">{h(item["flow_condition"])}</p>{results}<p class="note">{h(item["metric"])}</p></details><details class="nozzle-limits"><summary>Fit, model limits and evidence</summary><p class="note">{h(item["limits"])}</p><p class="note">Printed attachment fit: untested. STL coordinates: mm. STEP coordinates: metres. CAD preview is from the linked STL.</p>'+link('Source verification',item['evidence'])+'</details></div></article>')
        manifest.append({k:(url(v) if isinstance(v,Path) else v) for k,v in item.items()})
    (DEST/'catalogue.json').write_text(json.dumps(dict(count=len(items),current=14,early=4,conical=5,hardware_fit_verified=0,items=manifest),indent=2))
    with zipfile.ZipFile(DEST/'all-nozzle-cad.zip','w',zipfile.ZIP_DEFLATED) as z:
        def member(name,content):z.writestr(zipfile.ZipInfo(str(name),date_time=(2026,10,23,0,0,0)),content,compress_type=zipfile.ZIP_DEFLATED)
        for f in sorted(files):member(f.relative_to(ASSESS),f.read_bytes())
        member('CATALOGUE.json',(DEST/'catalogue.json').read_bytes())
        member('READ-FIRST.txt','23 flow designs. STL mm; STEP metres. Only C24_a3 includes a provisional threaded prototype. Commercial Milton tip fit was user-confirmed; no printed mount fit is verified. Current slots: 100 mm unfitted hose spigot. Smooth STEP files do not include printed threads. No pressure rating. Check nozzle-catalogue/catalogue.json in the web dashboard for matched CFD conditions and limits.\n')
    with zipfile.ZipFile(DEST/'all-nozzle-cad.zip') as z:assert z.testzip() is None
    fragment='''<section class="card" id="nozzle-catalogue"><div class="section-head"><div><p class="eyebrow">ALL DESIGNED NOZZLES · CAD + RANGE RESULTS</p><h2>Choose a nozzle. Check its evidence.</h2></div><a href="nozzle-catalogue/all-nozzle-cad.zip" download>Download all CAD ↓</a></div><p>23 flow designs: 14 current slots, four early concepts and five conical designs. Mesh refinements, thread tolerances and repeated seat/pass-by bodies are variants of these designs.</p><p class="banner warn"><strong>Attachment status:</strong> C24 3° includes the provisional 3/8-18 NPT male model and three fit coupons. The commercial Milton tip fit was confirmed on Jeanoko. No printed nozzle fit is verified. Current slots have a 100 mm hose spigot; hose/clamp selection is pending. The remaining bodies have no fitted connector.</p><p class="note">CFD values below are temperature drops relative to each run’s ambient. Current slots use the best sampled 5 cm patch at 10 s. Older conical runs use a fixed centred patch in a steady field, with different source conditions and no gravity. These are separate comparisons. Early unconverged results are withheld.</p><div class="catalogue-controls"><label>Design group<select id="catalogueGroup"><option value="all">All 23 designs</option><option value="current">Current slots · 14</option><option value="cone">Conical designs · 5</option><option value="early">Early concepts · 4</option><option value="threaded">Threaded prototype · C24 3°</option></select></label><label>Find nozzle<input id="catalogueSearch" type="search" placeholder="Name or outlet size"></label><p id="catalogueCount" role="status"></p></div><div class="nozzle-grid">'''+''.join(cards)+'''</div><details class="nozzle-limits"><summary>Earlier seat and pass-by CAD revisions</summary><p class="note">The current 140 × 80 and 280 × 40 mm files replace repeated bodies from earlier studies. The rejected 50 mm inlet remains a historical artifact. Seat/enclosure CFD does not describe this outdoor setup.</p><div class="links">'''+link('Previous 140 × 80 mm body',ASSESS/'motor-seat-study/cad/side-slot-140x80-print-mm.stl')+link('Rejected 50 mm inlet revision',ASSESS/'motor-seat-study/cad/rejected-50mm-inlet/side-slot-140x80-print-mm.stl')+link('Earlier pass-by CAD manifest',ASSESS/'pass-by-study/results/package-manifest.json')+'''</div></details><div class="links"><a href="nozzle-catalogue/catalogue.json">Full CAD / CFD mapping</a><a href="nozzle-catalogue/legacy-ranges.json">Older 20 / 50 cm extraction and hashes</a></div></section>'''
    (DEST/'catalogue.html').write_text(fragment)
    print(json.dumps(dict(designs=len(items),matched_current_runs=sum(len(x['runs']) for x in items),files_in_bundle=len(files))))
    return fragment

if __name__=='__main__':build()
