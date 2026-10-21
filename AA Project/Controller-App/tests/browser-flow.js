return (async()=>{
 const assert=(ok,message)=>{if(!ok)throw Error(message);};
 const report=[];
 assert(isSecureContext&&!!navigator.serial,'File URL must support Web Serial');
 assert($('signal').textContent==='—','Offline live panel must be blank');
 assert($('apply').disabled,'Offline Apply must be disabled');
 $('seconds').value='1';configChanged();
 document.querySelector('[data-tab="preview"]').click();
 $('previewPulse').click();assert(previewTimer.remaining(performance.now())>900,'Preview first pulse');
 await wait(700);$('previewPulse').click();await wait(500);
 assert(previewTimer.remaining(performance.now())>400,'Second pulse must refill');
 assert($('signal').textContent==='—','Simulation must not populate live panel');
 await wait(600);assert(previewTimer.remaining(performance.now())===0,'Preview expires');
 report.push('offline serial capability; preview retrigger and expiry; live remains blank');
 $('seconds').value='12.3';$('polarity').value='1';configChanged();
 const oldDownload=downloaded;let exported;downloaded=(name,data)=>{exported={name,data};};$('download').click();downloaded=oldDownload;
 assert(exported.name.includes('12.3s LOW'),'Export selected setting');
 window.__exportZip='data:application/zip;base64,'+btoa(Array.from(exported.data,x=>String.fromCharCode(x)).join(''));
 report.push('one-click firmware ZIP exported with 12.3 s / LOW trigger');
 // TEST ONLY: inject USB streams that send firmware messages. Never saved in production app.
 let usbController,hold=12300,low=1,seq=0,shouldAck=true,writes=[];
 const emit=obj=>usbController.enqueue(new TextEncoder().encode(JSON.stringify(obj)+'\n'));
 const info=kind=>({kind,protocol:1,hold_ms:hold,active_low:low});
 const port={async open(){},async close(){},async setSignals(){},readable:new ReadableStream({start(c){usbController=c;}}),writable:new WritableStream({write(data){const line=new TextDecoder().decode(data).trim();writes.push(line);if(line==='HELLO')emit(info('info'));if(line.startsWith('SET ')&&shouldAck){[,hold,low]=line.split(' ').map(Number);emit(info('applied'));}}})};
 Object.defineProperty(navigator,'serial',{configurable:true,value:{requestPort:async()=>port}});
 await connect();await wait(50);assert(compatible&&!$('apply').disabled,'HELLO acknowledges compatibility');
 emit({kind:'sample',protocol:1,seq:++seq,ms:2000,command:1,pin_high:0,feedback:0,detected:1,active_low:1,sensor_ok:1,match:1,fault:0,hold_ms:hold,remaining_ms:hold,voltage_mv:0,range_mm:350,range_status:0});
 await wait(50);assert($('signal').textContent==='HIGH'&&$('feedback').textContent==='LOW','Logical HIGH distinct from LOW-trigger physical feedback');
 $('seconds').value='2.5';configChanged();await $('apply').onclick();assert(writes.includes('SET 2500 1'),'SET wire command');assert(board.hold_ms===2500&&$('message').textContent.includes('Saved'),'Save only after ACK');
 report.push('mock USB connect/HELLO, actual-message rendering, LOW-trigger meaning, acknowledged SET');
 shouldAck=false;$('seconds').value='3';configChanged();await $('apply').onclick();assert($('message').textContent.includes('not confirmed'),'Missing ACK never claims save');assert(board.hold_ms===2500&&!pending,'Timeout clears pending and preserves last acknowledged setting');
 report.push('missing-ACK timeout preserves board setting and allows retry');
 await wait(1600);render();assert($('signal').textContent==='—','Stale USB signal must blank');
 await $('disconnect').onclick();assert(!link&&$('signal').textContent==='—','Disconnect clears live');
 report.push('stale readings blank; disconnect does not send output stop');
 document.querySelector('[data-tab="wiring"]').click();
 return {passed:report,hardware:'USB stream simulated; no physical board',export:exported.name};
})()
