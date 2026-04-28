$fn = 80;   

// 1 : Spuehlmaschine
// 2 : Spuelbecken
auswahl = 2;

use <threadlib.scad>;

da_spuelbecken      = 32;
da_spuelmaschine    = 25.5;
l_steckrohr         = 30;
d_wand              = 5;
d_durchlass         = 8;


module rohr(da,dw,l) {
    difference() {
        cylinder(l, da/2, da/2);
        translate([0,0,-.1])
            cylinder(l+.2, d_durchlass, d_durchlass);
    }
    translate([0,0,l]) cylinder(dw, da/2, da/2);
}

difference() {
    union() {
        if ( 1 == auswahl )
            rohr(da_spuelmaschine,d_wand,l_steckrohr);
        else
            rohr(da_spuelbecken,d_wand,l_steckrohr);
        translate([0,0,l_steckrohr+d_wand]) bolt("G3/4", turns=10);
    }
    cylinder(l_steckrohr+30, d_durchlass, d_durchlass);
}
