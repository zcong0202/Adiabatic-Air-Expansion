(async()=>{
 const checks=[],assert=(name,v)=>{checks.push({name,pass:!!v});if(!v)throw Error(name)},$=id=>document.getElementById(id),cards=[...document.querySelectorAll('[data-nozzle]')];
 const set=(id,value,type='change')=>{$(id).value=value;$(id).dispatchEvent(new Event(type,{bubbles:true}));};
 const visible=()=>cards.filter(c=>!c.hidden);
 for(const [group,count] of [['current',14],['cone',5],['early',4],['threaded',1],['all',23]]){set('catalogueGroup',group);assert(group+' count',visible().length===count);}
 set('catalogueSearch','C24_a3','input');assert('Search keeps exact C24 design',visible().length===1&&visible()[0].dataset.nozzle==='C24_a3');set('catalogueSearch','none-123','input');assert('No-match search',visible().length===0);set('catalogueSearch','','input');
 const buttons=[...document.querySelectorAll('.catalogue-load')];assert('Each saved case has two distance buttons',buttons.length===110);
 for(const b of buttons){
  b.click();for(let i=0;i<1000;i++){if(!b.disabled&&AA_SweepViewer.getSelected().case===b.dataset.cfd&&AA_SweepViewer.getGeometry()?.case===b.dataset.cfd)break;await new Promise(r=>setTimeout(r,10));}
  assert(b.dataset.cfd+' button distance '+b.dataset.range,AA_SweepViewer.getSelected().case===b.dataset.cfd&&$('distance').value===b.dataset.range&&AA_SweepViewer.getTime()===10);
  const row=b.closest('tr'),r=AA_SweepViewer.getSelected();assert('20 cm table matches selected native data',Math.abs(parseFloat(row.cells[3].textContent)-r.final.sections[0].best_sampled_5cm_mean_drop_k)<=.0051);assert('50 cm table matches selected native data',Math.abs(parseFloat(row.cells[4].textContent)-r.final.sections[2].best_sampled_5cm_mean_drop_k)<=.0051);
 }
 for(const a of document.querySelectorAll('#nozzle-catalogue a'))assert('Catalogue link populated',a.getAttribute('href')&&a.getAttribute('href')!=='#');
 set('catalogueGroup','early');assert('Early numerical failures visible',visible().every(c=>c.textContent.includes('Unconverged')&&c.textContent.includes('Not available')));
 set('catalogueGroup','threaded');assert('C24 coupons and three threaded variants',visible()[0].querySelectorAll('[download]').length===8);set('catalogueGroup','all');
 await AA_SweepViewer.selectConfiguration(77,'wide',4,'opposed');AA_SweepViewer.setTime(10);
 return {checks:checks.length,failures:checks.filter(c=>!c.pass),status:'passed',designs:cards.length,range_buttons:buttons.length};
})()
