#include <Wire.h>
#include <VL53L1X.h>  // Pololu 1.3.1
#include "ActivationLogic.h"

// LED/logic prototype only. Do not connect a valve to these pins.
const bool ENABLE_TOF = false; // PIR bench session. Enable only after ToF voltage checks.
const uint8_t COMMAND_PIN = 8, FEEDBACK_PIN = 7, VOLTAGE_PIN = A0;
const uint8_t PIR_PIN = 2;
const uint16_t ENTER_MIN_MM = 400, ENTER_MAX_MM = 1500;
const uint16_t RETAIN_MIN_MM = 350, RETAIN_MAX_MM = 1600;
const uint32_t STALE_MS = 250, PIR_WARM_MS = 60000;
const uint32_t FEEDBACK_GRACE_MS = 10, FEEDBACK_FAULT_MS = 100;
const uint8_t ROI_SIZE = 16; // Baseline. Compare 8 and 4 separately.
const float ADC_REFERENCE_V = 5.0f; // Approximate. Measure actual 5V rail.

VL53L1X tof;
ActivationGate gate;
char mode = 'X';  // Boot disabled. T=ToF, P=PIR, H=PIR-confirmed ToF, B=loopback.
bool tofReady = false, tofValid = false, command = false, fault = false;
bool pirRaw = false, mismatchPending = false, pirSeen = false;
uint16_t rawMM = 0, filteredMM = 0, samples[3] = {0};
uint8_t sampleCount = 0, sampleIndex = 0, rangeStatus = 255;
uint32_t bootAt, sampleAt = 0, pollAt = 0, logAt = 0, changedAt = 0;
uint32_t mismatchAt = 0, pirAt = 0, benchAt = 0;
int8_t groundTruth = -1;

void setCommand(bool enabled) {
  if (enabled != command) { command = enabled; changedAt = millis(); }
  digitalWrite(COMMAND_PIN, command ? HIGH : LOW);
  digitalWrite(LED_BUILTIN, command ? HIGH : LOW);
}

bool ackToF() {
  Wire.beginTransmission(0x29);
  return Wire.endTransmission() == 0;
}

void setupToF() {
  tofReady = false; tofValid = false; sampleCount = 0;
  if (!ENABLE_TOF) return;
  Wire.clearWireTimeoutFlag();
  tof.setTimeout(100);
  if (!ackToF() || !tof.init()) return;
  // Medium supports the initial 1.5m threshold; outdoor reach must be measured.
  if (!tof.setDistanceMode(VL53L1X::Medium)) return;
  if (!tof.setMeasurementTimingBudget(33000)) return;
  tof.setROISize(ROI_SIZE, ROI_SIZE);
  tof.startContinuous(50);
  tofReady = (tof.last_status == 0 && !Wire.getWireTimeoutFlag());
}

void sampleToF(uint32_t now) {
  if (!tofReady || uint32_t(now - pollAt) < 10) return;
  pollAt = now;
  if (sampleCount && uint32_t(now - sampleAt) > STALE_MS) sampleCount = 0;
  if (!ackToF() || Wire.getWireTimeoutFlag()) {
    tofReady = false; tofValid = false; sampleCount = 0; return;
  }
  if (!tof.dataReady()) return;
  rawMM = tof.read(false);
  sampleAt = millis();
  rangeStatus = uint8_t(tof.ranging_data.range_status);
  tofValid = (rangeStatus == uint8_t(VL53L1X::RangeValid) &&
              tof.last_status == 0 && !Wire.getWireTimeoutFlag());
  if (!tofValid) { sampleCount = 0; return; }
  samples[sampleIndex] = rawMM;
  sampleIndex = (sampleIndex + 1) % 3;
  if (sampleCount < 3) ++sampleCount;
  uint16_t sorted[3] = {samples[0], samples[1], samples[2]};
  for (uint8_t i = 0; i < 3; ++i)
    for (uint8_t j = i + 1; j < 3; ++j)
      if (sorted[j] < sorted[i]) { uint16_t t=sorted[i]; sorted[i]=sorted[j]; sorted[j]=t; }
  filteredMM = sorted[1];
}

void serialCommands() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c >= 'a' && c <= 'z') c -= 32;
    if (c == '0' || c == '1') { groundTruth = c - '0'; continue; }
    if (c == '?') {
      Serial.println(F("# T=ToF P=PIR H=PIR-confirmed-ToF B=5s-loopback X=stop R=reset-fault/reinit 0/1=ground-truth"));
      continue;
    }
    if (c == 'R') {
      mode = 'X'; gate.reset(); setCommand(false);
      fault = false; mismatchPending = false; setupToF(); continue;
    }
    if ((c == 'T' || c == 'H') && !ENABLE_TOF) {
      Serial.println(F("# ToF disabled for PIR bench session")); continue;
    }
    if (c == 'T' || c == 'P' || c == 'H' || c == 'B' || c == 'X') {
      setCommand(false); gate.reset(); mode = c; benchAt = millis();
    }
  }
}

