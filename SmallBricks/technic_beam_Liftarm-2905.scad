// ============================================================
//  LEGO Technic 2905 – Liftarm Dreieck 5 x 3 x 0.5
//  (Technic Beam 5 x 3 x 0.5 Liftarm Triangle)
//
//  Form nach der LDraw-Geometrie von 2905.dat:
//   - unten ein Steg mit 5 Löchern im 8-mm-Raster
//       Loch 1 und 5: Achslöcher
//       Loch 2, 3, 4: Pinlöcher
//   - in der Mitte ein Arm nach oben mit 2 Pinlöchern
//   - die Flächen zwischen Steg und Arm sind geschlossen
//     (Schräge mit Steigung 1:2, tangential an die Endrundungen)
//
//  Koordinaten wie die übrigen Liftarme aus Technic.scad:
//   Ursprung unter der Mitte von Loch 1, Steg entlang +X,
//   Arm entlang +Y, Dicke entlang +Z (0 .. 3,9 mm).
//
//  LEGO and Technic are trademarks of the LEGO Group.
// ============================================================

include <Technic.scad>;

/* [Optionen] */
// Pinlöcher mit Senkung für den Pinkragen (wie technic_beam)
pin_senkung = true;

module technic_liftarm_dreieck_2905( senkung = true ) {
	p = technic_beam_hole_spacing;                   // 8 mm
	h = technic_height_in_mm / 2;                    // 3,9 mm (halbe Dicke)
	d = technic_pin_connector_outer_diameter;        // Außenbreite 7,36 mm
	e = EXTENSION_FOR_DIFFERENCE;

	achs = [ [ 0, 0 ], [ 4 * p, 0 ] ];
	pins = [ [ p, 0 ], [ 2 * p, 0 ], [ 3 * p, 0 ], [ 2 * p, p ], [ 2 * p, 2 * p ] ];

	difference() {
		// --- Außenkontur ---
		linear_extrude( h ) union() {
			// Dreieck: Hülle der beiden Endrundungen und der unteren Armrundung
			hull() for ( c = [ [ 0, 0 ], [ 4 * p, 0 ], [ 2 * p, p ] ] ) translate( c ) circle( d = d );
			// Arm nach oben
			hull() for ( c = [ [ 2 * p, 0 ], [ 2 * p, 2 * p ] ] ) translate( c ) circle( d = d );
		}

		// --- Pinlöcher ---
		for ( c = pins ) translate( [ c[0], c[1], 0 ] ) {
			translate( [ 0, 0, -e / 2 ] ) cylinder( d = technic_hole_diameter, h = h + e );
			if ( senkung ) {
				// Senkung oben und unten wie in technic_pin_connector()
				ds = d - 2 * technic_pin_connector_shoulder_wall_thickness;
				translate( [ 0, 0, -e ] ) cylinder( d = ds, h = technic_pin_connector_shoulder_depth + e );
				translate( [ 0, 0, h - technic_pin_connector_shoulder_depth ] ) cylinder( d = ds, h = technic_pin_connector_shoulder_depth + e );
			}
		}

		// --- Achslöcher an den Enden ---
		for ( c = achs ) translate( [ c[0], c[1], 0 ] ) technic_axle_hole( height = 1 );
	}
}

color( "green" ) technic_liftarm_dreieck_2905( senkung = pin_senkung );
