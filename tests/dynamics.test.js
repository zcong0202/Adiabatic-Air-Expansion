const {test}=require('node:test'),assert=require('node:assert/strict');
const M=require('../panel/model'),D=require('../panel/dynamics');
const near=(a,b,e=1e-7)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}, tolerance ${e}`);

test('Reduced charge pressure changes support, not invented rated motor flow',()=>{
 const a=M.calculate({chargeBar:7}),b=M.calculate({chargeBar:6.6}),x=M.calculate({chargeBar:6.7}),bad=M.calculate({chargeBar:8});
 assert.ok(a.valid);assert.ok(!b.valid);near(a.m,b.m);assert.ok(!x.valid);assert.ok(!bad.ok);assert.match(b.warnings.join(' '),/not a compressor pressure\/flow map/);
});
test('Pressure head extends finite receiver support and respects catalogue pressure cap',()=>{
 const a=M.calculate({source:'xas68',tankL:500,chargeBar:6.9}),b=M.calculate({source:'xas68',tankL:500,chargeBar:7});
 assert.ok(a.valid&&b.valid);assert.ok(b.receiver.served>a.receiver.served);near(a.m,b.m);
});
test('Well-mixed transient matches independent exponential heating/cooling and energy balance',()=>{
 const r=M.calculate(),s=D.simulate(r,{capture:.5,volume:.1,ambientExchange:.05,heatW:20,horizon:60}),mass=M.C.pa*.1/(M.C.R*303.15),mc=.5*r.m,k=(mc+.05)/mass,eq=(mc*(30-r.Ttotal)-20/M.C.cp)/(mc+.05);
 const at=t=>s.points.reduce((a,b)=>Math.abs(b.t-t)<Math.abs(a.t-t)?b:a);
 near(at(10).delta,eq*(1-Math.exp(-k*10)),1e-8);near(s.energyResidual,0,1e-6);near(s.deliveredMass,r.deliveredMass,1e-8);near(s.capturedMass,.5*r.deliveredMass,1e-8);
 const d30=eq*(1-Math.exp(-k*30)),decay=at(35).delta,ka=.05/mass,eqa=-20/(M.C.cp*.05);
 near(decay,eqa+(d30-eqa)*Math.exp(-ka*5),1e-8);
});
test('Capture, ambient exchange and volume have separate physical effects',()=>{
 const r=M.calculate(),a=D.simulate(r),capture=D.simulate(r,{capture:.1}),wind=D.simulate(r,{ambientExchange:.3}),large=D.simulate(r,{volume:1});
 assert.ok(a.maximumDrop>capture.maximumDrop);assert.ok(a.maximumDrop>wind.maximumDrop);assert.ok(large.firstReached>a.firstReached);near(large.steadyDrop,a.steadyDrop);
});
test('Unsupported source produces no direct cooling or delivered mass',()=>{
 const r=M.calculate({source:'xas38'}),s=D.simulate(r);assert.ok(!r.valid);near(s.maximumDrop,0);near(s.deliveredMass,0);near(s.duration,0);assert.equal(s.firstReached,null);
});
test('Warm valve output cannot claim cooling; longer observation cannot invent a pulse',()=>{
 const r=M.calculate({method:'throttle'}),s=D.simulate(r,{horizon:120});near(s.maximumDrop,0);near(s.duration,0);assert.ok(s.points.some(p=>p.delta<0));near(s.deliveredMass,r.deliveredMass,1e-8);
});
test('Receiver cutoff and temperature history drive the target model',()=>{
 const r=M.calculate({source:'xas68',tankL:500}),s=D.simulate(r,{horizon:60}),p=D.direct(r);assert.ok(r.valid);assert.ok(p(r.receiver.served-.001).m>0);near(p(r.receiver.served).m,0);near(s.deliveredMass,r.deliveredMass,1e-8);assert.ok(p(5).T<r.Ttotal);near(s.sourceEnds,r.receiver.served);
});
test('No ambient mixing or heat produces no assumed universal reheating time',()=>{
 const r=M.calculate(),s=D.simulate(r,{ambientExchange:0,heatW:0});near(s.points.at(-1).delta,s.points.find(p=>p.t>=30).delta,1e-8);assert.ok(s.clipped);assert.ok(s.duration>80);
 const none=D.simulate(r,{capture:0,ambientExchange:0});near(none.maximumDrop,0);assert.equal(none.steadyDrop,null);
});
test('Compressible orifice recovers low-pressure Bernoulli limit and choked plateau',()=>{
 const P=M.C.pa+1,T=280,A=.001,expected=.8*A*Math.sqrt(2*(P/(M.C.R*T))*1);near(D.orifice(P,T,A,.8)/expected,1,1e-4);
 const a=D.orifice(5e5,T,A,1,1e5),b=D.orifice(5e5,T,A,1,2e5);near(a,b);near(D.orifice(M.C.pa,T,A),0);near(D.orifice(5e5,T,A*2),a*2);
});
test('Precharged cold tank obeys independent adiabatic blowdown and conserves mass/energy',()=>{
 const r=M.calculate(),c={coldVolumeL:500,coldPressureBarG:.05,coldUA:0,coldHoldS:0,minimumHeadBar:.001,horizon:1},a=D.coldBurst(r,c,.005),b=D.coldBurst(r,c,.0025),P0=M.C.pa+.05e5,Pend=M.C.pa+.001e5;
 const mend=a.initialMass*(Pend/P0)**(1/M.C.gamma),exact=(a.initialMass-mend)/.0776;
 near(a.served,exact,1e-9);near(b.served,exact,1e-9);near(a.massResidual,0,1e-10);near(a.energyResidual,0,1e-6);assert.ok(a.massOut<a.initialMass*.05);
 const last=a.points.find(p=>p.m===0),exactT=274.15*(a.remainingMass/a.initialMass)**(M.C.gamma-1)-273.15;near(last.T,exactT,1e-8);
});
test('Cold reservoir size and burst rate change duration; atmospheric tank cannot force flow',()=>{
 const r=M.calculate(),a=D.coldBurst(r,{horizon:2,coldUA:0}),large=D.coldBurst(r,{horizon:2,coldUA:0,coldVolumeL:1000}),fast=D.coldBurst(r,{horizon:2,coldUA:0,burstGS:155.2}),atm=D.coldBurst(r,{horizon:2,coldPressureBarG:0,coldHoldS:0});
 assert.ok(large.served>a.served*1.9);assert.ok(fast.served<a.served*.6);near(atm.massOut,0);assert.ok(!a.chargeCompatible);
});
test('Cold hold warms storage and changes pressure; not a free charging process',()=>{
 const r=M.calculate(),a=D.coldBurst(r,{horizon:1,coldHoldS:0}),b=D.coldBurst(r,{horizon:1,coldHoldS:120});assert.ok(b.initialT>a.initialT);assert.ok(b.initialP>a.initialP);near(b.initialMass,a.initialMass);
});
test('Cold burst cooling integrates the actual discharged mass, not total inventory',()=>{
 const r=M.calculate(),s=D.simulate(r,{delivery:'cold',horizon:2,coldUA:0});near(s.deliveredMass,s.cold.massOut,1e-8);near(s.capturedMass,s.deliveredMass*.5,1e-8);near(s.energyResidual,0,1e-6);assert.ok(s.duration<1);
});
test('Transient input validation rejects invalid states',()=>{
 for(const x of [{capture:1.1},{volume:0},{horizon:601},{burstGS:0},{coldPressureBarG:-1},{delivery:'magic'},{ambientExchange:NaN}])assert.throws(()=>D.config(x));
});

test('Adaptive cold-tank steps preserve fast tiny-tank bursts and long horizons',()=>{
 const r=M.calculate(),fast=D.simulate(r,{delivery:'cold',coldVolumeL:1,coldPressureBarG:5,burstGS:2000,horizon:1,coldUA:0}),long=D.simulate(r,{delivery:'cold',horizon:600});
 near(fast.deliveredMass,fast.cold.massOut,1e-8);near(fast.energyResidual,0,1e-6);assert.ok(fast.cold.points.some(p=>nearOrFalse(p.m,2)));assert.ok(long.points.length>100000);assert.ok(Number.isFinite(long.maximumDrop));
 function nearOrFalse(a,b){return Math.abs(a-b)<1e-7;}
});
