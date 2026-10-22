/* Carry exact input state between local HTML views, including file:// tabs.
   Uses the panel's existing scenario-link format. No model conversion. */
(function(){
 const known=['system','compare','cfd','basis'];
 function prepare(a){
  if(!a)return;const href=a.getAttribute('href')||'';
  if(!/^(index|engineering)\.html(?:[#?]|$)/.test(href))return;
  const provider=globalThis.AA_Studio||globalThis.AA_Panel;if(!provider)return;
  const url=new URL(href,location.href);
  if(!a.dataset.targetTab){const hash=url.hash.slice(1);a.dataset.targetTab=known.includes(hash)?hash:'auto';}
  let saved={};try{saved=JSON.parse(localStorage.getItem('aa-panel-v2'))||{};}catch{}
  const tab=a.dataset.targetTab==='auto'?(saved.tab||'system'):a.dataset.targetTab;
  const payload={inputs:provider.getState(),cfd:saved.cfd||{id:'F01_wide_d35',region:'corridor',time:10},tab};
  url.hash='scenario='+btoa(encodeURIComponent(JSON.stringify(payload))).replace(/\+/g,'-').replace(/\//g,'_');
  a.href=url.href;
 }
 // Absolute URLs are re-encoded too; keep the original local target as metadata.
 function update(event){const a=event.target.closest?.('a');if(!a)return;
  const u=new URL(a.href,location.href),local=new URL('.',location.href);
  if(u.origin!==local.origin||!['index.html','engineering.html'].includes(u.pathname.slice(u.pathname.lastIndexOf('/')+1))||u.pathname.slice(0,u.pathname.lastIndexOf('/')+1)!==local.pathname)return;
  if(!a.dataset.targetTab){const h=u.hash.slice(1);a.dataset.targetTab=known.includes(h)?h:'auto';}
  a.setAttribute('href',u.pathname.endsWith('/engineering.html')?'engineering.html'+u.hash:'index.html'+u.hash);prepare(a);
 }
 for(const type of ['pointerdown','click','auxclick','contextmenu','focusin'])document.addEventListener(type,update);
 document.querySelectorAll('a[href]').forEach(prepare);
})();
