const assert=require('node:assert/strict'),{SerialLink,flashUno}=require('../src/serial.js');
let streamController,address=0,signals=[],memory=new Uint8Array(32768);memory.fill(255);
const telemetry=[],lost=[];
const port={async open(options){assert.equal(options.baudRate,115200);},async close(){},async setSignals(s){signals.push(s);},readable:new ReadableStream({start(c){streamController=c;}}),writable:new WritableStream({write(data){
 if(data[0]===72){ // HELLO line after upload; split JSON over chunks.
  streamController.enqueue(new TextEncoder().encode('{"kind":"info",'));
  streamController.enqueue(new TextEncoder().encode('"protocol":1}\n'));
  return;
 }
 assert.equal(data.at(-1),0x20);let result=new Uint8Array();
 switch(data[0]){case 0x30:case 0x50:case 0x51:break;case 0x75:result=Uint8Array.from([30,149,15]);break;case 0x55:address=2*(data[1]+256*data[2]);break;case 0x64:memory.set(data.slice(4,-1),address);break;case 0x74:result=memory.slice(address,address+128);break;default:throw Error('Unexpected command');}
 // Real transport receives split STK500 INSYNC / payload / OK packets.
 streamController.enqueue(Uint8Array.from([0x14]));if(result.length)streamController.enqueue(result);streamController.enqueue(Uint8Array.from([0x10]));
}})};
(async()=>{const link=new SerialLink(port,line=>telemetry.push(line),err=>lost.push(err));await link.open();const image=Uint8Array.from({length:257},(_,i)=>i&255);await flashUno(link,image);await new Promise(r=>setTimeout(r,20));assert.deepEqual(memory.slice(0,257),image);assert.equal(telemetry[0],'{"kind":"info","protocol":1}');assert(signals.some(s=>s.dataTerminalReady===false));await link.close();assert.equal(lost.length,0);console.log('PASS: actual SerialLink over mock Web Serial streams — split STK500 packets, flash readback, DTR reset calls, live JSON framing, clean close. Physical USB untested.');})().catch(e=>{console.error(e);process.exitCode=1;});
