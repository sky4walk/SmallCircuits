dicke = 1;
quad  = 2;


col_blau = [0.15, 0.45, 0.85];
col_gelb = [0.95, 0.78, 0.10];
col_rot  = [0.95, 0.20, 0.20];
col_grau = [0.15, 0.15, 0.15];

module oneQuad(posX=0, posY=0, posZ=0) {
    translate([posX*quad, posY*quad, posZ*dicke])
        cube([quad, quad, dicke]);
}

module platte(sX,sY) {
    for (y = [0 : sY-1]) {
        for (x = [0 : sX-1]) {
            oneQuad(x, y);
        }
    }
}

module oneHole(posX=0, posY=0) {
    translate([posX*quad, posY*quad, -0.1])
        cube([quad, quad, dicke + 0.2]);
}

module blech_And(posX=0,posY=0,posZ=0) {
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_blau)
            difference() {
                platte(4,8);
                union() {
                    // Aussparung oben rechts
                    oneHole(2, 6);
                    oneHole(1, 6);
                    oneHole(2, 5);
                    // Aussparung unten links
                    oneHole(2, 2);
                    oneHole(1, 1);
                    oneHole(2, 1);
                }
            }
}
module blech_XOR1(posX=0,posY=0,posZ=0) {
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_blau)
            difference() {
                platte(4,8);
                union() {
                    // Aussparung oben rechts
                    oneHole(2, 6);
                    oneHole(1, 6);
                    oneHole(2, 5);
                    // Aussparung unten links
                    oneHole(1, 2);
                    oneHole(1, 1);
                    oneHole(2, 1);
                }
            }
}
module blech_XOR2(posX=0,posY=0,posZ=0) {
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_blau)
            difference() {
                platte(4,8);
                union() {
                    // Aussparung oben rechts
                    oneHole(2, 6);
                    oneHole(1, 6);
                    oneHole(1, 5);
                    // Aussparung unten links
                    oneHole(2, 2);
                    oneHole(1, 1);
                    oneHole(2, 1);
                }
            }
}
module blech_ausgabe(posX=0,posY=0,posZ=0) {
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_gelb)
            difference() {
                platte(4,5);
                union() {
                    oneHole(1, 3);
                    oneHole(2, 3);
                }
            }
}

module blech_takt(posX=0,posY=0,posZ=0) {
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_gelb)
            difference() {
                platte(4,5);
                union() {
                    oneHole(1, 1);
                    oneHole(2, 1);
                }
            }
}

module blech_eingabe(posX=0,posY=0,posZ=0) {
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_rot)
            difference() {
                platte(5,4);
                union() {
                    oneHole(1, 1);
                    oneHole(1, 2);
                }
            }
}

module stift(posX=0,posY=0,hoehe=0) {
    translate([posX*quad+quad/2, posY*quad+quad/2,0])
        color(col_grau) {
            stift_laenge = hoehe*dicke;
            cylinder(h=hoehe*dicke, r=quad/2-.1, $fn=50);
            translate([0, 0, -dicke])
                cylinder(h=dicke, r=quad, $fn=50);
        }
}

module Z1_AND(print=false) {
    if ( print == false ) {
        blech_eingabe(0,0);
        blech_eingabe(0,5);
        blech_And(-1,1,1);
        blech_takt(-1,6,2);
        blech_ausgabe(-1,-1,2);
        stift(1,2,4);
        stift(1,7,4);
    } else {
        blech_eingabe(0,0);
        blech_eingabe(0,5);
        blech_And(-5,1,0);
        blech_takt(6,5,0);
        blech_ausgabe(6,-1,0);
        translate([0,0,dicke]) {
            stift(11,2,4);
            stift(11,7,4);
        }
    }
}

module Z1_XOR(print=false) {
    if ( print == false ) {
        blech_eingabe(0,0);
        blech_eingabe(0,5);
        blech_XOR1(-1,1,1);
        blech_XOR2(-1,1,2);
        blech_takt(-1,6,3);
        blech_ausgabe(-1,-1,3);
        stift(1,2,5);
        stift(1,7,5);
    } else {
        blech_eingabe(0,0);
        blech_eingabe(0,5);
        blech_XOR1(-5,1,0);
        blech_XOR2(-10,1,0);
        blech_takt(6,5,0);
        blech_ausgabe(6,-1,0);
        translate([0,0,dicke]) {
            stift(11,2,5);
            stift(11,7,5);
        }
    }
}

Z1_AND(true);
