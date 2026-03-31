dicke = 1;
quad  = 2;
lenInput = 8;


col_blau  = [0.15, 0.45, 0.85];
col_gelb  = [0.95, 0.78, 0.10];
col_rot   = [0.95, 0.20, 0.20];
col_grau  = [0.15, 0.15, 0.15];
col_gruen = [0.0, 0.50, 0.0];

module oneQuad(posX=0, posY=0, posZ=0) {
    translate([posX*quad, posY*quad, posZ*dicke])
        cube([quad, quad, dicke]);
}

module oneQuad_tol(posX=0, posY=0, posZ=0,dTol=.1,xyTol=.1) {
    translate([posX*quad+xyTol, posY*quad+xyTol, posZ*dicke])
        cube([quad-xyTol*2, quad-xyTol*2, dicke+dTol]);
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
    oLen = 3;
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_blau)
            difference() {
                translate([0,-quad*oLen,0])
                    platte(4,8+oLen*2);
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
    oLen = 3;
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_blau)
            difference() {
                translate([0,-quad*oLen,0])
                    platte(4,8+oLen*2);
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
    oLen = 3;
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_blau)
            difference() {
                translate([0,-quad*oLen,0])
                    platte(4,8+oLen*2);
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

module blech_SW(posX=0,posY=0,posZ=0) {
    oLen = 3;
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_blau)
            difference() {
                translate([0,-quad*oLen,0])
                    platte(4,8+oLen*2);
                union() {
                    // Aussparung oben rechts
                    oneHole(2, 6);
                    oneHole(1, 6);
                    oneHole(2, 5);
                    // Aussparung unten links
                    //oneHole(1, 1);
                    oneHole(2, 1);
                }
            }
}
    
module blech_ausgabe(posX=0,posY=0,posZ=0) {
    oLen = 2;
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_gelb)
            difference() {
                translate([0,-quad*(lenInput-3),0])
                    platte(4,3+lenInput);
                union() {
                    oneHole(1, 4);
                    oneHole(2, 4);
                }
            }
}

module blech_takt(posX=0,posY=0,posZ=0) {
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_gelb)
            difference() {
                platte(4,3+lenInput);
                union() {
                    oneHole(1, 1);
                    oneHole(2, 1);
                }
            }
}

module blech_eingabe(posX=0,posY=0,posZ=0) {
    oLen = 2;
    translate([(posX-1)*quad, posY*quad,posZ*dicke])
        color(col_rot)
            difference() {
                translate([-quad*oLen,0,0])
                    platte(5+lenInput+oLen,4);
                union() {
                    oneHole(2, 1);
                    oneHole(2, 2);
                }
            }
}

module stift(posX=0,posY=0,hoehe=0) {
    tol = .2;
    translate([posX*quad+quad/2, posY*quad+quad/2,0])
        color(col_grau) {
            stift_laenge = hoehe*dicke;
            cylinder(h=hoehe*dicke, r=quad/2-.1, $fn=50);
            translate([0, 0, -dicke+tol])
                cylinder(h=dicke-tol, r=quad, $fn=50);
        }
}

module gehaeuse_boden(type,posX=0,posY=0,posZ=0) {
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_gruen) {
            translate([-quad*2,-quad,-dicke*2]) platte(6,11);

            translate([-quad*2,-quad,-dicke]) platte(6,1);
            translate([-quad*2,quad*9,-dicke]) platte(6,1);
            translate([-quad*2,quad*4,-dicke]) platte(6,1);

            translate([-quad*2,-quad,-dicke]) platte(1,11);
            translate([quad*3,-quad,-dicke]) platte(1,11);
                    
            oneQuad_tol(-2,-1);
            oneQuad_tol(3,-1);
            oneQuad_tol(-2,-1,1);
            oneQuad_tol(3,-1,1);
            oneQuad_tol(-2,-1,2);
            oneQuad_tol(3,-1,2);

            oneQuad_tol(-2,4);
            oneQuad_tol(3,4);
            oneQuad_tol(-2,4,1);
            oneQuad_tol(3,4,1);
            oneQuad_tol(-2,4,-1);
            oneQuad_tol(3,4,-1);
            oneQuad_tol(-2,4,2);
            oneQuad_tol(3,4,2);

            oneQuad_tol(-2,9);
            oneQuad_tol(3,9);
            oneQuad_tol(-2,9,1);
            oneQuad_tol(3,9,1);
            oneQuad_tol(-2,9,2);
            oneQuad_tol(3,9,2);

            if ( type == 2) {
                oneQuad_tol(-2,4,3);
                oneQuad_tol(3,4,3);
                oneQuad_tol(-2,-1,3);
                oneQuad_tol(3,-1,3);
                oneQuad_tol(-2,9,3);
                oneQuad_tol(3,9,3);
            }

        }
}

