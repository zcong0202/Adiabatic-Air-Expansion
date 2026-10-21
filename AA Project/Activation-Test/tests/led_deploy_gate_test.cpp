#include <assert.h>
#include "../aa_presence_led_deploy/ActivationLogic.h"
int main(){
 ActivationGate gate;
 assert(!gate.update(0,true,true,true));
 assert(gate.update(150,true,true,true));
 assert(gate.update(60150,true,true,true));
 assert(gate.update(120150,true,true,true));
 assert(!gate.update(120151,false,true,true));
 assert(!gate.update(130000,true,true,true));
 assert(gate.update(130150,true,true,true));
 assert(gate.update(130151,true,false,false));
 assert(!gate.update(130351,true,false,false));
 gate.reset();
 assert(!gate.update(0xFFFFFF00u,true,true,true));
 assert(gate.update(0xFFFFFF96u,true,true,true));
 assert(gate.update(50u,true,true,true));
}
