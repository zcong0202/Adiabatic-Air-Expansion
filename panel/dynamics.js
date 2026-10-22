/* Conditional transient budgets. No spatial CFD or motor map is inferred here. */
(function(root){
'use strict';
const M=root.AA_Model||(typeof require==='function'?require('./model.js'):null),{C}=M;
const defaults={capture:.5,volume:.1,ambientExchange:.05,heatW:0,horizon:120,delivery:'direct',coldVolumeL:500,coldPressureBarG:.05,coldInitialC:1,coldUA:2,coldHoldS:0,burstGS:77.6,minimumHeadBar:.001};
function config(x={}){const c={...defaults,...x};for(const k of Object.keys(defaults))if(typeof defaults[k]==='number'&&!Number.isFinite(c[k]))throw Error('Enter a finite '+k+'.');
 if(c.capture<0||c.capture>1||c.volume<=0||c.volume>100||c.ambientExchange<0||c.heatW<0||c.horizon<1||c.horizon>600)throw Error('Check capture (0–1), volume (>0–100 m³), exchange, heat and horizon (1–600 s).');
 if(c.coldVolumeL<=0||c.coldVolumeL>100000||c.coldPressureBarG<0||c.coldPressureBarG>10||c.coldInitialC<=-100||c.coldInitialC>100||c.coldUA<0||c.coldHoldS<0||c.coldHoldS>86400||c.burstGS<=0||c.burstGS>2000||c.minimumHeadBar<0)throw Error('Cold-tank scenario is outside the declared range.');
 if(!['direct','cold'].includes(c.delivery))throw Error('Select direct supply or a precharged cold tank.');return c;}
function interp(points,t,key){if(!points.length)return null;if(t<=points[0].t)return points[0][key];let lo=0,hi=points.length-1;if(t>=points[hi].t)return points[hi][key];while(hi-lo>1){const mid=(hi+lo)>>1;if(points[mid].t<=t)lo=mid;else hi=mid;}const a=points[lo],b=points[hi],f=(t-a.t)/(b.t-a.t);return a[key]+f*(b[key]-a[key]);}
function direct(r){return t=>({m:r.ok&&r.valid&&t>=0&&t<r.receiver.served?r.m:0,T:r.sourceHistory?.length?interp(r.sourceHistory,t,'totalT'):r.Ttotal??r.c.ambient,p:r.ok?(r.receiver.points.length?interp(r.receiver.points,t,'p'):(r.Ps-C.pa)/1e5):0});}
// Ideal-gas isentropic orifice capacity, upstream stagnation state. Cd is explicit.
function orifice(P,T,A,cd=1,pout=C.pa){if(P<=pout||A<=0)return 0;const q=pout/P,g=C.gamma,critical=(2/(g+1))**(g/(g-1));
 const term=q<=critical?Math.sqrt(g)*(2/(g+1))**((g+1)/(2*(g-1))):Math.sqrt(2*g/(g-1)*(q**(2/g)-q**((g+1)/g)));
 return cd*A*P/Math.sqrt(C.R*T)*term;}
function coldBurst(r,input={},dt=.005){const c=config(input),Ta=r.c.ambient+C.T0,V=c.coldVolumeL/1000,T0=c.coldInitialC+C.T0,P0=C.pa+c.coldPressureBarG*1e5;
 const m0=P0*V/(C.R*T0),heldT=Ta+(T0-Ta)*Math.exp(-c.coldUA*c.coldHoldS/(m0*C.cv)),heldP=m0*C.R*heldT/V;
 let m=m0,T=heldT,t=0,massOut=0,energyOut=0,heatIn=0,deficitJ=0,stop=null,points=[];
 const U0=m0*C.cv*heldT,limit=C.pa+c.minimumHeadBar*1e5,requested=c.burstGS/1000;
 while(t<c.horizon-1e-9){let step=Math.min(dt,c.horizon-t,r.c.activation>t?r.c.activation-t:dt);const P=m*C.R*T/V;
  if(stop===null&&(P<=limit+1e-7||t>=r.c.activation))stop=t;
  const flow=stop===null?Math.min(requested,orifice(P,T,r.area,r.c.cd)):0;if(flow>0)step=Math.min(step,.05*m/flow);
  // Exact adiabatic removal, then exact fixed-mass heat relaxation.
  function state(h){const dm=Math.min(flow*h,m*.05),mn=m-dm,Tad=T*(mn/m)**(C.gamma-1),removed=m*C.cv*T-mn*C.cv*Tad;
   const nextT=Ta+(Tad-Ta)*Math.exp(-c.coldUA*h/(mn*C.cv));return {dm,mn,Tad,removed,nextT,p:mn*C.R*nextT/V};}
  let next=state(step);
  if(stop===null&&next.p<limit){let lo=0,hi=step;for(let i=0;i<36;i++){const mid=(lo+hi)/2;if(state(mid).p>limit)lo=mid;else hi=mid;}step=(lo+hi)/2;next=state(step);stop=t+step;}
  const {dm,mn,Tad,removed,nextT}=next,deliveryT=dm>0?removed/(dm*C.cp):T;
  points.push({t,m:dm/step,T:deliveryT-C.T0,p:(P-C.pa)/1e5});
  heatIn+=mn*C.cv*(nextT-Tad);energyOut+=removed;massOut+=dm;deficitJ+=dm*C.cp*(Ta-deliveryT);m=mn;T=nextT;t+=step;
 }
 points.push({t,m:0,T:T-C.T0,p:(m*C.R*T/V-C.pa)/1e5});
 return {points,initialMass:m0,initialT:heldT-C.T0,initialP:heldP,served:stop??c.horizon,censored:stop===null,massOut,deficitJ,remainingMass:m,energyResidual:m*C.cv*T-U0+energyOut-heatIn,massResidual:m-m0+massOut,
 chargeCompatible:r.ok&&P0<=r.Pex,chargePressureLimitBarG:r.ok?(r.Pex-C.pa)/1e5:null,
 scope:'Precharged isolated cold tank, ideal gas, explicit valve flow cap, direct orifice outlets. No downstream hose or regulator thermal inertia. Charging is not established by the stock motor model.'};}
function intervals(points,key,threshold){const segments=[];let start=points[0][key]>=threshold?points[0].t:null;
 for(let i=1;i<points.length;i++){const a=points[i-1],b=points[i],aboveA=a[key]>=threshold,aboveB=b[key]>=threshold;if(aboveA!==aboveB){const t=a.t+(b.t-a.t)*(threshold-a[key])/(b[key]-a[key]);if(aboveB)start=t;else {segments.push([start,t]);start=null;}}}
 if(start!==null)segments.push([start,points.at(-1).t]);return segments;}
function simulate(r,input={},dt=.05){const c=config(input);if(!r.ok)throw Error(r.error||'Source calculation failed.');
 const cold=c.delivery==='cold'?coldBurst(r,c):null;
 function coldProfile(t){const a=cold.points;let lo=0,hi=a.length-1;while(hi-lo>1){const mid=(hi+lo)>>1;if(a[mid].t<=t)lo=mid;else hi=mid;}return {...a[lo],next:a[hi].t};}
 const profile=cold?coldProfile:direct(r);if(cold)dt=Math.min(dt,.005);
 const mass=C.pa*c.volume/(C.R*(r.c.ambient+C.T0));let deficit=0,t=0,captured=0,delivered=0,inputColdJ=0,ambientLossJ=0,points=[];
 function record(){const s=profile(t);points.push({t,delta:deficit,T:r.c.ambient-deficit,m:s.m*1000,capturedGS:s.m*c.capture*1000,p:s.p,cooledMass:deficit>=r.c.delta?mass:0});}
 record();
 // Split at a direct-source cutoff and at the valve boundary; do not smear the pulse.
 while(t<c.horizon-1e-9){let step=Math.min(dt,c.horizon-t);if(cold){const next=profile(t+1e-10).next;if(next>t+1e-9)step=Math.min(step,next-t);}for(const stop of [cold?.served??r.receiver.served,r.c.activation])if(stop>t+1e-9&&stop<t+step)step=stop-t;
  const s=profile(t+step/2),mc=s.m*c.capture,k=(mc+c.ambientExchange)/mass,forcing=(mc*(r.c.ambient-s.T)-c.heatW/C.cp)/mass;
  const next=k>0?deficit*Math.exp(-k*step)+(forcing/k)*(1-Math.exp(-k*step)):deficit+forcing*step;
  // Integrate the exact step mean, to audit mass*cp*delta energy.
  const mean=k>0?(forcing/k)+(deficit-forcing/k)*(-Math.expm1(-k*step))/(k*step):(deficit+next)/2;
  inputColdJ+=mc*C.cp*(r.c.ambient-s.T)*step;ambientLossJ+=((mc+c.ambientExchange)*C.cp*mean+c.heatW)*step;
  deficit=next;delivered+=s.m*step;captured+=mc*step;t+=step;record();
 }
 const windows=intervals(points,'delta',r.c.delta),duration=windows.reduce((a,[s,e])=>a+e-s,0),max=points.reduce((v,p)=>Math.max(v,p.delta),0),last=points.at(-1),positive=points.filter(p=>p.m>0);
 return {c,points,windows,duration,firstReached:windows[0]?.[0]??null,maximumDrop:max,minimumT:r.c.ambient-max,targetMass:mass,targetVolume:c.volume,deliveredMass:delivered,capturedMass:captured,energyResidual:mass*C.cp*last.delta-inputColdJ+ambientLossJ,
 clipped:windows.length>0&&last.delta>=r.c.delta,sourceEnds:cold?.served??(r.valid?r.receiver.served:0),peakGS:positive.reduce((v,p)=>Math.max(v,p.m),0),cold,
 steadyDrop:r.valid&&c.capture*r.m+c.ambientExchange>0?(c.capture*r.m*(r.c.ambient-r.Ttotal)-c.heatW/C.cp)/(c.capture*r.m+c.ambientExchange):null,
 scope:'Well-mixed isobaric control-volume budget with fixed ambient-density inventory. Capture and ambient exchange are assumed. Not spatial CFD, a person model or a validated outdoor pocket.'};}
const api={defaults,config,interp,direct,orifice,coldBurst,intervals,simulate};root.AA_Dynamics=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
