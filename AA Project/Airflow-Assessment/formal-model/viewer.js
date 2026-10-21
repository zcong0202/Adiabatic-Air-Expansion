/* Float companion only. The Lean proof source and dependency record are separate. */
(()=>{
 'use strict';
 const data=JSON.parse(document.getElementById('aaFormalData').textContent);
 const cp=1005,rhoRef=101325/(287.05*293.15),alphaCFD=.3146377977016922;
 const by=id=>document.getElementById('af'+id),num=id=>Number(by(id).value);
 const fmt=(v,n=2)=>Number.isFinite(v)?v.toFixed(n):'not attainable';
 const providers={current:{flow:200,maxP:11,name:'Assumed current inlet budget'},bauer:{flow:100,maxP:331,name:'BAUER quoted 100 L/min'},lp:{flow:1100,maxP:11,name:'Kaneez assumed 1,100 L/min FAD'}};
 const ids=['Mode','Provider','Demand','Beta','Mass','Cold','Tin','Pin','Pmid','Eta','Ambient','Warm','UA','Alpha','Delta','Capture','WarmFlow','Load','Speed','Width','Height','Duty','Pulse'];
 function snapshot(){
  return {mode:by('Mode').value,provider:by('Provider').value,demand:num('Demand'),beta:num('Beta'),manualMass:num('Mass'),manualCold:num('Cold'),tin:num('Tin'),pin:num('Pin'),pmid:num('Pmid'),eta:num('Eta'),ambient:num('Ambient'),warm:num('Warm'),ua:num('UA'),alpha:num('Alpha'),delta:num('Delta'),capture:num('Capture'),warmFlow:num('WarmFlow'),load:num('Load'),speed:num('Speed'),width:num('Width'),height:num('Height'),duty:num('Duty'),pulse:num('Pulse')};
 }
 function source(s){
  const provider=providers[s.provider],warnings=[];
  let mass=s.manualMass,tc=s.manualCold,stages=0,work=0;
  if(s.demand<=0)throw Error('Required source inlet flow must be positive.');
  if(s.mode!=='manual')mass=s.demand/60000*rhoRef*1000*(s.mode==='vortex'?s.beta:1);
  if(s.mode==='vortex'&&!(s.beta>0&&s.beta<1))throw Error('A vortex split requires 0 < cold fraction < 1.');
  if(s.mode.includes('throttle')){
   if(s.mode==='ideal_throttle')tc=s.tin;
   else{
    const row=data.source_lookup.find(r=>r.method===s.mode&&r.inlet_temperature_c===s.tin&&r.inlet_pressure_bar_abs===s.pin);
    if(!row||row.error)throw Error(row?.error||'EOS state unavailable; no interpolation or ideal-gas fallback used.');
    tc=row.final_source_temperature_c;
   }
  }
  if(s.mode.includes('expander')){
   if(s.pin<s.pmid)throw Error('Expansion exit pressure must not exceed inlet pressure.');
   stages=s.pin===s.pmid?0:Math.ceil(Math.log(s.pin/s.pmid)/Math.log(3)-1e-12);
   if(s.mode==='ideal_expander'){
    let tk=s.tin+273.15;
    if(stages){const q=Math.pow(s.pmid/s.pin,1/stages);for(let i=0;i<stages;i++){const next=tk*(1-s.eta*(1-Math.pow(q,(1.4-1)/1.4)));work+=cp*(tk-next);tk=next;}}
    tc=tk-273.15;
   }else{
    const row=data.source_lookup.find(r=>r.method===s.mode&&r.inlet_temperature_c===s.tin&&r.inlet_pressure_bar_abs===s.pin&&r.expansion_exit_bar_abs===s.pmid&&r.per_stage_isentropic_efficiency===s.eta);
    if(!row||row.error)throw Error(row?.error||'EOS state unavailable.');
    tc=row.final_source_temperature_c;stages=row.expander_stage_count;work=row.shaft_work_j_kg;
   }
  }
  if(!(mass>0))throw Error('Cold flow must be positive.');
  if(!['manual','vortex'].includes(s.mode)&&s.pin>provider.maxP)warnings.push('Selected inlet pressure exceeds the selected supply envelope. Change supply or pressure; this source configuration is unavailable.');
  if(s.mode==='manual'&&mass>s.demand/60000*rhoRef*1000)warnings.push('Declared cold mass exceeds declared total inlet mass. Correct the flow assumptions.');
  if(s.mode==='manual')warnings.push('Manual cold flow and temperature are a candidate operating point, not measured source calibration.');
  if(s.mode==='vortex'){
   warnings.push('Vortex inlet pressure is not computed here. Use its manufacturer-approved regulated operating point and measure flow there; the regulator/expander pressure controls do not apply to this vortex model.');
   warnings.push('Vortex cold fraction and cold temperature are coupled in real hardware. This candidate operating point needs a measured map.');
   if(s.demand>220)warnings.push('This inlet demand needs a larger matched vortex or a bank. One existing small Jeanoko unit cannot use the whole compressor flow.');
  }
  if(s.mode.includes('expander'))warnings.push('Hypothetical matched expander: per-stage efficiency assumed; no such machine, drying/icing control, load or pressure installation is verified.');
  if(s.provider==='bauer')warnings.push('BAUER rating is a cylinder-fill delivery rate. Approved process-air supply, duty and regulation remain open.');
  if(Math.abs(mass-2)>.05||s.mode.includes('expander')||s.mode.includes('throttle'))warnings.push('R07 area fraction is not validated for this flow/source. Holding it fixed is a sensitivity assumption; measure it or re-run suitable CFD.');
  if(tc<0)warnings.push('Subzero source: dry-gas screen only. Water, icing, real density and personal exposure require separate evaluation.');
  return {mass,tc,stages,work,warnings,provider};
 }
 function evaluate(s){
  const src=source(s);
  if(Math.min(s.ambient,s.warm,src.tc)<=-273.15)throw Error('Temperature must exceed absolute zero.');
  for(const key of ['ambient','warm','ua','alpha','delta','capture','warmFlow','load','speed','width','height','duty','pulse'])if(!Number.isFinite(s[key]))throw Error('Enter finite values.');
  if(s.warm<s.ambient)throw Error('This envelope assumes entrained air at least as warm as reference ambient.');
  if(!(s.alpha>=0&&s.alpha<=1&&s.capture>0&&s.capture<=1&&s.delta>0&&s.ua>=0&&s.warmFlow>=0&&s.load>=0&&s.width>0&&s.height>0&&s.speed>0&&s.duty>0&&s.duty<=1&&s.pulse>=0))throw Error('Input outside the stated physical range.');
  const m=src.mass/1000,r=Math.exp(-s.ua/(m*cp)),td=s.warm-(s.warm-src.tc)*r;
  const needed=s.delta+s.warm-s.ambient,span=s.warm-src.tc;
  const drop=s.ambient-s.warm+s.alpha*r*span;
  const alphaRequired=span*r>0?needed/(span*r):NaN;
  const maxSource=s.alpha*r>0?s.warm-needed/(s.alpha*r):NaN;
  const logmargin=s.alpha*span>0?Math.log(s.alpha*span/needed):NaN;
  const maxUA=logmargin>0?m*cp*logmargin:NaN;
  const hoseMassMin=logmargin>0?s.ua/(cp*logmargin)*1000:NaN;
  function uniform(mc){const ret=Math.exp(-s.ua/(mc*cp)),cold=s.warm-(s.warm-src.tc)*ret,c=s.capture*mc,w=s.warmFlow/1000;return s.ambient-(c*cold+w*s.warm+s.load/cp)/(c+w);}
  let minMass=NaN;
  if(s.ambient-src.tc>s.delta){let lo=1e-10,hi=Math.max(.001,m);while(uniform(hi)<=s.delta&&hi<1e3)hi*=2;if(hi<1e3){for(let i=0;i<100;i++){const mid=(lo+hi)/2;if(uniform(mid)>s.delta)hi=mid;else lo=mid;}minMass=(lo+hi)/2*1000;}}
  const power=m*cp*(s.ambient-td),targetMass=101325/(287.05*(s.ambient+273.15))*(s.width/1000)*(s.height/1000)*s.speed;
  const energyRequired=targetMass*cp*s.delta,captured=s.capture*power-s.load;
  const dutyMax=Math.min(1,src.provider.flow/s.demand),supplyPass=s.duty*s.demand<=src.provider.flow;
  const inventory=Math.max(0,s.demand-src.provider.flow)/60000*rhoRef*s.pulse*1000;
  return {src,r,td,drop,alphaRequired,maxSource,maxUA,hoseMassMin,minMass,power,uniformDrop:uniform(m),energyRequired,captured,dutyMax,supplyPass,inventory};
 }
 function plot(s,a){
  const canvas=by('Map'),ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height,left=66,top=28,pw=w-90,ph=h-88;
  ctx.fillStyle='#fff';ctx.fillRect(0,0,w,h);
  const mmax=30,im=ctx.createImageData(pw,ph);
  for(let yy=0;yy<ph;yy++)for(let xx=0;xx<pw;xx++){
   const m=.1+xx/(pw-1)*(mmax-.1),alpha=1-yy/(ph-1),r=Math.exp(-s.ua/(m/1000*cp)),d=s.ambient-s.warm+alpha*r*(s.warm-a.src.tc);
   const c=Math.max(0,Math.min(1,d/(2*s.delta))),i=(yy*pw+xx)*4;
   im.data[i]=Math.round(246-190*c);im.data[i+1]=Math.round(224-50*c);im.data[i+2]=Math.round(211-40*c);im.data[i+3]=255;
  }
  ctx.putImageData(im,left,top);ctx.strokeStyle='#12394c';ctx.lineWidth=2;ctx.beginPath();let pen=false;
  for(let xx=0;xx<pw;xx++){
   const m=.1+xx/(pw-1)*(mmax-.1),r=Math.exp(-s.ua/(m/1000*cp)),alpha=(s.delta+s.warm-s.ambient)/(r*(s.warm-a.src.tc));
   if(alpha>=0&&alpha<=1){const yy=top+(1-alpha)*ph;pen?ctx.lineTo(left+xx,yy):ctx.moveTo(left+xx,yy);pen=true;}else pen=false;
  }
  ctx.stroke();ctx.strokeStyle='#56717e';ctx.lineWidth=1;ctx.strokeRect(left,top,pw,ph);ctx.font='13px system-ui';ctx.fillStyle='#163342';
  [0,25,50,75,100].forEach(v=>{const y=top+(1-v/100)*ph;ctx.fillText(v+'%',22,y+4);});
  [0,5,10,15,20,25,30].forEach(v=>ctx.fillText(v.toString(),left+(v-.1)/(mmax-.1)*pw-4,top+ph+21));
  ctx.fillText('Cold mass flow (g/s); source temperature held fixed',left+55,h-10);ctx.fillText('Area cold fraction',left,16);
  const px=left+(a.src.mass-.1)/(mmax-.1)*pw,py=top+(1-s.alpha)*ph;
  if(px>=left&&px<=left+pw){ctx.beginPath();ctx.arc(px,py,5,0,Math.PI*2);ctx.fillStyle='#fff';ctx.fill();ctx.strokeStyle='#062e40';ctx.stroke();}
 }
 function update(){
  try{
   const s=snapshot(),a=evaluate(s);window.aaFormalLast={inputs:s,result:a};
   by('Mass').disabled=s.mode!=='manual';by('Cold').disabled=!['manual','vortex'].includes(s.mode);by('Beta').disabled=s.mode!=='vortex';
   by('Pin').disabled=['manual','vortex'].includes(s.mode);by('Tin').disabled=s.mode==='manual';
   by('Pmid').disabled=!s.mode.includes('expander');by('Eta').disabled=!s.mode.includes('expander');
   by('AlphaValue').textContent=fmt(100*s.alpha,1)+'%';by('UAValue').textContent=fmt(s.ua,2)+' W/K';by('BetaValue').textContent=fmt(100*s.beta,0)+'%';by('CaptureValue').textContent=fmt(s.capture*100,0)+'%';
   by('AreaResult').textContent=fmt(a.drop)+'°C drop';by('AreaStatus').textContent=(a.drop>s.delta?'Conditional area criterion passes':'Area criterion fails under these inputs')+'; target air '+fmt(s.ambient-a.drop)+'°C.';
   by('SourceResult').textContent=fmt(a.src.mass)+' g/s · '+fmt(a.src.tc)+'°C';
   by('SourceDetail').textContent=fmt(a.power,1)+' W cold-stream sensible potential after modeled line.'+(s.mode.includes('expander')?' '+a.src.stages+' expander stages. Assumed limit 3:1 per stage; efficiency is per stage.':'')+(s.mode==='vortex'?' Dry energy balance would require a hot stream near '+fmt((s.tin-s.beta*s.manualCold)/(1-s.beta),1)+'°C, not a prediction.':'');
   by('FractionResult').textContent='Need αA > '+fmt(100*a.alphaRequired,1)+'%';
   by('FractionDetail').textContent='With current mixing and line assumptions: source must be below '+fmt(a.maxSource,1)+'°C. αA is an area average, not a cold-flow fraction or capture efficiency.';
   by('SupplyResult').textContent=a.supplyPass?'Ideal average supply budget passes':'Average supply budget fails';
   by('SupplyDetail').textContent='Maximum loss-free duty '+fmt(100*a.dutyMax,1)+'%; requested '+fmt(100*s.duty,0)+'%. Inlet-air inventory swing for '+fmt(s.pulse,1)+' s pulse: '+fmt(a.inventory,1)+' g. Tank volume/design not calculated.';
   by('Limits').textContent='Heat-conductance bound: UA < '+fmt(a.maxUA,3)+' W/K. Hose-only mass bound at FIXED αA: > '+fmt(a.hoseMassMin,3)+' g/s. This is not the target-load or overall system flow requirement.';
   by('MassResult').textContent='Uniform model: '+fmt(a.uniformDrop)+'°C drop; needs source flow > '+fmt(a.minMass,3)+' g/s at the fixed '+fmt(s.warmFlow,1)+' g/s warm inflow and '+fmt(s.capture*100,0)+'% capture. This alternative uniform model is not the nonuniform CFD area mean.';
   by('EnergyResult').textContent='Necessary flux budget: '+fmt(a.captured,1)+' W available versus > '+fmt(a.energyRequired,1)+' W required under the selected normal-speed lower bound. '+(a.captured>a.energyRequired?'Budget passes; spatial temperature can still fail.':'Budget fails.');
   const warnings=a.src.warnings.slice();
   if(s.width!==50||s.height!==50)warnings.push('You changed target area. Original success criterion remains 50 × 50 mm at 200 mm.');
   warnings.push('UA=0 is adiabatic. If the entered temperature is already measured at the final outlet, exclude earlier hose/nozzle heating to avoid counting it twice.');
   by('Warnings').replaceChildren(...warnings.map(t=>{const p=document.createElement('p');p.textContent=t;return p;}));
   plot(s,a);by('Error').textContent='';
  }catch(e){by('Error').textContent=e.message;['AreaResult','SourceResult','FractionResult','SupplyResult'].forEach(id=>by(id).textContent='Invalid input / unavailable state');}
 }
 function preset(which){
  const base={Mode:'manual',Provider:'current',Demand:200,Beta:.5,Mass:2,Cold:5,Tin:34,Pin:9,Pmid:1.01325,Eta:.6,Ambient:34,Warm:34,UA:0,Alpha:alphaCFD,Delta:6,Capture:.6,WarmFlow:5,Load:0,Speed:1,Width:50,Height:50,Duty:1,Pulse:3};
  const choices={current:{},lp:{Mode:'vortex',Provider:'lp'},bauer:{Mode:'vortex',Provider:'bauer'},bank:{Mode:'vortex',Provider:'lp',Demand:1000},jt:{Mode:'real_throttle',Provider:'bauer',Demand:100,Pin:201},lpExp:{Mode:'real_expander',Provider:'lp',Demand:1100},hpExp:{Mode:'real_expander',Provider:'bauer',Demand:100,Pin:201,Pmid:5}};
  Object.entries({...base,...choices[which]}).forEach(([id,value])=>by(id).value=value);update();
 }
 ids.forEach(id=>by(id).addEventListener('input',update));
 document.querySelectorAll('[data-af-preset]').forEach(b=>b.addEventListener('click',()=>preset(b.dataset.afPreset)));
 window.aaFormal={snapshot,evaluate,source,preset,update};
 preset('current');
})();
