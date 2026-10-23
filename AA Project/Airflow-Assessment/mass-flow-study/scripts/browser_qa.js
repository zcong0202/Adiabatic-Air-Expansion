(async()=>{
 const checks=[];const assert=(name,value)=>{checks.push({name,pass:!!value});if(!value)throw Error(name)};
 assert('55 audited native CFD cases',AA_SWEEP.cases.length===55);
 for(const flow of [2,27,52,77]){
  const select=document.querySelector('#flow');select.value=String(flow);select.dispatchEvent(new Event('change',{bubbles:true}));
  await AA_SweepViewer.selectCase(AA_SWEEP.representative_by_flow[String(flow)]);
  assert('Flow '+flow+' filters cases',Array.from(document.querySelector('#case').options).every(o=>AA_SWEEP.cases.find(d=>d.case===o.value).inputs.total_g_s===flow));
 }
 for(const mode of ['range','whole']){
  document.querySelector('#volumeRegion').value=mode;
  for(const data of AA_SWEEP.cases){
   await AA_SweepViewer.selectCase(data.case);const mesh=AA_SweepViewer.getGeometry(),region=mode==='range'?'range20to50':'domain';
   assert(mode+' geometry belongs to '+data.case,mesh.case===data.case);
   assert(mode+' volume equals native field '+data.case,Math.abs(mesh.volume_m3-data.final.regions[region]['6'].volume_m3)<1e-9);
   assert(mode+' nozzle count '+data.case,mesh.nozzles.length===data.inputs.outlets);
   assert(mode+' finite mesh '+data.case,mesh.vertices.every(v=>v.length===3&&v.every(Number.isFinite)));
   assert(mode+' no GLB link for empty mesh '+data.case,document.querySelector('#glb').hidden===(mesh.faces.length===0));
   assert(mode+' native sections match '+data.case,window.AA_SECTIONS.case===data.case);
  }
 }
 document.querySelector('#volumeRegion').value='range';await AA_SweepViewer.selectCase(AA_SWEEP.default_case);
 const canvas=document.querySelector('#volume'),before=canvas.toDataURL();canvas.dispatchEvent(new WheelEvent('wheel',{deltaY:90,cancelable:true,bubbles:true}));assert('3D zoom redraws actual geometry',canvas.toDataURL()!==before);
 assert('No horizontal document overflow',document.documentElement.scrollWidth<=innerWidth);
 return {status:'passed',passed:checks.length,failed:0,cases:55,regions:['range','whole'],checks,scope:'Browser data identity, filtering, geometry, links and zoom. Physical accuracy and pointer drag not established.'};
})()
