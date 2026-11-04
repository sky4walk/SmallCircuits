// LEGO 3010 – Stein 1 x 4 (ohne Löcher)
// Gleicher Aufbau und Ursprung wie Technic_1×4_3701.scad, nur ohne Technic-Löcher.
// LEGO is a trademark of the LEGO Group.
include <LEGO.scad>;

color( "lightgray" ) place(12, 0, 0) uncenter(1, 8) block(
            width=1,
            length=4,
            horizontal_holes=false
        );
