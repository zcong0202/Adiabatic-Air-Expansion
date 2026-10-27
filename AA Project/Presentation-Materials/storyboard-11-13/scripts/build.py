"""Editorial exports from unchanged native CFD. No solver, invented particles or people."""
from pathlib import Path
import csv, hashlib, io, json, re, subprocess, sys, zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
CFD = PROJECT/'Airflow-Assessment'
OUT = ROOT/'exports'
DATA = ROOT/'data'
TMP = Path('/tmp/aa-storyboard-11-13')
for p in [OUT, DATA, TMP]: p.mkdir(parents=True, exist_ok=True)
BG='#10151c'; FG='#f4f7fa'; MUTED='#a2b1bf'; CYAN='#82dcff'; GRID='#33414e'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':FG,'axes.labelcolor':MUTED,
    'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':GRID,'font.size':13,
    'savefig.facecolor':BG,'figure.facecolor':BG,'axes.facecolor':BG})
CMAP=LinearSegmentedColormap.from_list('temperature',['#b8f2ff','#59c2fa','#286492',BG])
SINGLE='scuba19_n1_wide_fine'
MULTI='m77_n4_wide_opposed_fine'
CONFIGS=[('m77_n1_wide','One wide outlet','280 × 40 mm','—'),
    ('m77_n2_wide','Two wide outlets','280 × 40 mm','400 mm horizontal'),
    ('m77_n4_base','Four compact outlets','140 × 80 mm','400 × 400 mm'),
    ('m77_n4_adaptive','Four adaptive outlets','141 × 71 mm','400 × 400 mm'),
    ('m77_n4_wide_opposed','Four opposed outlets','280 × 40 mm','1.10 m across; 400 mm high')]
EVIDENCE=[]

def read(path): return json.loads(path.read_text())
def js(path): return json.loads(path.read_text().split('=',1)[1].rstrip(';'))
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def native(study,name):
    base=CFD/study; result=read(base/'results'/f'{name}.json')
    timeline_path=base/'results'/f'{name}-timeline.js'
    audit=read(base/'results'/f'{name}-timeline-audit.json')
    assert digest(timeline_path)==audit['file_sha256']
    timeline=js(timeline_path)
    assert [f['time_s'] for f in timeline['frames']]==list(range(11))
    archive=base/'archives'/f'{name}.zip'
    archive_record=read(base/'results'/f'{name}-archive.json')
    assert digest(archive)==archive_record['sha256']
    with zipfile.ZipFile(archive) as z:
        raw=z.read(f'{name}/mesh-metadata.npz')
        assert hashlib.sha256(raw).hexdigest()==result['mesh_sha256']
        mesh=dict(np.load(io.BytesIO(raw))); idx=mesh['indices']; count=len(idx)
        shape=tuple(len(mesh[k])-1 for k in ['z','y','x']); grids=[]
        for t in range(11):
            raw=z.read(f'{name}/{t}/T')
            assert hashlib.sha256(raw).hexdigest()==result['field_sha256'][str(t)]['T']
            text=raw.decode()
            match=re.search(r'internalField\s+nonuniform\s+List<\w+>\s+(\d+)\s*\((.*?)\)\s*;',text,re.S)
            if match:
                values=np.fromstring(match.group(2),sep=' '); assert len(values)==count
            else:
                match=re.search(r'internalField\s+uniform\s+([^;]+)',text)
                values=np.full(count,float(match.group(1)))
            grid=np.full(shape,np.nan); grid[idx[:,2],idx[:,1],idx[:,0]]=values-273.15
            grids.append(grid)
            frame=timeline['frames'][t]
            assert abs(frame['whole']['volume_m3']-result['history'][t]['regions']['domain']['6']['volume_m3'])<1e-10
    EVIDENCE.append(dict(case=name,study=study,result=str((base/'results'/f'{name}.json').relative_to(PROJECT)),
        archive_sha256=archive_record['sha256'],timeline_sha256=audit['file_sha256'],native_T_hashes_verified=11,
        source_c=result['inputs']['source_c'],total_g_s=result['inputs']['total_g_s'],cells=result['inputs']['cells']))
    return result,timeline,mesh,grids

def canvas(number,title,subtitle):
    fig=plt.figure(figsize=(16,9),dpi=120)
    fig.text(.048,.935,f'{number:02d}',fontsize=17,color=CYAN,weight='bold')
    fig.text(.095,.927,title,fontsize=28,weight='bold')
    fig.text(.095,.879,subtitle,fontsize=13,color=MUTED)
    fig.add_artist(plt.Line2D([.048,.952],[.845,.845],color=GRID,lw=1))
    return fig

