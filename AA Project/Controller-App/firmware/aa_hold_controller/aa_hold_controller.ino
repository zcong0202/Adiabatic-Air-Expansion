#include "SafeI2C.h"
#include "VL53L1XSafe.h"
#include "HoldTimer.h"
#include "Defaults.h"
#include <EEPROM.h>
#include <avr/pgmspace.h>

// Uno R3 + tested 3.3V Walfront VL53L1X. D8 is LOGIC only, never a coil supply.
// D7/A0 loop back the D8 logic wire. D13 shows logical activation even for LOW-trigger relays.
const uint8_t OUT=8, FEEDBACK=7, VOLTAGE=A0;
const uint32_t MIN_HOLD=100, MAX_HOLD=3000, CHECK_KEY=0xAAB0531CUL;
struct __attribute__((packed)) Profile {
  uint8_t magic[8]; uint32_t hold, generation; uint8_t low, reserved[3]; uint32_t check;
};
extern const Profile firmware_profile PROGMEM __attribute__((used)) = {
  {'A','A','H','O','L','D','1',0},DEFAULT_HOLD_MS,DEFAULT_GENERATION,
  DEFAULT_ACTIVE_LOW,{0,0,0},DEFAULT_HOLD_MS^DEFAULT_GENERATION^DEFAULT_ACTIVE_LOW^CHECK_KEY
};
struct __attribute__((packed)) Settings {
  uint32_t magic,hold,generation; uint8_t low,reserved[3]; uint32_t check;
};
VL53L1X tof;
HoldTimer timer;
uint32_t generation=0, pollAt=0, sampleAt=0, retryAt=0, logAt=0, changedAt=0, mismatchAt=0, seq=0;
uint16_t rawMM=0;
uint8_t rangeStatus=255;
bool activeLow=false, command=false, sensorReady=false, detected=false, fault=false, mismatchPending=false;
char input[48]; uint8_t inputCount=0; bool inputOverflow=false;

