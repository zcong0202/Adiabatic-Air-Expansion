(async()=>{
const checks=[];const check=(name,value)=>{checks.push({name,pass:!!value});if(!value)throw Error(name)};
for(let i=0;i<300&&!AA_SweepViewer.getTimeline();i++)await new Promise(r=>setTimeout(r,20));
check('Nominal motor delivery',AA_SWEEP.cases.every(c=>Math.abs(c.inputs.total_g_s-19.4)<1e-9&&c.inputs.outlets===1));
for(const row of AA_SWEEP.cases){
 await AA_SweepViewer.selectCase(row.case);check(row.case+' native identity',AA_SweepViewer.getTimeline().case===row.case);check(row.case+' source temperature',Math.abs(AA_SweepViewer.getTimeline().source_c-row.inputs.source_c)<1e-10);
 for(const mode of ['range','whole']){document.getElementById('volumeRegion').value=mode;document.getElementById('volumeRegion').dispatchEvent(new Event('change'));for(const t of [0,5,10]){AA_SweepViewer.setTime(t);const m=AA_SweepViewer.getGeometry(),metric=row.history.find(x=>x.time_s===t).regions[mode==='range'?'range20to50':'domain']['6'];check(row.case+' '+mode+' '+t+'s native mesh',m.case===row.case&&m.time_s===t&&Math.abs(m.volume_m3-metric.volume_m3)<1e-9);}}
 for(let i=0;i<3;i++){document.getElementById('distance').value=i;document.getElementById('distance').dispatchEvent(new Event('change'));check(row.case+' section '+i,document.getElementById('patchReadout').textContent.includes([20,35,50][i]+' cm'));}
 check(row.case+' source-labelled scenario',document.getElementById('case').selectedOptions[0].textContent.includes(row.inputs.source_c.toFixed(2)+'°C'));
 check(row.case+' archive link',document.getElementById('native').getAttribute('href')==='../archives/'+row.case+'.zip');
}
await AA_SweepViewer.selectCase(AA_SWEEP.default_case);document.getElementById('volumeRegion').value='range';document.getElementById('volumeRegion').dispatchEvent(new Event('change'));AA_SweepViewer.setTime(10);document.getElementById('distance').value=2;document.getElementById('distance').dispatchEvent(new Event('change'));
check('No horizontal overflow',document.documentElement.scrollWidth<=innerWidth);
check('Tank pressure distinction stated',document.getElementById('scuba-summary').textContent.includes('7 bar g'));
check('CFD temperature is conditional',document.getElementById('scuba-summary').textContent.includes('assumed'));
check('CAD link retained',document.querySelector('a[href$="outlet-280x40-print-mm.stl"]')!==null);
return {status:'passed',checks:checks.length,viewport:{width:innerWidth,height:innerHeight},cases:AA_SWEEP.cases.length,items:checks,scope:'Saved frame identity, source, geometry and interface checks. No physical validation.'};
})()
