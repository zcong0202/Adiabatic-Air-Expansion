#pragma once
#include <stdint.h>
// One activation: at most 30 s total, at most 3 s after the last detection.
// At the total-time limit, wait for 3 s of valid empty-zone readings to re-arm.
class HoldTimer {
 public:
  static const uint32_t MAX_ON_MS=30000, MAX_DEPARTURE_MS=3000, REARM_MS=3000;
  uint32_t holdMs=3000, firstDetection=0, lastDetection=0, clearSince=0;
  bool seen=false, blocked=false, clearing=false;
  uint32_t departureMs() const {return holdMs>MAX_DEPARTURE_MS?MAX_DEPARTURE_MS:holdMs;}
  void reset(){seen=false;blocked=false;clearing=false;}
  void invalidate(){clearing=false;} // Missing/invalid readings cannot prove the zone is empty.
  void expire(uint32_t now){
    if(seen && uint32_t(now-firstDetection)>=MAX_ON_MS){seen=false;blocked=true;}
    if(seen && uint32_t(now-lastDetection)>=departureMs())seen=false;
    if(blocked && clearing && uint32_t(now-clearSince)>=REARM_MS){blocked=false;clearing=false;}
  }
  void setHold(uint32_t value,uint32_t now){expire(now);holdMs=value>MAX_DEPARTURE_MS?MAX_DEPARTURE_MS:value;expire(now);}
  bool active(uint32_t now) const {
    return seen && !blocked && uint32_t(now-firstDetection)<MAX_ON_MS && uint32_t(now-lastDetection)<departureMs();
  }
  uint32_t remaining(uint32_t now) const {
    if(!active(now))return 0;
    uint32_t total=MAX_ON_MS-uint32_t(now-firstDetection),tail=departureMs()-uint32_t(now-lastDetection);
    return total<tail?total:tail;
  }
  void observe(uint32_t now,bool present){
    expire(now);
    if(present){
      clearing=false;lastDetection=now;
      if(!blocked){if(!seen)firstDetection=now;seen=true;}
    }else if(!clearing){clearing=true;clearSince=now;}
  }
  void detect(uint32_t now){observe(now,true);}
};