module gehaeuse_deckel_and(posX=0,posY=0,posZ=0) {
    translate([posX*quad, posY*quad,posZ*dicke])
        color(col_grau) {
            translate([-quad*2,-quad,dicke*3+.1]) platte(6,1);
            translate([-quad*2,quad*4,dicke*3+.1]) platte(6,1);
            translate([-quad*2,quad*9,dicke*3+.1]) platte(6,1);
        }
}

module Z1_AND(print=false,A=false,B=false,t=false, gehause=false) {
    if ( print == false ) {
        if ( gehause ) {
            gehaeuse_boden(1);
//            gehaeuse_deckel_and();
        }

        inA = (A) ? 1 : 0;
        inB = (B) ? 1 : 0;
        and = (t && A ) ? 1 : 0;
        s1  = (t) ? 1 : 0;
        s2  = (t && A && B) ? 1 : 0;
        
        blech_eingabe(-inB,0);
        blech_eingabe(-inA,5);
        blech_And(-1,1-and,1);
        blech_takt(-1,6-s1,2);
        blech_ausgabe(-1,-2-s2,2);
        stift(1-inB,2-s2,4);
        stift(1-inA,7-s1,4);
    } else {
        gehaeuse_boden(1,3,11,2);
        blech_eingabe(3,0);
        blech_eingabe(3,5);
        blech_And(-5,1,0);
        blech_takt(-10,7,0);
        blech_ausgabe(-10,-1,0);
        translate([0,0,dicke]) {
            stift(17,2,4);
            stift(17,7,4);
        }
    }
}

function xor(a, b) = (a || b) && !(a && b);

module Z1_XOR(print=false,A=false,B=false,t=false, gehause=false) {
    if ( print == false ) {
        if ( gehause ) {
            gehaeuse_boden(2);
//            gehaeuse_deckel_and();
        }
        
        inA = (A) ? 1 : 0;
        inB = (B) ? 1 : 0;
        xor1 = (t && (xor(A,B) || A)) ? 1 : 0;
        xor2 = (t && (xor(A,B))) ? 1 : 0;
        s1  = (t) ? 1 : 0;
        s2  = (t && xor(A,B) ) ? 1 : 0;
        
        blech_eingabe(-inB,0);
        blech_eingabe(-inA,5);
        blech_XOR1(-1,1-xor1,1);
        blech_XOR2(-1,1-xor2,2);
        blech_takt(-1,6-s1,3);
        blech_ausgabe(-1,-2-s2,3);
        stift(1-inB,2-s2,5);
        stift(1-inA,7-s1,5);
    } else {
        gehaeuse_boden(1,3,11,2);
        blech_eingabe(0,0);
        blech_eingabe(0,5);
        blech_XOR1(-9,1,0);
        blech_XOR2(-15,1,0);
        blech_takt(13,6,0);
        blech_ausgabe(13,-1,0);
        translate([0,0,dicke]) {
            stift(18,2,5);
            stift(18,7,5);
        }
    }
}

module Z1_Switch(print=false,A=false,t=false, gehause=false) {
    if ( print == false ) {
        if ( gehause ) {
            gehaeuse_boden(2);
//            gehaeuse_deckel_and();
        }
        
        inA = (A) ? 1 : 0;
        s1  = (t) ? 1 : 0;
        s2  = (t && A) ? 1 : 0;
        
        blech_eingabe(-inA,5);
        stift(1-inA,7-s1,5);
        stift(1,2-s2,5);
        blech_SW(-1,1-s2,1);
        blech_takt(-1,6-s1,2);
        blech_ausgabe(-1,-2-s2,2);
    } else {
        gehaeuse_boden(1,3,7,2);
        blech_eingabe(0,0);
        blech_SW(-4,9,0);
        blech_ausgabe(13,1,0);
        blech_takt(13,9,0);
        translate([0,0,dicke]) {
            stift(10,10,5);
            stift(10,13,5);
        }
    }
}

Z1_XOR(false,true,true,true,true);