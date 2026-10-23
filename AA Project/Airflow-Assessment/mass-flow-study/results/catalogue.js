/* Local CAD catalogue. Load matching saved CFD; never rescale a field. */
(()=>{
 const cards=[...document.querySelectorAll('[data-nozzle]')],group=document.getElementById('catalogueGroup'),search=document.getElementById('catalogueSearch');
 function filter(){const query=search.value.trim().toLowerCase();let count=0;for(const card of cards){const match=(group.value==='all'||card.dataset.group===group.value||(group.value==='threaded'&&card.dataset.threaded==='true'))&&card.textContent.toLowerCase().includes(query);card.hidden=!match;if(match)count++;}document.getElementById('catalogueCount').textContent=`${count} of ${cards.length} designs shown`;}
 group.addEventListener('change',filter);search.addEventListener('input',filter);filter();
 let ticket=0;
 document.querySelectorAll('.catalogue-load').forEach(button=>button.addEventListener('click',async()=>{
  const request=++ticket;button.disabled=true;
  try{await AA_SweepViewer.selectCase(button.dataset.cfd);if(request!==ticket)return;AA_SweepViewer.pause();AA_SweepViewer.setTime(10);const distance=document.getElementById('distance');distance.value=button.dataset.range;distance.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('.viewer').scrollIntoView({behavior:'smooth',block:'start'});}
  finally{button.disabled=false;}
 }));
})();
