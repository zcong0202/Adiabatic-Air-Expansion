#pragma once
#include <stdint.h>

// Time-based gate. All timing settings below are prototype assumptions.
class ActivationGate {
 public:
  enum State { OFF, QUALIFY, ON, LIMIT };
  State state = OFF;
  uint32_t since = 0, onSince = 0, absentSince = 0;
  bool departing = false;
  static const uint32_t ENTER_MS = 150, EXIT_MS = 200;
  static const uint32_t MAX_ON_MS = 0, REARM_MS = 1000;

  void reset() { state = OFF; departing = false; }
  bool update(uint32_t now, bool healthy, bool enter, bool retain) {
    if (state == LIMIT) {
      // Re-arm only after a healthy, unoccupied interval.
      if (!healthy || retain) departing = false;
      else if (!departing) { departing = true; absentSince = now; }
      else if (uint32_t(now - absentSince) >= REARM_MS) reset();
      return false;
    }
    if (!healthy) { reset(); return false; }
    if (state == ON) {
      if (MAX_ON_MS && uint32_t(now - onSince) >= MAX_ON_MS) {
        state = LIMIT; departing = false; return false;
      }
      if (retain) departing = false;
      else if (!departing) { departing = true; absentSince = now; }
      else if (uint32_t(now - absentSince) >= EXIT_MS) reset();
      return state == ON;
    }
    if (!enter) { reset(); return false; }
    if (state == OFF) { state = QUALIFY; since = now; }
    if (uint32_t(now - since) >= ENTER_MS) {
      state = ON; onSince = now; departing = false;
    }
    return state == ON;
  }
};
