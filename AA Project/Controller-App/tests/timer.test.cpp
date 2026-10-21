#include "../firmware/aa_hold_controller/HoldTimer.h"
#include <assert.h>
#include <stdio.h>
int main(){
 HoldTimer t;assert(!t.active(0));t.detect(0);
 // An early departure closes exactly 3 s after the last positive reading.
 t.detect(4000);t.observe(4100,false);assert(t.active(6999));assert(t.remaining(6999)==1);
 t.expire(7000);assert(!t.active(7000));assert(!t.blocked);
 // Continued presence cannot extend the original 30 s deadline.
 t.reset();for(uint32_t n=0;n<30000;n+=100){t.detect(n);assert(t.active(n));}
 assert(t.active(29999));assert(t.remaining(29999)==1);t.detect(30000);
 assert(!t.active(30000));assert(t.blocked);
 for(uint32_t n=30100;n<180000;n+=100){t.detect(n);assert(!t.active(n));assert(t.blocked);}
 // Re-arm requires a continuous, valid clear interval. Bad samples cannot unlock it.
 t.observe(180000,false);t.expire(182999);assert(t.blocked);t.invalidate();t.expire(183000);assert(t.blocked);
 t.observe(184000,false);t.detect(185000);assert(t.blocked); // Person returns; clear interval restarts.
 t.observe(186000,false);t.expire(188999);assert(t.blocked);t.expire(189000);assert(!t.blocked);
 t.detect(189001);assert(t.active(189001));assert(t.firstDetection==189001);
 // Leaving near the deadline never adds a 3 s extension beyond the 30 s cap.
 t.reset();for(uint32_t n=0;n<=29000;n+=100)t.detect(n);t.observe(29100,false);assert(t.active(29999));t.expire(30000);assert(!t.active(30000));assert(t.blocked);
 // Brief absence refills the tail but does not restart the total-time budget.
 t.reset();t.detect(0);t.observe(1000,false);t.detect(2900);assert(t.firstDetection==0);assert(t.remaining(3000)==2900);
 for(uint32_t n=3000;n<30000;n+=100)t.detect(n);t.expire(30000);assert(t.blocked);
 // Settings changes cannot remove the cap, revive expired output, or bypass lockout.
 t.setHold(60000,30100);assert(t.holdMs==3000);assert(t.blocked);t.detect(30101);assert(!t.active(30101));
 t.reset();t.detect(0);t.setHold(1000,500);assert(t.active(999));t.expire(1000);assert(!t.active(1000));
 t.setHold(3000,1001);assert(!t.active(1001));
 // Both deadlines and the clear interval work through millis() wraparound.
 t.reset();t.holdMs=3000;t.detect(0xfffffff0UL);assert(t.active(0x20));assert(t.remaining(0x20)==2952);t.expire(0xba8);assert(!t.active(0xba8));
 t.reset();const uint32_t start=0xfffffff0UL;for(uint32_t n=0;n<30000;n+=100)t.detect(start+n);
 t.detect(start+30000);assert(t.blocked);t.observe(start+30100,false);t.expire(start+33099);assert(t.blocked);t.expire(start+33100);assert(!t.blocked);
 puts("PASS: 30 s total cap, 3 s departure limit, no immediate reopening, valid-clear re-arm, retrigger, settings bounds, clock wrap.");
}
