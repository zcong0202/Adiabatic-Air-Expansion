/* AA system screen. SI internally; pressures absolute unless labelled gauge.
   Browser + Node. Numerical models are conditional; CFD is independent evidence. */
(function(root){
'use strict';
const C={cp:1006,R:287.05,pa:101325,T0:273.15}; C.cv=C.cp-C.R; C.gamma=C.cp/C.cv;
const sources=[
 ['xas38','Atlas XAS 38',2,7,14.9],['xas48','Atlas XAS 48',2.5,7,18.5],
 ['xas58','Atlas XAS 58',3,7,26.5],['xas68','Atlas XAS 68',3.6,7,26.5],
 ['xas78','Atlas XAS 78',4.5,7,33],['xas88','Atlas XAS 88',5,7,33],['xas98','Atlas XAS 98',5.4,7,33],
 ['xahs38','Atlas XAHS 38',2,12,26.5],['xats68','Atlas XATS 68',3.6,10.3,33],
 ['kaneez','Kaneez 10 HP (listing)',1.1,8,null],['bauer','BAUER JUNIOR II (fill rating)',.1,200,null]
].map(([id,name,fad,bar,engine])=>({id,name,fad,bar,engine,status:id==='kaneez'?'Listing only; 1.0–1.2 m³/min; FAD unconfirmed':id==='bauer'?'Cylinder-fill rating; direct process supply unapproved':'Manufacturer pressure/FAD pair; rental variant must match'}));
const nozzles=[
 {id:'wide',name:'Custom wide slot · 280 × 40 mm',area:.28*.04,dh:2*.28*.04/(.28+.04),width:.28,height:.04},
 {id:'base',name:'Custom slot · 140 × 80 mm',area:.14*.08,dh:2*.14*.08/(.14+.08),width:.14,height:.08},
 {id:'round70',name:'Control · Ø70 mm per outlet',area:Math.PI*.07**2/4,dh:.07},
 {id:'duct150',name:'Control · Ø150 mm per outlet',area:Math.PI*.15**2/4,dh:.15},
 {id:'perforated',name:'Control · 0.5 m² face, 20% open (total)',area:.1,dh:.01,total:true},
 {id:'custom',name:'Custom open area per outlet',area:.0112,dh:.07}
];
const defaults={source:'xas78',eos:'ideal',ambient:30,sourceTemp:40,fadDensity:19.4/16.2,
 method:'motor',motors:4,motorLoad:1,motorHeat:0,motorPin:6.3,turbineEta:.65,processFad:3888,
 purge:.03,treatmentDrop:.3,regHead:.1,activation:30,plantKW:0,
 mainL:10,mainD:38,branchL:2,branchD:19,coldL:1,coldD:50,
 inletPortD:10,outletPortD:15,portL:.05,portK:1,
 roughness:.01,fittingK:2,wall:3,wallK:.2,insulation:20,insulationK:.035,hOutside:8,
 warmUAperM:0,coldMode:'reference',coldReferenceUA:2.518430164825,
 tankL:0,tankUA:20,ramp:0,tankMode:'energy',
 nozzle:'wide',outlets:4,customArea:112,cd:.9,distance:.35,layout:'one-side',pitch:0,wind:0,windDirection:'opposed',
 delta:6,targetVolume:.1,exchange:.05,
 coldTankL:0,coldTankTemp:1,coldHold:30,coldTankUA:1};
function config(overrides={}) {return {...defaults,...overrides};}
function bracket(a,x){if(x<a[0]||x>a[a.length-1])throw Error('Property table range exceeded. No extrapolation.');let l=0,r=a.length-1;while(r-l>1){let m=(l+r)>>1;if(a[m]<=x)l=m;else r=m;}return [l,(x-a[l])/(a[l+1]-a[l])];}
function properties(mode='ideal',table=root.AA_AIR){
 if(mode==='ideal')return {h:(T,p)=>C.cp*T,s:(T,p)=>C.cp*Math.log(T)-C.R*Math.log(p),rho:(T,p)=>p/(C.R*T),TfromH:(h,p)=>h/C.cp,TfromS:(s,p)=>Math.exp((s+C.R*Math.log(p))/C.cp),cp:(T,p)=>C.cp};
 if(!table)throw Error('Real-air table unavailable.');
 function get(key,T,p){const [i,a]=bracket(table.p_bar,p/1e5),[j,b]=bracket(table.t_k,T),v=table[key];return (1-a)*((1-b)*v[i][j]+b*v[i][j+1])+a*((1-b)*v[i+1][j]+b*v[i+1][j+1]);}
 function inv(key,value,p){let l=table.t_k[0],r=table.t_k.at(-1);if(value<get(key,l,p)||value>get(key,r,p))throw Error('Required air temperature is outside 160–500 K property table.');for(let i=0;i<44;i++){let m=(l+r)/2;if(get(key,m,p)<value)l=m;else r=m;}return (l+r)/2;}
 return {h:(T,p)=>get('h',T,p),s:(T,p)=>get('s',T,p),rho:(T,p)=>get('rho',T,p),TfromH:(h,p)=>inv('h',h,p),TfromS:(s,p)=>inv('s',s,p),cp:(T,p)=>(get('h',Math.min(500,T+.05),p)-get('h',Math.max(160,T-.05),p))/(Math.min(500,T+.05)-Math.max(160,T-.05))};
}
function viscosity(T){return 1.716e-5*(T/273.15)**1.5*(273.15+110.4)/(T+110.4);}
function friction(Re,relativeRoughness){if(Re<=0)return 0;if(Re<=2300)return 64/Re;let f=.25/Math.log10(relativeRoughness/3.7+5.74/Re**.9)**2;if(Re>=4000)return f;return (64/Re)*(4000-Re)/1700+f*(Re-2300)/1700;}
function pipeLoss(m,T,p,L,D,K=0,rough=.00001,eos=properties()){
 const A=Math.PI*D*D/4,rho=eos.rho(T,p),v=m/(rho*A),Re=m*D/(A*viscosity(T));
 const f=friction(Re,rough/D);return {dp:(f*L/D+K)*rho*v*v/2,Re,f,v,mach:v/Math.sqrt(C.gamma*C.R*T),rho};
}
function pressureRequired(m,T,pout,L,D,K,rough,eos){let pin=pout;for(let i=0;i<45;i++){const loss=pipeLoss(m,T,(pin+pout)/2,L,D,K,rough,eos);let next=pout+loss.dp;if(Math.abs(next-pin)<1e-6)return {pin:next,...loss};pin=.5*(pin+next);}return {pin,...pipeLoss(m,T,(pin+pout)/2,L,D,K,rough,eos)};}
function thermalUA(L,D,c){if(!L)return 0;const r1=D/2,r2=r1+c.wall/1000,r3=r2+c.insulation/1000;
 return L/(Math.log(r2/r1)/(2*Math.PI*c.wallK)+Math.log(r3/r2)/(2*Math.PI*c.insulationK)+1/(c.hOutside*2*Math.PI*r3)); // neglect internal resistance: conservative heat leak
}
function heatPipe(T,pin,pout,m,UA,Ta,eos){const hin=eos.h(T,pin),ha=eos.h(Ta,pout);const cp=eos.cp(T,pin);const hout=ha+(hin-ha)*Math.exp(-UA/(m*cp));return {T:eos.TfromH(hout,pout),q:m*(hout-hin),hin,hout,UA};}
function mixing(m,Tc,Ta,delta,exchange=0){
 const deficit=Ta-Tc,positive=Math.max(0,deficit);
 const f=positive>0?delta/positive:Infinity;
 const mixedMax=positive>=delta?m*positive/delta:0;
 const addedMax=Math.max(0,mixedMax-m);
 const mixedDelta=m*deficit/(m+exchange);
 return {deficit,coldFraction:f,mixedMax,addedMax,mixedDelta,canReach:positive>=delta};
}
function receiver(c,{mout,minP,source,availableFad},stepSize=.025){
 const Ta=c.ambient+C.T0,Tin=c.sourceTemp+C.T0,Tinitial=Tin;
 const Pset=C.pa+(source.bar-c.treatmentDrop)*1e5;
 const maxIn=availableFad/60*c.fadDensity; // m³/min × kg/m³ → kg/s
 const missing=Math.max(0,mout-maxIn);
 const isothermalLitres=Pset>minP?missing*c.activation*C.R*Tinitial/(Pset-minP)*1000:Infinity;
 if(c.tankL===0){const served=maxIn+1e-12>=mout&&Pset>=minP&&c.ramp===0?c.activation:0;return {served,full:served===c.activation,isothermalLitres,points:[],massDelivered:served*mout,storedMass:0,massResidual:0,energyResidual:0,initialP:Pset,minimumP:minP,capacityRatio:maxIn/mout,refillSeconds:0};}
 const V=c.tankL/1000,dt=stepSize,cv=C.cv,cp=C.cp;
 let m=Pset*V/(C.R*Tinitial),U=m*cv*Tinitial,t=0,del=0,mi=0,energy=0,served=0,stopped=Pset<minP;
 const m0=m,U0=U,points=[{t:0,p:Pset/1e5-1.01325,T:Tinitial-C.T0}],Twall=Ta;
 while(t<c.activation-1e-9){const step=Math.min(dt,c.activation-t),T=U/(m*cv),P=m*C.R*T/V;
  const ramp=c.ramp===0?1:Math.min(1,(t+step/2)/c.ramp);
  let incoming=maxIn*ramp;
  let outgoing=stopped?0:mout;
  const q=c.tankMode==='isothermal'?0:c.tankUA*(Twall-T);
  // Cap incoming mass/enthalpy so the next state does not exceed charge pressure.
  const cap=c.tankMode==='isothermal'?(m0-m)/step+outgoing:((U0-U)/step+outgoing*cp*T-q)/(cp*Tin);
  incoming=Math.max(0,Math.min(incoming,cap));
  let dm=(incoming-outgoing)*step,dE=(incoming*cp*Tin-outgoing*cp*T+q)*step;
  let mn=m+dm,Un=U+dE;
  if(c.tankMode==='isothermal'){Un=mn*cv*Tinitial;dE=Un-U;}
  const nextP=Un*C.R/(cv*V);
  let portion=1;
  if(!stopped&&nextP<minP){portion=Math.max(0,Math.min(1,(P-minP)/(P-nextP)));stopped=true;}
  // End the activation at first pressure failure; no restart credit.
  if(portion<1){dm*=portion;dE*=portion;incoming*=portion;outgoing*=portion;}
  m+=dm;U+=dE;mi+=incoming*step;del+=outgoing*step;energy+=dE;served+=outgoing>0?step*portion:0;t+=step*portion;
  if(points.length===1||t-points.at(-1).t>=.49||portion<1)points.push({t,p:U*C.R/(cv*V)/1e5-1.01325,T:U/(m*cv)-C.T0});
  if(stopped)break;
 }
 if(points.at(-1).t<t-1e-8)points.push({t,p:U*C.R/(cv*V)/1e5-1.01325,T:U/(m*cv)-C.T0});
 return {served,full:served>=c.activation-1e-6,isothermalLitres,points,massDelivered:del,storedMass:m0,massResidual:m-m0-mi+del,energyResidual:U-U0-energy,initialP:Pset,minimumP:minP,capacityRatio:maxIn/mout,refillSeconds:Math.max(0,m0-m)/Math.max(maxIn,1e-12),temperatureRange:points.map(p=>p.T)};
}
function coldStore(c){const V=c.coldTankL/1000,T0=c.coldTankTemp+C.T0,Ta=c.ambient+C.T0,m=C.pa*V/(C.R*T0);
 if(!m)return null;const T=Ta+(T0-Ta)*Math.exp(-c.coldTankUA*c.coldHold/(m*C.cv));
 return {mass:m,T:T-C.T0,initialSensibleJ:m*C.cp*Math.max(0,Ta-T0),remainingSensibleJ:m*C.cp*Math.max(0,Ta-T),pressureBarG:C.pa*T/T0/1e5-1.01325,initialPressureBarG:0,scope:'Sealed fixed-volume tank initially at atmospheric pressure. Budget only; no forced discharge or charging prediction.'};}
function validate(c){const numeric=Object.keys(defaults).filter(k=>typeof defaults[k]==='number');for(const k of numeric)if(!Number.isFinite(c[k]))throw Error('Enter a finite value for '+k+'.');
 if(!sources.some(s=>s.id===c.source)||!nozzles.some(n=>n.id===c.nozzle))throw Error('Select a catalogue option.');
 if(!['reference','insulated'].includes(c.coldMode)||!['energy','isothermal'].includes(c.tankMode)||!['one-side','two-side','overhead','one-row'].includes(c.layout)||!['front','opposed'].includes(c.windDirection))throw Error('Select a valid path model and layout.');
 if(!['ideal','real'].includes(c.eos)||!['motor','throttle','turbine','isentropic'].includes(c.method))throw Error('Select a valid model.');
 for(const k of ['motors','outlets'])if(c[k]<1||c[k]>16||!Number.isInteger(c[k]))throw Error(k+' must be an integer from 1 to 16.');
 for(const k of ['mainD','branchD','coldD','inletPortD','outletPortD','wall','wallK','insulationK','hOutside','fadDensity','customArea','delta','targetVolume','processFad'])if(c[k]<=0)throw Error(k+' must be positive.');
 for(const k of ['mainL','branchL','coldL','portL','portK','roughness','fittingK','insulation','warmUAperM','coldReferenceUA','tankL','tankUA','ramp','plantKW','coldTankL','coldHold','coldTankUA','exchange','wind','regHead','motorHeat','treatmentDrop'])if(c[k]<0)throw Error(k+' cannot be negative.');
 if(c.motorLoad<0||c.motorLoad>1||c.turbineEta<0||c.turbineEta>1||c.purge<0||c.purge>=1||c.cd<=0||c.cd>1)throw Error('Efficiency, load, purge and Cd must stay within their stated bounds.');
 if(c.activation<=0||c.activation>30)throw Error('Activation must be >0 and ≤30 s.');
 if(c.ambient< -10||c.ambient>60||c.sourceTemp< -10||c.sourceTemp>100||c.coldTankTemp<=-100||c.coldTankTemp>100)throw Error('Temperature outside the declared design range.');
 if(c.motorPin<=0||c.distance<.1||c.distance>2)throw Error('Check inlet pressure and target distance.');
 if(c.tankL>100000||c.mainL>1000||c.branchL>1000||c.coldL>1000)throw Error('Geometry exceeds this screening model.');
}
function calculate(input={},airTable,boundary){
 const c=config(input),warnings=[],blocks=[];try{validate(c);
 const source=sources.find(s=>s.id===c.source),nozzle=nozzles.find(n=>n.id===c.nozzle),eos=properties(c.eos,airTable);
 const Ta=c.ambient+C.T0,Ts=c.sourceTemp+C.T0;
 const requiredFad=c.method==='motor'?c.motors*16.2*60:c.processFad;
 const m=requiredFad/1000/60*c.fadDensity;
 const availableFad=source.fad*(1-c.purge);
 const area=nozzle.id==='custom'?c.customArea/1e4*c.outlets:nozzle.area*(nozzle.total?1:c.outlets);
 const dh=nozzle.id==='custom'?Math.sqrt(4*c.customArea/1e4/Math.PI):nozzle.dh;
 const Ps=boundary?.p??(C.pa+(source.bar-c.treatmentDrop)*1e5);
 const Pin=c.method==='motor'?C.pa+c.motorPin*1e5:Ps;
 if(Ps<=C.pa||Pin>Ps)blocks.push('Supply pressure cannot maintain the selected expander inlet pressure.');
 let Tex=Ts,Tcold=Ts,Pex=C.pa,Pnozzle=C.pa,shaft=0,idealWork=0,sourceHeat=c.method==='motor'?c.motors*c.motorHeat:0,lossCold,lossPort,hotMain,hotBranch;
 let inletPort=c.method==='motor'?pressureRequired(m/c.motors,Ts,Pin,c.portL,c.inletPortD/1000,c.portK,c.roughness/1000,eos):{pin:Pin,dp:0,mach:0};
 let warmLossMain=pressureRequired(m,Ts,Pin+c.regHead*1e5,c.mainL,c.mainD/1000,c.fittingK,c.roughness/1000,eos);
 let warmLossBranch=pressureRequired(m/c.motors,Ts,inletPort.pin+c.regHead*1e5,c.branchL,c.branchD/1000,c.fittingK,c.roughness/1000,eos);
 warmLossMain=pressureRequired(m,Ts,warmLossBranch.pin,c.mainL,c.mainD/1000,c.fittingK,c.roughness/1000,eos);
 let minP=warmLossMain.pin;
 // For non-motor modes, the available pressure is used after line losses, rather than requiring pressure above the source itself.
 const mainOut=Math.max(C.pa,Ps-warmLossMain.dp),branchOut=Math.max(C.pa,mainOut-warmLossBranch.dp);
 hotMain=heatPipe(Ts,Ps,mainOut,m,c.warmUAperM*c.mainL,Ta,eos);
 hotBranch=heatPipe(hotMain.T,mainOut,branchOut,m,c.warmUAperM*c.branchL*c.motors,Ta,eos);
 const expPin=c.method==='motor'?Pin:branchOut;
 const Tin=eos.TfromH(hotBranch.hout,expPin);
 if(c.method!=='motor')minP=C.pa+warmLossMain.dp+warmLossBranch.dp+.2e5;
 const coldUA=c.coldMode==='reference'?c.coldReferenceUA*c.coldL*c.motors:thermalUA(c.coldL,c.coldD/1000,c)*c.motors;
 // Fixed point: exhaust backpressure, temperature, cold pipe losses, outlet pressure.
 for(let i=0;i<35;i++){
  const rho=eos.rho(Tcold,C.pa),v=m/(rho*area);
  Pnozzle=C.pa+rho*v*v/(2*c.cd*c.cd);
  lossCold=pressureRequired(m/c.motors,Tex,Pnozzle,c.coldL,c.coldD/1000,c.fittingK,c.roughness/1000,eos);
  lossPort=c.method==='motor'?pressureRequired(m/c.motors,Tex,lossCold.pin,c.portL,c.outletPortD/1000,c.portK,c.roughness/1000,eos):{pin:lossCold.pin,dp:0,mach:0};
  Pex=lossPort.pin;
  if(Pex>=expPin){blocks.push('Outlet and pipe backpressure exceed expander inlet pressure.');break;}
  const hin=eos.h(Tin,expPin);
  try {const his=eos.h(eos.TfromS(eos.s(Tin,expPin),Pex),Pex);idealWork=m*(hin-his);}
  catch(e){if(c.method!=='throttle')throw e;idealWork=0;warnings.push('Isentropic reference leaves the real-air property table. Throttle enthalpy remains within the table.');}
  shaft=c.method==='motor'?c.motors*840*c.motorLoad:c.method==='throttle'?0:idealWork*(c.method==='isentropic'?1:c.turbineEta);
  if(shaft>idealWork+1e-6)blocks.push('Requested shaft work exceeds the reversible expansion limit.');
  Tex=eos.TfromH(hin-shaft/m+sourceHeat/m,Pex);
  const hpath=heatPipe(Tex,Pex,Pnozzle,m,coldUA,Ta,eos);
  const newT=hpath.T;
  if(Math.abs(newT-Tcold)<1e-7){Tcold=newT;break;}Tcold=.35*Tcold+.65*newT;
 }
 const cold=heatPipe(Tex,Pex,Pnozzle,m,coldUA,Ta,eos);
 // Exit kinetic energy comes from stagnation enthalpy; report total and static separately.
 let jetT=Tcold,v=0;for(let i=0;i<20;i++){v=m/(eos.rho(jetT,C.pa)*area);jetT=eos.TfromH(eos.h(cold.T,Pnozzle)-v*v/2,C.pa);if(!Number.isFinite(jetT)||jetT<=0)throw Error("No physical low-speed nozzle state. Use a compressible flow model.");}
 const mach=v/Math.sqrt(C.gamma*C.R*jetT);
 const hin=eos.h(Tin,expPin),hex=eos.h(Tex,Pex),hout=eos.h(jetT,C.pa)+v*v/2;
 const energyResidual=m*(hout-hin)+shaft-sourceHeat-cold.q;
 const ambientH=eos.h(Ta,C.pa),cooling=m*(ambientH-hout); // useful sensible enthalpy, retains kinetic energy
 const mix=mixing(m,jetT-C.T0,c.ambient,c.delta,c.exchange);
 const receiverResult=receiver(c,{mout:m,minP,source,availableFad});
 const steady=availableFad*1000>=requiredFad-1e-6&&Ps>=minP;
 if(!steady)warnings.push('Rated-flow continuous operation unavailable. Tank results only cover a finite burst.');
 if(source.id==='kaneez')warnings.push('Kaneez flow and FAD basis are unverified; 1.1 m³/min is the listing midpoint.');
 if(source.id==='bauer'){blocks.push('JUNIOR II is a cylinder-filling unit; direct process supply is not approved.');warnings.push('100 L/min is a filling rating. Continuous process flow is a hypothetical bound only.');}
 if(c.method==='motor'){
  if(c.motorPin>7)blocks.push('Motor inlet exceeds the 7 barg working-pressure rating on the supplier page.');
  if(c.ambient>40)blocks.push('Ambient exceeds the 40°C motor ambient rating on the supplier page.');
  warnings.push('Motor connection bores use the recommended 10 mm inlet / 15 mm outlet hose sizes as proxies. Port length and fitting K are assumed; actual internal areas are unknown.');
  warnings.push('840 W and 16.2 L/s per motor are a conditional loaded catalogue pair. Match the load, inlet state and exhaust conditions.');
  if(c.motorLoad!==1||Math.abs(c.motorPin-6.3)>.01||Math.abs(Tin-C.T0-40)>2||Pex-C.pa>2000)warnings.push('Outside the nominal motor comparison point. No validated off-design performance map.');
 }
 if(c.method==='turbine')warnings.push('Turbine efficiency is assumed. No matched off-the-shelf turbine is selected.');
 if(c.method==='isentropic')warnings.push('Reversible adiabatic expansion is an upper bound, not a component prediction.');
 if(c.eos==='ideal'&&c.method==='throttle')warnings.push('Ideal-gas isenthalpic throttling has zero temperature drop. Use real-air mode for a Joule–Thomson estimate.');
 if(Pex-C.pa>2000)warnings.push('Exhaust collector backpressure is material. Supplier motor data are needed.');
 if(Math.max(mach,lossCold?.mach||0,lossPort?.mach||0,inletPort.mach,warmLossMain.mach,warmLossBranch.mach)>.3)blocks.push('Mach >0.3. This low-speed pipe/nozzle model is not valid; compressible network analysis required.');
 if(receiverResult.served===0)blocks.push('No sustained rated-flow interval under the selected supply and pressure assumptions.');
 if(c.eos==='real'&&c.tankL>0)warnings.push('Receiver dynamics use ideal-gas cv. Real-air mode applies to the steady flow path only.');
 if(jetT<273.15)warnings.push('Subzero prediction assumes dry air. Dew point, condensation and icing are not modelled.');
 if(c.tankL>0)warnings.push('Receiver-source history assumes fixed motor shaft work during temperature drift; no motor off-design map or line thermal inertia is available.');
 warnings.push('Warm/cold pipe models assume steady wall temperature. First-pulse line cooldown and solar load are unresolved.');
 const valid=blocks.length===0;
 const result={ok:true,valid,c,source,nozzle,m,requiredFad,availableFad,area,dh,Tin:Tin-C.T0,Tex:Tex-C.T0,Tnozzle:jetT-C.T0,Ttotal:cold.T-C.T0,v,mach,shaft,idealWork,eta:idealWork>0?shaft/idealWork:0,sourceHeat,cooling,coldHeat:cold.q,warmHeat:hotMain.q+hotBranch.q,coldUA,expPin,Pex,Pnozzle,Ps,minP,pipeMain:warmLossMain,pipeBranch:warmLossBranch,pipeCold:lossCold,inletPort,outletPort:lossPort,mix,receiver:receiverResult,coldStore:coldStore(c),steady,blocks:[...new Set(blocks)],warnings:[...new Set(warnings)],energyResidual,
  deliveredMass:valid?receiverResult.massDelivered:0,
  idealMixedMass:valid&&mix.canReach?receiverResult.massDelivered*mix.deficit/c.delta:0,
  targetMass:C.pa/(C.R*(Ta-c.delta))*c.targetVolume,
  cop:c.plantKW>0&&valid?Math.max(0,cooling)/(c.plantKW*1000):null,
  maximumRatedMotors:Math.floor(availableFad*1000/(16.2*60)),
  scope:'Conditional source/network screen + ideal-gas receiver transient. Not a new CFD run.'};
 if(!boundary){
  const history=valid&&c.tankL>0?receiverResult.points.map(p=>{const z=calculate({...c,sourceTemp:p.T,tankL:0,ramp:0},airTable,{p:C.pa+p.p*1e5});return {t:p.t,T:z.ok?z.Tnozzle:null,cooling:z.ok?z.cooling:null,targetCooling:z.ok&&c.ambient-z.Tnozzle>=c.delta?Math.max(0,z.cooling):0};}):[];
  result.sourceHistory=history;result.deliveredColdEnergyJ=valid?cooling*receiverResult.served:0;
  if(history.length>1&&history.every(p=>p.cooling!==null)){result.deliveredColdEnergyJ=0;for(let i=1;i<history.length;i++)result.deliveredColdEnergyJ+=(history[i].t-history[i-1].t)*(history[i].cooling+history[i-1].cooling)/2;}
  let targetEnergy=valid&&mix.canReach?Math.max(0,result.deliveredColdEnergyJ):0;
  if(history.length>1){targetEnergy=0;for(let i=1;i<history.length;i++)targetEnergy+=(history[i].t-history[i-1].t)*(history[i].targetCooling+history[i-1].targetCooling)/2;}
  result.idealMixedMass=targetEnergy/(C.cp*c.delta);
 }
 return result;
 }catch(e){return {ok:false,valid:false,c,error:e.message,blocks:[e.message],warnings};}
}
function sweep(c,key,values,air){return values.map(value=>{const r=calculate({...c,[key]:value},air);return {value,ok:r.ok,valid:r.valid,source:r.source?.name,temperature:r.ok?r.Tnozzle:null,cooling:r.ok?r.cooling:null,mass:r.ok?r.m:null,served:r.ok?r.receiver.served:null,steady:r.steady,blocks:r.blocks};});}
function sizeReceiver(c,r){if(!r.ok||r.Ps<=r.minP)return null;const args={mout:r.m,minP:r.minP,source:r.source,availableFad:r.availableFad};if(receiver({...c,tankL:0},args).full)return 0;let l=0,h=100000;if(!receiver({...c,tankL:h},args).full)return null;for(let i=0;i<23;i++){let v=(l+h)/2;if(receiver({...c,tankL:v},args).full)h=v;else l=v;}return h;}
const api={sizeReceiver,C,sources,nozzles,defaults,config,properties,friction,pipeLoss,pressureRequired,thermalUA,heatPipe,mixing,receiver,coldStore,calculate,sweep};
root.AA_Model=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
