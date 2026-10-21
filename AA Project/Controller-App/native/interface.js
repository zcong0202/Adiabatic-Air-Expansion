// Guided native workflow layered on the tested firmware/telemetry code.
const originalFirmwareFiles=firmwareFiles;
firmwareFiles=f=>{const files=originalFirmwareFiles(f);files['READ ME.txt']=files['READ ME.txt'].replace('through Chrome Web Serial','through its built-in Mac USB connection');return files;};
const browserTell=tell;
tell=(message,tone='')=>{
 if(message.includes('Cannot reach Uno bootloader'))message='Arduino could not update. Close other Arduino apps, check the USB data cable, then try Save time again.';
 if(message.includes('bootloader did not respond'))message='Arduino did not respond. Reconnect USB, then try Save time again.';
 browserTell(message,tone);
};
downloaded=async(name,data)=>{try{const saved=await NativeAA.save(name,data);if(saved)tell('Saved '+name+'.','good');else tell('Save cancelled.');}catch(e){tell(e.message,'error');}};
const originalControls=controls;
controls=()=>{originalControls();$('apply').disabled=!link||flashing||!!pending;$('download').disabled=flashing;$('seconds').disabled=flashing||!!pending;$('polarity').disabled=flashing||!!pending;$('connect').textContent=link?'Arduino connected':'Connect Arduino';};
const originalConfig=configChanged;
configChanged=()=>{originalConfig();try{const s=chosen();$('setupSafety').hidden=!!(compatible&&board&&board.active_low===s.low);$('configuration').textContent=board?'Arduino currently set to '+board.hold_ms/1000+' seconds. Click Save time to use '+s.hold/1000+' seconds.':'Choose the time, connect Arduino, then click Save time. First setup is automatic.';}catch{}};
let nativeEdited=false;
$('seconds').addEventListener('input',()=>nativeEdited=true);$('polarity').addEventListener('change',()=>nativeEdited=true);
document.querySelectorAll('.preset').forEach(button=>button.addEventListener('click',()=>nativeEdited=true));
const oldReceived=received;
received=line=>{oldReceived(line);const m=Core.telemetry(line);if(m?.kind==='info'&&compatible){if(!nativeEdited){$('seconds').value=m.hold_ms/1000;$('polarity').value=String(m.active_low);configChanged();}$('connectHelp').textContent='Arduino ready. Set the time and click Save time.';}if(m?.kind==='legacy'){$('connectHelp').textContent='Arduino found. Click Save time for automatic first setup.';}};
const originalApply=$('apply').onclick;
$('apply').textContent='Save time to Arduino';
$('download').textContent='Save firmware file';
$('download').onclick=async()=>{try{const f=firmware();await downloaded('AA firmware '+f.hold/1000+'s.zip',Core.zip(firmwareFiles(f)),'application/zip');}catch(e){tell(e.message,'error');}};
$('install').hidden=true;
$('apply').onclick=async()=>{
 try{
  chosen();if(!link)throw Error('Connect the Arduino first.');
  // Require a concrete valve-isolated acknowledgement only before firmware/polarity work.
  if(!compatible||(board&&board.active_low!==chosen().low)){
   if(!$('valveIsolated').checked){$('setupSafety').hidden=false;$('valveIsolated').focus();tell('Before first setup or changing relay type, turn OFF the valve’s 12 V switch. Tick the box, then click Save time.');return;}
  }
  if(!compatible){
   flashing=true;controls();$('signal').textContent='—';$('remaining').textContent='—';$('signalBox').className='signalbox';
   await NativeAA.call('title',{updating:true});tell('First setup: updating Arduino. Keep the USB cable connected.');
   const f=firmware();await flashUno(link,f.bytes,p=>{$('uploadProgress').textContent='Setting up Arduino: '+p+'%';});
   const end=Date.now()+5000;while(!compatible&&Date.now()<end)await wait(50);
   if(!compatible)throw Error('Update finished, but Arduino settings are not confirmed. Reconnect USB and try again.');
   flashing=false;controls();$('uploadProgress').textContent='First setup complete.';
  }
  await originalApply();
 }catch(e){tell(e.message,'error');}
 finally{flashing=false;$('valveIsolated').checked=false;controls();await NativeAA.call('title',{updating:false}).catch(()=>{});}
};
$('valveIsolated').onchange=()=>{if(!$('valveIsolated').checked)$('setupSafety').hidden=false;};
$('connectHelp').textContent='Plug the Uno into this Mac with the USB data cable. Click Connect Arduino.';
configChanged();controls();tell('Start here: plug in Arduino, click Connect Arduino, choose seconds, then Save time.');
