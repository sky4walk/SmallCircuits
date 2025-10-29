// Kaesekorb

laenge   = 100;
breite   = laenge;
hoehe    = 20;
dicke    = 3;
abstandD = 5;
loecherD = 2;
korbH    = 100;
radSteps = 5;

PRESSDECKEL = false;
FUESSE      = false;
RAND        = true;
SIEB        = true;

stepsX = ( breite - loecherD ) / (loecherD * 2);
stepsY = ( laenge - loecherD ) / (loecherD * 2);
stepsZ = korbH / (loecherD * 2);


if ( SIEB ) {
    difference() {
        cube([laenge,breite,dicke]);
           
        for ( j = [0:1:stepsY-1] ) {
            for ( i = [0:1:stepsX-1] ) {
                translate([loecherD*2*(1+i),loecherD*2*(1+j),-.1])
                    cylinder(h=dicke+0.2,d=loecherD,$fn=50);    
                
            }
        }
    }
}

if ( FUESSE ) {
    //fuesse
    translate([breite/4  ,laenge/4  ,0]) cylinder(h=hoehe+dicke,d=abstandD*2,$fn=50);
    translate([breite/4*3,laenge/4*3,0]) cylinder(h=hoehe+dicke,d=abstandD*2,$fn=50);
    translate([breite/4  ,laenge/4*3,0]) cylinder(h=hoehe+dicke,d=abstandD*2,$fn=50);
    translate([breite/4*3,laenge/4  ,0]) cylinder(h=hoehe+dicke,d=abstandD*2,$fn=50);
}

if ( RAND ) { 
//Rand
    translate([breite/2,breite/2,-korbH]) {
        difference() 
        {
            cylinder(h=korbH,d=breite,$fn=90);
            translate([0,0,-0.1])
                cylinder(h=korbH+.11,d=breite-dicke,$fn=90);
            
            for ( j = [0:1:stepsZ] ) {
                translate([0,0,korbH-loecherD*1.5*(1+j)]) rotate([0,90,0]){
                    for ( i = [0:radSteps:360] ) {
                        rotate([i,0,0]) cylinder(h=breite/2+2,d=loecherD,$fn=50);
                    }
                }
            }

        }
    }
}

if ( PRESSDECKEL )
{
//pressdeckel
    translate([-breite/2,breite/2,-0.1])
                cylinder(h=dicke,d=breite-dicke-0.2,$fn=90);
}
