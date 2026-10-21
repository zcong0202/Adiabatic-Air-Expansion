const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..'),Core=require('../src/core.js');
const original=fs.readFileSync(path.join(root,'evidence/template.hex'),'utf8');
const bytes=Core.parseHex(original),at=Core.profile(bytes);
assert.equal(new DataView(bytes.buffer).getUint32(at+8,true),10000);
for(const [hold,low,token] of [[100,0,0],[12300,1,0xfedcba98],[3600000,1,0xffffffff]]){
 const f=Core.patch(original,hold,low,token),v=new DataView(f.bytes.buffer);
 assert.equal(v.getUint32(at+8,true),hold);assert.equal(v.getUint32(at+12,true),token);assert.equal(f.bytes[at+16],low);
 assert.equal(v.getUint32(at+20,true),(hold^token^low^0xAAB0531C)>>>0);
 assert.deepEqual(Core.parseHex(f.hex),f.bytes);
 for(let i=0;i<bytes.length;i++)if(i<at+8||i>=at+24)assert.equal(f.bytes[i],bytes[i]);
}
assert.throws(()=>Core.parseHex(original.replace(/.$/m,'0')));
assert.throws(()=>Core.parseHex(original.split(':00000001FF')[0]));
for(const x of ['',0,0.099,-1,3600.1,'abc','Infinity'])assert.throws(()=>Core.settings(x,false));
assert.deepEqual(Core.settings(12.3,true),{hold:12300,low:1});
assert.throws(()=>Core.patch(original,99,0,1));assert.throws(()=>Core.patch(original,1000,2,1));
let timer=new Core.TimerPreview(10000);assert.equal(timer.remaining(0),0);timer.detect(0);assert.equal(timer.remaining(8000),2000);timer.detect(8000);assert.equal(timer.remaining(10000),8000);assert.equal(timer.remaining(18000),0);
for(let now=0;now<180000;now+=100){timer.detect(now);assert.equal(timer.remaining(now),10000);}
const sample={kind:'sample',protocol:1,seq:1,ms:1000,command:1,pin_high:0,feedback:0,detected:1,active_low:1,sensor_ok:1,match:1,fault:0,hold_ms:10000,remaining_ms:10000,voltage_mv:0,range_mm:400,range_status:0};
assert.equal(Core.telemetry(JSON.stringify(sample)).command,1);
for(const patch of [{command:2},{voltage_mv:null},{remaining_ms:11000},{hold_ms:0},{protocol:2}])assert.equal(Core.telemetry(JSON.stringify({...sample,...patch})),null);
assert.equal(Core.telemetry('garbage'),null);assert.equal(Core.telemetry(JSON.stringify({kind:'applied',protocol:1,hold_ms:10000,active_low:1})).active_low,1);
assert.equal(Core.telemetry('1000,TOF,0,400,400,0,1,0,0,0,ON,1,1,1023,5.0,1,0').kind,'legacy');
assert.equal(Core.crc(new TextEncoder().encode('123456789')),0xcbf43926);
fs.writeFileSync(path.join(root,'evidence/zip-test.zip'),Core.zip({'read me.txt':'AA résumé\n','nested/firmware.hex':original}));
console.log('PASS: HEX checksum, profile patch, untouched flash, setting bounds, refill timer, continuous hold, telemetry rejection, legacy decoding, CRC32.');
