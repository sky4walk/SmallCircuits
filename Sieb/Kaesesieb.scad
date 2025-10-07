/*
 * sieb mit pyramidalen loechern
 * verhaeltnis wand:oeffnung 1:3
 * 
 * @param x the length
 * @param y the width
 * @param d the thickness of the sieve
 * @param s the width of the space between the holes
 * @param l the length and width of the holes 
 * @param rd the thickness of the frame
 * @param r the height of the frame
 * @param zr the zylinder radius
 * @param zh the zylinder hight
 */
module sieb(x, y, d, s, l, rd, r, zr, zh)
{
	nx = floor((x - 2*rd - 2*s) / (s + l));
	ny = floor((y - 2*rd - 2*s) / (s + l));
	
	difference()
	{
		union()
		{
			translate([-x/2, -y/2, 0])      cube([x, y, d]);			
			translate([-x/2, -y/2, 0])      cube([x, rd, r]);			
			translate([-x/2, y/2 - rd, 0])  cube([x, rd, r]);
			translate([-x/2, -y/2, 0])  	cube([rd, y, r]);
			translate([x/2 - rd, -y/2, 0])	cube([rd, y, r]);
		}
		
		translate([-nx/2*(s+l), -ny/2*(s+l), 0])
		for (dx = [0:nx])
			for (dy = [0:ny])
				translate([(s+l)*dx, (s+l)*dy, d])
                    polyhedron(
						points=	[ [l,l,-1.5*l],[l,-l,-1.5*l],[-l,-l,-1.5*l],[-l,l,-1.5*l],[0,0,1.5*l] ], 
						faces =	[ [0,1,4],[1,2,4],[2,3,4],[3,0,4],[1,0,3],[2,1,3] ]
 					);
	}
    translate([x/2-zr, y/2-zr, -zh+d])   cylinder(zh, zr, zr,$fn=50);
    translate([x/2-zr, -y/2+zr, -zh+d])  cylinder(zh, zr, zr,$fn=50);
    translate([-x/2+zr, y/2-zr, -zh+d])  cylinder(zh, zr, zr,$fn=50);
    translate([-x/2+zr, -y/2+zr, -zh+d]) cylinder(zh, zr, zr,$fn=50);
}

sieb(x=120, y=120, d=3, s=2, l=6, rd=4, r=3,zr=5,zh=15);

