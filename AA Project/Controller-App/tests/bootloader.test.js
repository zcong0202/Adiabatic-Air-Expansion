const assert=require('node:assert/strict'),{flashUno}=require('../src/serial.js');
class Bootloader{
 constructor({wrong=false,corrupt=false}={}){this.wrong=wrong;this.corrupt=corrupt;this.memory=new Uint8Array(32768);this.memory.fill(255);this.address=0;this.bytes=[];this.text='';this.resetCount=0;this.commands=[];}
 async reset(){this.resetCount++;}async send(line){this.sent=line;}
 async exchange(cmd,n){this.commands.push(cmd[0]);assert.equal(cmd.at(-1),0x20);
  switch(cmd[0]){case 0x30:case 0x50:case 0x51:return new Uint8Array();case 0x75:return Uint8Array.from(this.wrong?[0,0,0]:[0x1e,0x95,0x0f]);case 0x55:this.address=2*(cmd[1]+256*cmd[2]);return new Uint8Array();case 0x64:assert.equal(cmd[3],0x46);assert.equal(cmd[2],128);this.memory.set(cmd.slice(4,-1),this.address);return new Uint8Array();case 0x74:{assert.equal(n,128);const v=this.memory.slice(this.address,this.address+128);if(this.corrupt)v[0]^=1;return v;}default:throw Error('Unknown STK500 command');}
 }
}
(async()=>{
 const image=Uint8Array.from({length:513},(_,i)=>i%256),b=new Bootloader(),progress=[];
 await flashUno(b,image,p=>progress.push(p));assert.deepEqual(b.memory.slice(0,513),image);assert(b.memory.slice(513,640).every(x=>x===255));assert.equal(b.sent,'HELLO');assert.equal(b.phase,'live');assert.equal(progress.at(-1),100);assert.equal(b.commands.filter(x=>x===0x74).length,5);
 const wrong=new Bootloader({wrong:true});await assert.rejects(flashUno(wrong,image),/Wrong board/);assert(!wrong.commands.includes(0x64));assert.equal(wrong.resetCount,2);
 const bad=new Bootloader({corrupt:true});await assert.rejects(flashUno(bad,image),/verification failed/);assert.equal(bad.phase,'live');assert.equal(bad.resetCount,2);
 await assert.rejects(flashUno(b,new Uint8Array(32257)),/exceeds/);
 console.log('PASS: STK500 simulator — page program/readback, partial page padding, wrong board rejection, corrupt flash rejection, bounds, reset cleanup. Not a physical USB test.');
})().catch(e=>{console.error(e);process.exitCode=1;});
