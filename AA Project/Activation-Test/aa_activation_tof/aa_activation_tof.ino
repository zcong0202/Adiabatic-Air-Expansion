#include "SafeI2C.h"
#include "VL53L1XSafe.h" // Pololu 1.3.1, local transport adaptation
#include "ActivationLogic.h"

// LED/logic prototype only. Do not connect a valve to these pins.
const bool ENABLE_PIR = false; // Disconnected in this ToF session.
const bool ENABLE_TOF = true; // Low-voltage, open-drain software I2C. Sensor VCC must be 3.3V.
const uint8_t COMMAND_PIN = 8, FEEDBACK_PIN = 7, VOLTAGE_PIN = A0;
const uint8_t PIR_PIN = 2;
const uint16_t ENTER_MIN_MM = 0, ENTER_MAX_MM = 1500;
const uint16_t RETAIN_MIN_MM = 0, RETAIN_MAX_MM = 1600;
const uint32_t STALE_MS = 250, PIR_WARM_MS = 60000;
const uint32_t FEEDBACK_GRACE_MS = 10, FEEDBACK_FAULT_MS = 100;
const uint8_t ROI_SIZE = 16; // Baseline. Compare 8 and 4 separately.
const float ADC_REFERENCE_V = 5.0f; // Approximate. Measure actual 5V rail.

VL53L1X tof;
ActivationGate gate;
char mode = 'S';  // S=complete stop, T=complete start, X=output-only stop.
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
  SafeBus.beginTransmission(0x29);
  return SafeBus.endTransmission() == 0;
}

void setupToF() {
  tofReady = false; tofValid = false; sampleCount = sampleIndex = 0;
  rawMM = filteredMM = 0; rangeStatus = 255; sampleAt = 0;
  if (!ENABLE_TOF) return;
  SafeBus.clearWireTimeoutFlag();
  SafeBus.recover();
  tof.setTimeout(500);
  Serial.print(F("# ToF idle SDA=")); Serial.print(SafeBus.voltageADC(A4)*5.0f/1023.0f,3);
  Serial.print(F("V SCL=")); Serial.print(SafeBus.voltageADC(A5)*5.0f/1023.0f,3); Serial.println(F("V (ADC estimate)"));
  if (!SafeBus.idlePullupsOK()) {
    Serial.println(F("# ToF bus idle check failed: needs onboard low-voltage pull-ups")); return;
  }
  if (!ackToF()) { Serial.println(F("# ToF no ACK at 0x29")); return; }
  if (!tof.init()) { Serial.println(F("# ToF model/config init failed")); return; }
  // Medium supports the initial 1.5m threshold; outdoor reach must be measured.
  SafeBus.clearWireTimeoutFlag();
  uint32_t setupErrors = SafeBus.errors();
  if (!tof.setDistanceMode(VL53L1X::Medium)) return;
  if (!tof.setMeasurementTimingBudget(33000)) return;
  tof.setROISize(ROI_SIZE, ROI_SIZE);
  // Explicit new-sample interrupt; do not rely on factory/reset defaults.
  Serial.print(F("# ToF prior interrupt config=")); Serial.println(tof.readReg(VL53L1X::SYSTEM__INTERRUPT_CONFIG_GPIO),HEX);
  tof.writeReg(VL53L1X::SYSTEM__INTERRUPT_CONFIG_GPIO, 0x20);
  tof.writeReg(VL53L1X::GPIO_HV_MUX__CTRL, 0x11); // Active LOW matches dataReady().
  Serial.print(F("# ToF VHV init=")); Serial.print(tof.readReg(VL53L1X::VHV_CONFIG__INIT),HEX);
  Serial.print(F(" timeout=")); Serial.print(tof.readReg(VL53L1X::VHV_CONFIG__TIMEOUT_MACROP_LOOP_BOUND),HEX);
  Serial.print(F(" count=")); Serial.println(tof.readReg(VL53L1X::VHV_CONFIG__COUNT_THRESH),HEX);
  tof.startContinuous(100);
  tofReady = (tof.last_status == 0 && !SafeBus.getWireTimeoutFlag() && SafeBus.errors() == setupErrors);
  Serial.print(F("# ToF init=")); Serial.println(tofReady);
  Serial.print(F("# ToF mode=")); Serial.print(tof.readReg(VL53L1X::SYSTEM__MODE_START), HEX);
  Serial.print(F(" gpio=")); Serial.print(tof.readReg(VL53L1X::GPIO__TIO_HV_STATUS), HEX);
  Serial.print(F(" fw=")); Serial.print(tof.readReg(VL53L1X::FIRMWARE__SYSTEM_STATUS), HEX);
  Serial.print(F(" osc=")); Serial.print(tof.readReg16Bit(VL53L1X::RESULT__OSC_CALIBRATE_VAL));
  Serial.print(F(" errors=")); Serial.println(SafeBus.errors());
}

