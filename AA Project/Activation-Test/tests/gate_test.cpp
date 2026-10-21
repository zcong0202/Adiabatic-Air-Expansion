#include "../aa_activation/ActivationLogic.h"
#include <assert.h>
#include <stdio.h>
int main() {
  ActivationGate g;
  assert(!g.update(0, true, true, true));
  assert(!g.update(149, true, true, true));
  assert(g.update(150, true, true, true));
  // In hysteresis band: retain true even when entry false.
  assert(g.update(200, true, false, true));
  assert(g.update(300, true, false, false));
  assert(g.update(499, true, false, false));
  assert(!g.update(500, true, false, false));
  // Short detections do not activate; intermittent entry resets dwell.
  assert(!g.update(600, true, true, true));
  assert(!g.update(700, true, false, false));
  assert(!g.update(701, true, true, true));
  assert(g.update(851, true, true, true));
  // Sensor failure closes immediately.
  assert(!g.update(852, false, true, true));
  assert(g.state == ActivationGate::OFF);
  g.update(1000, true, true, true);
  assert(g.update(1150, true, true, true));
  assert(!g.update(61150, true, true, true));
  assert(g.state == ActivationGate::LIMIT);
  assert(!g.update(62000, true, true, true));
  assert(!g.update(63000, false, false, false));
  assert(!g.update(64000, true, false, false));
  assert(!g.update(64999, true, false, false));
  assert(g.state == ActivationGate::LIMIT);
  assert(!g.update(65000, true, false, false));
  assert(g.state == ActivationGate::OFF);
  // millis wraparound must preserve dwell and maximum-on timing.
  g.reset(); g.update(UINT32_MAX - 100, true, true, true);
  assert(!g.update(48, true, true, true));
  assert(g.update(49, true, true, true));
  assert(!g.update(60049, true, true, true));
  puts("PASS: entry dwell, hysteresis, exit dwell, noise rejection, fault close, maximum-on, re-arm, clock wraparound");
}
