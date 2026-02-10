include <Technic.scad>;

union() {
color( "white" )  technic_beam( length = 3, axle_holes = [1,3], height = 1/2  );
color( "white" )  rotate([0,0,90]) technic_beam( length = 3, axle_holes = [1,3], height = 1/2  );
}