void setup() {
  digitalWrite(COMMAND_PIN, LOW); pinMode(COMMAND_PIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW); pinMode(LED_BUILTIN, OUTPUT);
  pinMode(FEEDBACK_PIN, INPUT); pinMode(VOLTAGE_PIN, INPUT);
  pinMode(PIR_PIN, INPUT); // Add external 100k pull-down for disconnected PIR.
  Serial.begin(115200);
  bootAt = millis();
  if (ENABLE_TOF) {
    Wire.begin(); Wire.setClock(100000); Wire.setWireTimeout(25000, true);
  }
  setupToF();
  Serial.println(F("# AA LED prototype; outputs disabled at boot; send ? for commands"));
  Serial.println(F("ms,mode,gt,raw_mm,median_mm,range_status,tof_valid,tof_age_ms,pir_raw,pir_warm,state,command,feedback,adc,feedback_v,match,fault"));
}

void loop() {
  serialCommands();
  uint32_t now = millis();
  sampleToF(now);
  now = millis();
  pirRaw = digitalRead(PIR_PIN) == HIGH;
  bool pirWarm = uint32_t(now - bootAt) < PIR_WARM_MS;
  if (!pirWarm && pirRaw) { pirAt = now; pirSeen = true; }
  bool fresh = tofReady && tofValid && sampleCount == 3 && uint32_t(now - sampleAt) <= STALE_MS;
  bool enter = filteredMM >= ENTER_MIN_MM && filteredMM <= ENTER_MAX_MM;
  bool retain = filteredMM >= RETAIN_MIN_MM && filteredMM <= RETAIN_MAX_MM;
  bool request = false;
  if (!fault) {
    if (mode == 'T') request = gate.update(now, fresh, enter, retain);
    if (mode == 'P') request = gate.update(now, !pirWarm, pirRaw, pirRaw);
    // PIR confirms entry in the past 5s. ToF maintains stationary occupancy.
    if (mode == 'H') request = gate.update(now, fresh && !pirWarm,
      enter && pirSeen && uint32_t(now - pirAt) <= 5000, retain);
    // Explicit LED-only electrical test: 1s OFF, 1s ON, 1s OFF, 1s ON, 1s OFF.
    if (mode == 'B') {
      uint32_t age = uint32_t(now - benchAt);
      request = age < 5000 && ((age / 1000) % 2 == 1);
      if (age >= 5000) mode = 'X';
    }
  }
  setCommand(request);
  int feedback = digitalRead(FEEDBACK_PIN);
  int adc = analogRead(VOLTAGE_PIN);
  float volts = adc * ADC_REFERENCE_V / 1023.0f;
  bool match = feedback == (command ? HIGH : LOW) && (command ? volts >= 3.5f : volts <= 0.8f);
  if (uint32_t(now - changedAt) >= FEEDBACK_GRACE_MS && !match) {
    if (!mismatchPending) { mismatchPending = true; mismatchAt = now; }
    if (uint32_t(now - mismatchAt) >= FEEDBACK_FAULT_MS) {
      fault = true; gate.reset(); setCommand(false);
    }
  } else mismatchPending = false;
  // Snapshot command, feedback and voltage again after any fault transition.
  feedback = digitalRead(FEEDBACK_PIN);
  adc = analogRead(VOLTAGE_PIN);
  volts = adc * ADC_REFERENCE_V / 1023.0f;
  match = feedback == (command ? HIGH : LOW) && (command ? volts >= 3.5f : volts <= 0.8f);
  if (uint32_t(now - logAt) >= 50) {
    logAt = now;
    Serial.print(now); Serial.print(','); Serial.print(mode); Serial.print(',');
    Serial.print(groundTruth); Serial.print(','); Serial.print(rawMM); Serial.print(',');
    Serial.print(filteredMM); Serial.print(','); Serial.print(rangeStatus); Serial.print(',');
    Serial.print(fresh); Serial.print(','); Serial.print(uint32_t(now - sampleAt)); Serial.print(',');
    Serial.print(pirRaw); Serial.print(','); Serial.print(pirWarm); Serial.print(',');
    Serial.print(uint8_t(gate.state)); Serial.print(','); Serial.print(command); Serial.print(',');
    Serial.print(feedback); Serial.print(','); Serial.print(adc); Serial.print(',');
    Serial.print(volts, 3); Serial.print(','); Serial.print(match); Serial.print(','); Serial.println(fault);
  }
}
