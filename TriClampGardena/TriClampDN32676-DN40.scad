// DN40 1,5Zoll DIN 32676
// 1 : schweisstutzen
// 2 : gardena adapter
// 3 : IG1/2 
// 4 : AG1/2
type = 4;
draft = false;

use <threadlib/threadlib.scad>;

d1 = 38;
d2 = 41;
d3 = 50.5; // Flansch aussen
d4 = 43.5; // Ring
l3 = 21.5;
l4 = 2.85;
a1 = 20.0;
r1 = 1.2;
r2 = 0.8;
r3 = 3.0;
r4 = 8.8;

$fs = draft ? 3 : 0.25;
$fa = 2;
$fn = 128;



module GardenaConnector (inner_dia)
{
    inner_radius = inner_dia / 2;
    plate_thickness = 1;

    root_radius = 19.60 / 2;
    neck_radius = 13.94 / 2;
    collar_radius = 16.82 / 2;
    tip_radius = 15.68 / 2;
    channel_depth = 2.10;
    channel_radius = tip_radius - channel_depth;
    tip_chamfer_radius = 2.5;
    tip_chamfer_x = tip_radius - tip_chamfer_radius;

    channel_length = 2.90;

    ttf = 14.68;
    root_y =         0;
    neck_y =         18.71 - ttf;
    collar_out_y =   26.72 - ttf;
    collar_flat_y =  27.58 - ttf;
    collar_in_y =    29.64 - ttf;
    tip_y =          30.11 - ttf; 
    channel_y =      32.88 - ttf;
    channel_end_y =  channel_y + channel_length;
    end_y =          38.94 - ttf;
    tip_chamfer_y = end_y - tip_chamfer_radius;

    module quarter_circle(r)
    {
      intersection()
      {
        circle(r=r);
        square([r,r]);
      }
    }

    module filler(r)
    {
      difference()
      {
        square([r,r]);
        translate([r,r])
          circle(r=r);
      }
    }

    module profile ()
    {
        polygon ([
          [inner_radius,    -plate_thickness],
          [inner_radius,    -plate_thickness],
          [inner_radius,    0],
          [root_radius,     0],
          [root_radius,     neck_y],
          [neck_radius,     neck_y],
          [neck_radius,     collar_out_y],
          [collar_radius,   collar_flat_y],
          [collar_radius,   collar_in_y],
          [tip_radius,      tip_y],
          [tip_radius,      channel_y],
          [channel_radius,  channel_y],
          [channel_radius,  channel_end_y],
          [tip_radius,      channel_end_y],
          [tip_radius,      tip_chamfer_y],
          [tip_chamfer_x,   tip_chamfer_y],
          [tip_chamfer_x,   end_y],
          [inner_radius,    end_y],
        ]);

        translate ([neck_radius, neck_y])
            filler (r= root_radius - neck_radius);
        translate ([channel_radius, channel_y])
            filler (r= channel_length/2);
        translate ([channel_radius, channel_end_y])
            mirror ([0, 1])
                filler (r= channel_length/2);
        translate ([tip_chamfer_x, tip_chamfer_y])
            quarter_circle (tip_chamfer_radius);
    }

    rotate_extrude ()
        profile ();
}

module clamp_raw(opener)
{
    h1 = d3/2 / tan(90-a1);
    difference() {
        union() {
            cylinder(h=l4,r1=d3/2,r2=d3/2);
            translate ([0, 0, l4]) cylinder(h=h1,r1=d3/2,r2=0);
        }
        translate ([0, 0, -0.1]) cylinder(h=l3+0.2,r1=opener,r2=opener);
        rotate_extrude() translate([d4/2, 0, 0]) circle(r1); 
        
    }
}
module clamp_flansch()
{
    clamp_raw(d1/2);
    difference() {
        cylinder(h=l3+l4,r1=d2/2,r2=d2/2);
        translate ([0, 0, -0.1]) cylinder(h=l3+l4+.2,r1=d1/2,r2=d1/2);
    }    
}

if ( 1 == type )
{
    clamp_flansch();
} 
else if ( 2 == type )
{
    posGardena=6;
    translate ([0, 0,posGardena])GardenaConnector (r4);
    clamp_raw(r4/2);
}
else if ( 3 == type )
{
    posGardena=6;
    translate ([0, 0,posGardena])
        nut("G1/2", turns=10, Douter=25);
    clamp_raw(r4);
}
else if ( 4 == type )
{
    infill=6;
    difference() 
    {
        union()
        {
            translate ([0, 0,infill])
                bolt("G1/2", turns=10);
            clamp_raw(infill);
        }
        translate ([0, 0, -0.1]) cylinder(h=l3+l4+1.2,r1=infill,r2=infill);
    }    
}
