// Parametric Stabilo Boss Holder
// All measurements in mm

rotation = true;
pen_width = 28.8;
pen_thick = 18.8;
wall = 3.0;
depth = 45.0;
spacing = 5.0;
num_pens = 3;

block_width = (true==rotation) ? 
                num_pens * (pen_thick + spacing) - spacing + (2 * wall) : 
                num_pens * (pen_width + spacing) - spacing + (2 * wall) ;
block_depth = (true==rotation) ? pen_width + (2 * wall) : pen_thick + (2 * wall);
block_height = depth + wall;

module pen_profile() {
    // Rounded rectangle shape mimicking the Stabilo Boss body
    hull() {
        translate([pen_thick/2, pen_thick/2, 0]) cylinder(h=depth+5, r=pen_thick/2, $fn=50);
        translate([pen_width - pen_thick/2, pen_thick/2, 0]) cylinder(h=depth+5, r=pen_thick/2, $fn=50);
    }
}


difference() {
    // Main body block
    cube([block_width, block_depth, block_height]);
    
    // Cutouts for the highlighters
    for (i = [0 : num_pens - 1]) {
        if ( true == rotation ) {
            translate([pen_thick + wall + i * (pen_thick + spacing), wall, wall])
                rotate([0,0,90]) pen_profile();
        } else {
            translate([wall + i * (pen_width + spacing), wall, wall])
                pen_profile();
        }
    }
}


