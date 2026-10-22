/* A visual interface to the unchanged AA_Model. No new physics or CFD scaling. */
(function(){
'use strict';
const M=AA_Model,D=AA_CFD,$=s=>document.querySelector(s),S=()=>document.querySelectorAll('[data-key]');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(x,d=1)=>Number.isFinite(x)?x.toLocaleString('en-GB',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';
const study='AA%20Project/Airflow-Assessment/pass-by-study/';
let state=M.config(),r,part='source',view='design',pipe='cold',compareType='source',moving=true,pinned=M.config(),cfd={id:'F01_wide_d35',region:'corridor',time:10},timer,playTimer;
const parts=[['source','Compressor'],['tank','Buffer tank'],['pipes','Pipes'],['expansion','Expansion'],['nozzles','Nozzles']];
try{const x=JSON.parse(localStorage.getItem('aa-panel-v2'));if(x?.inputs)state=M.config(x.inputs);if(D.cases.some(c=>c.id===x?.cfd?.id))cfd={...cfd,...x.cfd};}catch{}
try{const x=JSON.parse(localStorage.getItem('aa-studio-ui-v1'));if(x){if(parts.some(p=>p[0]===x.part))part=x.part;if(['design','compare','cfd'].includes(x.view))view=x.view;}}catch{}
try{const x=localStorage.getItem('aa-studio-theme');if(x==='dark')document.body.dataset.theme=x;}catch{}
// Accept scenario links produced by the earlier panel at index.html.
try{if(location.hash.startsWith('#scenario=')){
 const x=JSON.parse(decodeURIComponent(atob(location.hash.slice(10).replace(/-/g,'+').replace(/_/g,'/'))));
 if(x.inputs&&M.calculate(x.inputs).ok)state=M.config(x.inputs);
 if(D.cases.some(c=>c.id===x.cfd?.id))cfd={...cfd,...x.cfd};
 if(x.tab==='system'||x.tab==='basis')view='design';if(['compare','cfd'].includes(x.tab))view=x.tab;
}}catch{notify('Scenario link could not be read. Use Reset to restore the reference.');}
if(location.hash==='#system')view='design';if(['compare','cfd'].includes(location.hash.slice(1)))view=location.hash.slice(1);

function clearScenarioLink(){if(location.hash.startsWith('#scenario='))history.replaceState(null,'',location.pathname+location.search);}
function persist(){try{localStorage.setItem('aa-panel-v2',JSON.stringify({inputs:state,cfd,tab:view==='design'?'system':view}));localStorage.setItem('aa-studio-ui-v1',JSON.stringify({part,view,cfd}));}catch{}}
function notify(text){$('#toast').textContent=text;$('#toast').classList.add('show');clearTimeout(timer);timer=setTimeout(()=>$('#toast').classList.remove('show'),3500);}
function select(key,label,options){return `<label class="field"><span>${label}</span><select data-key="${key}" aria-label="${label}">${options.map(([value,text])=>`<option value="${value}" ${state[key]===value?'selected':''}>${esc(text)}</option>`).join('')}</select></label>`;}
function number(key,label,min,max,step=1){return `<label class="field"><span>${label}</span><input type="number" data-key="${key}" aria-label="${label}" min="${min}" max="${max}" step="${step}" value="${state[key]}"></label>`;}
function range(key,label,min,max,step,unit='',digits=0){if(Number.isFinite(state[key])){min=Math.min(min,state[key]);max=Math.max(max,state[key]);}const factor=['motorLoad','turbineEta','distance'].includes(key)?100:1,displayUnit=key==='distance'?'cm':['motorLoad','turbineEta'].includes(key)?'%':unit,displayDigits=factor===100?0:digits;return `<label class="field"><span>${label}<output data-output="${key}" data-factor="${factor}" data-unit="${displayUnit}" data-digits="${displayDigits}">${fmt(state[key]*factor,displayDigits)} ${displayUnit}</output></span><input type="range" data-key="${key}" aria-label="${label}" min="${min}" max="${max}" step="${step}" value="${state[key]}"><span class="ends"><span>${fmt(min*factor,0)}${displayUnit}</span><span>${fmt(max*factor,0)}${displayUnit}</span></span></label>`;}
function readout(rows){return `<div class="editor-readout">${rows.map(([a,b])=>`<div class="readout-row"><span>${a}</span><strong>${b}</strong></div>`).join('')}</div>`;}
function advanced(contents){return `<details><summary>More settings</summary>${contents}</details>`;}
function sync(){for(const e of document.querySelectorAll('[data-set]'))e.classList.toggle('active',String(state[e.dataset.set])===e.dataset.value);for(const e of S())if(document.activeElement!==e)e.value=state[e.dataset.key];for(const e of document.querySelectorAll('[data-output]'))e.textContent=fmt(state[e.dataset.output]*(Number(e.dataset.factor)||1),+e.dataset.digits||0)+' '+(e.dataset.unit||'');}
function renderQuick(){const defs=[['ambient','Outdoor air',-10,60,1,'°C',0],['delta','Target temperature drop',.5,30,.5,'°C',1],['activation','Valve-open time',1,30,1,'s',0]];$('#quickControls').innerHTML=defs.map(([k,l,min,max,step,u,d])=>`<div class="quick-control"><label for="quick-${k}">${l}<b data-output="${k}" data-unit="${u}" data-digits="${d}">${fmt(state[k],d)} ${u}</b></label><input id="quick-${k}" type="range" data-key="${k}" aria-label="${l}" min="${min}" max="${max}" step="${step}" value="${state[k]}"></div>`).join('');}
function renderEditor(){
 $('#partNumber').textContent='EDIT / '+String(parts.findIndex(p=>p[0]===part)+1).padStart(2,'0');$('#editorTitle').textContent=parts.find(p=>p[0]===part)[1];
 let h='';const ok=r?.ok;
 if(part==='source'){
  h=select('source','Off-the-shelf compressor',M.sources.map(s=>[s.id,`${s.name} · ${s.fad} m³/min`]))+range('sourceTemp','Air after the cooler',0,80,1,'°C');
  h+=ok?readout([['Working pressure',fmt(r.source.bar)+' barg'],['Flow after purge',fmt(r.availableFad,2)+' m³/min'],['Motor-bank demand',fmt(r.requiredFad/1000,2)+' m³/min']]):'';
  h+='<p class="small-note">Spare compressor capacity does not increase flow through a fixed motor bank.</p>';
  h+=advanced(number('purge','Air lost to dryer / purge (fraction)',0,.95,.01)+number('treatmentDrop','Treatment pressure loss (bar)',0,10,.05)+number('fadDensity','Free-air reference density (kg/m³)',.8,1.5,.001)+number('plantKW','Measured full plant input (kW)',0,1000,.1));
 }else if(part==='tank'){
  h=range('tankL','Warm receiver volume',0,3000,50,'L')+'<div class="mini-segments">'+[0,500,1000,2000].map(v=>`<button data-set="tankL" data-value="${v}" class="${state.tankL===v?'active':''}">${v===0?'None':v+' L'}</button>`).join('')+'</div>';
  h+=ok?readout([['Supported activation',fmt(r.receiver.served,1)+' s'],['Pressure floor',fmt((r.minP-M.C.pa)/1e5,2)+' barg'],['Refill after burst',fmt(r.receiver.refillSeconds,1)+' s']]):'';
  h+='<p class="small-note">This receiver is before expansion. It extends a burst; it does not fix a continuous flow deficit.</p>';
  h+=advanced(number('ramp','Compressor response ramp (s)',0,30,.5)+number('tankUA','Receiver heat conductance (W/K)',0,1000,5)+select('tankMode','Receiver model',[['energy','Mass + energy transient'],['isothermal','Fixed temperature · bound']])+number('coldTankL','Separate cold-storage volume (L)',0,100000,50)+number('coldTankTemp','Initial cold-storage air (°C)',-99,100,1)+number('coldHold','Cold-storage hold (s)',0,3600,10)+number('coldTankUA','Cold-storage heat leak (W/K)',0,1000,.1)+'<p class="small-note">Cold storage is a separate sealed-tank energy budget. Charging and driven discharge are not established.</p>');
 }else if(part==='pipes'){
  h='<div class="mini-segments">'+[['main','Warm main'],['branch','Warm branch'],['cold','Cold branch']].map(([v,l])=>`<button data-pipe="${v}" class="${v===pipe?'active':''}">${l}</button>`).join('')+'</div>';
  h+=range(pipe+'L','Hose length',0,30,.5,'m',1)+number(pipe+'D','Inside diameter (mm)',1,250,1);
  if(pipe==='cold')h+=select('coldMode','Cold-pipe heat model',[['reference','Reference heat leakage'],['insulated','Wall + insulation']])+(state.coldMode==='insulated'?range('insulation','Insulation thickness',0,80,1,'mm'):range('coldReferenceUA','Heat leakage per metre / branch',0,10,.1,'W/K',1));
  h+=ok?readout([['Cold path heat exchange',fmt(r.coldHeat,0)+' W'],['Total exhaust backpressure',fmt((r.Pex-M.C.pa)/1e5,3)+' bar']]):'';
  h+='<p class="small-note">Longer cold hoses gain heat and add backpressure. Each branch has the entered length.</p>';
  h+=advanced(number('warmUAperM','Warm-pipe heat leakage (W/K per m)',0,30,.1)+number('inletPortD','Motor inlet connector bore (mm)',1,100,1)+number('outletPortD','Motor outlet connector bore (mm)',1,100,1)+number('fittingK','Fitting loss K per pipe',0,100,.5)+number('roughness','Absolute roughness (mm)',0,5,.005));
 }else if(part==='expansion'){
  h=select('method','How pressure becomes cooling',[['motor','Loaded air motors'],['throttle','Regulator · isenthalpic'],['turbine','Turbine · assumed efficiency'],['isentropic','Isentropic · ideal upper bound']]);
  if(state.method==='motor')h+=select('motors','LZB46 motor count',Array.from({length:16},(_,i)=>[i+1,String(i+1)+' motors']))+range('motorLoad','Shaft extraction',0,1,.05,'× rated',2)+'<p class="small-note">Load changes are fixed-flow sensitivities. A real motor performance map is still needed.</p>';
  else if(state.method==='turbine')h+=range('turbineEta','Assumed isentropic efficiency',0,1,.05,'',2)+'<p class="small-note">No matched stock turbine has been selected.</p>';
  else h+='<p class="small-note">'+(state.method==='throttle'?'A regulator removes no shaft work. Real-air mode estimates Joule–Thomson cooling.':'This is a reversible thermodynamic limit, not an available component.')+'</p>';
  h+=ok?readout([['Shaft work removed',fmt(r.shaft/1000,2)+' kW'],['Air leaving expander',fmt(r.Tex,1)+'°C']]):'';
  h+=advanced(select('eos','Air properties',[['ideal','Dry ideal gas · CFD basis'],['real','Real air · CoolProp']])+number('motorPin','Motor inlet pressure (barg)',.1,7,.1)+number('motorHeat','Heat returned per motor (W)',0,2000,10)+number('processFad','Non-motor demand (L/min)',1,10000,100)+number('regHead','Regulator pressure headroom (bar)',0,5,.05));
 }else{
  h='<div class="shape-options">'+[['base','Standard slot','standard'],['wide','Wide slot','wide']].map(([id,l,shape])=>`<button data-set="nozzle" data-value="${id}" class="${state.nozzle===id?'active':''}"><i class="${shape}"></i>${l}</button>`).join('')+'</div>';
  h+=select('nozzle','Outlet design',M.nozzles.map(n=>[n.id,n.name.replace('Custom ','').replace('Control · ','')]))+select('layout','Nozzle arrangement',[['one-side','One side of the path'],['two-side','Both sides'],['overhead','Overhead'],['one-row','Four along the path']])+range('distance','Nozzle to target',.2,.5,.05,'m',2);
  h+=ok?readout([['Outlet air speed',fmt(r.v,2)+' m/s'],['Total open area',fmt(r.area*10000,0)+' cm²']]):'';
  h+='<p class="small-note">Shape changes coverage and mixing. Reach is supported only by a matching saved CFD case.</p>';
  h+=advanced(number('outlets','Number of outlets',1,16,1)+number('customArea','Custom area per outlet (cm²)',.01,10000,1)+number('cd','Assumed discharge coefficient',.01,1,.05)+range('pitch','Upward pitch',0,15,1,'°')+range('wind','Outdoor wind',0,2,.1,'m/s',1)+number('targetVolume','Required cooled volume (m³)',.001,100,.01));
 }
 $('#editorBody').innerHTML=h;$('#componentNav').innerHTML=parts.map(([id,title],i)=>`<button data-edit="${id}" class="${part===id?'active':''}" aria-pressed="${part===id}"><small>0${i+1}</small>${title}</button>`).join('');
 updateSceneSelection();sync();
}
function tube(d){return `<path d="${d}" fill="none" stroke="var(--anatomy-mid)" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/><path d="${d}" fill="none" stroke="var(--anatomy-shade-2)" stroke-width="8.5" stroke-linejoin="round" stroke-linecap="round"/><path d="${d}" class="flow-line"/>`;}
function stand(x,y,wide,count=2){const w=wide?33:23,h=wide?6:12;return `<g><path d="M${x-13} ${y+3}l13 -8 16 5 -13 9Z" class="new-top"/><path d="M${x} ${y-4}v-103l4 1v103Z" class="new-side"/>${(count===1?[y-75]:[y-87,y-55]).map(n=>`<path class="new-side" d="M${x-10} ${n}l8 -6 ${w} 10 -8 6Z"/><path class="new-front" d="M${x-10} ${n}l${w} 10v${h}l-${w} -10Z"/><path class="iso-line" data-tone="mid" d="M${x-6} ${n+2}l${w-8} 7"/>`).join('')}</g>`;}
function nozzleArrangement(wide){
 if(state.layout==='overhead')return `<path d="M576 281V128l144 44v121" class="iso-line" data-tone="mid"/>${[610,640,670,700].map((x,i)=>`<path class="new-front" d="M${x} ${138+i*9}l16 5v5l-16-5Z"/>`).join('')}`;
 if(state.layout==='two-side')return stand(565,283,wide)+stand(735,302,wide)+'<path d="M565 268L735 320" class="iso-line" data-tone="faint" stroke-dasharray="3 4"/>';
 if(state.layout==='one-row')return [548,578,608,638].map((x,i)=>stand(x,275+i*9,wide,1)).join('');
 return stand(565,283,wide)+stand(606,299,wide)+'<path d="M565 260L606 273" class="iso-line" data-tone="mid"/>';
}
function jetTraces(){
 if(state.layout==='overhead')return [0,1,2,3].map(i=>`<path class="air-line" d="M${620+i*30} ${150+i*9}Q${630+i*25} 195 ${661+i*14} 224"/>`).join('');
 if(state.layout==='two-side')return '<path class="air-line" d="M590 198Q638 195 683 213"/><path class="air-line" d="M590 232Q638 230 684 238"/><path class="air-line" d="M731 215Q713 214 699 220"/><path class="air-line" d="M731 248Q713 245 699 239"/>';
 return [0,1,2,3].map(i=>`<path class="air-line" d="M${593+i*4} ${197+i*13}C630 ${193+i*13} 651 ${200+i*10} 682 ${203+i*8}"/>`).join('');
}
function boxLabel(x,y,title,text,anchor){return `<g class="scene-label"><path class="scene-leader" d="M${x+48} ${y+29}V${anchor[1]-12}H${anchor[0]}V${anchor[1]}"/><circle cx="${anchor[0]}" cy="${anchor[1]}" r="1.1" fill="var(--anatomy-mid)"/><rect x="${x}" y="${y}" width="132" height="30" rx="3"/><text class="label-title" x="${x+7}" y="${y+10}">${title}</text><text x="${x+7}" y="${y+23}">${esc(text)}</text></g>`;}
function drawScene(){
 const source=M.sources.find(x=>x.id===state.source),ok=r.ok,wide=state.nozzle==='wide';
 $('#scene').innerHTML=AA_ARTWORK;
 const svg=$('#scene svg');svg.setAttribute('viewBox','30 0 755 385');
 svg.insertAdjacentHTML('beforeend',`<g data-part-edit="pipes">${tube('M391 104 Q405 107 438 117 L539 149 Q551 152 553 164 L563 208')}</g><g data-part-edit="nozzles">${nozzleArrangement(wide)}</g><g class="walker" aria-hidden="true"><ellipse class="head" cx="691" cy="174" rx="7" ry="9"/><path d="M689 184l-7 25 11 25 8 1 1-26-4-23Z" fill="var(--anatomy-shade-3)"/><path d="M685 190l-15 23 8 14 M697 192l11 25 10 5 M687 232l-9 27-13 27 M699 235l8 23 12 25 M664 286l-10 1 M720 284l9 2"/></g><g><path d="M626 305l95 28M640 300l95 28" class="dimension" stroke-dasharray="4 5"/><path d="M731 326l4 2-6 1" class="dimension"/><text class="dimension-text" x="657" y="346">WALKING PATH</text><path d="M625 291L675 306M624 286l-2 9M676 301l-3 9" class="dimension"/><text class="dimension-text" x="632" y="289">${fmt(state.distance,2)} m</text></g><g class="air-traces">${jetTraces()}</g><g class="scene-label"><text x="630" y="121">${state.outlets} OUTLETS · ${esc({'one-side':'ONE SIDE','two-side':'BOTH SIDES','overhead':'OVERHEAD','one-row':'ALONG PATH'}[state.layout])}</text></g>`);
 const labels=[boxLabel(79,8,'COMPRESSOR',source?`${fmt(source.bar)} barg · ${fmt(source.fad,1)} m³/min`:'Select source',[155,93]),boxLabel(252,8,'WARM RECEIVER',state.tankL?fmt(state.tankL,0)+' L':'Bypassed · no storage',[281,118]),boxLabel(384,44,'EXPANSION',ok?`${fmt(r.shaft/1000,2)} kW shaft out`:'Check settings',[421,210]),boxLabel(535,49,'AIR AT NOZZLE',ok?`${fmt(r.Tnozzle,1)}°C · ${fmt(r.m*1000,1)} g/s`:'Outside model',[587,220])].join('');
 svg.insertAdjacentHTML('beforeend',labels);
 const hits=[['source',84,68,167,128],['tank',251,73,56,133],['expansion',313,166,214,119],['pipes',365,92,187,69],['nozzles',550,182,91,125]];
 svg.insertAdjacentHTML('beforeend',hits.map(([id,x,y,w,h])=>`<g data-edit="${id}" class="scene-hotspot" role="button" tabindex="0" aria-label="Edit ${parts.find(p=>p[0]===id)[1]}"><rect class="part-outline" x="${x-5}" y="${y-5}" width="${w+10}" height="${h+10}" rx="8"/><rect class="part-target" x="${x}" y="${y}" width="${w}" height="${h}" rx="8"/></g>`).join(''));
 for(const el of svg.querySelectorAll('[data-name]')){const n=el.dataset.name;if(n.startsWith('tank.')&&state.tankL===0)el.style.opacity='.32';const index=n.match(/^(motor|gen|shaft|coupling)(\d)/);if(index&&(Number(index[2])>=state.motors||state.method!=='motor'))el.style.opacity='.2';}
 if(state.method!=='motor')svg.insertAdjacentHTML('beforeend',`<g class="scene-label"><rect x="349" y="240" width="156" height="28" rx="3"/><text x="358" y="257">${esc({throttle:'REGULATOR · NO SHAFT WORK',turbine:'TURBINE · ASSUMED η',isentropic:'IDEAL EXPANSION BOUND'}[state.method])}</text></g>`);
 $('#scene').classList.toggle('heating',ok&&r.cooling<0);$('#scene').classList.toggle('inactive',!ok||!r.valid);$('#scene').classList.toggle('paused',!moving);$('#scene').classList.toggle('hide-values',!$('#showValues').checked);updateSceneSelection();
}
function updateSceneSelection(){for(const g of document.querySelectorAll('.scene-hotspot')){g.classList.toggle('part-selected',g.dataset.edit===part);g.setAttribute('aria-pressed',String(g.dataset.edit===part));}}
function metric(name,value,unit,note,blue=false){return `<div class="result"><span class="name">${name}</span><strong class="value ${blue?'blue':''}">${value}<small>${unit}</small></strong><span class="detail">${note}</span></div>`;}
function currentCase(){return D.cases.find(c=>c.id===cfd.id)||D.cases.find(c=>c.id==='F01_wide_d35');}
function snapshot(c=currentCase(),t=cfd.time){let j=0;D.thresholds_k.forEach((x,i)=>{if(Math.abs(x-state.delta)<Math.abs(D.thresholds_k[j]-state.delta))j=i;});const s=c.snapshots.reduce((a,b)=>Math.abs(b.time_s-t)<Math.abs(a.time_s-t)?b:a);const region=['domain','corridor'].includes(cfd.region)?cfd.region:'corridor';return {s,j,delta:D.thresholds_k[j],v:s.regions[region].values[j],region};}
function mismatches(c){if(!r.ok||!r.valid)return ['supply is unsupported'];const a=[];if(Math.abs(r.m-c.source_kg_s)>.0004)a.push('air flow');if(Math.abs(r.Tnozzle-c.source_c)>.1)a.push('source temperature');if(Math.abs(state.ambient-c.ambient_c)>.1)a.push('ambient');if(state.eos!=='ideal')a.push('air model');if(state.outlets!==4)a.push('outlet count');if(r.nozzle.width!==c.width_m||r.nozzle.height!==c.height_m)a.push('shape');if(state.layout!==c.layout)a.push('layout');if(Math.abs(state.distance-c.distance_m)>.005)a.push('distance');if(Math.abs(state.pitch-c.pitch_deg)>.01)a.push('pitch');if(Math.abs(state.wind-c.wind_m_s)>.01||state.wind>0&&state.windDirection!==c.wind_direction)a.push('wind');if(r.receiver.served+1e-5<cfd.time)a.push('supply duration');if(r.sourceHistory?.some(p=>Math.abs(p.T-c.source_c)>.1))a.push('temperature drift');return a;}
function nearestCase(){const candidates=D.cases.filter(c=>c.layout===state.layout&&Math.abs(c.distance_m-state.distance)<.005&&c.width_m===r.nozzle?.width&&c.height_m===r.nozzle?.height&&c.wind_m_s===state.wind&&c.pitch_deg===state.pitch);return candidates.sort((a,b)=>b.cells-a.cells)[0]||currentCase();}
function renderOutputs(){
 r=M.calculate(state);sync();drawScene();
 if(!r.ok){$('#outcome').innerHTML=`<div class="status bad"><span class="label">Check the settings</span><span>${esc(r.error)}</span></div>`;$('#results').innerHTML=metric('Calculation stopped','—','','Enter a supported value');$('#insight').innerHTML='<h3>No result available</h3><p>Correct the input. Detailed limits are in the engineering view.</p>';$('#evidence').innerHTML='<h3>Saved CFD</h3><p>Current source calculation is unsupported.</p>';if(view==='cfd')renderCFD();if(view==='compare')renderComparison();persist();return;}
 const status=r.valid?(r.steady?'Conditional · supply fits the selected demand':'Conditional · receiver supports a finite burst'):'Selected operating point is unsupported';
 $('#outcome').innerHTML=`<div class="status ${r.valid?'':'bad'}"><span class="label">${status}</span><span>${r.valid?'Calculated source states · hardware unvalidated':'Nominal temperatures below assume the requested flow'}</span></div>`;
 $('#results').innerHTML=metric('Air at the nozzle',fmt(r.Tnozzle,1),'°C',fmt(Math.abs(r.mix.deficit),1)+'°C '+(r.mix.deficit>=0?'below':'above')+' ambient',r.mix.deficit>0)+metric('Source cooling',fmt(r.cooling/1000,2),'kW',r.valid?'Sensible cooling at delivery':'Nominal only · unsupported supply')+metric('Cold-air flow',fmt(r.m*1000,1),'g/s',fmt(r.deliveredMass,2)+' kg delivered in this activation')+metric('Supported activation',fmt(r.valid?r.receiver.served:0,1),'s','Requested '+fmt(state.activation,0)+' s · valve time');
 const coldEnough=r.mix.canReach,store=r.coldStore;
 let insight=`<h3>${!r.valid?'Resolve the supply first.':coldEnough?'The source is cold enough.':'The source is too warm for this target.'}</h3><p>${!r.valid?esc(r.blocks.join(' ')):coldEnough?`A ${fmt(state.delta,1)}°C drop needs at least <b>${fmt(r.mix.coldFraction*100,1)}% cold air</b> in an ideal mix. Nozzle shape and distance determine how much reaches the target.`:`Mixing this stream with ambient air cannot reach a ${fmt(state.delta,1)}°C drop. Increase net expansion work or reduce heat gain.`}</p>`;
 if(store)insight+=`<p>Separate cold-storage budget: <b>${fmt(store.remainingSensibleJ/1000,1)} kJ</b> after ${fmt(state.coldHold,0)} s. Charging and driven discharge remain unspecified.</p>`;
 insight+='<a class="link-button" href="engineering.html#system">View mass, energy and tank calculations ↗</a>';$('#insight').innerHTML=insight;
 const c=nearestCase(),v=snapshot(c,Math.min(cfd.time,c.times.at(-1))),diff=mismatches(c);
 $('#evidence').innerHTML=`<span class="tag ${diff.length?'warn':''}">${diff.length?'REFERENCE ONLY':'BOUNDARY CLOSE'}</span><h3>Saved CFD · ${v.region==='corridor'?'walking corridor':'whole domain'}</h3><div class="number">${fmt(v.v[0],3)} m³ <small>at ≥${fmt(v.delta,1)}°C drop</small></div><p>${c.id} · ${v.s.time_s} s · ${fmt(c.source_kg_s*1000,1)} g/s at ${fmt(c.source_c,2)}°C. ${diff.length?'Your inputs differ. A new spatial result needs a CFD rerun.':'Exit boundary is close. This does not validate the hardware.'}</p><button class="text-button link-button" data-open-case="${c.id}">Explore this CFD case →</button>`;
 $('#assumptionsSummary').textContent=`Assumptions & limits · ${r.warnings.length+r.blocks.length} notes`;$('#assumptionsBody').innerHTML='<ul>'+[...r.blocks,...r.warnings].map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul><a href="engineering.html#basis">First principles, Lean coverage and validation ↗</a>';
 if(view==='compare')renderComparison();if(view==='cfd')renderCFD();persist();
}
function setPart(id){if(!parts.some(p=>p[0]===id))return;part=id;renderEditor();persist();}
function setView(id){view=id;for(const e of document.querySelectorAll('.view'))e.hidden=e.id!==id;for(const e of document.querySelectorAll('[data-view]')){e.classList.toggle('active',e.dataset.view===id);e.setAttribute('aria-pressed',String(e.dataset.view===id));}if(id==='compare')renderComparison();if(id==='cfd')renderCFD();if(id!=='cfd')stopTime();persist();}
function renderComparison(){
 const b=M.calculate(pinned);$('#baseline').innerHTML=`<div class="baseline"><div><small>Pinned baseline</small><b>${esc(M.sources.find(s=>s.id===pinned.source)?.name||'Reference')}</b><em>Pin any design to compare it here.</em></div>${[['Nozzle air',r.Tnozzle,b.Tnozzle,'°C'],['Source cooling',r.cooling/1000,b.cooling/1000,'kW'],['Supported activation',r.valid?r.receiver?.served:0,b.valid?b.receiver?.served:0,'s']].map(([name,v,bv,u])=>`<div><small>${name}</small><b>${fmt(v,2)} ${u}</b><em>${Number.isFinite(v-bv)?(v-bv>0?'+':'')+fmt(v-bv,2):'—'} ${u} from baseline</em></div>`).join('')}</div>`;
 const definitions={source:[M.sources.map(s=>s.id),M.sources.map(s=>s.name),'Compressor capacity changes supply support. A fixed motor bank still draws the same rated flow.'],nozzle:[['base','wide','round70','duct150','perforated'],['Standard slot','Wide slot','Ø70 mm control','Ø150 mm control','Perforated control'],'Source cooling stays nearly the same at fixed flow. Shape and reach require the matching CFD case.'],tankL:[[0,100,500,1000,2000,3000],['No receiver','100 L','500 L','1,000 L','2,000 L','3,000 L'],'Receiver volume changes supported burst time. It cannot remove a continuous flow deficit.'],coldL:[[.5,1,2,5,10,20],['0.5 m','1 m','2 m','5 m','10 m','20 m'],'Each cold branch has this length. Bore and heat-leak model remain fixed.'],method:[['motor','throttle','turbine','isentropic'],['Loaded air motors','Isenthalpic regulator','Turbine · assumed η','Isentropic upper bound'],'Same rated motor-bank flow for this comparison. No commercial turbine has been matched.']};
 const [values,names,note]=definitions[compareType];const rows=values.map((v,i)=>({value:v,name:names[i],result:M.calculate({...state,...(compareType==='method'?{processFad:state.motors*972}:{}),[compareType]:v},undefined,{})}));
 const max=Math.max(.1,...rows.map(e=>e.result.ok?Math.max(0,e.result.cooling/1000):0));
 $('#comparison').innerHTML=`<p class="compare-note">${note}</p><div class="table-card">${rows.map(({value,name,result:z})=>`<div class="comparison-row ${state[compareType]===value?'current':''}"><div>${esc(name)}<small>${z.valid?(z.steady?'Conditional steady supply':'Finite burst · '+fmt(z.receiver.served)+' s'):'Unsupported / not supplied'}</small></div><div><div class="comparison-bar"><i style="width:${z.ok?Math.max(0,z.cooling/1000)/max*100:0}%;${!z.valid?'background:var(--line-strong)':''}"></i></div><small>${fmt(z.cooling/1000,2)} kW ${z.valid?'initial source cooling':'nominal only'} · ${fmt(z.Tnozzle)}°C</small></div><div class="numeric">${fmt(z.valid?z.receiver?.served:0)} s</div><button data-apply="${compareType}" data-option="${value}">Use</button></div>`).join('')}</div><p class="small-note">Only one input changes. Unsupported source budgets are grey. These are calculations, not new CFD.</p>`;
}
function chart(points){const W=650,H=200,L=50,R=15,T=20,B=34,maxT=Math.max(...points.map(p=>p[0])),maxV=Math.max(.001,...points.map(p=>p[1]))*1.1,X=t=>L+(W-L-R)*t/Math.max(1,maxT),Y=v=>H-B-(H-B-T)*v/maxV;return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Cooled volume at saved CFD times"><title>Cooled volume at saved CFD times</title>${[0,.5,1].map(n=>`<line x1="${L}" x2="${W-R}" y1="${Y(n*maxV)}" y2="${Y(n*maxV)}" stroke="var(--line)"/><text x="${L-8}" y="${Y(n*maxV)+3}" text-anchor="end">${fmt(n*maxV,3)}</text>`).join('')}<path d="M${points.map(p=>X(p[0])+','+Y(p[1])).join(' L')}" fill="none" stroke="var(--blue)" stroke-width="2"/><line x1="${X(cfd.time)}" x2="${X(cfd.time)}" y1="${T}" y2="${H-B}" stroke="var(--text)" stroke-dasharray="3 4"/>${[0,.5,1].map(n=>`<text x="${X(n*maxT)}" y="${H-10}" text-anchor="middle">${fmt(n*maxT,0)} s</text>`).join('')}<text x="${L}" y="11">m³</text></svg>`;}
function renderCFD(){const c=currentCase(),x=snapshot(c);cfd.time=x.s.time_s;cfd.region=x.region;$('#caseSelect').value=c.id;$('#region').value=cfd.region;$('#time').max=c.times.at(-1);$('#time').value=cfd.time;$('#timeLabel').textContent=cfd.time+' s';const mismatch=mismatches(c);
 $('#caseStatus').innerHTML=`<div class="status"><span class="label">${mismatch.length?'Saved reference · current inputs differ':'Current exit boundary is close to this reference'}</span><span>${mismatch.length?'Changed: '+mismatch.join(', '):'Prescribed supply · hardware unvalidated'}</span></div>`;
 $('#cfdResults').innerHTML=metric('Cooled air volume',fmt(x.v[0],3),'m³','Air with ≥'+fmt(x.delta,1)+'°C drop',true)+metric('Cooled air mass',fmt(x.v[1],3),'kg','Source + entrained ambient air')+metric('Source air in this region',fmt(x.v[2],3),'kg','Tracer share of cooled mass')+metric('Cold energy in this region',fmt(x.v[3]/1000,2),'kJ',cfd.region==='corridor'?'0.448 m³ analysis corridor':'Whole simulated fluid domain');
 $('#timeChart').innerHTML=chart(c.snapshots.map(s=>[s.time_s,s.regions[cfd.region].values[x.j][0]]));
 const hasAnimation=['P00_one_d20','R00_wide_d35'].includes(c.id);const signature=c.id;
 if($('#animation').dataset.case!==signature){$('#animation').dataset.case=signature;$('#animation').innerHTML=hasAnimation?`<h3>Saved cooling animation · ${c.id}</h3><video controls loop playsinline poster="${study}results/${c.id}-air-field.png"><source src="${study}results/${c.id}-air-exposure.mp4" type="video/mp4"></video><p class="small-note">Executed source-field animation. Video has its own playback clock. System inputs do not change the saved fields.</p>`:`<h3>Saved fields · ${c.id}</h3><p class="small-note">This case has saved numerical fields. It has no exported animation. Use the time control to explore its cooled mass and volume.</p><p class="small-note">An animation is available for the coarse-grid wide-slot case. Selecting it also changes the displayed case results.</p><button data-open-case="R00_wide_d35">View wide-slot animation →</button>`;}
 persist();
}
function stopTime(){if(playTimer)clearInterval(playTimer);playTimer=null;$('#playTime').textContent='Play saved time';}
function loadCase(id){if(!D.cases.some(c=>c.id===id))return;cfd.id=id;cfd.time=Math.min(10,currentCase().times.at(-1));stopTime();setView('cfd');}
$('#caseSelect').innerHTML=D.cases.map(c=>`<option value="${c.id}">${c.id} · ${c.width_m*1000} × ${c.height_m*1000} mm · ${fmt(c.distance_m,2)} m${c.cells>100000?' · finer grid':''}</option>`).join('');
let updateTimer;document.addEventListener('input',e=>{const key=e.target.dataset.key;if(!key)return;clearScenarioLink();state[key]=typeof M.defaults[key]==='number'?(e.target.value===''?NaN:Number(e.target.value)):e.target.value;$('#preset').value='custom';sync();clearTimeout(updateTimer);updateTimer=setTimeout(()=>{renderOutputs();updateEditorReadout();},50);});
function updateEditorReadout(){// Keep active sliders and focus stable while updating computed values.
 const holder=$('#editorBody .editor-readout');if(!holder||!r.ok)return;
 let rows=[];if(part==='source')rows=[['Working pressure',fmt(r.source.bar)+' barg'],['Flow after purge',fmt(r.availableFad,2)+' m³/min'],['Motor-bank demand',fmt(r.requiredFad/1000,2)+' m³/min']];if(part==='tank')rows=[['Supported activation',fmt(r.receiver.served,1)+' s'],['Pressure floor',fmt((r.minP-M.C.pa)/1e5,2)+' barg'],['Refill after burst',fmt(r.receiver.refillSeconds,1)+' s']];if(part==='pipes')rows=[['Cold path heat exchange',fmt(r.coldHeat,0)+' W'],['Total exhaust backpressure',fmt((r.Pex-M.C.pa)/1e5,3)+' bar']];if(part==='expansion')rows=[['Shaft work removed',fmt(r.shaft/1000,2)+' kW'],['Air leaving expander',fmt(r.Tex,1)+'°C']];if(part==='nozzles')rows=[['Outlet air speed',fmt(r.v,2)+' m/s'],['Total open area',fmt(r.area*10000,0)+' cm²']];holder.outerHTML=readout(rows);
}
document.addEventListener('change',e=>{if(['method','coldMode'].includes(e.target.dataset.key)){clearTimeout(updateTimer);renderOutputs();renderEditor();}});
document.addEventListener('click',e=>{
 const edit=e.target.closest('[data-edit],[data-part-edit]');if(edit){setPart(edit.dataset.edit||edit.dataset.partEdit);return;}
 const b=e.target.closest('button');if(!b)return;
 if(b.dataset.view){clearScenarioLink();setView(b.dataset.view);}
 if(b.dataset.pipe){pipe=b.dataset.pipe;renderEditor();}
 if(b.dataset.set){clearScenarioLink();const k=b.dataset.set;state[k]=typeof M.defaults[k]==='number'?Number(b.dataset.value):b.dataset.value;$('#preset').value='custom';renderOutputs();renderEditor();}
 if(b.dataset.compare){compareType=b.dataset.compare;for(const el of document.querySelectorAll('[data-compare]'))el.classList.toggle('active',el===b);renderComparison();}
 if(b.dataset.apply){clearScenarioLink();const k=b.dataset.apply;state[k]=typeof M.defaults[k]==='number'?Number(b.dataset.option):b.dataset.option;if(k==='method')state.processFad=state.motors*972;$('#preset').value='custom';renderOutputs();renderEditor();notify('Option applied to the current design.');}
 if(b.dataset.openCase)loadCase(b.dataset.openCase);
});
$('#scene').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){const p=e.target.closest('[data-edit]');if(p){e.preventDefault();setPart(p.dataset.edit);}}});
$('#preset').addEventListener('change',e=>{clearScenarioLink();const variants={reference:{},burst:{source:'xas68',tankL:500},throttle:{method:'throttle',eos:'real'},ideal:{method:'isentropic'}};state=M.config(variants[e.target.value]||{});renderQuick();renderOutputs();renderEditor();});
$('#reset').addEventListener('click',()=>{history.replaceState(null,'',location.pathname+location.search);state=M.config();cfd={id:'F01_wide_d35',region:'corridor',time:10};$('#preset').value='reference';renderQuick();renderOutputs();renderEditor();notify('Reference system restored.');});
$('#theme').addEventListener('click',()=>{const dark=document.body.dataset.theme!=='dark';document.body.dataset.theme=dark?'dark':'light';$('#theme').setAttribute('aria-label','Switch to '+(dark?'light':'dark')+' theme');try{localStorage.setItem('aa-studio-theme',document.body.dataset.theme);}catch{}});
$('#showValues').addEventListener('change',()=>$('#scene').classList.toggle('hide-values',!$('#showValues').checked));$('#motion').addEventListener('click',()=>{moving=!moving;$('#scene').classList.toggle('paused',!moving);$('#motion').textContent=moving?'Pause flow':'Show flow';$('#motion').setAttribute('aria-pressed',String(moving));});
$('#pin').addEventListener('click',()=>{pinned={...state};renderComparison();notify('Current design pinned as the baseline.');});
$('#caseSelect').addEventListener('change',e=>{cfd.id=e.target.value;stopTime();cfd.time=Math.min(cfd.time,currentCase().times.at(-1));renderCFD();});$('#region').addEventListener('change',e=>{cfd.region=e.target.value;renderCFD();});$('#time').addEventListener('input',e=>{cfd.time=Number(e.target.value);renderCFD();});
$('#playTime').addEventListener('click',()=>{if(playTimer){stopTime();return;}$('#playTime').textContent='Pause saved time';playTimer=setInterval(()=>{const c=currentCase();const i=c.times.indexOf(cfd.time);cfd.time=c.times[(i+1)%c.times.length];renderCFD();},650);});
$('#save').addEventListener('click',()=>{const value={schema:'AA-computation-panel/2',generated:new Date().toISOString(),inputs:state,cfd,tab:view==='design'?'system':view,result:r,scope:'Calculated source/network. Saved CFD is independent. No new CFD run.'};const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='AA-air-cycle-design.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);notify('Scenario saved. Import it in the engineering view.');});
// Retain exact state when opening a detailed tab. No model values are translated.
for(const a of document.querySelectorAll('a[href^="engineering.html"]'))a.addEventListener('click',persist);
$('#preset').value=JSON.stringify(state)===JSON.stringify(M.config())?'reference':'custom';
$('#theme').setAttribute('aria-label','Switch to '+(document.body.dataset.theme==='dark'?'light':'dark')+' theme');
renderQuick();renderOutputs();renderEditor();setView(view);
window.addEventListener('hashchange',()=>{
 try{if(location.hash.startsWith('#scenario=')){
  const x=JSON.parse(decodeURIComponent(atob(location.hash.slice(10).replace(/-/g,'+').replace(/_/g,'/'))));
  if(x.inputs&&M.calculate(x.inputs).ok)state=M.config(x.inputs);
  if(D.cases.some(c=>c.id===x.cfd?.id))cfd={...cfd,...x.cfd};
  const next=['compare','cfd'].includes(x.tab)?x.tab:'design';
  $('#preset').value=JSON.stringify(state)===JSON.stringify(M.config())?'reference':'custom';
  renderQuick();renderOutputs();renderEditor();setView(next);
 }else if(['system','compare','cfd'].includes(location.hash.slice(1)))setView(location.hash==='#system'?'design':location.hash.slice(1));
 }catch{notify('Scenario link could not be read.');}
});
globalThis.AA_Studio={getState:()=>({...state}),getResult:()=>r,getView:()=>view,getPart:()=>part,getCFD:()=>({id:currentCase().id,...snapshot()}),getPinned:()=>({...pinned})};
})();