def footer(fig,text):
    fig.text(.048,.050,text,fontsize=11,color=MUTED)
    fig.text(.952,.050,'SIMULATION',fontsize=10,color=MUTED,ha='right')

def stat(fig,y,value,label):
    fig.text(.76,y,value,fontsize=29,color=CYAN,weight='bold')
    fig.text(.76,y-.037,label,fontsize=12,color=MUTED)

def side(result,timeline,mesh,grids,t):
    frame=timeline['frames'][t]
    fig=canvas(11,'Cold dispersion','One outlet · 19.4 g/s · 4.31°C assumed source · 30°C ambient')
    ax=fig.add_axes([.085,.225,.61,.55])
    ix=int(np.searchsorted(mesh['x'],0,side='right')-1)
    plane=grids[t][:,:,ix]; im=ax.pcolormesh(mesh['y']+.55,mesh['z'],plane,cmap=CMAP,vmin=4.31,vmax=30,shading='flat',rasterized=True)
    ax.set(xlim=(-.09,1.02),ylim=(.48,1.72),xlabel='Distance from outlet (m)',ylabel='Height (m)')
    ax.add_patch(Rectangle((-.04,1.33),.04,.04,facecolor=FG,edgecolor=FG))
    ax.text(-.045,1.405,'OUTLET',fontsize=10,color=FG,ha='center')
    for distance in [.2,.5]:
        ax.axvline(distance,color=FG,alpha=.5,ls=(0,(4,5)),lw=1)
        ax.text(distance,1.68,f'{distance*100:.0f} cm',ha='center',fontsize=12)
    ax.set_xticks([0,.2,.5,1]); ax.set_yticks([.5,.75,1,1.25,1.5])
    cb=fig.colorbar(im,cax=fig.add_axes([.115,.132,.53,.019]),orientation='horizontal',ticks=[5,10,15,20,25,30])
    cb.set_label('Air temperature (°C)',fontsize=11);cb.ax.tick_params(labelsize=10)
    fig.text(.76,.76,f'SIMULATED TIME  {t:02d} s',fontsize=13,weight='bold')
    fig.text(.76,.70,'Best 5 × 5 cm air patch',fontsize=13,color=MUTED)
    for y,s in zip([.61,.47],[frame['sections'][0],frame['sections'][2]]):
        stat(fig,y,f"{s['best_sampled_5cm_mean_c']:.1f}°C",f"at {s['distance_m']*100:.0f} cm · simulated")
    fig.text(.76,.325,'The jet mixes and sinks.\nCooling remains local.',fontsize=15,linespacing=1.6)
    fig.text(.76,.19,'Centre side slice.\nPatch values use full cross-sections;\nnot physical probe measurements.',fontsize=10.5,color=MUTED,linespacing=1.5)
    footer(fig,'Native CFD · still air + gravity · no person · assumed source · no hardware validation')
    return fig

BOXF=np.array([[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]])
def volume_axes(fig,position,geo,nozzles,azimuth=-58):
    ax=fig.add_axes(position,projection='3d',computed_zorder=False)
    v=np.array(geo['vertices']);f=np.array(geo['faces'],int)
    for x in np.linspace(-1.25,1.25,6): ax.plot([x,x],[-1.1,1.1],[0,0],color=GRID,lw=.6,alpha=.6)
    for y in np.linspace(-1.1,1.1,5): ax.plot([-1.25,1.25],[y,y],[0,0],color=GRID,lw=.6,alpha=.6)
    if len(f):
        tri=v[f];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12)
        brightness=.55+.45*np.abs(norm@np.array([.35,-.4,.85]))
        colors=np.column_stack([.30*brightness,.79*brightness,.99*brightness,np.full(len(f),.88)])
        ax.add_collection3d(Poly3DCollection(tri,facecolor=colors,edgecolor='none',zsort='average'))
    for nozzle in nozzles:
        x,y,z=nozzle['box'];v=np.array([[xx,yy,zz] for zz in z for yy in y for xx in x])
        ax.add_collection3d(Poly3DCollection(v[BOXF],facecolor='#e2e9ef',edgecolor='#7c8c9e',linewidth=.5))
    ax.set(xlim=(-1.25,1.25),ylim=(-1.1,1.1),zlim=(0,2.7),box_aspect=(2.5,2.2,2.7))
    ax.view_init(22,azimuth);ax.set_axis_off()
    return ax

