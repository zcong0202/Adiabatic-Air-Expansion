// Native macOS USB and file operations. No browser or external runtime required.
(()=>{
 let sequence=0;const requests=new Map();let reader=null,waiter=null,queue=[],ended=false;
 const bytes=base64=>Uint8Array.from(atob(base64),c=>c.charCodeAt(0));
 function call(action,args={}){const id=++sequence;return new Promise((resolve,reject)=>{requests.set(id,{resolve,reject});window.webkit.messageHandlers.aa.postMessage({id,action,...args});});}
 window.__aaReply=(id,value,error)=>{const pending=requests.get(id);if(!pending)return;requests.delete(id);error?pending.reject(Error(error)):pending.resolve(value);};
 window.__aaBytes=base64=>{const value=bytes(base64);if(waiter){const p=waiter;waiter=null;p.resolve({value,done:false});}else{queue.push(value);if(queue.reduce((n,v)=>n+v.length,0)>65536)__aaLost('USB input overflow. Please reconnect.');}};
 window.__aaLost=message=>{ended=true;queue=[];if(waiter){const p=waiter;waiter=null;p.reject(Error(message));}};
 const port={
  async open(){queue=[];ended=false;await call('open');},
  async close(){ended=true;await call('close');},
  setSignals(signals){return call('signals',{signals});},
  readable:{getReader(){reader={read(){if(queue.length)return Promise.resolve({value:queue.shift(),done:false});if(ended)return Promise.resolve({done:true});return new Promise((resolve,reject)=>{waiter={resolve,reject};});},async cancel(){ended=true;queue=[];if(waiter){waiter.resolve({done:true});waiter=null;}},releaseLock(){}};return reader;}},
  writable:{getWriter(){return {write(data){return call('write',{base64:btoa(Array.from(data,c=>String.fromCharCode(c)).join(''))});},releaseLock(){}};}}
 };
 Object.defineProperty(navigator,'serial',{configurable:true,value:{async requestPort(){await call('choose');return port;}}});
 window.NativeAA={call,async save(name,data){return call('save',{name,base64:btoa(Array.from(data,c=>String.fromCharCode(c)).join(''))});}};
})();
