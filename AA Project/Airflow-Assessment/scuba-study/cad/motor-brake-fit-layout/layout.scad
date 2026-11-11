// STATIC FIT CHECK ONLY. Example dimensions, not actual AM0701 measurements.
// No pressure component or powered torque coupling is defined here.
// Units mm. Metal fasteners assumed. No operating load/temperature rating.
part="assembly"; // assembly, base, cradle, bearing_blank, brake_blank, coupler_envelope
body_example_d=80;
axis_height=100;
$fn=64;
module base(){difference(){translate([0,-90,-8])cube([300,180,8]);
    for(x=[30,100,190,275])for(y=[-60,60])translate([x-7,y-2.75,-10])cube([14,5.5,12]);
    for(x=[225,245])translate([x,60,-10])cylinder(d=5.5,h=12);}}
module cradle(){difference(){union(){translate([-8,-50,0])cube([16,100,100]);translate([-18,-70,0])cube([36,140,8]);}
    translate([0,0,axis_height])rotate([0,90,0])cylinder(d=body_example_d+2,h=30,center=true);
    for(y=[-60,60])translate([0,y,-1])cylinder(d=5.5,h=12);}}
module bearing_blank(){difference(){union(){translate([-6,-35,0])cube([12,70,100]);translate([-18,-70,0])cube([36,140,8]);}
    for(y=[-60,60])translate([0,y,-1])cylinder(d=5.5,h=12);}}
module brake_blank(){difference(){union(){translate([-6,-17,0])cube([12,34,110]);translate([-18,-30,0])cube([36,60,8]);}
    for(x=[-10,10])translate([x,0,-1])cylinder(d=5.5,h=12);}}
module coupler_envelope(){ // solid envelope, deliberately no shaft bores/clamp: NOT A COUPLER
    rotate([0,90,0])cylinder(d=36,h=34,center=true);}
if(part=="base")base();
else if(part=="cradle")cradle();
else if(part=="bearing_blank")bearing_blank();
else if(part=="brake_blank")brake_blank();
else if(part=="coupler_envelope")assert(false,"Envelope only. Measured interfaces and powered-use validation missing.");
else if(part=="assembly"){
    color("lightgray")base();
    for(x=[30,100])translate([x,0,0])color("slategray")cradle();
    for(x=[190,275])translate([x,0,0])color("lightblue")bearing_blank();
    translate([235,60,0])color("lightblue")brake_blank();
    %translate([68,0,axis_height])rotate([0,90,0])cylinder(d=body_example_d,h=110,center=true);
    %translate([160,0,axis_height])coupler_envelope();
    %translate([235,0,axis_height])rotate([0,90,0])cylinder(d=160,h=3,center=true);
}
