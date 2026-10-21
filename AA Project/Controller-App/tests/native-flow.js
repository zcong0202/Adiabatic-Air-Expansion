return (async()=>{
 const assert=(x,msg)=>{if(!x)throw Error(msg);},r=[];
 assert($('signal').textContent==='—'&&$('compatibility').hidden,'Native bridge available; no simulated live data');
 $('seconds').value='20';$('seconds').dispatchEvent(new Event('input'));
 await connect();await wait(30);assert(link&&!compatible&&!$('apply').disabled,'Old firmware accepts guided Save');
 await $('apply').onclick();assert(__simUSB.pages===0,'Cannot flash until 12V isolated');
 $('valveIsolated').checked=true;await $('apply').onclick();
 assert(__simUSB.pages>80&&__simUSB.hold===20000&&compatible,'One Save installs and verifies full firmware');
 assert($('message').textContent.includes('Saved 20'),'Save acknowledged');assert(!$('valveIsolated').checked,'Isolation acknowledgement resets after work');
 r.push('single Save installs old board firmware; full page readback; settings ACK; isolation acknowledgement enforced');
 $('seconds').value='12.3';$('seconds').dispatchEvent(new Event('input'));const pages=__simUSB.pages;await $('apply').onclick();assert(__simUSB.hold===12300&&__simUSB.pages===pages,'Later Save updates time without flash');
 r.push('later Save changes time directly, without build/reinstall');
 const sample={kind:'sample',protocol:1,seq:1,ms:2000,command:1,pin_high:1,feedback:1,detected:1,active_low:0,sensor_ok:1,match:1,fault:0,hold_ms:12300,remaining_ms:12000,voltage_mv:4800,range_mm:350,range_status:0};__simUSB.emit(sample);await wait(30);assert($('signal').textContent==='HIGH','Live HIGH rendered from USB');
 await $('download').onclick();assert(__simUSB.saved[0].name.includes('12.3s'),'Firmware saves with selected time');assert($('message').textContent.startsWith('Saved AA firmware'),'Only native save completion claims success');
 __simUSB.cancelSave=true;await $('download').onclick();assert(!__simUSB.saved.at(-1).ok&&$('message').textContent==='Save cancelled.','File save cancellation supported');
 r.push('telemetry HIGH; firmware export through native file bridge; cancellation without false save success');
 await $('disconnect').onclick();assert(!link&&$('signal').textContent==='—','Disconnect blanks actual data');
 return {passed:r,physical_usb:'not tested; native bridge emulated for guided flow'};
})()
