inner_width_of_collars = 60;
height_of_holder       = 200; 
depth_of_hook          = 40;
height_of_hook         = 30;
height_of_collars      = 30; 
thickness_of_holder    = 8;
thickness_of_collars   = 5;
thickness_of_bottom    = 5; 
$fn=100;

BASE_WIDTH            = inner_width_of_collars + 1;
OUTER_DIAMETER        = BASE_WIDTH + thickness_of_collars * 2;
HOLDER_POSITION       = BASE_WIDTH / 2 + thickness_of_holder / 2;
width_of_holder       = OUTER_DIAMETER;
upper_collar_position = height_of_holder - height_of_collars; 

module Holder() {
    translate([0, HOLDER_POSITION, height_of_holder / 2]) {
        cube(size = [width_of_holder, thickness_of_holder, height_of_holder], center = true);
    }
    difference() {
        translate([0,-1,(thickness_of_bottom + height_of_collars)/2])            
            cube([OUTER_DIAMETER,OUTER_DIAMETER,thickness_of_bottom + height_of_collars],true);
        translate([0,-1,thickness_of_bottom])
            cylinder(h=height_of_collars+.1 , d=BASE_WIDTH);
    }
    translate([0, -1, upper_collar_position]) {
        difference() 
        {
            translate([0,0,height_of_collars/2])            
                cube([OUTER_DIAMETER,OUTER_DIAMETER,height_of_collars],true);
            translate([0,0,-.1])
                cylinder(h=height_of_collars+.2, d=BASE_WIDTH);
        }
    }       
    translate([0, (BASE_WIDTH + depth_of_hook) / 2 + thickness_of_holder, height_of_holder - thickness_of_holder / 2]) {
        cube([width_of_holder, depth_of_hook, thickness_of_holder], center = true);
    }
    translate([0, BASE_WIDTH / 2 + depth_of_hook + thickness_of_holder * 1.5, height_of_holder - height_of_hook / 2 - thickness_of_holder / 2]) {
        cube([width_of_holder, thickness_of_holder, height_of_hook + thickness_of_holder], true);
    } 
}

Holder();
