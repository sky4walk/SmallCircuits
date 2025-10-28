schlauchD = 22;
schlauchT =  2;
schlauchE = 15;
halterL   = 40;
halterB   = 10;
halterR   = 10;
halterNr  =  5;
wallMntD  = 10;
screwM    = 5;
new = true;


module prism(l, w, h) {
    polyhedron(// pt      0        1        2        3        4        5
               points=[[0,0,0], [0,w,h], [l,w,h], [l,0,0], [0,w,0], [l,w,0]],
               // top sloping face (A)
               faces=[[0,1,2,3],
               // vertical rectangular face (B)
               [2,1,4,5],
               // bottom face (C)
               [0,3,5,4],
               // rear triangular face (D)
               [0,4,1],
               // front triangular face (E)
               [3,2,5]]
               );}

module Halter() {
    translate([0,0,-halterL]) 
        cube([halterB,schlauchD+schlauchE+schlauchT,halterL]);
    if ( true == new ) {
        translate([0,schlauchD+schlauchE,-halterL]) 
            cube([halterB,halterR,halterR+halterL]);   
    } else {
        prism(halterB, schlauchD+schlauchE+schlauchT, halterR);
    }
}

for ( i = [0:halterNr] ) {
    translate([(halterB+schlauchD+schlauchT)*i,0,0]) Halter();
}

translate([0,-halterB,-halterL])
difference() 
{
    cube([halterNr*(halterB+schlauchD+schlauchT)+halterB,wallMntD,halterL]);
    rotate([90,0,0]){
        d2 = (halterB+schlauchD+schlauchT)*(halterNr-1);
        translate([schlauchD/2+halterB,halterL*3/4,-wallMntD-schlauchT/2])
            cylinder(wallMntD+schlauchT,screwM/2,screwM/2,$fn=50);
        translate([schlauchD/2+halterB,halterL/4,-wallMntD-schlauchT/2])
            cylinder(wallMntD+schlauchT,screwM/2,screwM/2,$fn=50);
        translate([schlauchD/2+halterB+d2,halterL*3/4,-wallMntD-schlauchT/2])
            cylinder(wallMntD+schlauchT,screwM/2,screwM/2,$fn=50);
        translate([schlauchD/2+halterB+d2,halterL/4,-wallMntD-schlauchT/2])
            cylinder(wallMntD+schlauchT,screwM/2,screwM/2,$fn=50);
    }
}

echo( "Laenge:",(halterB+schlauchD+schlauchT)*(halterNr) );




