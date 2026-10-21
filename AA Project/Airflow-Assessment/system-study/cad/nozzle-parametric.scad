// Flow body only. Millimetres. No fitted source connector or pressure rating.
D=28; halfAngle=5; inlet=8; wall=2; inletLand=15; outletLand=10;
cone=(D-inlet)/2/tan(halfAngle); $fn=180;
module body(w) {
 cylinder(h=inletLand,r=inlet/2+w);
 translate([0,0,inletLand]) cylinder(h=cone,r1=inlet/2+w,r2=D/2+w);
 translate([0,0,inletLand+cone]) cylinder(h=outletLand,r=D/2+w);
}
difference() { body(wall); translate([0,0,-0.01]) cylinder(h=inletLand+.02,r=inlet/2);
 translate([0,0,inletLand]) cylinder(h=cone,r1=inlet/2,r2=D/2);
 translate([0,0,inletLand+cone-.01]) cylinder(h=outletLand+.02,r=D/2); }