def config_figure(result,geo,title,size,spacing,index):
    a=result['inputs'];r=result['final']['regions']['range20to50']['6'];w=result['final']['regions']['domain']['6']
    fig=canvas(12,'Nozzle setup','CONTROLLED SWEEP · 77 g/s total · 0.96°C assumed source · 30°C ambient · 10 s')
    volume_axes(fig,[.02,.12,.69,.70],geo,a['geometry'])
    fig.text(.08,.78,title,fontsize=21,weight='bold')
    fig.text(.76,.765,f'{index+1} / {len(CONFIGS)}',fontsize=12,color=MUTED)
    stat(fig,.68,f"{a['per_outlet_g_s']:.2f} g/s",'per outlet')
    stat(fig,.535,f"{w['volume_m3']*1000:.0f} L",'air ≥6°C colder · whole domain')
    fig.text(.76,.385,f'Outlet: {size}\nSpacing: {spacing}',fontsize=12,linespacing=1.65)
    fig.text(.76,.27,'Supply cooling budget\n2.25 kW in every case',fontsize=15,color=CYAN,linespacing=1.6)
    fig.text(.76,.16,'Q̇ = ṁ cₚ (Tₐ − Tₛ)\nSupply budget ≠ cooling at a person',fontsize=11,color=MUTED,linespacing=1.6)
    fig.text(.08,.15,'Blue: native cells at ≤24°C. White: outlet boundary geometry.',fontsize=11,color=MUTED)
    footer(fig,'Historical fixed-source CFD · same source and domain · still air + gravity · no body')
    return fig

def space(result,timeline,mesh,grids,t,azimuth):
    a=result['inputs'];frame=timeline['frames'][t];metrics=result['history'][t]['regions']
    fig=canvas(13,'A localized cold volume','FOUR OPPOSED OUTLETS · 77 g/s total · 0.96°C assumed source · 30°C ambient')
    volume_axes(fig,[.015,.14,.70,.68],frame['whole'],a['geometry'],azimuth)
    fig.text(.08,.78,f'SIMULATED TIME  {t:02d} s',fontsize=13,weight='bold')
    fig.text(.08,.15,'Blue: native cell boundary at ≤24°C. Open domain: 2.5 × 2.2 × 2.7 m.',fontsize=11,color=MUTED)
    stat(fig,.745,f"{metrics['domain']['6']['volume_m3']*1000:.0f} L",'air ≥6°C colder · whole domain')
    stat(fig,.60,f"{metrics['range20to50']['6']['volume_m3']*1000:.1f} L",'air ≥6°C colder · 20–50 cm bands')
    ax=fig.add_axes([.755,.245,.195,.24])
    iz=int(np.searchsorted(mesh['z'],1.6,side='right')-1)
    im=ax.pcolormesh(mesh['x'],mesh['y'],grids[t][iz,:,:],cmap=CMAP,vmin=.96,vmax=30,shading='flat',rasterized=True)
    ax.set(xlim=(-1.25,1.25),ylim=(-1.1,1.1),aspect='equal');ax.set_xticks([]);ax.set_yticks([])
    ax.set_title('Horizontal slice at 1.6 m',fontsize=11,color=MUTED,pad=10)
    cb=fig.colorbar(im,cax=fig.add_axes([.765,.214,.18,.010]),orientation='horizontal',ticks=[1,15,30])
    cb.ax.tick_params(labelsize=9);cb.ax.set_xlabel('Air temperature (°C)',fontsize=9,labelpad=0)
    fig.text(.76,.125,'No people or comfort model.\nNot evidence of room-scale cooling.',fontsize=10.5,color=MUTED,linespacing=1.55)
    footer(fig,'Native CFD · still air + gravity · no field interpolation · source stays ON through 10 s')
    return fig

def save(fig,path):
    fig.savefig(path,dpi=120)
    if path.parent==OUT: fig.savefig(path.with_suffix('.svg'))
    plt.close(fig)

def concat_video(paths,durations,dest):
    listing=TMP/(dest.stem+'.txt')
    lines=[]
    for p,d in zip(paths,durations): lines.extend([f"file '{p}'",f'duration {d:.9f}'])
    lines.append(f"file '{paths[-1]}'");listing.write_text('\n'.join(lines)+'\n')
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-t',str(sum(durations)),
        '-vf','fps=30,format=yuv420p','-c:v','libx264','-preset','fast','-crf','18','-movflags','+faststart',str(dest)],check=True)

