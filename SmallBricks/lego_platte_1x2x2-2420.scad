include <LEGO.scad>;
color( "green" ) 
        uncenter(1, 0, 0) 
            rotate([0, 0, 0]) 
                block(
                    dual_sided=false,
                    width=1,
                    length=2,
                    height=1/3
                );
color( "green" ) 
        uncenter(0, 1, 0) 
            rotate([0, 0, 90]) 
                block(
                    dual_sided=false,
                    width=1,
                    length=2,
                    height=1/3
                );                