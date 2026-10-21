'use strict';
const Core=(()=>{
 const encoder=new TextEncoder();
 const MAGIC=[65,65,72,79,76,68,49,0],KEY=0xAAB0531C;
 function settings(seconds,low){const hold=Math.round(Number(seconds)*1000);if(!Number.isFinite(Number(seconds))||hold<100||hold>3600000)throw Error('Choose 0.1 to 3600 seconds.');return {hold,low:low?1:0};}
 function parseHex(text){let base=0,end=0,eof=false;const records=[];
  for(const raw of text.trim().split(/\r?\n/)){const line=raw.trim();if(!line)continue;if(eof)throw Error('Data after HEX end marker.');if(!/^:[0-9a-f]+$/i.test(line)||line.length%2!==1)throw Error('Invalid Intel HEX record.');const b=Uint8Array.from(line.slice(1).match(/../g),x=>parseInt(x,16));if(b.length!==b[0]+5||b.reduce((a,x)=>a+x,0)%256)throw Error('HEX checksum failed.');const addr=(b[1]<<8)|b[2],type=b[3],data=b.slice(4,-1);
   if(type===0){const position=base+addr;if(position+data.length>32256)throw Error('Firmware exceeds Uno application flash.');records.push([position,data]);end=Math.max(end,position+data.length);}else if(type===1){if(b[0]!==0)throw Error('Invalid EOF.');eof=true;}else if(type===4){if(data.length!==2)throw Error('Invalid base.');base=((data[0]<<8)|data[1])*65536;}else if(type===2){if(data.length!==2)throw Error('Invalid segment.');base=((data[0]<<8)|data[1])*16;}else if(type!==3&&type!==5)throw Error('Unsupported HEX record.');
  }if(!eof||!end)throw Error('Incomplete firmware HEX.');const bytes=new Uint8Array(end);bytes.fill(255);for(const [pos,data]of records)bytes.set(data,pos);return bytes;
 }
 function record(address,type,data){const b=[data.length,address>>8,address&255,type,...data];b.push((-b.reduce((a,x)=>a+x,0))&255);return ':'+b.map(x=>x.toString(16).padStart(2,'0')).join('').toUpperCase();}
 function hex(bytes){const lines=[];for(let at=0;at<bytes.length;at+=16)lines.push(record(at,0,[...bytes.slice(at,at+16)]));lines.push(':00000001FF');return lines.join('\n')+'\n';}
 function profile(bytes){const hits=[];for(let i=0;i<=bytes.length-24;i++)if(MAGIC.every((v,j)=>bytes[i+j]===v))hits.push(i);if(hits.length!==1)throw Error('Firmware settings marker is missing or ambiguous.');return hits[0];}
 function patch(template,hold,low,token){if(!Number.isInteger(hold)||hold<100||hold>3600000||![0,1].includes(low))throw Error('Invalid firmware settings.');const bytes=parseHex(template),at=profile(bytes),view=new DataView(bytes.buffer);token=token>>>0;view.setUint32(at+8,hold,true);view.setUint32(at+12,token,true);bytes[at+16]=low;bytes.fill(0,at+17,at+20);view.setUint32(at+20,(hold^token^low^KEY)>>>0,true);return {bytes,hex:hex(bytes),token,hold,low};}
 const crcTable=Array.from({length:256},(_,n)=>{let c=n;for(let i=0;i<8;i++)c=c&1?0xEDB88320^(c>>>1):c>>>1;return c>>>0;});
 function crc(data){let c=0xffffffff;for(const v of data)c=crcTable[(c^v)&255]^(c>>>8);return (c^0xffffffff)>>>0;}
 function concat(parts){const result=new Uint8Array(parts.reduce((s,p)=>s+p.length,0));let at=0;for(const p of parts){result.set(p,at);at+=p.length;}return result;}
 function zip(files){const locals=[],centrals=[];let offset=0;for(const [name,value]of Object.entries(files)){const n=encoder.encode(name),data=typeof value==='string'?encoder.encode(value):value,checksum=crc(data);const h=new Uint8Array(30),v=new DataView(h.buffer);v.setUint32(0,0x04034b50,true);v.setUint16(4,20,true);v.setUint16(6,0x800,true);v.setUint16(12,33,true);v.setUint32(14,checksum,true);v.setUint32(18,data.length,true);v.setUint32(22,data.length,true);v.setUint16(26,n.length,true);locals.push(h,n,data);
 const c=new Uint8Array(46),cv=new DataView(c.buffer);cv.setUint32(0,0x02014b50,true);cv.setUint16(4,20,true);cv.setUint16(6,20,true);cv.setUint16(8,0x800,true);cv.setUint16(14,33,true);cv.setUint32(16,checksum,true);cv.setUint32(20,data.length,true);cv.setUint32(24,data.length,true);cv.setUint16(28,n.length,true);cv.setUint32(42,offset,true);centrals.push(c,n);offset+=h.length+n.length+data.length;}
 const central=concat(centrals),end=new Uint8Array(22),ev=new DataView(end.buffer),count=Object.keys(files).length;ev.setUint32(0,0x06054b50,true);ev.setUint16(8,count,true);ev.setUint16(10,count,true);ev.setUint32(12,central.length,true);ev.setUint32(16,offset,true);return concat([...locals,central,end]);}
 class TimerPreview{constructor(hold=10000){this.hold=hold;this.last=null;}detect(now){this.last=now;}remaining(now){return this.last===null?0:Math.max(0,this.hold-(now-this.last));}}
 function telemetry(line){try{const obj=JSON.parse(line);if(!obj||!['info','sample','applied','error','reset'].includes(obj.kind))return null;if(obj.kind==='sample'){
   if(obj.protocol!==1||!['command','feedback','pin_high','detected','active_low','sensor_ok','match','fault'].every(k=>[0,1].includes(obj[k])))return null;
   if(!['ms','seq','hold_ms','remaining_ms','voltage_mv','range_mm','range_status'].every(k=>Number.isInteger(obj[k])&&obj[k]>=0))return null;
   if(obj.hold_ms<100||obj.hold_ms>3600000||obj.remaining_ms>obj.hold_ms||obj.voltage_mv>5500)return null;
  }else if(['info','applied','reset'].includes(obj.kind)){
   if(obj.protocol!==1||!Number.isInteger(obj.hold_ms)||obj.hold_ms<100||obj.hold_ms>3600000||![0,1].includes(obj.active_low))return null;
  }else if(typeof obj.message!=='string')return null;return obj;}catch{}
  const row=line.split(',');if(row.length===17&&/^\d+$/.test(row[0])){const n=row.map(Number);if(!n.every((v,i)=>i===1||i===10||Number.isFinite(v))||![11,12,15,16].every(k=>[0,1].includes(n[k])))return null;return {kind:'legacy',ms:n[0],command:n[11],pin_high:n[11],feedback:n[12],voltage_mv:n[14]*1000,fault:n[16],match:n[15],detected:n[6]&&n[4]<=1500?1:0};}return null;
 }
 return {settings,parseHex,hex,patch,profile,zip,crc,TimerPreview,telemetry};
})();
if(typeof module!=='undefined')module.exports=Core;