def build(movies=False):
    single=native('scuba-study',SINGLE)
    multi=native('mass-flow-study',MULTI)
    config_data=[]
    for name,title,size,spacing in CONFIGS:
        base=CFD/'mass-flow-study/results';result=read(base/f'{name}.json');geo=js(base/f'{name}-volume.js')
        assert geo['time_s']==10 and geo['threshold_k']==6
        assert abs(geo['volume_m3']-result['final']['regions']['domain']['6']['volume_m3'])<1e-10
        assert abs(result['inputs']['total_g_s']-77)<1e-10
        config_data.append((result,geo,title,size,spacing))
        EVIDENCE.append(dict(case=name,result=str((base/f'{name}.json').relative_to(PROJECT)),
            field_T_sha256=result['field_sha256']['10']['T'],volume_file_sha256=digest(base/f'{name}-volume.js'),
            volume_m3=geo['volume_m3'],source_c=result['inputs']['source_c'],total_g_s=77))
    save(side(*single,10),OUT/'11-cold-dispersion.png')
    for i,case in enumerate(config_data): save(config_figure(*case,i),OUT/f'12-{i+1:02d}-{CONFIGS[i][0]}.png')
    save(space(*multi,10,-58),OUT/'13-localized-cold-volume.png')
    # Compact comparison contact sheet; each tile retains source/case labels in separate full-size files.
    cards=[Image.open(OUT/f'12-{i+1:02d}-{c[0]}.png').convert('RGB') for i,c in enumerate(CONFIGS)]
    sheet=Image.new('RGB',(1920,1080),BG)
    for i,im in enumerate(cards): sheet.paste(im.resize((640,360),Image.Resampling.LANCZOS),((i%3)*640,(i//3)*360))
    draw=ImageDraw.Draw(sheet);draw.text((50,850),'Five configurations / same source. Full-resolution cards and CFD records included.',fill=FG)
    sheet.save(OUT/'12-nozzle-comparison-contact-sheet.png')
    with (DATA/'12-configurations.csv').open('w') as f:
        fields=['case','outlets','outlet_mm','spacing','total_g_s','per_outlet_g_s','source_c','source_cooling_w','cold_band_l','cold_domain_l']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for d,g,title,size,spacing in config_data:
            a=d['inputs'];w.writerow(dict(case=d['case'],outlets=a['outlets'],outlet_mm=size,spacing=spacing,
                total_g_s=a['total_g_s'],per_outlet_g_s=a['per_outlet_g_s'],source_c=a['source_c'],source_cooling_w=d['source_cooling_w'],
                cold_band_l=d['final']['regions']['range20to50']['6']['volume_m3']*1000,cold_domain_l=g['volume_m3']*1000))
    with (DATA/'11-simulated-patches.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['native_time_s','distance_m','best_5cm_mean_c','best_5cm_drop_k','status'])
        for frame in single[1]['frames']:
            for s in [frame['sections'][0],frame['sections'][2]]:
                w.writerow([frame['time_s'],s['distance_m'],s['best_sampled_5cm_mean_c'],s['best_sampled_5cm_mean_drop_k'],'simulated; not measured'])
    if movies:
        paths=[]
        for t in range(11):
            p=TMP/f'11-{t:02d}.png';save(side(*single,t),p);paths.append(p)
        concat_video(paths,[1.2]*10+[2],OUT/'11-cold-dispersion-14s.mp4')
        concat_video([OUT/f'12-{i+1:02d}-{c[0]}.png' for i,c in enumerate(CONFIGS)],[2.8]*5,OUT/'12-nozzle-setup-14s.mp4')
        paths=[]
        for i in range(160):
            t=min(10,int(i/128*10));p=TMP/f'13-{i:03d}.png'
            save(space(*multi,t,-78+45*i/159),p);paths.append(p)
            if i%20==0: print(f'orbit {i}/160',flush=True)
        concat_video(paths,[.1]*160,OUT/'13-localized-cold-volume-16s.mp4')
    manifest=dict(date='2026-10-27',new_cfd=False,field_interpolation=False,dimensions=[1920,1080],
        physical_times_s=list(range(11)),spray_off_simulated=False,hardware_validated=False,measured_points_overlaid=False,
        sources=EVIDENCE,notes=['Shot 11 uses current scuba reference; shots 12–13 use historical 77 g/s fixed-source study.',
            'No 14 October deck/measurement linkage verified. No measured probes are shown.',
            'Cold-cell surfaces are grid boundaries, not smoothed continuum isosurfaces.',
            'No simulated people, wind, solar load or pedestrian comfort.',
            'Layout-specific 20–50 cm analysis regions differ; volume is not equal body coverage.',
            'Video duration differs from simulated time. Native fields are held between saved times; only camera rotates continuously.',
            'Shot 11 does not claim that all cooling disappears by 50 cm. Shot 13 does not claim an occupied room is cooled.'])
    manifest['exports']=[dict(file=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(OUT.iterdir()) if p.is_file()]
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Done: '+str(OUT),flush=True)

if __name__=='__main__': build('--movies' in sys.argv)
