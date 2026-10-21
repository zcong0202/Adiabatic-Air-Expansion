// Millimetres. Approximate hull representation; exact BRep/STL from make_cad.py.
wall=2.4; W=140; H=80; OD=100; L=205; $fn=96;
module shape(r,w,h) {
 cylinder(h=30,r=r);
 hull(){translate([0,0,29]) cylinder(h=1,r=r); translate([-w/2,-h/2,190]) cube([w,h,1]);}
 translate([-w/2,-h/2,190]) cube([w,h,15]);
}
difference(){shape(OD/2,W+2*wall,H+2*wall);translate([0,0,-0.1])shape(OD/2-wall,W,H);translate([-W/2,-H/2,204.8])cube([W,H,1]);}
