'use strict';
const wait=ms=>new Promise(r=>setTimeout(r,ms));
class SerialLink{
 constructor(port,onLine,onLost){this.port=port;this.onLine=onLine;this.onLost=onLost;this.phase='live';this.bytes=[];this.text='';this.closed=false;this.reader=null;this.writer=null;}
 async open(){await this.port.open({baudRate:115200,bufferSize:16384});this.writer=this.port.writable.getWriter();this.reader=this.port.readable.getReader();this.readPromise=this.readLoop();await this.port.setSignals({dataTerminalReady:true});}
 async readLoop(){let failure=null;try{while(!this.closed){const {value,done}=await this.reader.read();if(done)break;if(this.phase==='flash'){this.bytes.push(...value);if(this.bytes.length>65536)throw Error('Bootloader receive buffer overflow.');}else{this.text+=new TextDecoder().decode(value);if(this.text.length>65536)this.text='';let at;while((at=this.text.indexOf('\n'))>=0){const line=this.text.slice(0,at).trim();this.text=this.text.slice(at+1);if(line)this.onLine(line);}}}}catch(e){failure=e;}finally{if(!this.closed)this.onLost(failure||Error('USB serial disconnected.'));}}
 async send(text){await this.writer.write(new TextEncoder().encode(text+'\n'));}
 async raw(data){await this.writer.write(Uint8Array.from(data));}
 async readBytes(count,timeout=1000){const end=Date.now()+timeout;while(this.bytes.length<count){if(this.closed)throw Error('USB disconnected.');if(Date.now()>end)throw Error('Uno bootloader did not respond.');await wait(2);}return Uint8Array.from(this.bytes.splice(0,count));}
 async exchange(data,n=0,timeout=1000){await this.raw(data);const end=Date.now()+timeout;let first=0;while(first!==0x14){first=(await this.readBytes(1,Math.max(1,end-Date.now())))[0];if(Date.now()>end)throw Error('Bootloader sync failed.');}const result=await this.readBytes(n+1,Math.max(1,end-Date.now()));if(result[n]!==0x10)throw Error('Bootloader rejected the command.');return result.slice(0,n);}
 async reset(){this.bytes=[];this.text='';await this.port.setSignals({dataTerminalReady:false,requestToSend:false});await wait(70);await this.port.setSignals({dataTerminalReady:true,requestToSend:true});}
 async close(){this.closed=true;try{await this.reader?.cancel();}catch{}try{await this.readPromise;}catch{}this.reader?.releaseLock();this.writer?.releaseLock();await this.port.close();}
}
async function flashUno(link,image,onProgress=()=>{}){
 if(image.length>32256)throw Error('Firmware exceeds Uno sketch area.');
 link.phase='flash';let completed=false;
 try{
  await link.reset();let synced=false;
  for(let i=0;i<15;i++){try{await link.exchange([0x30,0x20],0,120);synced=true;break;}catch{link.bytes=[];await wait(30);}}
  if(!synced)throw Error('Cannot reach Uno bootloader. Close Arduino IDE/Serial Monitor; use a data cable. Download firmware and use Arduino IDE if needed.');
  const sig=await link.exchange([0x75,0x20],3);if(sig.join(',')!=='30,149,15')throw Error('Wrong board. Only Arduino/Elegoo Uno R3 with ATmega328P is supported.');
  await link.exchange([0x50,0x20]);const pages=Math.ceil(image.length/128);
  for(let page=0;page<pages;page++){
   const at=page*128,word=at/2,bytes=new Uint8Array(128);bytes.fill(255);bytes.set(image.slice(at,at+128));
   await link.exchange([0x55,word&255,word>>8,0x20]);
   await link.exchange([0x64,0,128,0x46,...bytes,0x20]);
   await link.exchange([0x55,word&255,word>>8,0x20]);
   const read=await link.exchange([0x74,0,128,0x46,0x20],128);
   if(!bytes.every((v,i)=>v===read[i]))throw Error('Flash verification failed at address '+at+'. Reinstall before connecting valve power.');
   onProgress(Math.round((page+1)/pages*100));
  }
  await link.exchange([0x51,0x20]);completed=true;
 }finally{link.phase='live';link.bytes=[];link.text='';if(!completed)try{await link.reset();}catch{}}
 await wait(1200);await link.send('HELLO');
}
if(typeof module!=='undefined')module.exports={flashUno,SerialLink};
