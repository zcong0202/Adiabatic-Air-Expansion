const {test}=require('node:test');const assert=require('node:assert/strict');
const M=require('../panel/model.js'),air=require('../panel/data/air.json'),checks=require('../panel/data/eos-checks.json'),cfd=require('../panel/data/cfd.json');
function near(a,b,eps=1e-7){assert.ok(Math.abs(a-b)<=eps,`${a} != ${b} (tol ${eps})`);}

test('Reference source reproduces independently specified motor energy balance',()=>{
 const r=M.calculate();assert.ok(r.ok&&r.valid);near(r.m,.0776);near(r.requiredFad,3888);near(r.shaft,3360);
 near(r.Tex,40-3360/(.0776*1006));near(r.Ttotal,.959275276178,1e-7);
 near(r.cooling,2267.0816,1e-6);near(r.energyResidual,0,1e-7);near(r.receiver.served,30);
});
test('Ideal-gas throttle removes no work and preserves total temperature',()=>{
 const r=M.calculate({method:'throttle',coldReferenceUA:0,coldL:0});assert.ok(r.ok);near(r.shaft,0);near(r.Tex,40);near(r.Ttotal,40);
 assert.ok(r.cooling<0);near(r.energyResidual,0,1e-7);
});
test('Reversible expansion bounds shaft extraction and real turbine lies between throttle and bound',()=>{
 const z=M.calculate({method:'throttle',coldReferenceUA:0}),a=M.calculate({method:'turbine',turbineEta:.5,coldReferenceUA:0}),b=M.calculate({method:'isentropic',coldReferenceUA:0});
 assert.ok(z.Tex>a.Tex&&a.Tex>b.Tex);near(a.shaft/a.idealWork,.5);near(b.eta,1);
 const analytic=(a.Tin+273.15)*(a.Pex/a.expPin)**(M.C.R/M.C.cp)-273.15;
 near(a.Tex,(a.Tin+analytic)/2,1e-8);
});
test('Mixing inequality, dilution limit and colder-source leverage',()=>{
 for(const m of [.001,.02,.0776])for(const deficit of [4,10,30,70])for(const d of [3,6,12]){
  const r=M.mixing(m,30-deficit,30,d);if(deficit>=d){near(m*deficit/(m+r.addedMax),d);assert.ok(r.mixedMax>=m);}else assert.equal(r.canReach,false);
 }
 assert.ok(M.mixing(.0776,-50,30,6).addedMax>M.mixing(.0776,1,30,6).addedMax);
});
test('Nozzle equal area preserves budget; geometry alone does not invent added flow',()=>{
 const a=M.calculate({nozzle:'wide'}),b=M.calculate({nozzle:'base'});near(a.area,b.area);near(a.cooling,b.cooling);near(a.v,b.v);near(a.m,b.m);
 const r=M.calculate({nozzle:'round70'});near(r.m,a.m);assert.ok(r.v>a.v);assert.ok(r.Pnozzle>a.Pnozzle);
});
test('Darcy losses increase with length and drop with larger bore',()=>{
 const e=M.properties();let loss=(L,D)=>M.pipeLoss(.0776,313.15,7e5,L,D,0,1e-5,e).dp;
 near(loss(0,.038),0);assert.ok(loss(20,.038)>loss(10,.038));assert.ok(loss(10,.05)<loss(10,.038));near(M.friction(1000,0),.064);
});
test('Pipe heat leak respects zero UA, ambient relaxation and insulation',()=>{
 const e=M.properties();near(M.heatPipe(270,2e5,2e5,.08,0,303,e).T,270);
 const a=M.heatPipe(270,2e5,2e5,.08,3,303,e),b=M.heatPipe(270,2e5,2e5,.08,10,303,e);assert.ok(a.T>270&&b.T>a.T&&b.T<303);
 near(a.q,.08*1006*(a.T-270));assert.ok(M.thermalUA(1,.05,M.config({insulation:20}))<M.thermalUA(1,.05,M.config({insulation:0})));
});
test('Cold hose length changes enthalpy and cannot ignore backpressure',()=>{
 const a=M.calculate({coldL:.5}),b=M.calculate({coldL:5});assert.ok(b.Tnozzle>a.Tnozzle);assert.ok(b.cooling<a.cooling);assert.ok(b.Pex>a.Pex);
 const c=M.calculate({coldD:1});assert.ok(!c.valid);assert.ok(c.blocks.some(x=>/Mach|backpressure/.test(x)));
});
test('Receiver fixed-T inventory matches analytic deficit duration',()=>{
 const c=M.config({source:'xas68',tankL:500,tankMode:'isothermal',purge:0,tankUA:0,activation:30});
 const source=M.sources.find(s=>s.id===c.source),minP=7.5e5,mout=.0776,availableFad=3.6;
 const b=M.receiver(c,{mout,minP,source,availableFad});const massStored=(b.initialP-minP)*(c.tankL/1000)/(M.C.R*(c.sourceTemp+273.15));
 near(b.served,massStored/(mout-availableFad/60*c.fadDensity),1e-6);near(b.massResidual,0,1e-10);near(b.energyResidual,0,1e-6);
});
test('Receiver energy ODE conserves mass and energy; adiabatic blowdown cools faster',()=>{
 const c=M.config({source:'xas38',tankL:500,tankUA:0}),r=M.calculate(c),iso=M.calculate({...c,tankMode:'isothermal'});
 assert.ok(r.receiver.served<iso.receiver.served);assert.ok(r.receiver.points.at(-1).T<40);near(r.receiver.massResidual,0,1e-9);near(r.receiver.energyResidual,0,1e-6);
});
test('Receiver cutoff preserves motor pressure and longer pipe raises floor',()=>{
 const r=M.calculate({source:'xas68',tankL:500}),long=M.calculate({source:'xas68',tankL:500,mainL:50});
 assert.ok(r.minP>M.C.pa+6.4e5);assert.ok(long.minP>r.minP);assert.ok(long.receiver.served<r.receiver.served);
 assert.ok(r.receiver.points.at(-1).p>=6.3);assert.equal(r.steady,false);
});
test('Storage changes burst duration, not continuous flow capacity',()=>{
 const small=M.calculate({source:'xas68',tankL:100}),large=M.calculate({source:'xas68',tankL:2000});
 assert.ok(large.receiver.served>small.receiver.served);assert.ok(large.receiver.full);assert.equal(large.steady,false);near(large.cooling,small.cooling);
 const n=M.sizeReceiver(large.c,large);assert.ok(n>100&&n<2000);assert.ok(M.calculate({...large.c,tankL:n+1}).receiver.full);
 assert.equal(M.calculate({source:'xas68',tankL:0}).valid,false);
});
test('Supply response needs a receiver even with excess steady flow',()=>{
 const r=M.calculate({ramp:3});assert.equal(r.valid,false);const b=M.calculate({ramp:3,tankL:1000});assert.ok(b.valid&&b.receiver.full);assert.ok(M.sizeReceiver(b.c,b)>0);
});
test('Whole-plant ratio uses full entered power, not a flow fraction',()=>{
 const a=M.calculate({source:'xas78',plantKW:30}),b=M.calculate({source:'xas88',plantKW:30});near(a.cop,a.cooling/30000);near(a.cop,b.cop);assert.equal(M.calculate().cop,null);
});
test('Cold tank is a finite initial mass and loses sensible budget while held',()=>{
 const c=M.config({coldTankL:500,coldTankUA:2,coldHold:30}),r=M.coldStore(c);near(r.mass,M.C.pa*.5/(M.C.R*274.15));assert.ok(r.T>1&&r.T<30);assert.ok(r.remainingSensibleJ<r.initialSensibleJ);assert.ok(r.pressureBarG>0);
});
test('Invalid or unsupported states do not produce an approved result',()=>{
 for(const inputs of [{motors:0},{mainL:-1},{delta:NaN},{purge:1},{activation:31},{eos:'bad'},{source:'made-up'}])assert.equal(M.calculate(inputs).ok,false);
 assert.equal(M.calculate({source:'bauer',tankL:1000}).valid,false);
});
test('Real-air grid matches independent CoolProp states and inverse temperatures',()=>{
 const e=M.properties('real',air);for(const c of checks){const p=c.p_bar*1e5,po=c.pout_bar*1e5;
  assert.ok(Math.abs(e.h(c.T_k,p)-c.h)<20);assert.ok(Math.abs(e.s(c.T_k,p)-c.s)<.8);assert.ok(Math.abs(e.rho(c.T_k,p)/c.rho-1)<.001);
  near(e.TfromH(e.h(c.T_k,p),po),c.throttle_T,.04);
  if(c.isentropic_T!==null)near(e.TfromS(e.s(c.T_k,p),po),c.isentropic_T,.12);
 }
 assert.throws(()=>e.h(150,7e5),/range/);assert.throws(()=>e.h(300,400e5),/range/);
});
test('Real-air stage energy closes for motor, regulator and turbine',()=>{
 for(const method of ['motor','throttle','turbine','isentropic']){const r=M.calculate({method,eos:'real'},air);assert.ok(r.ok,r.error);near(r.energyResidual,0,1e-6);}
 const r=M.calculate({method:'throttle',eos:'real'},air);assert.ok(r.Tex<40&&r.Tex>35);
});
test('CFD dataset has complete cases, monotone thresholds and conserved subregion measures',()=>{
 assert.equal(cfd.cases.length,16);for(const c of cfd.cases){assert.ok(c.numerical_screens_pass);assert.equal(c.times.length,c.snapshots.length);
 for(const s of c.snapshots){assert.match(s.T_sha256,/^[a-f0-9]{64}$/);for(const key of ['domain','corridor']){
  const r=s.regions[key];assert.equal(r.values.length,60);for(let j=0;j<60;j++){const [v,m,ms,e]=r.values[j];assert.ok(v>=0&&m>=0&&e>=0);assert.ok(ms>=-1e-6&&ms<=m+1e-5);assert.ok(v<=r.fluid_volume_m3+1e-7);if(j)assert.ok(v<=r.values[j-1][0]+1e-8);if(key==='corridor')assert.ok(v<=s.regions.domain.values[j][0]+1e-8);}
 }} }
});
test('CFD independent high-resolution geometry comparison is retained, not scaled to inputs',()=>{
 const a=cfd.cases.find(c=>c.id==='F00_base_d35'),b=cfd.cases.find(c=>c.id==='F01_wide_d35');
 near(a.source_kg_s,b.source_kg_s);near(a.source_c,b.source_c);assert.equal(a.times.at(-1),10);
 const v=b.snapshots.at(-1).regions.domain.values[11];near(v[0],.49777557,1e-8);near(v[1],.59968438,1e-8);
});
test('Compressible ideal mean-density Darcy solve matches independent squared-pressure result',()=>{
 const m=.0776,T=313.15,pout=7e5,L=10,D=.038,K=2,A=Math.PI*D**2/4;
 const Re=m*D/(A*(1.716e-5*(T/273.15)**1.5*(273.15+110.4)/(T+110.4)));
 const f=.25/Math.log10((1e-5/D)/3.7+5.74/Re**.9)**2;
 const expected=Math.sqrt(pout**2+(f*L/D+K)*m*m*M.C.R*T/(A*A));
 near(M.pressureRequired(m,T,pout,L,D,K,1e-5,M.properties()).pin,expected,1e-5);
});
test('Adiabatic zero-inflow tank matches blowdown law; time-step refinement converges',()=>{
 const c=M.config({tankL:500,tankUA:0,activation:30}),source=M.sources.find(s=>s.id==='xas38');
 const args={mout:.0776,minP:7.5e5,source,availableFad:0},a=M.receiver(c,args),b=M.receiver(c,args,.0125);
 const initial=M.C.pa+(source.bar-c.treatmentDrop)*1e5,m0=initial*.5/(M.C.R*(c.sourceTemp+273.15));
 const mend=m0*(args.minP/initial)**(1/M.C.gamma),exact=(m0-mend)/args.mout;
 assert.ok(Math.abs(b.served-exact)<Math.abs(a.served-exact));near(a.served,exact,.002);
 const expectedT=(c.sourceTemp+273.15)*(args.minP/initial)**((M.C.gamma-1)/M.C.gamma)-273.15;
 near(a.points.at(-1).T,expectedT,.002);
});
test('Receiver pressure controller never overcharges the selected pressure',()=>{
 for(const tankMode of ['isothermal','energy']){const r=M.calculate({tankL:100,tankMode,source:'xas88'});assert.ok(r.receiver.points.every(p=>p.p<=(r.Ps-M.C.pa)/1e5+1e-8));}
});
test('Warm source cannot claim any cumulative mixed mass at the colder target',()=>{
 const r=M.calculate({method:'throttle'});assert.ok(r.Tnozzle>30);near(r.idealMixedMass,0);
 const b=M.calculate({method:'motor',motorLoad:.25});assert.ok(!b.mix.canReach);near(b.idealMixedMass,0);
});
