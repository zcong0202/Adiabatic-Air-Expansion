#include <assert.h>
#include <stdio.h>
#include "../../aa_activation_tof/SafeI2C.h"
int modes[20]={0};
bool transfer=false,ackEnabled=true,clockStuck=false,pullups=true;
bool dataStuck=false; unsigned recoveryEdges=0;
unsigned edges=0; uint8_t addressByte=0; uint32_t us=0;
void digitalWrite(uint8_t pin,uint8_t value) {
  assert(pin==A4 || pin==A5); assert(value==LOW); // Never a 5V pull-up or HIGH output.
}
void pinMode(uint8_t pin,uint8_t mode) {
  assert(mode==INPUT || mode==OUTPUT);
  int old=modes[pin]; modes[pin]=mode;
  if (pin==A5 && old==OUTPUT && mode==INPUT && dataStuck && ++recoveryEdges>=9) dataStuck=false;
  if(pin==A4 && mode==OUTPUT && old==INPUT && modes[A5]==INPUT) {
    transfer=true; edges=0; addressByte=0;
  }
  if(pin==A5 && mode==INPUT && old==OUTPUT && transfer) {
    ++edges;
    if(edges<=8) addressByte=uint8_t((addressByte<<1)|(modes[A4]==INPUT));
  }
  if(pin==A4 && mode==INPUT && old==OUTPUT && modes[A5]==INPUT) transfer=false;
}
int analogRead(uint8_t pin) {
  us+=100;
  if(modes[pin]==OUTPUT || !pullups) return 0;
  if(pin==A5) return clockStuck?0:600;
  if(dataStuck) return 0;
  if(transfer && edges && edges%9==0 && ackEnabled) return 0;
  if(transfer && edges>=10 && (addressByte&1)) {
    unsigned bit=(edges-10)%9;
    if(bit<8) return (0xA5&(128>>bit))?600:0;
  }
  return 600;
}
uint32_t micros(){return us;}
void delay(unsigned long ms){us+=uint32_t(ms*1000);}
void delayMicroseconds(unsigned int delta){us+=delta;}
int main(){
  SafeI2C bus; bus.begin(); assert(modes[A4]==INPUT && modes[A5]==INPUT);
  assert(bus.idlePullupsOK());
  dataStuck=true; recoveryEdges=0; assert(bus.recover());
  assert(!dataStuck && recoveryEdges==9);
  bus.beginTransmission(0x29); bus.write(0x12); bus.write(0x34);
  assert(bus.endTransmission()==0); assert(addressByte==0x52);
  assert(modes[A4]==INPUT && modes[A5]==INPUT);
  assert(bus.requestFrom(0x29,2)==2); assert(addressByte==0x53);
  assert(bus.read()==0xA5 && bus.read()==0xA5 && bus.read()==-1);
  ackEnabled=false; bus.beginTransmission(0x29);
  assert(bus.endTransmission()==2 && bus.errors()>0);
  ackEnabled=true; pullups=false; assert(!bus.idlePullupsOK()); pullups=true;
  clockStuck=true; bus.beginTransmission(0x29);
  assert(bus.endTransmission()==4 && bus.getWireTimeoutFlag());
  assert(modes[A4]==INPUT && modes[A5]==INPUT);
  bus.clearWireTimeoutFlag(); assert(!bus.getWireTimeoutFlag()); clockStuck=false;
  bus.beginTransmission(0x29); for(int i=0;i<33;++i)bus.write(0);
  assert(bus.endTransmission()==1);
  puts("PASS: all GPIO writes LOW; release leaves input; nine-clock bus recovery; address/ACK; byte reads; NACK; missing pull-ups; clock timeout; buffer overflow. Mock transport only; live sensor results are separate evidence.");
}
