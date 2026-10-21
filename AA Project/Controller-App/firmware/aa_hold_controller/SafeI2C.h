#pragma once
#include <Arduino.h>

// Uno-only prototype transport. Pull LOW or release; never drive HIGH.
// HIGH is detected through the ADC, so 2.8/3.3V does not depend on 5V GPIO VIH.
// The breakout must provide its own pull-ups to its low-voltage supply.
class SafeI2C {
 public:
  void begin() {
#ifdef __AVR__
    TWCR = 0; // Hardware TWI stays disabled.
#endif
    release(A4); release(A5);
    recover();
  }
  bool recover() {
    // Uno resets can interrupt a slave read. NXP bus clear: up to nine clocks.
    release(A4); release(A5);
    if (!clockHigh()) return false;
    if (high(A4)) return true;
    for (uint8_t i=0; i<9 && !high(A4); ++i) {
      low(A5); delayMicroseconds(5);
      if (!clockHigh()) return false;
    }
    low(A5);
    return stopBus() && high(A4);
  }
  void setClock(uint32_t) {} // ADC reads define this deliberately slow bus.
  void setWireTimeout(uint32_t us, bool) { timeoutUs = us; }
  void clearWireTimeoutFlag() { timedOut = false; }
  bool getWireTimeoutFlag() const { return timedOut; }
  uint32_t errors() const { return errorCount; }
  uint16_t voltageADC(uint8_t pin) {
#ifdef __AVR__
    // 500 kHz ADC for binary bus sensing; restore normal ADC speed for A0.
    uint8_t prior=ADCSRA & 0x07;
    ADCSRA=(ADCSRA & 0xF8) | 0x05; // 16 MHz / 32
#endif
    analogRead(pin); uint16_t value=analogRead(pin);
#ifdef __AVR__
    ADCSRA=(ADCSRA & 0xF8) | prior;
#endif
    return value;
  }
  bool idlePullupsOK() {
    release(A4); release(A5); delay(2);
    uint16_t a=voltageADC(A4), b=voltageADC(A5);
    // Idle must sit below AVCC. ADC ratio allows USB AVCC variation.
    // This is a bus-contact check, not a voltmeter; VCC must be wired to 3.3V.
    return a>=409 && a<=850 && b>=409 && b<=850;
  }
  void beginTransmission(uint8_t addr) { address=addr; txSize=0; overflow=false; }
  size_t write(uint8_t value) {
    if (txSize >= sizeof(tx)) { overflow=true; return 0; }
    tx[txSize++]=value; return 1;
  }
  uint8_t endTransmission() {
    if (overflow) { ++errorCount; return 1; }
    if (!start()) { stopBus(); ++errorCount; return 4; }
    if (!writeByte(uint8_t(address<<1))) { stopBus(); ++errorCount; return 2; }
    for (uint8_t i=0;i<txSize;++i) {
      if (!writeByte(tx[i])) { stopBus(); ++errorCount; return 3; }
    }
    if (!stopBus()) { ++errorCount; return 4; }
    return 0;
  }
  uint8_t requestFrom(uint8_t addr, uint8_t count) {
    rxSize=rxIndex=0;
    if (count>sizeof(rx) || !start()) { stopBus(); ++errorCount; return 0; }
    if (!writeByte(uint8_t((addr<<1)|1))) { stopBus(); ++errorCount; return 0; }
    for (uint8_t i=0;i<count;++i) {
      uint8_t value;
      if (!readByte(value,i+1<count)) { stopBus(); ++errorCount; rxSize=0; return 0; }
      rx[rxSize++]=value;
    }
    if (!stopBus()) { ++errorCount; rxSize=0; }
    return rxSize;
  }
  int read() { return rxIndex<rxSize ? rx[rxIndex++] : -1; }
 private:
  uint8_t tx[32]={0},rx[32]={0},txSize=0,rxSize=0,rxIndex=0,address=0;
  bool overflow=false,timedOut=false;
  uint32_t timeoutUs=25000,errorCount=0;
  static void low(uint8_t pin) { digitalWrite(pin,LOW); pinMode(pin,OUTPUT); }
  static void release(uint8_t pin) { digitalWrite(pin,LOW); pinMode(pin,INPUT); }
  bool high(uint8_t pin) { return voltageADC(pin)>256; }
  bool clockHigh() {
    release(A5);
    uint32_t at=micros();
    while (!high(A5)) {
      if (uint32_t(micros()-at)>=timeoutUs) { timedOut=true; return false; }
    }
    delayMicroseconds(5); return true;
  }
  bool start() {
    release(A4);
    if (!clockHigh() || !high(A4)) return false;
    low(A4); delayMicroseconds(5); low(A5); return true;
  }
  bool stopBus() {
    low(A4);
    bool ok=clockHigh();
    release(A4); delayMicroseconds(5); return ok;
  }
  bool writeByte(uint8_t value) {
    for (uint8_t mask=128;mask;mask>>=1) {
      if (value&mask) release(A4); else low(A4);
      delayMicroseconds(5);
      if (!clockHigh()) { low(A5); return false; }
      low(A5);
    }
    release(A4);
    if (!clockHigh()) { low(A5); return false; }
    bool ack=!high(A4);
    low(A5); return ack;
  }
  bool readByte(uint8_t &value,bool acknowledge) {
    value=0; release(A4);
    for (uint8_t i=0;i<8;++i) {
      if (!clockHigh()) { low(A5); return false; }
      value=uint8_t((value<<1)|(high(A4)?1:0)); low(A5);
    }
    if (acknowledge) low(A4); else release(A4);
    if (!clockHigh()) { low(A5); release(A4); return false; }
    low(A5); release(A4); return true;
  }
};
extern SafeI2C SafeBus;
