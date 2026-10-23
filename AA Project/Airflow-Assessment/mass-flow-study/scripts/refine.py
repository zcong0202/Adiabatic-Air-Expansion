"""Second loop: closure sensitivity, then fine grids on the best tested candidates."""
import json,time,concurrent.futures,subprocess,sys
from campaign import execute,STATUS,save
from build import STUDY
OUT=STUDY/'results'
if __name__=='__main__':
    while True:
        parent=json.loads((OUT/'campaign-status.json').read_text())
        if 'ended_utc' in parent and not parent['failed']:break
        time.sleep(15)
    if parent['failed']:
        (OUT/'refinement-status.json').write_text(json.dumps(dict(status='Awaiting failed-case repair',failed=parent['failed']),indent=2));raise SystemExit(1)
    subprocess.run([sys.executable,str(STUDY/'scripts/range_metrics.py')],check=True)
    primary={r['name'] for r in json.loads((OUT/'campaign-plan.json').read_text())['cases']}
    rows=[]
    for f in OUT.glob('*.json'):
        d=json.loads(f.read_text())
        if isinstance(d,dict) and d.get('numerical_screens_pass') and 'final' in d and d['case'] in primary and not d['case'].endswith('_laminar'):rows.append(d)
    extra=[]
    for n in [1,2]:extra.append(dict(name=f'm02_n{n}_adaptive_laminar',mass_g=2,count=n,design='adaptive',layout='side',h=.065,closure='laminar',ranks=1 if n==1 else 2,phase='transition-sensitivity'))
    extra.append(dict(name='m02_n4_wide_RAS',mass_g=2,count=4,design='wide',layout='side',h=.065,closure='kEpsilon',ranks=1,phase='low-flow-closure-sensitivity'))
    selected=[]
    for mass in [2,27,52,77]:
        d=max([r for r in rows if r['inputs']['total_g_s']==mass],key=lambda r:r['final']['regions']['range20to50']['6']['mass_kg']);c=d['inputs']
        job=dict(name=d['case']+'_fine',mass_g=mass,count=c['outlets'],design=c['design'],layout=c['layout'],h=.045,closure=c['closure'],ranks=4 if mass==2 else 1,phase='grid-refinement',parent=d['case']);extra.append(job);selected.append(job)
    (OUT/'refinement-plan.json').write_text(json.dumps(dict(selection='Maximum 10 s >=6 K cold air mass in the defined 20–50 cm band among primary coarse cases. Band sample volumes differ by layout. Not a global optimum.',cases=extra),indent=2))
    # Reuse the same executor but a separate status file by executing each case and copying its result.
    old=json.loads((OUT/'campaign-status.json').read_text());extra_names={r['name'] for r in extra};STATUS.update(old);STATUS.pop('ended_utc',None);STATUS['completed']=[n for n in old['completed'] if n not in extra_names];STATUS['failed']=[r for r in old['failed'] if r['case'] not in extra_names];STATUS['running']=[];STATUS['total']=len(primary)+len(extra);save()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(execute,extra))
    STATUS['ended_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save()
    (OUT/'refinement-status.json').write_text(json.dumps(dict(status='complete' if not STATUS['failed'] else 'failures',selected=selected,total_cases=STATUS['total'],failed=STATUS['failed']),indent=2))