void output(bool enable){
  if(command!=enable){command=enable;changedAt=millis();}
  digitalWrite(OUT,(command != activeLow)?HIGH:LOW);
  digitalWrite(LED_BUILTIN,command?HIGH:LOW);
}
uint32_t checksum(uint32_t hold,uint32_t token,uint8_t low){return hold^token^low^CHECK_KEY;}
void loadSettings(){
  Profile profile; memcpy_P(&profile,&firmware_profile,sizeof(profile));
  timer.holdMs=profile.hold;generation=profile.generation;activeLow=profile.low;
  if(timer.holdMs<MIN_HOLD || timer.holdMs>MAX_HOLD || profile.low>1 || profile.check!=checksum(profile.hold,profile.generation,profile.low)){
    timer.holdMs=3000;activeLow=true;generation=0;
  }
  Settings saved;EEPROM.get(0,saved);
  if(saved.magic==0x41414831UL && saved.generation==generation && saved.hold>=MIN_HOLD && saved.hold<=MAX_HOLD && saved.low<=1 && saved.check==checksum(saved.hold,saved.generation,saved.low)){
    timer.holdMs=saved.hold;activeLow=saved.low;
  }
}
void saveSettings(){
  Settings saved={0x41414831UL,timer.holdMs,generation,uint8_t(activeLow),{0,0,0},checksum(timer.holdMs,generation,activeLow)};
  EEPROM.put(0,saved); // Uses update semantics. Only called on a confirmed SET command.
}
void info(const __FlashStringHelper* kind){
  Serial.print(F("{\"kind\":\""));Serial.print(kind);
  Serial.print(F("\",\"protocol\":1,\"firmware\":\"AA-BOUNDED-1.1\",\"hold_ms\":"));Serial.print(timer.holdMs);
  Serial.print(F(",\"active_low\":"));Serial.print(activeLow?1:0);
  Serial.print(F(",\"generation\":"));Serial.print(generation);
  Serial.print(F(",\"maximum_on_ms\":30000,\"rearm_ms\":3000"));Serial.println('}');
}
bool ack(){SafeBus.beginTransmission(0x29);return SafeBus.endTransmission()==0;}
void setupSensor(){
  sensorReady=false;detected=false;rangeStatus=255;
  SafeBus.clearWireTimeoutFlag();
  if(!SafeBus.recover() || !SafeBus.idlePullupsOK() || !ack())return;
  tof.setTimeout(500);
  if(!tof.init())return;
  SafeBus.clearWireTimeoutFlag();uint32_t errors=SafeBus.errors();
  if(!tof.setDistanceMode(VL53L1X::Medium) || !tof.setMeasurementTimingBudget(33000))return;
  tof.setROISize(16,16);
  tof.writeReg(VL53L1X::SYSTEM__INTERRUPT_CONFIG_GPIO,0x20);
  tof.writeReg(VL53L1X::GPIO_HV_MUX__CTRL,0x11);
  tof.startContinuous(100);
  sensorReady=tof.last_status==0 && SafeBus.errors()==errors && !SafeBus.getWireTimeoutFlag();
}
void sampleSensor(uint32_t now){
  if(!sensorReady || uint32_t(now-pollAt)<10)return;
  pollAt=now;uint32_t errors=SafeBus.errors();
  bool ready=tof.dataReady();
  if(SafeBus.errors()!=errors || SafeBus.getWireTimeoutFlag()){sensorReady=false;detected=false;timer.invalidate();return;}
  if(!ready)return;
  rawMM=tof.read(false);sampleAt=millis();rangeStatus=uint8_t(tof.ranging_data.range_status);
  bool valid=rangeStatus==uint8_t(VL53L1X::RangeValid) && tof.last_status==0 && SafeBus.errors()==errors && !SafeBus.getWireTimeoutFlag();
  // Presence refills only the departure tail, never the 30 s activation limit.
  detected=valid && rawMM<=((timer.active(sampleAt)||timer.blocked)?1600:1500);
  if(!valid)timer.invalidate();
  else if(!fault)timer.observe(sampleAt,detected);
  if(SafeBus.errors()!=errors || SafeBus.getWireTimeoutFlag())sensorReady=false;
}
bool parseUInt(const char* text,uint32_t &value){
  if(!*text)return false;value=0;
  for(;*text;++text){if(*text<'0'||*text>'9')return false;uint8_t digit=*text-'0';if(value>(MAX_HOLD-digit)/10)return false;value=value*10+digit;}
  return true;
}
void handleLine(){
  input[inputCount]=0;
  if(!strcmp(input,"HELLO")){info(F("info"));return;}
  if(!strcmp(input,"RESET")){
    output(false);timer.reset();fault=false;mismatchPending=false;setupSensor();info(F("reset"));return;
  }
  if(!strncmp(input,"SET ",4)){
    char* split=strchr(input+4,' ');uint32_t hold=0,low=0;
    if(split){*split=0;
      if(parseUInt(input+4,hold) && parseUInt(split+1,low) && hold>=MIN_HOLD && hold<=MAX_HOLD && low<=1){
        // Polarity changes require a fresh detection and de-energize logical output first.
        if(bool(low)!=activeLow){output(false);timer.reset();activeLow=low;output(false);}
        timer.setHold(hold,millis());saveSettings();info(F("applied"));return;
      }
    }
  }
  Serial.println(F("{\"kind\":\"error\",\"message\":\"Use SET milliseconds polarity(0/1); departure delay range 100..3000; total ON limit 30000\"}"));
}
void serialCommands(){
  while(Serial.available()){
    char c=Serial.read();
    if(c=='\n'){
      if(!inputOverflow && inputCount)handleLine();
      else if(inputOverflow)Serial.println(F("{\"kind\":\"error\",\"message\":\"Command too long\"}"));
      inputCount=0;inputOverflow=false;
    }else if(c!='\r'){
      if(inputCount<sizeof(input)-1)input[inputCount++]=c;else inputOverflow=true;
    }
  }
}
void setup(){
  loadSettings();
  digitalWrite(OUT,activeLow?HIGH:LOW);pinMode(OUT,OUTPUT);
  digitalWrite(LED_BUILTIN,LOW);pinMode(LED_BUILTIN,OUTPUT);
  pinMode(FEEDBACK,INPUT);pinMode(VOLTAGE,INPUT);
  Serial.begin(115200);SafeBus.begin();SafeBus.setWireTimeout(25000,true);
  info(F("info"));setupSensor();retryAt=millis();
}
void loop(){
  serialCommands();sampleSensor(millis());uint32_t now=millis();
  if(!sensorReady || uint32_t(now-sampleAt)>250){detected=false;timer.invalidate();}
  timer.expire(now); // Latch at 30 s; valid empty-zone readings are needed to re-arm.
  output(!fault && timer.active(now));
  int feedback=digitalRead(FEEDBACK),adc=analogRead(VOLTAGE);bool pinHigh=command!=activeLow;
  bool match=feedback==pinHigh && (pinHigh?adc>=716:adc<=164);
  if(uint32_t(now-changedAt)>=10 && !match){
    if(!mismatchPending){mismatchPending=true;mismatchAt=now;}
    if(uint32_t(now-mismatchAt)>=100){fault=true;timer.reset();output(false);}
  }else mismatchPending=false;
  if(!sensorReady && !timer.active(now) && uint32_t(now-retryAt)>=3000){retryAt=now;setupSensor();now=millis();}
  if(uint32_t(now-logAt)>=100){
    logAt=now;feedback=digitalRead(FEEDBACK);adc=analogRead(VOLTAGE);pinHigh=command!=activeLow;
    match=feedback==pinHigh && (pinHigh?adc>=716:adc<=164);
    Serial.print(F("{\"kind\":\"sample\",\"protocol\":1,\"seq\":"));Serial.print(++seq);
    Serial.print(F(",\"ms\":"));Serial.print(now);Serial.print(F(",\"detected\":"));Serial.print(detected?1:0);
    Serial.print(F(",\"command\":"));Serial.print(command?1:0);Serial.print(F(",\"pin_high\":"));Serial.print(pinHigh?1:0);
    Serial.print(F(",\"feedback\":"));Serial.print(feedback);Serial.print(F(",\"voltage_mv\":"));Serial.print(uint32_t(adc)*5000/1023);
    Serial.print(F(",\"hold_ms\":"));Serial.print(timer.holdMs);Serial.print(F(",\"active_low\":"));Serial.print(activeLow?1:0);
    Serial.print(F(",\"remaining_ms\":"));Serial.print(fault?0:timer.remaining(now));
    Serial.print(F(",\"maximum_on_ms\":30000,\"limited\":"));Serial.print(timer.blocked?1:0);
    Serial.print(F(",\"range_mm\":"));Serial.print(rawMM);Serial.print(F(",\"range_status\":"));Serial.print(rangeStatus);
    Serial.print(F(",\"sensor_ok\":"));Serial.print(sensorReady?1:0);Serial.print(F(",\"match\":"));Serial.print(match?1:0);
    Serial.print(F(",\"fault\":"));Serial.print(fault?1:0);Serial.println('}');
  }
}
