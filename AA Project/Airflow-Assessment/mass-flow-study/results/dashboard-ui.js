/* Four focused views. Navigation changes presentation only. */
(()=>{
 const main=document.querySelector('main'),tabs=document.getElementById('dashboardTabs');
 const groups={cfd:[...main.querySelectorAll(':scope > .run-context,:scope > #metrics,:scope > .controls,:scope > .timeline,:scope > .workspace,:scope > .history-panel,:scope > #run-files')],components:[document.getElementById('components')],nozzles:[document.getElementById('nozzle-catalogue')],evidence:[document.getElementById('source-temperature'),...main.querySelectorAll(':scope > details.matrix')]};
 const hashes={cfd:'#airflow',components:'#components',nozzles:'#nozzle-catalogue',evidence:'#source-temperature'};
 function show(name,update=true){if(!groups[name])name='cfd';for(const [key,nodes] of Object.entries(groups))for(const node of nodes)if(node)node.hidden=key!==name;for(const b of tabs.querySelectorAll('button'))b.setAttribute('aria-pressed',String(b.dataset.panel===name));if(update)history.replaceState(null,'',hashes[name]);window.dispatchEvent(new Event('resize'));return name;}
 function fromHash(){const hash=location.hash;return hash.startsWith('#components')?'components':hash.startsWith('#nozzle-catalogue')?'nozzles':hash.startsWith('#source-temperature')?'evidence':'cfd';}
 tabs.querySelectorAll('button').forEach(b=>b.onclick=()=>{show(b.dataset.panel);tabs.scrollIntoView({block:'start',behavior:'smooth'});});
 window.addEventListener('hashchange',()=>show(fromHash(),false));
 document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>{const hash=a.getAttribute('href');if(hash==='#components')show('components',false);else if(hash==='#nozzle-catalogue')show('nozzles',false);else if(hash==='#source-temperature')show('evidence',false);}));
 document.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>window.dispatchEvent(new Event('resize'))));
 window.AA_DashboardUI={show,selected:()=>tabs.querySelector('[aria-pressed="true"]').dataset.panel};show(fromHash(),false);
})();