void sampleToF(uint32_t now) {
  if (!tofReady || uint32_t(now - pollAt) < 10) return;
  pollAt = now;
  if (sampleCount && uint32_t(now - sampleAt) > STALE_MS) sampleCount = 0;
  if (!ackToF() || SafeBus.getWireTimeoutFlag()) {
    Serial.print(F("# ToF poll ACK/clock failed; errors=")); Serial.print(SafeBus.errors()); Serial.print(F(" timeout=")); Serial.println(SafeBus.getWireTimeoutFlag());
    tofReady = false; tofValid = false; sampleCount = 0; return;
  }
  uint32_t readErrors = SafeBus.errors();
  bool ready = tof.dataReady();
  if (SafeBus.errors() != readErrors || SafeBus.getWireTimeoutFlag()) {
    Serial.print(F("# ToF readiness read failed; errors=")); Serial.println(SafeBus.errors());
    tofReady = false; tofValid = false; sampleCount = 0; return;
  }
  if (!ready) {
    static uint32_t diagnosticAt = 0;
    if (uint32_t(now-diagnosticAt)>2000 && uint32_t(now-sampleAt)>1000) {
      diagnosticAt=now;
      Serial.print(F("# ToF waiting; mode=")); Serial.print(tof.readReg(VL53L1X::SYSTEM__MODE_START),HEX);
      Serial.print(F(" gpio=")); Serial.print(tof.readReg(VL53L1X::GPIO__TIO_HV_STATUS),HEX);
      Serial.print(F(" mux=")); Serial.print(tof.readReg(VL53L1X::GPIO_HV_MUX__CTRL),HEX);
      Serial.print(F(" stream=")); Serial.print(tof.readReg(VL53L1X::RESULT__STREAM_COUNT));
      Serial.print(F(" status=")); Serial.print(tof.readReg(VL53L1X::RESULT__RANGE_STATUS));
      Serial.print(F(" fastosc=")); Serial.print(tof.readReg16Bit(VL53L1X::OSC_MEASURED__FAST_OSC__FREQUENCY));
      Serial.print(F(" budget=")); Serial.print(tof.getMeasurementTimingBudget());
      Serial.print(F(" directmm=")); Serial.print(tof.readReg16Bit(VL53L1X::RESULT__FINAL_CROSSTALK_CORRECTED_RANGE_MM_SD0));
      Serial.print(F(" errors=")); Serial.println(SafeBus.errors());
    }
    return;
  }
  rawMM = tof.read(false);
  sampleAt = millis();
  rangeStatus = uint8_t(tof.ranging_data.range_status);
  tofValid = (rangeStatus == uint8_t(VL53L1X::RangeValid) &&
              tof.last_status == 0 && !SafeBus.getWireTimeoutFlag() && SafeBus.errors() == readErrors);
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

void stopAll() {
  setCommand(false); gate.reset(); mode = 'S';
  SafeBus.clearWireTimeoutFlag();
  bool busRecovered = ENABLE_TOF && SafeBus.recover();
  if (busRecovered && ackToF()) {
    uint32_t errors = SafeBus.errors();
    tof.stopContinuous();
    uint8_t stoppedMode = tof.readReg(VL53L1X::SYSTEM__MODE_START);
    Serial.print(F("# Complete stop; ranging register=")); Serial.print(stoppedMode, HEX);
    Serial.print(F(" confirmed="));
    Serial.println((stoppedMode == 0x00 || stoppedMode == 0x80) && SafeBus.errors() == errors && !SafeBus.getWireTimeoutFlag());
  } else Serial.println(F("# Complete stop; sensor stop unconfirmed (no ACK)"));
  tofReady = tofValid = false; sampleCount = sampleIndex = 0;
  rawMM = filteredMM = 0; rangeStatus = 255; sampleAt = 0;
}

void serialCommands() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c >= 'a' && c <= 'z') c -= 32;
    if (c == '0' || c == '1') { groundTruth = c - '0'; continue; }
    if (c == '?') {
      Serial.println(F("# T=ToF P=PIR H=PIR-confirmed-ToF B=5s-loopback S=complete-stop X=output-stop R=reset-fault 0/1=ground-truth"));
      continue;
    }
    if (c == 'R') {
      stopAll(); fault = false; mismatchPending = false; continue;
    }
    if (c == 'S') { stopAll(); continue; }
    if (c == 'T') {
      setCommand(false); gate.reset();
      if (!tofReady) setupToF();
      mode = tofReady ? 'T' : 'S';
      if (!tofReady) Serial.println(F("# Start failed; output remains OFF"));
      continue;
    }
    if ((c == 'P' || c == 'H') && !ENABLE_PIR) {
      Serial.println(F("# PIR disconnected; mode disabled")); continue;
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
    SafeBus.begin(); SafeBus.setClock(100000); SafeBus.setWireTimeout(25000, true);
  }
  Serial.println(F("# Low-voltage ToF bench: VCC=3.3V, SDA=A4, SCL=A5, no internal 5V pull-ups"));
  stopAll();
  Serial.println(F("# AA LED prototype; outputs disabled at boot; send ? for commands"));
  Serial.println(F("ms,mode,gt,raw_mm,median_mm,range_status,tof_valid,tof_age_ms,pir_raw,pir_warm,state,command,feedback,adc,feedback_v,match,fault"));
}

void loop() {
  serialCommands();
  uint32_t now = millis();
  sampleToF(now);
  now = millis();
  pirRaw = ENABLE_PIR && digitalRead(PIR_PIN) == HIGH;
  bool pirWarm = ENABLE_PIR && uint32_t(now - bootAt) < PIR_WARM_MS;
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
      if (age >= 5000) stopAll();
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
