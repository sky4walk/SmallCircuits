/**
 * LEGO and Technic are trademarks of the LEGO Group.
 *
 * For standard LEGO-compatible bricks, see LEGO.scad. This module
 * is specifically for parts without studs, like gears and axles.
 *
 * Copyright (c) 2025 Christopher Finke (cfinke@gmail.com)
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
/***
 * @module Technic.scad
 * An OpenSCAD Technic-compatible piece generator. It currently supports generation of beams, axles, pin connectors, axle pins, elbows, and gears.
 */
$fa = 1; $fs = 0.05;

// LEGO.scad values.
stud_spacing = 8; // Matches LEGO.stud_spacing
stud_diameter = 4.85; // Matches LEGO.stud_diameter
stud_height = 1.8; // Matches LEGO.stud_height
stud_inner_diameter = 3.1; // Matches LEGO.hollow_stud_inner_diameter
stud_outer_diameter = 4.85; // Matches LEGO.stud_diameter

// Global Technic.scad values.
technic_height_in_mm = 7.8; // Vertically-oriented technic pieces (like pin connectors) use this
technic_hole_diameter = 4.85; // Matches LEGO.stud_diameter
technic_axle_interference_fit_ratio = 1.022;

technic_axle_and_pin_connector_face_thickness = 1; // You would think this would match technic_bush_shoulder_height, but it doesn't really.

technic_axle_spline_thickness = 1.8;
technic_axle_spline_width = 4.85; // Matches LEGO.stud_diameter
technic_axle_spline_corner_radius = 0.4;
technic_axle_cross_section_radius = 1;
technic_axle_stop_thickness = 0.7; // Matches technic_pin_collar_thickness
technic_axle_stop_diameter = 5.9;
technic_axle_stud_height = 1.8; // Matches LEGO.stud_height
technic_axle_stud_inner_diameter = 3.1; // Matches LEGO.hollow_stud_inner_diameter
technic_axle_stud_outer_diameter = 4.85; // Matches LEGO.stud_diameter
technic_axle_notch_height = 1.3; // Matches technic_bush_shoulder_height
technic_axle_notch_diameter = 4.2;

technic_axle_connector_outer_diameter = 7.36; // @todo Measure IRL
technic_axle_connector_ridged_inner_diameter = 6.5; // @todo Measure IRL
technic_axle_connector_ridge_thickness = 0.6; // @todo Measure IRL

technic_bar_connector_outer_diameter = 7.36; // @todo Measure IRL
technic_bar_connector_inner_diameter = 3.2; // @todo Measure IRL

technic_bush_big_diameter = 7.4;
technic_bush_small_diameter = 5.8;
technic_bush_shoulder_height = 1.3; // Should this match technic_pin_multiple_center_lip_thickness ?

technic_pin_connector_outer_diameter = 7.36;
technic_pin_connector_wall_thickness = 1.3;
technic_pin_connector_shoulder_wall_thickness = 0.6;
technic_pin_connector_shoulder_depth = 0.70;

technic_gear_12_tooth_gear_diameter = 12.7;
technic_gear_12_tooth_base_thickness = 0.4;
technic_gear_12_tooth_diameter = 12.6;
technic_gear_12_tooth_hub_diameter = 6.3;
technic_gear_12_tooth_lip_inner_diameter = 6.9;
technic_gear_12_tooth_lip_outer_diameter = 8.8;
technic_gear_12_tooth_lip_thickness = 0.8;
technic_gear_12_tooth_tooth_height = 2.4;
technic_gear_12_tooth_tooth_thickness = 2.4;
technic_gear_12_tooth_tooth_width_at_bottom = 1.4;
technic_gear_12_tooth_tooth_width_at_top = 0.8;

technic_gear_24_tooth_outer_diameter = 25.4;
technic_gear_24_tooth_bottom_diameter = 21.65;
technic_gear_24_tooth_inner_diameter = 19.6;
technic_gear_24_tooth_tooth_depth = ( technic_gear_24_tooth_outer_diameter - technic_gear_24_tooth_bottom_diameter ) / 2;
technic_gear_pin_hole_outer_diameter = 6.1;
technic_gear_pin_hole_offset_from_center = 5.675;
technic_gear_pin_hole_thickness = 6.1;
technic_gear_tooth_thickness = 3.7;
technic_gear_wheel_thickness = 1.3;
technic_gear_axle_reinforcement_width = 10;
technic_gear_axle_reinforcement_height = 6;
technic_gear_axle_reinforcement_thickness = 7.73;
technic_gear_axle_slot_length = ( ( technic_gear_pin_hole_offset_from_center * 2 ) + technic_hole_diameter ) * .8; // Close enough :)

technic_pin_outer_diameter = 4.85; // Matches LEGO.stud_diameter.
technic_pin_inner_diameter = 3.1; // Matches LEGO.hollow_stud_inner_diameter
technic_pin_collar_diameter = 5.6;
technic_pin_collar_thickness = 0.7; // Matches technic_axle_stop_thickness
technic_pin_lip_diameter = 5;
technic_pin_lip_thickness = 0.75;
technic_pin_slit_width = 0.75;
technic_pin_slit_length = 3.2;
technic_pin_slot_width = 0.75;
technic_pin_slot_length = 5.2;
technic_pin_friction_thickness = 0.15;
technic_pin_friction_width = 0.8;
technic_pin_friction_vertical_length = 5;
technic_pin_multiple_center_width = 7.8;
technic_pin_multiple_center_lip_thickness = 1.2; // Should this match technic_bush_shoulder_height ?
technic_pin_multiple_offset = 7.75;
technic_pin_multiple_center_lip_overhang = 1.35;
technic_pin_tow_ball_total_length = 6.6;
technic_pin_tow_ball_neck_diameter = 3.2; // I believe this "neck" is really just a bar.

technic_elbow_outer_diameter = 7.9; // Matches LEGO.stud_spacing - LEGO.wall_play
technic_elbow_inner_diameter = 5;
technic_elbow_radius = 12;
technic_elbow_straight_length = 4.85; // Matches LEGO.stud_diameter
technic_elbow_overall_width = 16; // Matches ( LEGO.stud_spacing * 1.5 ) + ( technic_elbow_outer_diameter / 2 )
technic_elbow_axle_socket_depth = 2.4; // Matches LEGO.stud_spacing

technic_beam_hole_spacing = 8; // Matches LEGO.stud_spacing
technic_beam_webbing_thickness = 0.8;

technic_tow_ball_diameter = 5.85;

// @todo These values are preliminary.
wheel_face_inset = 2.8;
wheel_wall_thickness = 1;
wheel_center_groove_depth = 6.5;
wheel_center_groove_width = 1.5;
wheel_spoke_connection_depth = .75;
wheel_spoke_edge_width = 0.9;
wheel_spoke_width = 3;

technic_worm_gear_diameter = 14; // @todo Measure IRL. Measurement from https://www.briquespassion.fr/en/boutique/101_technic-gear-vis/8605_lego-technic-gear-worm-screw-short
technic_worm_gear_end_inset = 0.5; // @todo Measure IRL.

// When OpenSCAD does the preview render, if two objects in a difference() end at exactly
// the same plane, it will show a shadowy 0-thickness layer. If instead, one of the difference()
// children extends any amount past that surface, the preview is much cleaner.
EXTENSION_FOR_DIFFERENCE = 1;

/***
 * @function technic_axle();
 * Generate a Technic-compatible axle.
 * @brief Technic, Axle [x]L [with Stud|Stop]
 * The origin is centered at the bottom of the axle.
 *
 * ![An axle compatible with LEGO part #3704.](images/technic_axle.png)
 *
 * **Part Support:**
 * - `part #3704`:  technic_axle( length = 2 );
 * - `part #3705`:  technic_axle( length = 4 );
 * - `part #3706`:  technic_axle( length = 6 );
 * - `part #3707`:  technic_axle( length = 8 );
 * - `part #3708`:  technic_axle( length = 12 );
 * - `part #3737`:  technic_axle( length = 10 );
 * - `part #4519`:  technic_axle( length = 3 );
 * - `part #6587`:  technic_axle( length = 3, stud = true );
 * - `part #15462`: technic_axle( length = 5, stop = true );
 * - `part #23948`: technic_axle( length = 11 );
 * - `part #24316`: technic_axle( length = 3, stop = true );
 * - `part #32062`: technic_axle( length = 2, notch = true );
 * - `part #32073`: technic_axle( length = 5 );
 * - `part #44294`: technic_axle( length = 7 );
 * - `part #50450`: technic_axle( length = 32 );
 * - `part #50451`: technic_axle( length = 16 );
 * - `part #55013`: technic_axle( length = 8, stop = true );
 * - `part #60485`: technic_axle( length = 9 );
 * - `part #87073`: technic_axle( length = 4, stop = true );
 * @param length *float*  The length of the axle, in Technic units.
 * @param stop *bool* Whether there is a stop at the end.
 * @param stud *bool* Whether there is a stud at the end.
 * @param notch *bool* Wether the axle is notched
 */
module technic_axle(
	length = 2, // The length in studs. An axle of length 2 will be the same length as a 2-stud brick.
	stop = false, // Should it have a stop at the end?
	stud = false, // Should it have a stud on the end?
	notch = false
) {
	translate( [ 0, 0, stud ? technic_axle_stud_height : 0 ] ) {
		// A stud always requires a stop, in my opinion.
		let( has_stop = stop || stud ) {
			difference() {
				union() {
					// If there's a stop (and thus an extra segment of length to cut off, we need to move the axle
					// down a segment, since it's returned from technic_axle_spline with the center of its base at the origin.
					translate( [ 0, 0, has_stop ? - ( stud_spacing ) : 0 ] ) {
						// If there's a stop, add an extra bit of length so that we can cut it off flush without seeing the small bit of rounded corners.
						                       technic_axle_spline( length = has_stop ? length + 1 : length );
						rotate( [ 0, 0, 90 ] ) technic_axle_spline( length = has_stop ? length + 1 : length );
					}

					if ( has_stop ) {
						// The stop itself.
						cylinder( d = technic_axle_stop_diameter, h = technic_axle_stop_thickness );
					}
				}

				if ( has_stop ) {
					// Cut off the extra axle below the stop.
					translate([ 0, 0, -( ( stud_spacing ) + EXTENSION_FOR_DIFFERENCE ) ] ) {
						cylinder( d = technic_axle_spline_width + EXTENSION_FOR_DIFFERENCE, h = ( stud_spacing ) + EXTENSION_FOR_DIFFERENCE );
					}
				}

				if ( notch ) {
					for ( i = [ 0.5 : 1 : length ] ) {
						translate( [ 0, 0, ( technic_height_in_mm * i ) - ( 
technic_axle_notch_height / 2 ) ] ) {
							difference() {
								cylinder( d = technic_axle_stud_outer_diameter + EXTENSION_FOR_DIFFERENCE, h = technic_axle_notch_height );
								translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE ] ) {
									cylinder( d = technic_axle_notch_diameter, h = technic_axle_notch_height + 2 * EXTENSION_FOR_DIFFERENCE );
								}
							}
						}
					}
				}
			}

			if ( stud ) {
				// Add a stud on the bottom.
				translate( [ 0, 0, -technic_axle_stud_height ] ) {
					technic_hollow_stud();
				}
			}
		}
	}

	/**
	 * Generate one of the axle splines. An axle is made up of two splines, rotated 90º from each other.
	 * Positioned with the bottom center of the axle spline at the origin.
	 */
	module technic_axle_spline( length ) {
		translate( [ 0, 0, technic_height_in_mm * length / 2 ] ) {
			rotate( [ 90, 0, 0 ] ) {
				minkowski() {
					union () {
						translate( [ 0, 0, - ( technic_axle_spline_thickness - ( 2 * technic_axle_spline_corner_radius ) ) / 2 ] ) linear_extrude( technic_axle_spline_thickness - ( 2 * technic_axle_spline_corner_radius ) ) {
							technic_rounded_rectangle(
								width = technic_axle_spline_width - ( 2 * technic_axle_spline_corner_radius ),
								height = ( technic_height_in_mm * length ) - ( 2 * technic_axle_spline_corner_radius ),
								radius = technic_axle_cross_section_radius
							);
						}
					}

					sphere( r = technic_axle_spline_corner_radius );
				}
			}
		}
	}
}

/***
 * @function technic_axle_and_pin_connector();
 * Generate a Technic-compatible axle and pin connector.
 * @brief Technic, Axle and Pin Connector Perpendicular
 * Axle and pin connectors: they connect axles to pins.
 * The origin is centered underneath the first axle hole.
 *
 * ![An axle connector compatible with LEGO part #6538a.](images/technic_axle_and_pin_connector.png)
 *
 * **Part Support:**
 * - `part #32184`: technic_axle_and_pin_connector( length = 3 );
 * @param length *float* The length of the connector, in Technic holes.
 * @param height *float* The height of the connector, in multiples of standard connector heights.
 */
module technic_axle_and_pin_connector( length = 4, height = 1 ) {
	// Add the two bushes, one on each end.
	                                                     technic_bush( height = height, stud_cutouts = false );
	translate( [ ( length - 1 ) * stud_spacing, 0, 0 ] ) technic_bush( height = height, stud_cutouts = false );

	// Add the connector faces.
	difference() {
		union() {
			difference() {
				union() {
					// The bottom face of the connector.
					hull() {
						cylinder( d = technic_pin_outer_diameter + ( technic_pin_multiple_center_lip_overhang * 2 ), h = technic_axle_and_pin_connector_face_thickness );

						translate( [ stud_spacing * ( length - 1 ), 0, 0 ] ) {
							cylinder( d = technic_pin_outer_diameter + ( technic_pin_multiple_center_lip_overhang * 2 ), h = technic_axle_and_pin_connector_face_thickness );
						}
					}

					// The top face of the connector.
					translate( [ 0, 0, ( height * technic_height_in_mm ) - technic_axle_and_pin_connector_face_thickness ] ) { // 1 is the height of the connector, which in LEGO, is always 1, but we could customize.
						hull() {
							cylinder( d = technic_pin_outer_diameter + ( technic_pin_multiple_center_lip_overhang * 2 ), h = technic_axle_and_pin_connector_face_thickness );

							translate( [ stud_spacing * ( length - 1 ), 0, 0 ] ) {
								cylinder( d = technic_pin_outer_diameter + ( technic_pin_multiple_center_lip_overhang * 2 ), h = technic_axle_and_pin_connector_face_thickness );
							}
						}
					}

				}

				// Remove the cylinders from the face that are occupied by the bushes.
				translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE / 2 ] ) {
					cylinder( d = technic_bush_big_diameter, h = ( height * technic_height_in_mm ) + EXTENSION_FOR_DIFFERENCE );

					translate( [ stud_spacing * ( length - 1 ), 0, 0 ] ) {
						cylinder( d = technic_bush_big_diameter, h = ( height * technic_height_in_mm ) + EXTENSION_FOR_DIFFERENCE);
					}
				}
			}

			let ( webbing_thickness = technic_pin_connector_shoulder_wall_thickness ) {
				// The webbing inside the connector, just like it is in a beam.
				translate( [ technic_bush_small_diameter / 2, -(webbing_thickness/2), 0 ] ) cube( [ ( length - 1 ) * stud_spacing - technic_bush_small_diameter, webbing_thickness,( height * technic_height_in_mm ) ] );
			}
		}

		// Remove the cylinders from the center that are occupied by the pin connectors.
		for ( i = [ 1 : length - 2 ] ) {
			for ( j = [ 1 : height ] ) {
				translate( [ i * technic_beam_hole_spacing, 0, ((j-1) * technic_height_in_mm ) + ( technic_height_in_mm / 2 ) ] ) rotate( [ 90, 0, 0 ] ) translate( [ 0, 0, -( technic_height_in_mm / 2 ) ] ) cylinder( d = technic_pin_connector_outer_diameter, h = technic_height_in_mm );
			}
		}
	}

	// Add the pin holes along the center, essentially a beam portion.
	// These protrude every so slightly past the outer connector faces, which looks like an error,
	// but is how those pieces actually are in reality.
	for ( i = [ 1 : length - 2 ] ) {
		for ( j = [ 1 : height ] ) {
			translate( [ i * technic_beam_hole_spacing, 0, ((j-1) * technic_height_in_mm ) + ( technic_height_in_mm / 2 ) ] ) rotate( [ 90, 0, 0 ] ) translate( [ 0, 0, -( technic_height_in_mm / 2 ) ] ) technic_pin_connector();
		}
	}
}

/***
 * @function technic_axle_connector();
 * Generate a Technic-compatible axle connector.
 * @brief Technic, Axle Connector [x]L [(Ridged)]
 * Origin is centered at the bottom center of the axle connector.
 *
 * ![An axle connector compatible with LEGO part #6538a.](images/technic_axle_connector.png)
 *
 * **Part Support:**
 * - `part #6538a`: technic_axle_connector( length = 2, ridged = true )
 * - `part #6538c`: technic_axle_connector( length = 2 )
 * @param length *int* The length of the axle connector, in Technic units.
 * @param ridged *bool* Whether the connector should have ridges on it.
 */
module technic_axle_connector(
	length = 1,
	ridged = false
) {
	difference() {
		union() {
			cylinder( d = technic_axle_connector_outer_diameter, h = length * technic_height_in_mm );
			if ( length >= 1 && ridged ) {
				for ( i = [ 1 : (length * 2) - 1 ] ) {
					translate( [ 0, 0, i * technic_height_in_mm / 2 - technic_axle_connector_ridge_thickness ] ) cylinder( d = technic_axle_connector_outer_diameter + technic_axle_connector_ridge_thickness, h = technic_axle_connector_ridge_thickness );
				}
			}
		}
		translate( [ 0, 0, length * technic_height_in_mm / 2 ] ) {
				technic_axle_hole( height = length );
		}
		if ( ridged ) {
			technic_stud_cutouts( height = length, diameter = stud_diameter - (technic_axle_connector_outer_diameter - technic_axle_connector_ridged_inner_diameter ) / 2 );
		} else {
			technic_stud_cutouts( height = length );
		}
	}
}

/***
 * @function technic_connector_hub();
 * A connector hub. Some sort of round connector with things like axles or pins protruding like spokes.
 * @brief Technic, Axle and Pin Connector
 * The origin is centered underneath the hub.
 * @todo I haven't measured this in real life to confirm dimensions.
 *
 * ![A connector hub compatible with LEGO part #27940, for example.](images/technic_connector_hub.png)
 *
 * **Part Support:**
 * - `part #4450`:  technic_connector_hub( hub_type = "pin", spoke_angles = [ 0, 168.75 ], spoke_lengths = [ 1, 1 ], spoke_heights = [ 1, 1 ], spoke_types = [ "axle connector", "axle connector" ] )
 * - `part #6611`:  technic_connector_hub( hub_type = "pin", spoke_angles = [ 0, 120, 240 ], spoke_lengths = [ 1, 1, 1 ], spoke_heights = [ 1, 1, 1 ], spoke_types = [ "axle connector", "axle connector", "axle connector" ] )
 * - `part #7329`:  technic_connector_hub( hub_type = "pin", spoke_angles = [ 0, 60, 180 ], spoke_lengths = [ 1, 1, 1 ], spoke_heights = [ 1, 1, 1 ], spoke_types = [ "axle connector", "axle connector", "axle connector" ] )
 * - `part #5713`:  technic_connector_hub( spoke_angles = [ 0 ], spoke_lengths = [ 1 ], spoke_heights = [ 1 ], spoke_types = [ "axle" ], spoke_lengths = [ 3 ] )
 * - `part #10197`: technic_connector_hub( spoke_angles = [ 0, 90 ] )
 * - `part #10288`: technic_connector_hub( hub_type = "pin", spoke_angles = [ 0, 60, 120, 180 ], spoke_lengths = [ 1, 1, 1, 1 ], spoke_heights = [ 1, 1, 1, 1 ], spoke_types = [ "axle connector", "axle connector", "axle connector", "axle connector" ] )
 * - `part #15100`: technic_connector_hub( hub_type = "pin", spoke_lengths = [ 1 ], spoke_angles = [ 0 ], spoke_heights = [ 1 ], spoke_types = [ "pin" ])
 * - `part #15460`: technic_connector_hub( hub_type = "pin", spoke_lengths = [ 1, 1, 1 ], spoke_angles = [ 0, 90, 180 ], spoke_heights = [ 1, 1, 1 ], spoke_types = [ "tow ball", "tow ball", "tow ball" ] );
 * - `part #22961`: technic_connector_hub( spoke_angles = [ 0 ], spoke_lengths = [ 1 ], spoke_heights = [ 1 ], spoke_types = [ "axle" ] )
 * - `part #27940`: technic_connector_hub( spoke_angles = [ 0, 180 ] )
 * - `part #32013`: technic_connector_hub( hub_type = "pin", spoke_angles = [ 0 ], spoke_lengths = [ 1 ], spoke_heights = [ 1 ], spoke_types = [ "axle connector" ] )
 * - `part #32014`: technic_connector_hub( hub_type = "pin", spoke_angles = [ 0, 90 ], spoke_lengths = [ 1, 1 ], spoke_heights = [ 1, 1 ], spoke_types = [ "axle connector", "axle connector" ] )
 * - `part #32015`: technic_connector_hub( hub_type = "pin", spoke_angles = [ 0, 157.5 ], spoke_lengths = [ 1, 1 ], spoke_heights = [ 1, 1 ], spoke_types = [ "axle connector", "axle connector" ] )
 * - `part #32016`: technic_connector_hub( hub_type = "pin", spoke_angles = [ 0, 112.5 ], spoke_lengths = [ 1, 1 ], spoke_heights = [ 1, 1 ], spoke_types = [ "axle connector", "axle connector" ] )
 * - `part #32034`: technic_connector_hub( hub_type = "pin", spoke_angles = [ 0, 180 ], spoke_lengths = [ 1, 1 ], spoke_heights = [ 1, 1 ], spoke_types = [ "axle connector", "axle connector" ] )
 * - `part #32192`: technic_connector_hub( hub_type = "pin", spoke_angles = [ 0, 135 ], spoke_lengths = [ 1, 1 ], spoke_heights = [ 1, 1 ], spoke_types = [ "axle connector", "axle connector" ] )
 * - `part #24122`: technic_connector_hub( hub_type = "axle", spoke_types = [ "bar connector", "bar connector" ] )
 * - `part #57585`: technic_connector_hub( hub_type = "axle", spoke_lengths = [ 1, 1, 1 ], spoke_angles = [ 0, 120, 240 ], spoke_heights = [ 1, 1, 1 ], spoke_types = [ "axle", "axle", "axle" ] )
 * - `part #87082`: technic_connector_hub( hub_type = "pin", spoke_lengths = [ 1, 1 ], spoke_angles = [ 0, 180 ], spoke_heights = [ 1, 1 ], spoke_types = [ "pin", "pin" ])
 * @param hub_height *int* The height of the hub, in Technic units.
 * @param hub_type *string* What type of hub should it be? Either "axle" or "pin".
 * @param spoke_lengths *float[]* How long should each spoke be?
 * @param spoke_angles *float[]* At what angle should each spoke connect?
 * @param spoke_heights *float[]* How high up on the hub should each spoke be placed?
 * @param spoke_types *string[]* What type of connector should each spoke be? Either "axle", "axle connector", "pin", "bar connector" or "tow ball"
 */
module technic_connector_hub(
	hub_height = 1,
	hub_type = "pin",
	spoke_lengths = [ 1, 1 ],
	spoke_angles = [ 0, 180 ],
	spoke_heights = [ 1, 1 ],
	spoke_types = [ "axle", "axle" ]
) {

	if ( len( spoke_lengths ) == 0 ) {
		echo( "You must provide at least one spoke." );
	} else if ( len( spoke_lengths ) != len( spoke_angles ) ) {
		echo( "The number of spoke lengths must match the number of spoke lengths." );
	} else if ( len( spoke_lengths ) != len( spoke_types ) ) {
		echo( "The number of spoke types must match the number of spoke lengths." );
	} else if ( max( spoke_heights ) > hub_height ) {
		echo( "You cannot have a spoke placed higher than the top of the hub." );
	} else {
		// The central hub.
		if ( hub_type == "pin" ) {
			technic_pin_connector( length = hub_height );
		} else if ( hub_type == "axle" ) {
			difference() {
				cylinder( d = technic_pin_connector_outer_diameter, h = hub_height * technic_height_in_mm );
				translate( [ 0, 0, hub_height * technic_height_in_mm / 2 ] ) {
					technic_axle_hole( height = hub_height );
				}
			}
		}

		// The spokes.
		difference() {
			for ( i = [ 0 : len( spoke_angles ) - 1 ] ) {
				rotate( [ 0, 0, spoke_angles[i] ] ) {
					translate( [ 0, 0, (( spoke_heights[i] - 1 ) * technic_height_in_mm ) + ( technic_height_in_mm / 2 ) ] ) {
						rotate( [ 0, 90, 0 ] ) {
							if ( spoke_types[i] == "axle" ) {
								technic_axle( length = spoke_lengths[i] + .5 );
							} else if ( spoke_types[i] == "bar connector" ) {
								linear_extrude( ( technic_height_in_mm * ( spoke_lengths[i] ) ) ) {
									difference() {
										circle( d = technic_bar_connector_outer_diameter );
										circle( d = technic_bar_connector_inner_diameter );
									}
								}
							} else if ( spoke_types[i] == "pin" ) {
								technic_pin_half( length = spoke_lengths[i] + .5, friction = true, squared_pin_holes = false );
							} else if ( spoke_types[i] == "tow ball" ) {
								translate( [ 0, 0, -(spoke_lengths[i] + 1) * technic_pin_tow_ball_total_length ] ) technic_tow_ball( length = spoke_lengths[i] + .5 );
							} else if ( spoke_types[i] == "axle connector" ) {
								technic_axle_connector( length = spoke_lengths[i] + .5);
							}

							if ( spoke_types[i] != "tow ball" && spoke_types[i] != "axle connector" ) {
								cylinder( d = technic_pin_connector_outer_diameter, h = technic_height_in_mm / 2 );
							}
						}
					}
				}
			}

			// Remove anything that has overlapped into the center of the hub.
			translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE ] ) cylinder( d = technic_pin_connector_outer_diameter, h = hub_height * technic_height_in_mm +  EXTENSION_FOR_DIFFERENCE * 2 );
		}
	}
}

/***
 * @function technic_axle_pin();
 * Generate a Technic-compatible axle pin.
 * @brief Technic, Axle [x]L with Pin [x]L [with Friction Ridges]
 * The origin is centered at the bottom of the axle.
 *
 * ![An axle pin compatible with LEGO part #11214.](images/technic_axle_pin.png)
 *
 * **Part Support:**
 * - `part #11214`: technic_axle_pin( axle_length = 1, pin_length = 2 );
 * @param axle_length *int* In studs, how long the axle component should be.
 * @param pin_length *int* In studs, how long the pin component should be.
 * @param friction *bool* Whether the pin component should have friction ridges on it.
 */
module technic_axle_pin(
	axle_length = 1,
	pin_length = 2,
	friction = true
) {
	translate( [ 0, 0, technic_height_in_mm * axle_length ] ) {
		intersection() {
			// Position it so the axle ends at the origin and the pin is above it.
			rotate( [ 180, 0, 0 ] ) {
				// Include a stop, which is the same as the pin collar.
				technic_axle( length = axle_length, stop = true );
			}

			translate( [ 0, 0, -( ( technic_height_in_mm * axle_length ) + EXTENSION_FOR_DIFFERENCE ) ] ) {
				linear_extrude( ( technic_height_in_mm * axle_length ) + EXTENSION_FOR_DIFFERENCE ) {
					circle( d = technic_axle_spline_width + EXTENSION_FOR_DIFFERENCE );
				}
			}
		};

		// The pin collar is already generated in technic_axle() as the stop, so shift the pin down a bit so it's not doubled.
		// @todo In a real piece like this, is the collar part of the axle length or the pin length?
		translate( [ 0, 0, -technic_pin_collar_thickness ] ) {
			technic_pin_half( length = pin_length, friction = friction );
		}
	}
}

/***
 * @function technic_beam();
 * Generate a Technic-compatible beam.
 * @brief Technic, Liftarm [Thick] [x]x[x] - [x]
 * Origin is below the center of the first hole.
 *
 * ![A beam compatible with LEGO part #32524, for example.](images/technic_beam.png)
 *
 * **Part Support:**
 * - `part #6629`:  technic_beam( length = 9, angles = [ 53.5 ], vertices = [ 6 ], axle_holes = [ 1, 9 ] )
 * - `part #6632`:  technic_beam( length = 3, height = 1/2, axle_holes = [ 1, 3 ] )
 * - `part #7229`:  technic_beam( length = 3, axle_holes = [ 2 ] )
 * - `part #11478`: technic_beam( length = 5, height = 1/2, axle_holes = [1, 5] )
 * - `part #18654`: technic_beam( length = 1 ) [equivalent to a pin connector]
 * - `part #32009`: technic_beam( length = 12, vertices = [ 3, 6 ], angles = [ 45, 45 ], axle_holes = [ 1, 12 ] );
 * - `part #32017`: technic_beam( length = 5, height = 1/2 )
 * - `part #32056`: technic_beam( length = 5, height = 1/2, angles = [ 90 ], vertices = [ 3 ], axle_holes = [ 1, 3, 5 ] )
 * - `part #32063`: technic_beam( length = 6, height = 1/2 )
 * - `part #32065`: technic_beam( length = 7, height = 1/2 )
 * - `part #32140`: technic_beam( length = 5, angles = [ 90 ], vertices = [ 4 ], axle_holes = [ 1 ] )
 * - `part #32271`: technic_beam( length = 9, angles = [ 53.5 ], vertices = [ 7 ], axle_holes = [ 1, 9 ] )
 * - `part #32278`: technic_beam( length = 15 )
 * - `part #32316`: technic_beam( length = 5 )
 * - `part #32348`: technic_beam( length = 7, angles = [ 53.5 ], vertices = [ 4 ], axle_holes = [ 1, 7 ] )
 * - `part #32449`: technic_beam( length = 4, height = 1/2, axle_holes = [ 1, 4 ] )
 * - `part #32523`: technic_beam( length = 3 )
 * - `part #32524`: technic_beam( length = 7 )
 * - `part #32525`: technic_beam( length = 11 )
 * - `part #32526`: technic_beam( length = 7, angles = [ 90 ], vertices = [ 1 ] )
 * - `part #40490`: technic_beam( length = 9 )
 * - `part #41239`: technic_beam( length = 13 )
 * - `part #41677`: technic_beam( length = 2, height = 1/2, axle_holes = [ 1, 2 ] )
 * - `part #43857`: technic_beam( length = 2 )
 * - `part #60483`: technic_beam( length = 2, axle_holes = [ 1 ] )
 * - `part #77107`: technic_beam( length = 33, axle_holes = [ 1, 17 ], angles = [ 11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25,11.25 ], vertices = [ 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32 ] ); // This is roughly equivalent but not visually identical.
 * @param length *int* The number of holes in the beam.
 * @param height *float* How tall (in multiples of technic beam thicknesses) should the beam be?
 * @param angles *float[]* The change in angle (clockwise) that will occur at the vertex'th hole.
 * @param vertices *int[]* The number of each hole at which the angle should change.
 * @param axle_holes *int[]* Which holes should be axle holes instead.
 */
module technic_beam( length = 5, height = 1, angles = [], vertices = [], axle_holes = [], depth = 0 ) {
	// When making the second part of an angled beam, remap the axle hole locations for that smaller beam.
	function angled_axle_holes( all_axle_holes, original_vertex ) = [
		if ( len( all_axle_holes ) > 0 ) for ( i = [ 0 : len( all_axle_holes ) - 1 ] ) if ( all_axle_holes[i] > original_vertex ) all_axle_holes[i] - original_vertex + 1
	];

	// Some error cases.
	if ( length < 1 ) {
		echo( "Length must be one or greater: ", length );
	} else if ( len( angles ) != len( vertices ) ) {
		echo( "Number of angles (", len(angles), ") must equal number of vertices (", len( vertices ), ")." );
	} else if ( len( vertices ) >= length ) {
		echo( "The number of vertices", len( vertices ), " cannot be as long as the length." );
	} else if ( len( vertices ) > 0 && max( vertices ) >= length ) {
		echo( "The largest vertex ", max( vertices ), " has to be smaller than the length, ", length );
	} else {
		if ( len( angles ) > 0 ) {
			let(
				// Each section of the beam will be as long as the first vertex in the list.
				this_length = vertices[0],
				this_angle = angles[0],
				// Remove the first vertex from the list.
				new_vertices = [ for ( i = [ 0 : ( len( vertices ) - 1 ) ] ) if ( i > 0 ) vertices[i] - this_length + 1 ],
				// Remove the first angle from the list.
				new_angles = [ for ( i = [ 0 : ( len( angles ) - 1 ) ] ) if ( i > 0 ) angles[i] ],
				// Remove any axle holes we've already added, and shift the axle hole indices down to account for the beam portion we've already output.
				new_axle_holes = len( axle_holes ) > 0 ? [ for ( i = [ 0 : ( len( axle_holes ) - 1 ) ] ) if ( axle_holes[i] > this_length ) axle_holes[i] - this_length + 1 ] : []
			) {
				technic_beam( length = vertices[0], height = height, axle_holes = axle_holes, depth = depth + 1 );

				translate( [ ( this_length - 1 ) * technic_beam_hole_spacing, 0, 0 ] ) {
					rotate( [ 0, 0, this_angle ] ) {
						technic_beam(
							// The length argument should be the total remaining length, plus the additional hole that will be overlayed on the last output hole. It came into the function as length, we output vertices[0] holes, so now we still need to output length - vertices[0] + 1 holes.
							length = length - this_length + 1,
							height = height,
							angles = new_angles,
							vertices = new_vertices,
							axle_holes = new_axle_holes,
							depth = depth + 1
						);
					}
				}
			}
		} else {
			// Generate the pin connectors that make up the inside of the beam.
			for ( i = [ 1 : length ] ) {
				translate( [ technic_beam_hole_spacing * ( i - 1 ), 0, 0 ] ) {
					if ( len( search( i, axle_holes ) ) > 0 ) {
						difference() {
							cylinder( d = technic_pin_connector_outer_diameter, h = height * technic_height_in_mm );

							// @todo This still leaves a tiny bit of extra material in the axle hole at the vertex of an angled beam (if there is one there).
							translate( [ 0, 0, -height * technic_height_in_mm ] ) {
								technic_axle_hole( height = height * 2 );
							}
						}
					} else {
						technic_pin_connector( length = height );
					}
				}
			}

			// Add the walls along the edges of the rows of pins.
			translate( [ 0, -( technic_pin_connector_outer_diameter / 2 ), ( technic_height_in_mm * height ) / 2 ] ) {
				difference() {
					translate( [ 0, 0, -technic_beam_webbing_thickness / 2 ] ) {
						cube( [ ( length - 1 ) * technic_beam_hole_spacing, technic_pin_connector_outer_diameter, technic_beam_webbing_thickness ] );
					}

					union () {
						for ( i = [ 1 : length ] ) {
							translate( [ technic_beam_hole_spacing * ( i - 1 ), technic_pin_connector_outer_diameter / 2, 0 ] ) {
								cylinder( d = technic_pin_connector_outer_diameter, h = technic_beam_webbing_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
							}
						}
					}
				}
			}

			// Add the webbing between the pin connector walls.
			// @todo 1/2 thick beams don't have webbing, they're just solid.
			translate( [ 0, - ( technic_pin_connector_outer_diameter / 2 ), 0 ] ) {
				cube( [ ( length - 1 ) * technic_beam_hole_spacing, technic_pin_connector_shoulder_wall_thickness, technic_height_in_mm * height ] );
				translate( [ 0, technic_pin_connector_outer_diameter - technic_pin_connector_shoulder_wall_thickness, 0 ] ) {
					cube( [ ( length - 1 ) * technic_beam_hole_spacing, technic_pin_connector_shoulder_wall_thickness, technic_height_in_mm * height ] );
				}
			}
		}
	}
}

/***
 * @function technic_bush();
 * Generate a Technic-compatible bush.
 * @brief Technic Bush
 * Origin is centered beneath the bush.
 *
 * ![A bush compatible with LEGO part #4265c, for example.](images/technic_bush.png)
 *
 * **Part Support:**
 * - `part #3713`:  technic_bush( height = 1 )
 * - `part #4265c`: technic_bush( height = 1/2 );
 * @param height *int* The height of the bush.
 * @param stud_cutouts *bool* Whether one end should have cutouts in the edge to fit between studs. Only applies to heights greater than 1/2.
 */
module technic_bush( height = 1/2, stud_cutouts = true ) {
	difference() {
		union () {
			difference() {
				// The main inner cylinder that forms the interior walls.
				cylinder( h = height * technic_height_in_mm, d = technic_bush_small_diameter );

				// Bushes at least 1 unit tall have slots in the side (for air? material savings?)
				if ( height >= 1 ) {
					translate ( [ 0,  ( technic_bush_small_diameter + EXTENSION_FOR_DIFFERENCE ) / 2, ( ( height * technic_height_in_mm ) - ( 2 * technic_bush_shoulder_height ) ) / 2 + technic_bush_shoulder_height ]) {
						rotate( [ 90, 0, 0 ] ) {
							linear_extrude( technic_bush_small_diameter + EXTENSION_FOR_DIFFERENCE ) {
								technic_rounded_rectangle( width = technic_pin_slot_width, height = ( height * technic_height_in_mm ) - ( 2 * technic_bush_shoulder_height ) );
							}
						}
					}
				}
			}

			// The bottom shoulder.
			cylinder( h = technic_bush_shoulder_height, d = technic_bush_big_diameter );

			// The top shoulder.
			translate( [ 0, 0, ( height * technic_height_in_mm ) - technic_bush_shoulder_height ] ) {
				difference() {
					cylinder( h = technic_bush_shoulder_height, d = technic_bush_big_diameter );

					if ( height > 1/2 && stud_cutouts ) {
						// Bushes taller than 1/2 units get cutouts in the lip so that they'll fit between studs.
						technic_stud_cutouts( height = technic_bush_shoulder_height );
					}
				}
			}
		}

		// The axle hole.
		translate( [ 0, 0, ( height * technic_height_in_mm ) / 2 ] ) technic_axle_hole( height = height );
	}
}

/***
 * @function technic_elbow();
 * Generate a Technic-compatible 90º elbow.
 * @brief Brick, Round Tube 1 x 1 d. 90 degrees Elbow Macaroni
 * Origin is at the point where the X and Y axes would meet, with each of them centered in the hole at the end of each leg of the elbow.
 *
 * ![A 90º elbow compatible with LEGO part #25214.](images/technic_elbow.png)
 *
 * **Part Support:**
 * - `part #25214`: technic_elbow( length = 2, width = 2 )
 * @param length *int* The number of studs one leg would cover, if laid down on a plate.
 * @param width *int* The number of studs the other leg would cover, if laid down on a plate.
 * @param axle_socket_on_length *bool* Whether there should be an interior socket for accepting an axle on the X axis.
 * @param axle_socket_on_width *bool* Whether there should be an interior socket for accepting an axle on the Y axis.
 */
module technic_elbow(
	length = 2, // The number of studs one leg would cover, if laid down on a plate.
	width = 2, // The number of studs the other leg would cover, if laid down on a plate.
	axle_socket_on_length = true, // Whether there should be an interior socket for accepting an axle on the X axis.
	axle_socket_on_width = true, // Whether there should be an interior socket for accepting an axle on the Y axis.
) {
	// Use the longer dimension as the length and the shorter dimension as the width.
	// This simplifies some decisions we need to make about what goes where.
	//
	// length is along the X axis, width is along the Y axis.
	real_length = max( 2, max( length, width ) );
	real_width = max( 2, min( length, width ) );

	difference() {
		union() {
			// The two straight parts can be placed in their known positions, and then we can calculate
			// the starting and stopping points of the elbow.
			translate( [ ( real_length * stud_spacing ) - technic_elbow_straight_length, 0, 0 ] ) {
				rotate( [ 0, 90, 0 ] ) {
					difference() {
						cylinder( d = technic_elbow_outer_diameter, h = technic_elbow_straight_length );
						translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE ] ) {
							cylinder( d = technic_elbow_inner_diameter, h = technic_elbow_straight_length + ( 2 * EXTENSION_FOR_DIFFERENCE ) );
						}
					}

					if ( axle_socket_on_length ) {
						// Add the material that will be the ridges for the axle socket.
						cylinder( d = technic_elbow_inner_diameter, h = technic_elbow_straight_length - technic_elbow_axle_socket_depth );
					}
				}
			}

			translate( [ 0, ( real_width * stud_spacing ) - technic_elbow_straight_length, 0 ] ) {
				rotate( [ -90, 0, 0 ] ) {
					difference() {
						cylinder( d = technic_elbow_outer_diameter, h = technic_elbow_straight_length );
						translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE ] ) cylinder( d = technic_elbow_inner_diameter, h = technic_elbow_straight_length + ( 2 * EXTENSION_FOR_DIFFERENCE ) );
					}

					if ( axle_socket_on_width ) {
						// Add the material that will be the ridges for the axle socket.
						cylinder( d = technic_elbow_inner_diameter, h = technic_elbow_straight_length - technic_elbow_axle_socket_depth );
					}
				}
			}

			// So we need a tube to connect ( real_width * stud_spacing ) - technic_elbow_straight_length on both X and Y.
			translate( [ ( real_width * stud_spacing ) - technic_elbow_straight_length, ( real_width * stud_spacing ) - technic_elbow_straight_length, 0 ] ) {
				rotate( [ 180, 180, 0 ] ) {
					rotate_extrude( angle = 90 ) {
						translate( [ ( real_width * stud_spacing ) - technic_elbow_straight_length, 0, 0 ] ) {
							circle( d = technic_elbow_outer_diameter );
						}
					}
				}
			}

			// And we also need to fill in any gaps if length doesn't match width.
			if ( real_length > real_width ) {
				translate( [ ( real_width * stud_spacing ) - technic_elbow_straight_length, 0, 0 ] ) {
					rotate( [ 0, 90, 0 ] ) {
						cylinder( d = technic_elbow_outer_diameter, h = ( real_length - real_width ) * stud_spacing );
					}
				}
			}
		}

		if ( axle_socket_on_length ) {
			// Subtract the axle socket area along the length.
			translate( [ real_width * stud_spacing, 0, 0 ] ) {
				rotate( [ 0, -90, 0 ] ) {
					technic_axle_hole( height = 1 );
				}
			}
		}

		if ( axle_socket_on_width ) {
			// Subtract the axle socket area along the width.
			translate( [ 0, real_length * stud_spacing, 0 ] ) {
				rotate( [ 90, 0, 0 ] ) {
					technic_axle_hole( height = 1 );
				}
			}
		}
	}
}

/***
 * @function technic_gear_double_sided();
 * Generate a Technic-compatible double-sided spur gear.
 * @brief Technic, Gear [x] Tooth with [x] Axle Hole
 * Double-sided gears (as opposed to the one-sided gears sometimes called "half-gears").
 * Origin is at the center of the gear in all directions.
 *
 * ![A spur gear compatible with LEGO part #3648.](images/technic_gear_double_sided.png)
 *
 * **Part Support:**
 * - `part #3647`:  technic_gear_double_sided( teeth = 8, width = 1.5 ); // @todo Multiple issues.
 * - `part #3648`:  technic_gear_double_sided( teeth = 24 );
 * - `part #3549`:  technic_gear_double_sided( teeth = 40 );
 * - `part #10928`: technic_gear_double_sided( teeth = 8, width = 1.5 ); // @todo The teeth are not exactly right.
 * @param teeth *int* How many teeth should the gear have? The minimum reasonable value is probably X.
 * @param width *int* In multiples of the original gear width, how wide should it be? e.g., a width of 3 would generate a single gear with the same total width as three gears set side-by-side.
 */
module technic_gear_double_sided(
	teeth = 24,
	width = 1
) {
	//include <gears.scad>;

	// The overall widest part of a gear is the axle reinforcement.
	// For determining the other widths (thicknesses), the constants are:
	// * the difference between the axle reinforcement thickness and the pin hole thickness.
	// * the difference between the tooth thickness and the wheel thickness.
	// * the difference between the wheel thickness and the pin hole thickness.
	// Calculate the remaining values based on these differences.
	desired_gear_axle_reinforcement_thickness = width * technic_gear_axle_reinforcement_thickness;
	desired_pin_hole_thickness = desired_gear_axle_reinforcement_thickness - ( technic_gear_axle_reinforcement_thickness - technic_gear_pin_hole_thickness );
	desired_gear_tooth_thickness = desired_gear_axle_reinforcement_thickness - ( technic_gear_axle_reinforcement_thickness - technic_gear_tooth_thickness );
	desired_gear_wheel_thickness = desired_gear_axle_reinforcement_thickness - ( technic_gear_axle_reinforcement_thickness - technic_gear_wheel_thickness );

	// A gear is 1 inch wide for every 24 teeth.
	gear_diameter = ( teeth / 24 ) * technic_gear_24_tooth_outer_diameter;

	// For the inner sunken area, use the measured size of a 24-tooth gear to scale it, always leaving the raised part near the teeth a constant size.
	gear_inner_diameter = gear_diameter - ( technic_gear_24_tooth_outer_diameter - technic_gear_24_tooth_inner_diameter );

	// The diagonal distance from the center of the gear to the center of a pin hole in a 24-tooth gear is technic_gear_pin_hole_offset_from_center.
	// This means the horizontal and vertical distances will be found via cosine 45º = X / technic_gear_pin_hole_offset_from_center. => ( 1 / sqrt( 2 ) ) = X / technic_gear_pin_hole_offset_from_center => technic_gear_pin_hole_offset_from_center / sqrt( 2 ) = X
	technic_gear_pin_hole_horizontal_offset_from_center = technic_gear_pin_hole_offset_from_center / sqrt(2);

	difference() {
		union() {
			// The central hub,
			difference() {
				union () {
					// The hub of the gear.
					cylinder( d = gear_inner_diameter, h = desired_gear_wheel_thickness, center = true );

					// The walls of the pin holes
					union () {
						rotate( [ 0, 0, 45 ] ) {
							for ( x = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : gear_inner_diameter / 2 ] ) {
								for ( y = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : ( gear_inner_diameter / 2 ) ] ) {
									diagonal = sqrt( x ^ 2 + y ^ 2 );

									if ( diagonal + ( technic_gear_pin_hole_outer_diameter / 2 ) <= ( gear_inner_diameter / 2 ) ) {
										translate( [ x, y, 0 ] ) {
											cylinder( d = technic_gear_pin_hole_outer_diameter, h = desired_pin_hole_thickness, center = true );
										};

										translate( [ x, -y, 0 ] ) difference() {
											cylinder( d = technic_gear_pin_hole_outer_diameter, h = desired_pin_hole_thickness, center = true );
										};

										translate( [ -x, y, 0 ] ) difference() {
											cylinder( d = technic_gear_pin_hole_outer_diameter, h = desired_pin_hole_thickness, center = true );
										};

										translate( [ -x, -y, 0 ] ) difference() {
											cylinder( d = technic_gear_pin_hole_outer_diameter, h = desired_pin_hole_thickness, center = true );
										};
									}
								}
							}
						}
					};
				};

				// The pin holes.
				union() {
					// As long as the gear is big enough to allow it in the center section, create a grid of pin holes spaced 2 * technic_gear_pin_hole_horizontal_offset_from_center from each other.

					rotate( [ 0, 0, 45 ] ) {
						for ( x = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : gear_inner_diameter / 2 ] ) {
							for ( y = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : ( gear_inner_diameter / 2 ) ] ) {
								diagonal = sqrt( x ^ 2 + y ^ 2 );

								if ( diagonal + ( technic_gear_pin_hole_outer_diameter / 2 ) <= ( gear_inner_diameter / 2 ) ) {
									translate( [ x, y, 0 ] ) {
										cylinder( d = technic_hole_diameter, h = desired_pin_hole_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
									};

									translate( [ x, -y, 0 ] ) difference() {
										cylinder( d = technic_hole_diameter, h = desired_pin_hole_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
									};

									translate( [ -x, y, 0 ] ) difference() {
										cylinder( d = technic_hole_diameter, h = desired_pin_hole_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
									};

									translate( [ -x, -y, 0 ] ) difference() {
										cylinder( d = technic_hole_diameter, h = desired_pin_hole_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
									};
								}
							}
						}
					}
				};
			};

			// The teeth.
			translate( [ 0, 0, - ( desired_gear_tooth_thickness / 2 ) ] ) {
				// The gear teeth seem like they're a little too long (exceeding gear_diameter), but I can't tell if it matters.
				spur_gear( modul = 1, tooth_number = teeth, width = desired_gear_tooth_thickness, bore = gear_inner_diameter, pressure_angle=20, optimized = false );
			};

			// The gear function leaves very small gaps at the bottom corners of the teeth. Fill that all in.
			difference() {
				cylinder( d = gear_diameter - ( technic_gear_24_tooth_tooth_depth * 2 ), h = desired_gear_tooth_thickness, center = true );
				cylinder( d = gear_inner_diameter, h = desired_gear_tooth_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
			};

			// The supports around the axle holes.
			difference() {
				union() {
					rotate( [ 0, 0, 45 ] ) {
						// The center hole.
						if ( teeth  >= 14 ) { // If the tooth count is 14 or below, the axle reinforcement will conflict with the teeth, so omit it.

							rotate( [ 0, 0, 90 ] ) {
								cube( size = [ technic_gear_axle_reinforcement_width, technic_gear_axle_reinforcement_height, desired_gear_axle_reinforcement_thickness ], center = true );
							}
						}

						let ( x = technic_gear_pin_hole_horizontal_offset_from_center ) {
							for ( y = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : ( gear_inner_diameter / 2 ) ] ) {
								if ( y != technic_gear_pin_hole_horizontal_offset_from_center ) {
									diagonal = sqrt( x ^ 2 + y ^ 2 );

									if ( diagonal + ( technic_gear_pin_hole_outer_diameter / 2 ) <= ( gear_inner_diameter / 2 ) ) {
										translate( [ 0, y - technic_gear_pin_hole_horizontal_offset_from_center, 0 ] ) rotate( [ 0, 0, 90 ] ) {
											cube( size = [ technic_gear_axle_reinforcement_width, technic_gear_axle_reinforcement_height, desired_gear_axle_reinforcement_thickness ], center = true );
										}

										if ( y != technic_gear_pin_hole_horizontal_offset_from_center ) { // Don't add the center hole twice.
											translate( [ 0, -y + technic_gear_pin_hole_horizontal_offset_from_center, 0 ] ) rotate( [ 0, 0, 90 ] ) {
												cube( size = [ technic_gear_axle_reinforcement_width, technic_gear_axle_reinforcement_height, desired_gear_axle_reinforcement_thickness ], center = true );
											}
										}
									}
								}
							}
						}

						for ( x = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : gear_inner_diameter / 2 ] ) {
							let ( y = technic_gear_pin_hole_horizontal_offset_from_center ) {
								if ( x != technic_gear_pin_hole_horizontal_offset_from_center ) {
									diagonal = sqrt( x ^ 2 + y ^ 2 );

									if ( diagonal + ( technic_gear_pin_hole_outer_diameter / 2 ) <= ( gear_inner_diameter / 2 ) ) {
										translate( [ x - technic_gear_pin_hole_horizontal_offset_from_center, 0, 0 ] ) {
											cube( size = [ technic_gear_axle_reinforcement_width, technic_gear_axle_reinforcement_height, desired_gear_axle_reinforcement_thickness ], center = true );
										}

										translate( [ -x + technic_gear_pin_hole_horizontal_offset_from_center, 0, 0 ] ) {
											cube( size = [ technic_gear_axle_reinforcement_width, technic_gear_axle_reinforcement_height, desired_gear_axle_reinforcement_thickness ], center = true );
										}
									}
								}
							}
						}
					}
				}

				// The walls of the pin holes
				union () {
					rotate( [ 0, 0, 45 ] ) {
						// The max() calls in these loops is to ensure the support around the axle hole is shaped as if the pin holes were there even if the gear is too small for the pin holes. Otherwise it looks like just a big cube.
						for ( x = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : max( technic_gear_pin_hole_horizontal_offset_from_center, gear_inner_diameter / 2 ) ] ) {
							for ( y = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : max( technic_gear_pin_hole_horizontal_offset_from_center, ( gear_inner_diameter / 2 ) ) ] ) {
								translate( [ x, y, 0 ] ) {
									cylinder( d = technic_gear_pin_hole_outer_diameter, h = desired_gear_axle_reinforcement_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
								};

								translate( [ x, -y, 0 ] ) difference() {
									cylinder( d = technic_gear_pin_hole_outer_diameter, h = desired_gear_axle_reinforcement_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
								};

								translate( [ -x, y, 0 ] ) difference() {
									cylinder( d = technic_gear_pin_hole_outer_diameter, h = desired_gear_axle_reinforcement_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
								};

								translate( [ -x, -y, 0 ] ) difference() {
									cylinder( d = technic_gear_pin_hole_outer_diameter, h = desired_gear_axle_reinforcement_thickness + EXTENSION_FOR_DIFFERENCE, center = true );
								};
							}
						}
					}
				};
			};
		};

		// The axle holes.
		rotate( [ 0, 0, 45 ] ) {
			// The center hole.
			rotate( [ 0, 0, 90 ] ) {
				if ( teeth >= 14 ) {
					technic_gear_wide_axle_hole( height = desired_gear_axle_reinforcement_thickness, center_of_multiple = true ); // @todo Theoretically, center_of_multiple should be false if there's only one axle hole in total.
				} else {
					technic_axle_hole( height = desired_gear_axle_reinforcement_thickness );
				}
			}

			// Run along the x axis and add the other holes.
			// Rather than setting x,y to 0,0, we're using the same math here that we did to determine whether there would be pin holes
			// past this point. This looks a little more complicated but lets us reuse the same logic, ensuring that the pin holes and
			// axle holes always match. Maybe I'll come back and simplify this some day.
			let ( x = technic_gear_pin_hole_horizontal_offset_from_center ) {
				for ( y = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : ( gear_inner_diameter / 2 ) ] ) {
					if ( y != technic_gear_pin_hole_horizontal_offset_from_center ) {
						diagonal = sqrt( x ^ 2 + y ^ 2 );

						if ( diagonal + ( technic_gear_pin_hole_outer_diameter / 2 ) <= ( gear_inner_diameter / 2 ) ) {
							translate( [ 0, y - technic_gear_pin_hole_horizontal_offset_from_center, 0 ] ) rotate( [ 0, 0, 90 ] ) {
								technic_gear_wide_axle_hole( height = desired_gear_axle_reinforcement_thickness );
							}

							if ( y != technic_gear_pin_hole_horizontal_offset_from_center ) { // Don't add the center hole twice.
								translate( [ 0, -y + technic_gear_pin_hole_horizontal_offset_from_center, 0 ] ) rotate( [ 0, 0, 90 ] ) {
									technic_gear_wide_axle_hole( height = desired_gear_axle_reinforcement_thickness );
								}
							}
						}
					}
				}
			}

			// Run along the y axis and add the other holes.
			for ( x = [ technic_gear_pin_hole_horizontal_offset_from_center : technic_gear_pin_hole_horizontal_offset_from_center * 2 : gear_inner_diameter / 2 ] ) {
				let ( y = technic_gear_pin_hole_horizontal_offset_from_center ) {
					if ( x != technic_gear_pin_hole_horizontal_offset_from_center ) {
						diagonal = sqrt( x ^ 2 + y ^ 2 );

						if ( diagonal + ( technic_gear_pin_hole_outer_diameter / 2 ) <= ( gear_inner_diameter / 2 ) ) {
							translate( [ x - technic_gear_pin_hole_horizontal_offset_from_center, 0, 0 ] ) {
								technic_gear_wide_axle_hole( height = desired_gear_axle_reinforcement_thickness );
							}

							translate( [ -x + technic_gear_pin_hole_horizontal_offset_from_center, 0, 0 ] ) {
								technic_gear_wide_axle_hole( height = desired_gear_axle_reinforcement_thickness );
							}
						}
					}
				}
			}
		}
	}
}

/***
 * @function technic_gear_single_sided();
 * Generate a single-sided gear, sometimes called a half-gear.
 * @brief Technic, Gear [x] Tooth Bevel
 * Origin is centered at the bottom of the gear (the non-toothed side).
 *
 * ![A single-sided gear, compatible with LEGO part #6589.](images/technic_gear_single_sided.png)
 *
 * **Part Support:**
 * - `part #6589`:  technic_gear_single_sided()
 * - `part #32198`: technic_gear_single_sided( teeth = 20 )
 * - `part #87407`: technic_gear_single_sided( teeth = 20, center_hole = "pin" )
 * @param teeth *int* How many teeth should the gear have? The minimum reasonable value is probably 10.
 * @param bevel *bool* Should the gear teeth be beveled?
 * @param center_hole *string* What connector should the center hole be compatible with? Supported values are "axle" and "pin".
 */
module technic_gear_single_sided( teeth = 12, bevel = true, center_hole = "axle" ) {
	// Gears appear to be one inch wide for every 24 teeth they have.
	gear_diameter = ( teeth / 12 ) * technic_gear_12_tooth_gear_diameter;

	// The diameter of the hub grows with gear diameter enough to keep the length of the exposed teeth constant.
	exposed_tooth_length = ( technic_gear_12_tooth_gear_diameter - technic_gear_12_tooth_hub_diameter );

	// ...but the 12-tooth size is the minimum in order to support the axle or pin hole in the center.
	hub_diameter = max( technic_gear_12_tooth_hub_diameter, gear_diameter - exposed_tooth_length );

	difference() {
		union() {
			// The lip that acts as a washer between the gear and a beam or brick.
			linear_extrude( technic_gear_12_tooth_lip_thickness ) {
				difference() {
					circle( d = technic_gear_12_tooth_lip_outer_diameter );
					circle( d = technic_gear_12_tooth_lip_inner_diameter );
				}
			}

			// The base of the gear.
			translate( [ 0, 0, technic_gear_12_tooth_lip_thickness ] ) cylinder( d = gear_diameter, h = technic_gear_12_tooth_base_thickness );

			// The hub of the gear.
			translate( [ 0, 0, technic_gear_12_tooth_lip_thickness + technic_gear_12_tooth_base_thickness ] ) cylinder( d = hub_diameter, h = technic_gear_12_tooth_tooth_thickness );

			// The teeth.
			// @todo Is the tooth width/depth/etc. a function of the number of teeth? Or the diameter of the gear? Or something else?
			translate( [ 0, 0, technic_gear_12_tooth_base_thickness + technic_gear_12_tooth_lip_thickness ] ) {
				let( inward_slant = ( technic_gear_12_tooth_tooth_width_at_bottom - technic_gear_12_tooth_tooth_width_at_top ) / 2 ) {
					for ( i = [ 1 : teeth ] ) {
						rotate( [ 0, 0, 360 / teeth * i ] ) {
							rotate( [ 90, 0, 0 ] ) {
								translate( [ 0, 0, -gear_diameter / 2 ] ) {
									difference() {
										linear_extrude( gear_diameter / 2 ) {
											translate( [ -technic_gear_12_tooth_tooth_width_at_bottom / 2, 0, 0 ] ) polygon(
												points = [
													[ 0, 0 ],
													[ technic_gear_12_tooth_tooth_width_at_bottom, 0 ],
													[ technic_gear_12_tooth_tooth_width_at_bottom - inward_slant, technic_gear_12_tooth_tooth_height ],
													[ inward_slant, technic_gear_12_tooth_tooth_height ],
													[ 0, 0 ]
												]
											);
										}

										// Remove the bevel.
										if ( bevel ) {
											let( extra_offset_for_preview = 0.001 ) {
												translate( [-technic_gear_12_tooth_tooth_width_at_bottom / 2 - extra_offset_for_preview, technic_gear_12_tooth_tooth_height / 2 + extra_offset_for_preview, -extra_offset_for_preview ] ) {
													rotate( [ 90, 0, 90 ] ) {
														linear_extrude( technic_gear_12_tooth_tooth_width_at_bottom ) {
															// The bevel is assumed to be a 45º cut that is half as tall as the tooth. This might be wrong.
															polygon(
																points = [
																	[ 0, 0 ],
																	[ technic_gear_12_tooth_tooth_height / 2, 0 ],
																	[ technic_gear_12_tooth_tooth_height / 2, technic_gear_12_tooth_tooth_height / 2 ],
																	[ 0, 0 ]
																]
															);
														}
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}

		if ( center_hole == "axle" ) {
			// Remove the axle hole.
			technic_axle_hole( height = 1 ); // @todo If we add a width/thickness option, it would replace 1 here.
		} else if ( center_hole == "pin" ) {
			translate( [ 0, 0, technic_gear_12_tooth_lip_thickness - ( EXTENSION_FOR_DIFFERENCE / 2 ) ] ) {
				cylinder( d = min( technic_pin_connector_outer_diameter, technic_gear_12_tooth_lip_inner_diameter ), h = technic_gear_12_tooth_base_thickness + technic_gear_12_tooth_tooth_height + EXTENSION_FOR_DIFFERENCE );
			}
		}
	}

	if ( center_hole == "pin" ) {
		translate( [ 0, 0, technic_gear_12_tooth_lip_thickness ] ) {
			technic_pin_connector( length = 1 );
		}
	}
}

/***
 * @function technic_pin();
 * Generate a Technic-compatible pin.
 * @brief Technic, Pin [with Friction Ridges]
 * Origin is centered at the bottom of the pin.
 *
 * ![A pin compatible with LEGO part #2780.](images/technic_pin.png)
 *
 * **Part Support:**
 * - `part #2780`:  technic_pin( top_length = 1, top_friction = true, bottom_length = 1, bottom_friction = true )
 * - `part #3673`:  technic_pin( top_length = 1, top_friction = false, bottom_length = 1, bottom_friction = false )
 * - `part #4274`:  technic_pin( top_length = 1, stud = true )
 * - `part #4459`:  technic_pin( top_length = 1, top_friction = true, bottom_length = 1, bottom_friction = true ) // This part has long friction ridges along the length of the pin, which isn't supported yet.
 * - `part #6558`:  technic_pin( top_length = 2, top_friction = true, bottom_length = 1, bottom_friction = true )
 * - `part #6628`:  technic_pin( bottom_type = "tow ball" )
 * - `part #32054`: technic_pin( top_length = 2, bottom_length = 1, bottom_type = "bush" )
 * - `part #32138`: technic_pin( multiplier = 2 )
 * - `part #32556`: technic_pin( top_length = 2, top_friction = false, bottom_length = 1, bottom_friction = false )
 * - `part #65098`: technic_pin( multiplier = 2, squared_pin_holes = true )
 * - `part #77765`: technic_pin( top_length = 3, top_friction = false, bottom_length = 0, bottom_friction = false )
 * - `part #80477`: technic_pin( bottom_length = 2, bottom_type = "tow ball" )
 * - `part #89678`: technic_pin( top_length = 1, top_friction = true, bottom_type = "stud" )
 * @param top_length *float* How long is the pin on the top?
 * @param top_friction *bool* Should the top part have friction ridges?
 * @param bottom_type *string* What should the bottom of the pin be? "pin", "tow ball", "stud", or "bush"
 * @param bottom_length *float* How long is the pin on the bottom?
 * @param bottom_friction *bool* Should the bottom part have friction ridges?
 * @param multiplier *int* How many pin sets should there be?
 * @param axle_hole *bool* If a multiple pin, should there be an axle hole?
 */
module technic_pin(
	top_length = 1,
	top_friction = true,
	bottom_length = 1,
	bottom_friction = true,
	multiplier = 1,
	axle_holes = true,
	squared_pin_holes = false,
	bottom_type = "pin"
) {
	let ( bottom_length_in_mm = ( bottom_type == "stud" ? stud_height : ( bottom_type == "tow ball" ? bottom_length * technic_pin_tow_ball_total_length : bottom_length * technic_height_in_mm ) ) ) {
		if ( multiplier > 1 ) {
			translate( [ 0, 0, bottom_length_in_mm ] ) {
				difference() {
					union() {
						// The pin halves.
						for ( i = [ 1 : multiplier ] ) {
							translate( [ ( i - 1 ) * technic_pin_multiple_offset, 0, technic_pin_multiple_center_width ] ) technic_pin_half( length = top_length, friction = top_friction, squared_pin_holes = squared_pin_holes );

							if ( bottom_type == "stud" ) {
								translate( [ ( i - 1 ) * technic_pin_multiple_offset, 0, -bottom_length_in_mm] ) technic_hollow_stud();
							} else if ( bottom_type == "tow ball" ) {
								translate( [ ( i - 1 ) * technic_pin_multiple_offset, 0, -bottom_length_in_mm] ) technic_tow_ball( length = bottom_length );
							} else if ( bottom_type == "bush" ) {
								rotate( a = 180, v = [ 0, 1, 0 ] ) technic_bush( height = bottom_length, stud_cutouts = false );
							} else {
								translate( [ ( i - 1 ) * technic_pin_multiple_offset, 0, 0 ] ) rotate( [ 0, 180, 0 ] ) technic_pin_half( length = bottom_length, friction = bottom_friction, squared_pin_holes = squared_pin_holes );
							}
						}

						// The bottom lip that separates the pins from the center section.
						hull() {
							cylinder( d = technic_pin_outer_diameter + ( technic_pin_multiple_center_lip_overhang * 2 ), h = technic_pin_multiple_center_lip_thickness );
							translate( [ technic_pin_multiple_offset * ( multiplier - 1 ), 0, 0 ] ) {
								cylinder( d = technic_pin_outer_diameter + ( technic_pin_multiple_center_lip_overhang * 2 ), h = technic_pin_multiple_center_lip_thickness );
							}
						}

						// The top lip that separates the pins from the center section.
						translate( [ 0, 0, technic_pin_multiple_center_width - technic_pin_multiple_center_lip_thickness ] ) {
							hull() {
								cylinder( d = technic_pin_outer_diameter + ( technic_pin_multiple_center_lip_overhang * 2 ), h =technic_pin_multiple_center_lip_thickness );
								translate( [ technic_pin_multiple_offset * ( multiplier - 1 ), 0, 0 ] ) cylinder( d = technic_pin_outer_diameter + ( technic_pin_multiple_center_lip_overhang * 2 ), h =technic_pin_multiple_center_lip_thickness );
							}
						}

						// The body of the center section.
						hull() {
							cylinder( d = technic_pin_outer_diameter, h = technic_pin_multiple_center_width );
							translate( [ technic_pin_multiple_offset * ( multiplier - 1 ), 0, 0 ] ) cylinder( d = technic_pin_outer_diameter, h = technic_pin_multiple_center_width );
						}

						if ( axle_holes ) {
							// Generate the support area around the axle holes.
							for ( i = [ 1 : multiplier - 1 ] ) {
								translate( [ ( ( i - .5 ) * technic_pin_multiple_offset ), 0, technic_pin_multiple_center_width / 2 ] ) {
									rotate( [ 90, 0, 0 ] ) {
										intersection() {
											// 1.5 is an arbitrary choice that is correct enough, assuming the cross-section size of an axle can't be customized and the width of the center of a multiple-pin can't be customized.
											scale( [ 1.5, 1.5, 1 ] ) {
												technic_axle_hole( height = technic_pin_outer_diameter + EXTENSION_FOR_DIFFERENCE );
											}

											// Only allow the axle support to extend as far as the edge of the lip of the center section.
											cube( [ technic_pin_multiple_center_width, technic_pin_multiple_center_width, technic_pin_outer_diameter + ( 2 * technic_pin_multiple_center_lip_overhang ) ], center = true );
										}
									}
								}
							}

						}
					}

					if ( axle_holes ) {
						// Remove the axle holes.
						for ( i = [ 1 : multiplier - 1 ] ) {
							translate( [ ( ( i - .5 ) * technic_pin_multiple_offset ), 0, technic_pin_multiple_center_width / 2 ] ) {
								rotate( [ 90, 0, 0 ] ) {
									translate( [ 0, 0, 0 ] ) {
										technic_axle_hole( height = technic_pin_outer_diameter + EXTENSION_FOR_DIFFERENCE );
									}
								}
							}
						}
					}
				}
			}
		} else {
			translate( [ 0, 0, ( bottom_length_in_mm ) - ( bottom_type == "pin" ? technic_pin_collar_thickness : 0 ) ] ) {
				// The top half of the pin.
				technic_pin_half( length = top_length, friction = top_friction, squared_pin_holes = squared_pin_holes );

				if ( bottom_type == "stud" ) {
					// The stud.
					translate( [ 0, 0, -bottom_length_in_mm ] ) technic_hollow_stud();
				} else if ( bottom_type == "tow ball" ) {
					// The tow ball.
					translate( [ 0, 0, -bottom_length_in_mm ] ) technic_tow_ball( length = bottom_length );
				} else if ( bottom_type == "bush" ) {
					// The bush.
					rotate( a = 180, v = [ 0, 1, 0 ] ) technic_bush( height = bottom_length, stud_cutouts = false );
				} else {
					// The bottom half of the pin.
					translate( [ 0, 0, technic_pin_collar_thickness ] ) rotate( [ 0, 180, 0 ] ) technic_pin_half( length = bottom_length, friction = bottom_friction, squared_pin_holes = squared_pin_holes );
				}
			}
		}
	}
}

/***
 * @function technic_pin_connector();
 * Generate a Technic-compatible pin connector.
 * @brief Technic, Liftarm Thick 1 x 1 (Spacer)
 * Origin is centered at the bottom center of the pin connector.
 *
 * ![A pin connector compatible with LEGO part #18654.](images/technic_pin_connector.png)
 *
 * **Part Support:**
 * - `part #18654`: technic_pin_connector( length = 1 ) [equivalent to a 1-hole beam]
 * @param length *int* The length of the pin connector in "studs." FWIW, LEGO only makes these in length 1.
 */
module technic_pin_connector(
	length = 1, // The length in studs. An axle of length 2 will be the same length as a 2-stud brick.
) {
	translate( [ 0, 0, ( technic_height_in_mm * length ) / 2 ] ) {
		union() {
			// The hollow cylinder that forms the outer wall.
			difference() {
				cylinder( h = technic_height_in_mm * length, d = technic_pin_connector_outer_diameter, center = true );
				cylinder( h = technic_height_in_mm * length + EXTENSION_FOR_DIFFERENCE, r = ( technic_pin_connector_outer_diameter / 2 ) - technic_pin_connector_shoulder_wall_thickness, center = true );
			};

			difference() {
				cylinder( h = ( technic_height_in_mm * length ) - ( technic_pin_connector_shoulder_depth * 2 ), d = technic_pin_connector_outer_diameter, center = true );
				cylinder( h = ( technic_height_in_mm * length ) - ( technic_pin_connector_shoulder_depth * 2 ) + EXTENSION_FOR_DIFFERENCE, r = ( technic_hole_diameter / 2 ), center = true );
			};
		};
	}
}

/**
 * @param float length How long, in Technic units, is the pin half?
 * @param bool friction Whether it should have friction ridges.
 * @param bool squared_pin_holes Apparently "squared" pin holes mean the slits at the end of the pin are rotated 90º from their usual orientation.
 */
module technic_pin_half(
	length = 1,
	friction = true,
	squared_pin_holes = false
) {
	if ( length > 0 ) { // A "half pin" just has a 1.7mm extension (2.5 including the collar) of the pin body past the collar.
		difference() {
			union() {
				// Pin body
				if ( length == 0.5 ) {
					cylinder( d = technic_pin_outer_diameter, h = 1.8 + technic_pin_collar_thickness ); // 1.8 matches stud height
				} else {
					cylinder( d = technic_pin_outer_diameter, h = length * technic_height_in_mm );
				}

				// Pin collar.
				cylinder( d = technic_pin_collar_diameter, h = technic_pin_collar_thickness );

				if ( length > ( 0.5 ) ) {
					// Pin lip
					translate( [ 0, 0, ( length * technic_height_in_mm ) - technic_pin_lip_thickness ] ) {
						cylinder( d = technic_pin_lip_diameter, h = technic_pin_lip_thickness );
					}

					if ( friction ) {
						// End lines
						intersection() {
							// The cylinders that define the areas vertically where the friction lines will appear
							union() {
								for ( idx = [ 0 : 1 : length ] ) {
									// Center.
									translate( [ 0, 0, ( idx * 2 * technic_height_in_mm ) / 2 - ( technic_pin_friction_vertical_length / 2 )  ] ) {
										cylinder( d = technic_pin_outer_diameter + ( 2 * technic_pin_friction_thickness ), h = technic_pin_friction_vertical_length );
									}
								}
							}

							// The cubes that define the areas radially where the friction lines will appears.
							union() {
								rotate( [0, 0, 45 ] ) translate( [0, 0, ( length * technic_height_in_mm ) / 2 ] ) {
									cube( [ technic_pin_friction_width, technic_pin_outer_diameter * 2, length * technic_height_in_mm ], center = true );
								}

								rotate( [0, 0, 135 ] ) translate( [0, 0, ( length * technic_height_in_mm ) / 2 ] ) {
									cube( [ technic_pin_friction_width, technic_pin_outer_diameter * 2, length * technic_height_in_mm ], center = true );
								}
							}
						}

						// The radial friction lines
						if ( length > 1 ) {
							for ( idx = [ 1 : 1 : length - 1 ] ) {
								translate( [ 0, 0, ( idx * 2 * technic_height_in_mm ) / 2 ] ) {
									cylinder( d = technic_pin_outer_diameter + ( 2 * technic_pin_friction_thickness ), h = technic_pin_friction_width, center = true );
								}
							}
						}
					}
				}
			};

			// Remove the center of the pin.
			translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE ] ) cylinder( d = technic_pin_inner_diameter, h = ( length * technic_height_in_mm ) + ( 2 * EXTENSION_FOR_DIFFERENCE ) );

			if ( length >= 1 ) { // Half-pins don't get slits and slots.
				// Remove the slit at the top that makes the pin end flex.
				rotate( [ 0, 0, squared_pin_holes ? 90 : 0 ] ) {
					translate( [ 0, technic_pin_lip_diameter, length * technic_height_in_mm ] ) {
						rotate( [ 90, 0, 0 ] ) {
							linear_extrude( technic_pin_lip_diameter * 2 ) {
								technic_rounded_rectangle( width = technic_pin_slit_width, height = technic_pin_slit_length * 2, radius = technic_pin_slit_width / 2 );
							}
						}
					}
				}
			}

			// Remove the slot across the center of the pin.
			if ( length > 1 ) {
				for ( idx = [ 1 : 1 : length - 1 ] ) {
					translate( [ 0, 0, ( idx * 2 * technic_height_in_mm ) / 2 ] ) {
						rotate( [ 90, 0, idx % 2 == 0 ? 0 : 90 ] ) {
							translate( [ 0, 0, - technic_pin_lip_diameter ] ) {
								linear_extrude( technic_pin_lip_diameter * 2 ) {
									technic_rounded_rectangle( width = technic_pin_slot_width, height = technic_pin_slot_length, radius = technic_pin_slot_width / 2 );
								}
							}
						}
					}
				}
			}
		}
	}
}

/***
 * @function technic_tire();
 * Generate a Technic-compatible tire.
 * @brief Tyre
 * @todo Tread pattern.
 * @todo Inner band
 *
 * ![A tire connector compatible with LEGO part #89201.](images/technic_tire.png)
 *
 * @param tread_width *float* Width of the tire tread.
 * @param diameter *float* Outer diameter of the tire.
 * @param tread_thickness *float* Thickness of the tire tread.
 */
module technic_tire(
	tread_width = 14,
	diameter = 24,
	tread_thickness = 3
) {
	linear_extrude( tread_width ) {
		difference() {
			circle( d = diameter );
			circle( d = diameter - ( tread_thickness * 2 ) );
		}
	}
}

/***
 * @function technic_wheel();
 * Generate a Technic-compatible wheel (also referred to as rims).
 * @brief Wheel
 * @todo Fake studs.
 * @todo spokes aren't curved downward.
 * @todo Multiple grooves.
 *
 * ![A wheel compatible with LEGO part #20896.](images/technic_wheel.png)
 *
 * @param diameter *float* The diameter of the wheel.
 * @param width *float* The width of the wheel, across where the tread would lie.
 * @param center_groove *bool* Whether it has a center groove for holding a tire in place.
 * @param hole_type *string* Is the center hole for an "axle" or a "pin"?
 * @param spoke_count *int* How many spokes should it have?
 * @param spoke_style *string* What style of spoke does it have? Only "double" is supported now.
 */
module technic_wheel( diameter = 1, width = 1, center_groove = true, hole_type = "axle", spoke_count = 6, spoke_style = "double" ) {
	difference() {
		union() {
			difference() {
				// The bulk of the wheel.
				cylinder( d = diameter, h = width );

				// Remove the inset portions on either face.
				translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE / 2 ] ) cylinder( d = diameter - ( wheel_wall_thickness * 2 ), h = wheel_face_inset + EXTENSION_FOR_DIFFERENCE );
				translate( [ 0, 0, width - wheel_face_inset + ( EXTENSION_FOR_DIFFERENCE / 2 ) ] ) cylinder( d = diameter - ( wheel_wall_thickness * 2 ), h = wheel_face_inset + EXTENSION_FOR_DIFFERENCE );

				// Remove the center groove.
				if ( center_groove ) {
					translate( [ 0, 0, ( width / 2 ) - ( wheel_center_groove_width / 2 ) ] ) {
						difference() {
							cylinder( d = diameter + EXTENSION_FOR_DIFFERENCE, h = wheel_center_groove_width );
							cylinder( d = diameter - wheel_center_groove_depth, h = wheel_center_groove_width );
						}
					}
				}
			}

			// Add any support around the center hole.
			if ( hole_type == "axle" ) {
				cylinder( d = technic_pin_connector_outer_diameter, h = width );
			} else if ( hole_type == "pin" ) {
				technic_pin_connector( length = width / technic_height_in_mm );
			}

			// Remove
			difference() {
				translate([ 0, 0, width - wheel_face_inset ] ) {
					intersection() {
						// Add the spokes.
						if ( spoke_count > 0 ) {
							for ( i = [ 1 : spoke_count ] ) {
								rotate( [ 0, 0, ( 360 / spoke_count ) * i ] ) {
									translate( [ 0, -wheel_spoke_width / 2, 0 ] ) {
										difference() {
											cube( [ diameter, wheel_spoke_width, wheel_face_inset ] );
											translate( [ 0, wheel_spoke_edge_width, 0 ] ) cube( [ diameter, wheel_spoke_width - ( 2 * wheel_spoke_edge_width ), wheel_face_inset + EXTENSION_FOR_DIFFERENCE ] );
										}
									}
								}
							}
						}

						// But only keep the part of the spokes that are inside the wheel.
						cylinder( d = diameter, h = wheel_face_inset );
					}

				}

				// Remove the spoke parts that cross into the center hole.
				cylinder( d = technic_pin_connector_outer_diameter, h = width + EXTENSION_FOR_DIFFERENCE );
			}

		}

		// Remove the center hole.
		if ( hole_type == "axle" ) {
			technic_axle_hole( height = width );
		} else if ( hole_type == "pin" ) {
			translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE / 2 ] ) cylinder( d = technic_pin_connector_outer_diameter - ( 2 * technic_pin_connector_wall_thickness ), h = width + EXTENSION_FOR_DIFFERENCE );
		}
	}
}

/***
 * @function technic_worm_gear();
 * Generate a Technic-compatible worm gear.
 * @brief Technic, Gear Worm Screw
 *
 * ![A worm gear compatible with LEGO part #4716.](images/technic_worm_gear.png)
 *
 * **Part Support:**
 * - `part #4716`:  technic_worm_gear( height = 2, width = 3 );                    // 10mm   wide, 16mm   tall
 * - `part #27938`: technic_worm_gear( height = 1, width = 4 );                    // 13.5mm wide, 8mm    tall
 * - `part #32905`: technic_worm_gear( height = 2, width = 3, opening = "axle2" ); // 10mm   wide, 15.7mm tall
 * @param height *float* The height of the gear, in Technic units.
 * @param width *int* The width of the gear, in some unknown units. The two real-world Technic worm gears seem to be roughly multiples of 3.5mm (3x and 4x), and values outside of 3-5 don't really work.
 * @param opening *string* Whether the opening should be axle shaped, or the half-axle/half-circle shape that some new gears use. "axle" or "axle2"
 */
module technic_worm_gear( height = 2, width = 3, opening = "axle" ) {
	//include <gears.scad>;

	// This is BS, but it works for values 1 through 5
	lead_angle = 102.37 - 106.1667 * width + 44.55417 * width^2 - 8.333333 * width^3 + 0.5758333 * width^4;

	difference() {
		// These parameters appear to be correct, but I can't guarantee that they are.
		worm( modul = 1, thread_starts = 1, length = technic_height_in_mm * height, bore = 0, lead_angle = lead_angle, pressure_angle = 30 );

		// Remove the axle hole.
		technic_axle_hole( height = height );

		// Remove a little indented circle around the axle at each end.
		translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE ] ) cylinder( d = technic_pin_connector_outer_diameter, h = technic_worm_gear_end_inset + EXTENSION_FOR_DIFFERENCE );
		translate( [ 0, 0, technic_height_in_mm * height - technic_worm_gear_end_inset ] ) cylinder( d = technic_pin_connector_outer_diameter, h = technic_worm_gear_end_inset + EXTENSION_FOR_DIFFERENCE );
	}
}

/**
 * Utility modules. None of these produce an entire Technic-compatible piece on their own.
 */

/**
 * Generate a rounded rectangle.
 */
module technic_rounded_rectangle( width = 1, height = 1, radius = 0.1 ) {
	hull() {
		// Position a circle to act as each rounded corner of the axle.
		translate( [ -( width / 2 ) + radius,  ( height / 2 ) - radius, 0 ] ) circle( r = radius );
		translate( [  ( width / 2 ) - radius,  ( height / 2 ) - radius, 0 ] ) circle( r = radius );
		translate( [  ( width / 2 ) - radius, -( height / 2 ) + radius, 0 ] ) circle( r = radius );
		translate( [ -( width / 2 ) + radius, -( height / 2 ) + radius, 0 ] ) circle( r = radius );
	}
}

module technic_axle_hole( height = 1 ) {
	scale( [ technic_axle_interference_fit_ratio, technic_axle_interference_fit_ratio, technic_axle_interference_fit_ratio ] ) {
		translate( [ 0, 0, - ( height * 2 * technic_height_in_mm ) / 2 ] ) technic_axle( length = height * 2 );
	}
}

module technic_gear_wide_axle_hole( height, center_of_multiple = false ) {
	technic_axle_hole( height = height );

	scale( [ technic_axle_interference_fit_ratio, technic_axle_interference_fit_ratio, technic_axle_interference_fit_ratio ] ) {
		// The cross-opening for the axle fit is as wide as the widest edges of the pin holes. ~12.75
		linear_extrude( height = height + EXTENSION_FOR_DIFFERENCE, center = true ) {
			technic_rounded_rectangle(
				width = technic_axle_spline_thickness * technic_axle_interference_fit_ratio,
				height = technic_gear_axle_slot_length * ( center_of_multiple ? 0.7 : 1 ),
				radius = ( technic_axle_spline_thickness * technic_axle_interference_fit_ratio ) / 2
			);
		}
	}
}

module technic_hollow_stud() {
	linear_extrude( stud_height ) {
		difference() {
			circle( d = stud_outer_diameter );
			circle( d = stud_inner_diameter );
		}
	}
}

module technic_tow_ball( length = 1 ) {
	// I don't have a tow ball piece longer than length 1, but I'm assuming it's just a multiple of the original length. @todo
	translate( [ 0, 0, technic_tow_ball_diameter / 2 ] ) {
		sphere( d = technic_tow_ball_diameter );
		cylinder( h = ( length * technic_pin_tow_ball_total_length ) - ( technic_tow_ball_diameter / 2 ), d = technic_pin_tow_ball_neck_diameter );
	}
}

module technic_stud_cutouts( height = 1, diameter = stud_diameter ) {
	translate( [ 0, 0, -EXTENSION_FOR_DIFFERENCE / 2 ] ) {
		union () {
			translate( [ -0.5 * stud_spacing, -0.5 * stud_spacing, 0 ] )cylinder( d = diameter, h = height * technic_height_in_mm + EXTENSION_FOR_DIFFERENCE );
			translate( [ -0.5 * stud_spacing, 0.5 * stud_spacing, 0 ] ) cylinder( d = diameter, h = height * technic_height_in_mm + EXTENSION_FOR_DIFFERENCE );
			translate( [ 0.5 * stud_spacing, -0.5 * stud_spacing, 0 ] ) cylinder( d = diameter, h = height * technic_height_in_mm + EXTENSION_FOR_DIFFERENCE );
			translate( [ 0.5 * stud_spacing, 0.5 * stud_spacing, 0 ] ) cylinder( d = diameter, h = height * technic_height_in_mm + EXTENSION_FOR_DIFFERENCE );
		}
	}
}

$fn = 50;

/* Library for Involute Gears, Screws and Racks

This library contains the following modules
- rack(modul, length, height, width, pressure_angle=20, helix_angle=0)
- mountable_rack(modul, length, height, width, pressure_angle=20, helix_angle=0, fastners, profile, head)
- herringbone_rack(modul, length, height, width, pressure_angle = 20, helix_angle=45)
- mountable_herringbone_rack(modul, length, height, width, pressure_angle=20, helix_angle=45, fastners, profile, head)
- spur_gear(modul, tooth_number, width, bore, pressure_angle=20, helix_angle=0, optimized=true)
- herringbone_gear(modul, tooth_number, width, bore, pressure_angle=20, helix_angle=0, optimized=true)
- rack_and_pinion (modul, rack_length, gear_teeth, rack_height, gear_bore, width, pressure_angle=20, helix_angle=0, together_built=true, optimized=true)
- ring_gear(modul, tooth_number, width, rim_width, pressure_angle=20, helix_angle=0)
- herringbone_ring_gear(modul, tooth_number, width, rim_width, pressure_angle=20, helix_angle=0)
- planetary_gear(modul, sun_teeth, planet_teeth, number_planets, width, rim_width, bore, pressure_angle=20, helix_angle=0, together_built=true, optimized=true)
- bevel_gear(modul, tooth_number,  partial_cone_angle, tooth_width, bore, pressure_angle=20, helix_angle=0)
- bevel_herringbone_gear(modul, tooth_number, partial_cone_angle, tooth_width, bore, pressure_angle=20, helix_angle=0)
- bevel_gear_pair(modul, gear_teeth, pinion_teeth, axis_angle=90, tooth_width, bore, pressure_angle = 20, helix_angle=0, together_built=true)
- bevel_herringbone_gear_pair(modul, gear_teeth, pinion_teeth, axis_angle=90, tooth_width, bore, pressure_angle = 20, helix_angle=0, together_built=true)
- worm(modul, thread_starts, length, bore, pressure_angle=20, lead_angle=10, together_built=true)
- worm_gear(modul, tooth_number, thread_starts, width, length, worm_bore, gear_bore, pressure_angle=20, lead_angle=0, optimized=true, together_built=true)

Examples of each module are commented out at the end of this file

Author:     Dr Jörg Janssen
Contributions By:   Keith Emery, Chris Spencer
Last Verified On:      1. June 2018
Version:    2.2
License:     Creative Commons - Attribution, Non Commercial, Share Alike

Permitted modules according to DIN 780:
0.05 0.06 0.08 0.10 0.12 0.16
0.20 0.25 0.3  0.4  0.5  0.6
0.7  0.8  0.9  1    1.25 1.5
2    2.5  3    4    5    6
8    10   12   16   20   25
32   40   50   60

*/


// General Variables
pi = 3.14159;
rad = 57.29578;
clearance = 0.05;   // clearance between teeth

/*  Converts Radians to Degrees */
function grad(pressure_angle) = pressure_angle*rad;

/*  Converts Degrees to Radians */
function radian(pressure_angle) = pressure_angle/rad;

/*  Converts 2D Polar Coordinates to Cartesian
    Format: radius, phi; phi = Angle to x-Axis on xy-Plane */
function polar_to_cartesian(polvect) = [
    polvect[0]*cos(polvect[1]),
    polvect[0]*sin(polvect[1])
];

/*  Circle Involutes-Function:
    Returns the Polar Coordinates of an Involute Circle
    r = Radius of the Base Circle
    rho = Rolling-angle in Degrees */
function ev(r,rho) = [
    r/cos(rho),
    grad(tan(rho)-radian(rho))
];

/*  Sphere-Involutes-Function
    Returns the Azimuth Angle of an Involute Sphere
    theta0 = Polar Angle of the Cone, where the Cutting Edge of the Large Sphere unrolls the Involute
    theta = Polar Angle for which the Azimuth Angle of the Involute is to be calculated */
function sphere_ev(theta0,theta) = 1/sin(theta0)*acos(cos(theta)/cos(theta0))-acos(tan(theta0)/tan(theta));

/*  Converts Spherical Coordinates to Cartesian
    Format: radius, theta, phi; theta = Angle to z-Axis, phi = Angle to x-Axis on xy-Plane */
function sphere_to_cartesian(vect) = [
    vect[0]*sin(vect[1])*cos(vect[2]),
    vect[0]*sin(vect[1])*sin(vect[2]),
    vect[0]*cos(vect[1])
];

/*  Check if a Number is even
    = 1, if so
    = 0, if the Number is not even */
function is_even(number) =
    (number == floor(number/2)*2) ? 1 : 0;

/*  greatest common Divisor
    according to Euclidean Algorithm.
    Sorting: a must be greater than b */
function ggt(a,b) =
    a%b == 0 ? b : ggt(b,a%b);

/*  Polar function with polar angle and two variables */
function spiral(a, r0, phi) =
    a*phi + r0;

/*  Copy and rotate a Body */
module copier(vect, number, distance, winkel){
    for(i = [0:number-1]){
        translate(v=vect*distance*i)
            rotate(a=i*winkel, v = [0,0,1])
                children(0);
    }
}

/*  rack
    modul = Height of the Tooth Tip above the Rolling LIne
    length = Length of the Rack
    height = Height of the Rack to the Pitch Line
    width = Width of a Tooth
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle of the Rack Transverse Axis; 0° = Spur Teeth */
module rack(modul, length, height, width, pressure_angle = 20, helix_angle = 0) {

    // Dimension Calculations
    modul=modul*(1-clearance);
    c = modul / 6;                                              // Tip Clearance
    mx = modul/cos(helix_angle);                          // Module Shift by Helix Angle in the X-Direction
    a = 2*mx*tan(pressure_angle)+c*tan(pressure_angle);       // Flank Width
    b = pi*mx/2-2*mx*tan(pressure_angle);                      // Tip Width
    x = width*tan(helix_angle);                          // Topside Shift by Helix Angle in the X-Direction
    nz = ceil((length+abs(2*x))/(pi*mx));                       // Number of Teeth

    translate([-pi*mx*(nz-1)/2-a-b/2,-modul,0]){
        intersection(){                                         // Creates a Prism that fits into a Geometric Box
            copier([1,0,0], nz, pi*mx, 0){
                polyhedron(
                    points=[[0,-c,0], [a,2*modul,0], [a+b,2*modul,0], [2*a+b,-c,0], [pi*mx,-c,0], [pi*mx,modul-height,0], [0,modul-height,0], // Underside
                        [0+x,-c,width], [a+x,2*modul,width], [a+b+x,2*modul,width], [2*a+b+x,-c,width], [pi*mx+x,-c,width], [pi*mx+x,modul-height,width], [0+x,modul-height,width]],   // Topside
                    faces=[[6,5,4,3,2,1,0],                     // Underside
                        [1,8,7,0],
                        [9,8,1,2],
                        [10,9,2,3],
                        [11,10,3,4],
                        [12,11,4,5],
                        [13,12,5,6],
                        [7,13,6,0],
                        [7,8,9,10,11,12,13],                    // Topside
                    ]
                );
            };
            translate([abs(x),-height+modul-0.5,-0.5]){
                cube([length,height+modul+1,width+1]);          // Cuboid which includes the Volume of the Rack
            }
        };
    };
}

/* Mountable-rack; uses module "rack"
    modul = Height of the Tooth Tip above the Rolling LIne
    length = Length of the Rack
    height = Height of the Rack to the Pitch Line
    width = Width of a Tooth
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle of the Rack Transverse Axis; 0° = Spur Teeth
    fastners = Total number of fastners.
    profile = Metric standard profile for fastners (ISO machine screws), M4 = 4, M6 = 6 etc.

    head = Style of fastner to accomodate.
    PH = Pan Head, C = Countersunk, RC = Raised Countersunk, CS = Cap Screw, CSS = Countersunk Socket Screw. */
module mountable_rack(modul, length, height, width, pressure_angle, helix_angle, fastners, profile, head) {
    difference(){
    rack(modul, length, height, width, pressure_angle, helix_angle);
    offset = (length/fastners);
    translate([-length/2+(offset/2),0,0])
    for(i = [0:fastners-1]){
                if (head=="PH"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=profile*0.6+modul*2.25, d=profile*2, center=false);
                    }
                if (head=="CS"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=profile*1.25+modul*2.25, d=profile*1.5, center=false);
                    }
                if (head=="C"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=modul*2.25, d=profile*2, center=false);
                    translate([i*offset,-modul*1.25,width/2])
                    rotate([90,0,0])
                    cylinder (h=profile/2, d1=profile*2, d2=profile, center=false);
                    }
                if (head=="RC"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=modul*2.25+profile/4, d=profile*2, center=false);
                    translate([i*offset,-modul*1.25-profile/4,width/2])
                    rotate([90,0,0])
                    cylinder (h=profile/2, d1=profile*2, d2=profile, center=false);
                    }
                if (head=="CSS"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=modul*2.25, d=profile*2, center=false);
                    translate([i*offset,-modul*1.25,width/2])
                    rotate([90,0,0])
                    cylinder (h=profile*0.6, d1=profile*2, d2=profile, center=false);
                    }
                }
            }
        }

/*  Spur gear
    modul = Height of the Tooth Tip beyond the Pitch Circle
    tooth_number = Number of Gear Teeth
    width = tooth_width
    bore = Diameter of the Center Hole
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle to the Axis of Rotation; 0° = Spur Teeth
    optimized = Create holes for Material-/Weight-Saving or Surface Enhancements where Geometry allows */
module spur_gear(modul, tooth_number, width, bore, pressure_angle = 20, helix_angle = 0, optimized = true) {

    // Dimension Calculations
    d = modul * tooth_number;                                           // Pitch Circle Diameter
    r = d / 2;                                                      // Pitch Circle Radius
    alpha_spur = atan(tan(pressure_angle)/cos(helix_angle));// Helix Angle in Transverse Section
    db = d * cos(alpha_spur);                                      // Base Circle Diameter
    rb = db / 2;                                                    // Base Circle Radius
    da = (modul <1)? d + modul * 2.2 : d + modul * 2;               // Tip Diameter according to DIN 58400 or DIN 867
    ra = da / 2;                                                    // Tip Circle Radius
    c =  (tooth_number <3)? 0 : modul/6;                                // Tip Clearance
    df = d - 2 * (modul + c);                                       // Root Circle Diameter
    rf = df / 2;                                                    // Root Radius
    rho_ra = acos(rb/ra);                                           // Maximum Rolling Angle;
                                                                    // Involute begins on the Base Circle and ends at the Tip Circle
    rho_r = acos(rb/r);                                             // Rolling Angle at Pitch Circle;
                                                                    // Involute begins on the Base Circle and ends at the Tip Circle
    phi_r = grad(tan(rho_r)-radian(rho_r));                         // Angle to Point of Involute on Pitch Circle
    gamma = rad*width/(r*tan(90-helix_angle));               // Torsion Angle for Extrusion
    step = rho_ra/16;                                            // Involute is divided into 16 pieces
    tau = 360/tooth_number;                                             // Pitch Angle

    r_hole = (2*rf - bore)/8;                                    // Radius of Holes for Material-/Weight-Saving
    rm = bore/2+2*r_hole;                                        // Distance of the Axes of the Holes from the Main Axis
    z_hole = floor(2*pi*rm/(3*r_hole));                             // Number of Holes for Material-/Weight-Saving

    optimized = (optimized && r >= width*1.5 && d > 2*bore);    // is Optimization useful?

    // Drawing
    union(){
        rotate([0,0,-phi_r-90*(1-clearance)/tooth_number]){                     // Center Tooth on X-Axis;
                                                                        // Makes Alignment with other Gears easier

            linear_extrude(height = width, convexity = 10, twist = gamma){
                difference(){
                    union(){
                        tooth_width = (180*(1-clearance))/tooth_number+2*phi_r;
                        circle(rf);                                     // Root Circle
                        for (rot = [0:tau:360]){
                            rotate (rot){                               // Copy and Rotate "Number of Teeth"
                                polygon(concat(                         // Tooth
                                    [[0,0]],                            // Tooth Segment starts and ends at Origin
                                    [for (rho = [0:step:rho_ra])     // From zero Degrees (Base Circle)
                                                                        // To Maximum Involute Angle (Tip Circle)
                                        polar_to_cartesian(ev(rb,rho))],       // First Involute Flank

                                    [polar_to_cartesian(ev(rb,rho_ra))],       // Point of Involute on Tip Circle

                                    [for (rho = [rho_ra:-step:0])    // of Maximum Involute Angle (Tip Circle)
                                                                        // to zero Degrees (Base Circle)
                                        polar_to_cartesian([ev(rb,rho)[0], tooth_width-ev(rb,rho)[1]])]
                                                                        // Second Involute Flank
                                                                        // (180*(1-clearance)) instead of 180 Degrees,
                                                                        // to allow clearance of the Flanks
                                    )
                                );
                            }
                        }
                    }
                    circle(r = rm+r_hole*1.49);                         // "bore"
                }
            }
        }
        // with Material Savings
        if (optimized) {
            linear_extrude(height = width, convexity = 10){
                difference(){
                        circle(r = (bore+r_hole)/2);
                        circle(r = bore/2);                          // bore
                    }
                }
            linear_extrude(height = (width-r_hole/2 < width*2/3) ? width*2/3 : width-r_hole/2, convexity = 10){
                difference(){
                    circle(r=rm+r_hole*1.51);
                    union(){
                        circle(r=(bore+r_hole)/2);
                        for (i = [0:1:z_hole]){
                            translate(sphere_to_cartesian([rm,90,i*360/z_hole]))
                                circle(r = r_hole);
                        }
                    }
                }
            }
        }
        // without Material Savings
        else {
            linear_extrude(height = width, convexity = 10){
                difference(){
                    circle(r = rm+r_hole*1.51);
                    circle(r = bore/2);
                }
            }
        }
    }
}

/* Herringbone_rack; uses the module "rack"
    modul = Height of the Tooth Tip above the Rolling LIne
    length = Length of the Rack
    height = Height of the Rack to the Pitch Line
    width = Width of a Tooth
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle of the Rack Transverse Axis; 0° = Spur Teeth */
module herringbone_rack(modul, length, height, width, pressure_angle = 20, helix_angle) {
 width = width/2;
 translate([0,0,width]){
        union(){
            rack(modul, length, height, width, pressure_angle, helix_angle);      // bottom Half
            mirror([0,0,1]){
                rack(modul, length, height, width, pressure_angle, helix_angle);  // top Half
            }
        }
    }
}

/* Mountable_herringbone_rack; uses module "herringbone_rack"
    modul = Height of the Tooth Tip above the Rolling LIne
    length = Length of the Rack
    height = Height of the Rack to the Pitch Line
    width = Width of a Tooth
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle of the Rack Transverse Axis; 0° = Spur Teeth
    fastners = Total number of fastners.
    profile = Metric standard profile for fastners (ISO machine screws), M4 = 4, M6 = 6 etc.

    head = Style of fastner to accomodate.
    PH = Pan Head, C = Countersunk, RC = Raised Countersunk, CS = Cap Screw, CSS = Countersunk Socket Screw. */
module mountable_herringbone_rack(modul, length, height, width, pressure_angle, helix_angle, fastners, profile, head) {
    difference(){
    herringbone_rack(modul, length, height, width, pressure_angle, helix_angle);
    offset = (length/fastners);
    translate([-length/2+(offset/2),0,0])
    for(i = [0:fastners-1]){
                if (head=="PH"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=profile*0.6+modul*2.25, d=profile*2, center=false);
                    }
                if (head=="CS"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=profile*1.25+modul*2.25, d=profile*1.5, center=false);
                    }
                if (head=="C"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=modul*2.25, d=profile*2, center=false);
                    translate([i*offset,-modul*1.25,width/2])
                    rotate([90,0,0])
                    cylinder (h=profile/2, d1=profile*2, d2=profile, center=false);
                    }
                if (head=="RC"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=modul*2.25+profile/4, d=profile*2, center=false);
                    translate([i*offset,-modul*1.25-profile/4,width/2])
                    rotate([90,0,0])
                    cylinder (h=profile/2, d1=profile*2, d2=profile, center=false);
                    }
                if (head=="CSS"){
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=height+modul, d=profile, center=false);
                    translate([i*offset,modul,width/2])
                    rotate([90,0,0])
                    cylinder(h=modul*2.25, d=profile*2, center=false);
                    translate([i*offset,-modul*1.25,width/2])
                    rotate([90,0,0])
                    cylinder (h=profile*0.6, d1=profile*2, d2=profile, center=false);
                    }
                }
            }
        }

/* Herringbone_gear; uses the module "spur_gear"
    modul = Height of the Tooth Tip beyond the Pitch Circle
    tooth_number = Number of Gear Teeth
    width = tooth_width
    bore = Diameter of the Center Hole
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle to the Axis of Rotation, Standard = 0° (Spur Teeth)
    optimized = Holes for Material-/Weight-Saving */
module herringbone_gear(modul, tooth_number, width, bore, pressure_angle = 20, helix_angle=0, optimized=true){

    width = width/2;
    d = modul * tooth_number;                                           // Pitch Circle Diameter
    r = d / 2;                                                      // Pitch Circle Radius
    c =  (tooth_number <3)? 0 : modul/6;                                // Tip Clearance

    df = d - 2 * (modul + c);                                       // Root Circle Diameter
    rf = df / 2;                                                    // Root Radius

    r_hole = (2*rf - bore)/8;                                    // Radius of Holes for Material-/Weight-Saving
    rm = bore/2+2*r_hole;                                        // Distance of the Axes of the Holes from the Main Axis
    z_hole = floor(2*pi*rm/(3*r_hole));                             // Number of Holes for Material-/Weight-Saving

    optimized = (optimized && r >= width*3 && d > 2*bore);      // is Optimization useful?

    translate([0,0,width]){
        union(){
            spur_gear(modul, tooth_number, width, 2*(rm+r_hole*1.49), pressure_angle, helix_angle, false);      // bottom Half
            mirror([0,0,1]){
                spur_gear(modul, tooth_number, width, 2*(rm+r_hole*1.49), pressure_angle, helix_angle, false);  // top Half
            }
        }
    }
    // with Material Savings
    if (optimized) {
        linear_extrude(height = width*2){
            difference(){
                    circle(r = (bore+r_hole)/2);
                    circle(r = bore/2);                          // bore
                }
            }
        linear_extrude(height = (2*width-r_hole/2 < 1.33*width) ? 1.33*width : 2*width-r_hole/2){ //width*4/3
            difference(){
                circle(r=rm+r_hole*1.51);
                union(){
                    circle(r=(bore+r_hole)/2);
                    for (i = [0:1:z_hole]){
                        translate(sphere_to_cartesian([rm,90,i*360/z_hole]))
                            circle(r = r_hole);
                    }
                }
            }
        }
    }
    // without Material Savings
    else {
        linear_extrude(height = width*2){
            difference(){
                circle(r = rm+r_hole*1.51);
                circle(r = bore/2);
            }
        }
    }
}

/*  Rack and Pinion
    modul = Height of the Tooth Tip beyond the Pitch Circle
    rack_length = Length of the Rack
    gear_teeth = Number of Gear Teeth
    rack_height = Height of the Rack to the Pitch Line
    gear_bore = Diameter of the Center Hole of the Spur Gear
    width = Width of a Tooth
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle to the Axis of Rotation, Standard = 0° (Spur Teeth) */
module rack_and_pinion (modul, rack_length, gear_teeth, rack_height, gear_bore, width, pressure_angle=20, helix_angle=0, together_built=true, optimized=true) {

    distance = together_built? modul*gear_teeth/2 : modul*gear_teeth;

    rack(modul, rack_length, rack_height, width, pressure_angle, -helix_angle);
    translate([0,distance,0])
        rotate(a=360/gear_teeth)
            spur_gear (modul, gear_teeth, width, gear_bore, pressure_angle, helix_angle, optimized);
}

/*  Ring gear
    modul = Height of the Tooth Tip beyond the Pitch Circle
    tooth_number = Number of Gear Teeth
    width = tooth_width
    rim_width = Width of the Rim from the Root Circle
    bore = Diameter of the Center Hole
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle to the Axis of Rotation, Standard = 0° (Spur Teeth) */
module ring_gear(modul, tooth_number, width, rim_width, pressure_angle = 20, helix_angle = 0) {

    // Dimension Calculations
    ha = (tooth_number >= 20) ? 0.02 * atan((tooth_number/15)/pi) : 0.6;    // Shortening Factor of Tooth Head Height
    d = modul * tooth_number;                                           // Pitch Circle Diameter
    r = d / 2;                                                      // Pitch Circle Radius
    alpha_spur = atan(tan(pressure_angle)/cos(helix_angle));// Helix Angle in Transverse Section
    db = d * cos(alpha_spur);                                      // Base Circle Diameter
    rb = db / 2;                                                    // Base Circle Radius
    c = modul / 6;                                                  // Tip Clearance
    da = (modul <1)? d + (modul+c) * 2.2 : d + (modul+c) * 2;       // Tip Diameter
    ra = da / 2;                                                    // Tip Circle Radius
    df = d - 2 * modul * ha;                                        // Root Circle Diameter
    rf = df / 2;                                                    // Root Radius
    rho_ra = acos(rb/ra);                                           // Maximum Involute Angle;
                                                                    // Involute begins on the Base Circle and ends at the Tip Circle
    rho_r = acos(rb/r);                                             // Involute Angle at Pitch Circle;
                                                                    // Involute begins on the Base Circle and ends at the Tip Circle
    phi_r = grad(tan(rho_r)-radian(rho_r));                         // Angle to Point of Involute on Pitch Circle
    gamma = rad*width/(r*tan(90-helix_angle));               // Torsion Angle for Extrusion
    step = rho_ra/16;                                            // Involute is divided into 16 pieces
    tau = 360/tooth_number;                                             // Pitch Angle

    // Drawing
    rotate([0,0,-phi_r-90*(1+clearance)/tooth_number])                      // Center Tooth on X-Axis;
                                                                    // Makes Alignment with other Gears easier
    linear_extrude(height = width, twist = gamma){
        difference(){
            circle(r = ra + rim_width);                            // Outer Circle
            union(){
                tooth_width = (180*(1+clearance))/tooth_number+2*phi_r;
                circle(rf);                                         // Root Circle
                for (rot = [0:tau:360]){
                    rotate (rot) {                                  // Copy and Rotate "Number of Teeth"
                        polygon( concat(
                            [[0,0]],
                            [for (rho = [0:step:rho_ra])         // From zero Degrees (Base Circle)
                                                                    // to Maximum Involute Angle (Tip Circle)
                                polar_to_cartesian(ev(rb,rho))],
                            [polar_to_cartesian(ev(rb,rho_ra))],
                            [for (rho = [rho_ra:-step:0])        // von Maximum Involute Angle (Kopfkreis)
                                                                    // to zero Degrees (Base Circle)
                                polar_to_cartesian([ev(rb,rho)[0], tooth_width-ev(rb,rho)[1]])]
                                                                    // (180*(1+clearance)) statt 180,
                                                                    // to allow clearance of the Flanks
                            )
                        );
                    }
                }
            }
        }
    }

    echo("Ring Gear Outer Diamater = ", 2*(ra + rim_width));

}

/*  Herringbone Ring Gear; uses the Module "ring_gear"
    modul = Height of the Tooth Tip over the Partial Cone
    tooth_number = Number of Gear Teeth
    width = tooth_width
    bore = Diameter of the Center Hole
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle to the Axis of Rotation, Standard = 0° (Spur Teeth) */
module herringbone_ring_gear(modul, tooth_number, width, rim_width, pressure_angle = 20, helix_angle = 0) {

    width = width / 2;
    translate([0,0,width])
        union(){
        ring_gear(modul, tooth_number, width, rim_width, pressure_angle, helix_angle);       // bottom Half
        mirror([0,0,1])
            ring_gear(modul, tooth_number, width, rim_width, pressure_angle, helix_angle);   // top Half
    }
}

/*  Planetary Gear; uses the Modules "herringbone_gear" and "herringbone_ring_gear"
    modul = Height of the Tooth Tip over the Partial Cone
    sun_teeth = Number of Teeth of the Sun Gear
    planet_teeth = Number of Teeth of a Planet Gear
    number_planets = Number of Planet Gears. If null, the Function will calculate the Minimum Number
    width = tooth_width
    rim_width = Width of the Rim from the Root Circle
    bore = Diameter of the Center Hole
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle to the Axis of Rotation, Standard = 0° (Spur Teeth)
    together_built =
    optimized = Create holes for Material-/Weight-Saving or Surface Enhancements where Geometry allows
    together_built = Components assembled for Construction or separated for 3D-Printing */
module planetary_gear(modul, sun_teeth, planet_teeth, number_planets, width, rim_width, bore, pressure_angle=20, helix_angle=0, together_built=true, optimized=true){

    // Dimension Calculations
    d_sun = modul*sun_teeth;                                     // Sun Pitch Circle Diameter
    d_planet = modul*planet_teeth;                                   // Planet Pitch Circle Diameter
    center_distance = modul*(sun_teeth +  planet_teeth) / 2;        // Distance from Sun- or Ring-Gear Axis to Planet Axis
    ring_teeth = sun_teeth + 2*planet_teeth;              // Number of Teeth of the Ring Gear
    d_ring = modul*ring_teeth;                                 // Ring Pitch Circle Diameter

    rotate = is_even(planet_teeth);                                // Does the Sun Gear need to be rotated?

    n_max = floor(180/asin(modul*(planet_teeth)/(modul*(sun_teeth +  planet_teeth))));
                                                                        // Number of Planet Gears: at most as many as possible without overlap

    // Drawing
    rotate([0,0,180/sun_teeth*rotate]){
        herringbone_gear (modul, sun_teeth, width, bore, pressure_angle, -helix_angle, optimized);      // Sun Gear
    }

    if (together_built){
        if(number_planets==0){
            list = [ for (n=[2 : 1 : n_max]) if ((((ring_teeth+sun_teeth)/n)==floor((ring_teeth+sun_teeth)/n))) n];
            number_planets = list[0];                                      // Determine Number of Planet Gears
             center_distance = modul*(sun_teeth + planet_teeth)/2;      // Distance from Sun- / Ring-Gear Axis
            for(n=[0:1:number_planets-1]){
                translate(sphere_to_cartesian([center_distance,90,360/number_planets*n]))
                    rotate([0,0,n*360*d_sun/d_planet])
                        herringbone_gear (modul, planet_teeth, width, bore, pressure_angle, helix_angle, optimized); // Planet Gears
            }
       }
       else{
            center_distance = modul*(sun_teeth + planet_teeth)/2;       // Distance from Sun- / Ring-Gear Axis
            for(n=[0:1:number_planets-1]){
                translate(sphere_to_cartesian([center_distance,90,360/number_planets*n]))
                rotate([0,0,n*360*d_sun/(d_planet)])
                    herringbone_gear (modul, planet_teeth, width, bore, pressure_angle, helix_angle, optimized); // Planet Gears
            }
        }
    }
    else{
        planet_distance = ring_teeth*modul/2+rim_width+d_planet;     // Distance between Planets
        for(i=[-(number_planets-1):2:(number_planets-1)]){
            translate([planet_distance, d_planet*i,0])
                herringbone_gear (modul, planet_teeth, width, bore, pressure_angle, helix_angle, optimized); // Planet Gears
        }
    }

    herringbone_ring_gear (modul, ring_teeth, width, rim_width, pressure_angle, helix_angle); // Ring Gear

}

/*  Bevel Gear
    modul = Height of the Tooth Tip over the Partial Cone; Specification for the Outside of the Cone
    tooth_number = Number of Gear Teeth
    partial_cone_angle = (Half)angle of the Cone on which the other Ring Gear rolls
    tooth_width = Width of the Teeth from the Outside toward the apex of the Cone
    bore = Diameter of the Center Hole
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle, Standard = 0° */
module bevel_gear(modul, tooth_number, partial_cone_angle, tooth_width, bore, pressure_angle = 20, helix_angle=0) {

    // Dimension Calculations
    d_outside = modul * tooth_number;                                    // Part Cone Diameter at the Cone Base,
                                                                    // corresponds to the Chord in a Spherical Section
    r_outside = d_outside / 2;                                        // Part Cone Radius at the Cone Base
    rg_outside = r_outside/sin(partial_cone_angle);                      // Large-Cone Radius for Outside-Tooth, corresponds to the Length of the Cone-Flank;
    rg_inside = rg_outside - tooth_width;                              // Large-Cone Radius for Inside-Tooth
    r_inside = r_outside*rg_inside/rg_outside;
    alpha_spur = atan(tan(pressure_angle)/cos(helix_angle));// Helix Angle in Transverse Section
    delta_b = asin(cos(alpha_spur)*sin(partial_cone_angle));          // Base Cone Angle
    da_outside = (modul <1)? d_outside + (modul * 2.2) * cos(partial_cone_angle): d_outside + modul * 2 * cos(partial_cone_angle);
    ra_outside = da_outside / 2;
    delta_a = asin(ra_outside/rg_outside);
    c = modul / 6;                                                  // Tip Clearance
    df_outside = d_outside - (modul +c) * 2 * cos(partial_cone_angle);
    rf_outside = df_outside / 2;
    delta_f = asin(rf_outside/rg_outside);
    rkf = rg_outside*sin(delta_f);                                   // Radius of the Cone Foot
    height_f = rg_outside*cos(delta_f);                               // Height of the Cone from the Root Cone

    echo("Part Cone Diameter at the Cone Base = ", d_outside);

    // Sizes for Complementary Truncated Cone
    height_k = (rg_outside-tooth_width)/cos(partial_cone_angle);          // Height of the Complementary Cone for corrected Tooth Length
    rk = (rg_outside-tooth_width)/sin(partial_cone_angle);               // Foot Radius of the Complementary Cone
    rfk = rk*height_k*tan(delta_f)/(rk+height_k*tan(delta_f));        // Tip Radius of the Cylinders for
                                                                    // Complementary Truncated Cone
    height_fk = rk*height_k/(height_k*tan(delta_f)+rk);                // height of the Complementary Truncated Cones

    echo("Bevel Gear Height = ", height_f-height_fk);

    phi_r = sphere_ev(delta_b, partial_cone_angle);                      // Angle to Point of Involute on Partial Cone

    // Torsion Angle gamma from Helix Angle
    gamma_g = 2*atan(tooth_width*tan(helix_angle)/(2*rg_outside-tooth_width));
    gamma = 2*asin(rg_outside/r_outside*sin(gamma_g/2));

    step = (delta_a - delta_b)/16;
    tau = 360/tooth_number;                                             // Pitch Angle
    start = (delta_b > delta_f) ? delta_b : delta_f;
    mirrpoint = (180*(1-clearance))/tooth_number+2*phi_r;

    // Drawing
    rotate([0,0,phi_r+90*(1-clearance)/tooth_number]){                      // Center Tooth on X-Axis;
                                                                    // Makes Alignment with other Gears easier
        translate([0,0,height_f]) rotate(a=[0,180,0]){
            union(){
                translate([0,0,height_f]) rotate(a=[0,180,0]){                               // Truncated Cone
                    difference(){
                        linear_extrude(height=height_f-height_fk, scale=rfk/rkf) circle(rkf*1.001); // 1 permille Overlap with Tooth Root
                        translate([0,0,-1]){
                            cylinder(h = height_f-height_fk+2, r = bore/2);                // bore
                        }
                    }
                }
                for (rot = [0:tau:360]){
                    rotate (rot) {                                                          // Copy and Rotate "Number of Teeth"
                        union(){
                            if (delta_b > delta_f){
                                // Tooth Root
                                flankpoint_under = 1*mirrpoint;
                                flankpoint_over = sphere_ev(delta_f, start);
                                polyhedron(
                                    points = [
                                        sphere_to_cartesian([rg_outside, start*1.001, flankpoint_under]),    // 1 permille Overlap with Tooth
                                        sphere_to_cartesian([rg_inside, start*1.001, flankpoint_under+gamma]),
                                        sphere_to_cartesian([rg_inside, start*1.001, mirrpoint-flankpoint_under+gamma]),
                                        sphere_to_cartesian([rg_outside, start*1.001, mirrpoint-flankpoint_under]),
                                        sphere_to_cartesian([rg_outside, delta_f, flankpoint_under]),
                                        sphere_to_cartesian([rg_inside, delta_f, flankpoint_under+gamma]),
                                        sphere_to_cartesian([rg_inside, delta_f, mirrpoint-flankpoint_under+gamma]),
                                        sphere_to_cartesian([rg_outside, delta_f, mirrpoint-flankpoint_under])
                                    ],
                                    faces = [[0,1,2],[0,2,3],[0,4,1],[1,4,5],[1,5,2],[2,5,6],[2,6,3],[3,6,7],[0,3,7],[0,7,4],[4,6,5],[4,7,6]],
                                    convexity =1
                                );
                            }
                            // Tooth
                            for (delta = [start:step:delta_a-step]){
                                flankpoint_under = sphere_ev(delta_b, delta);
                                flankpoint_over = sphere_ev(delta_b, delta+step);
                                polyhedron(
                                    points = [
                                        sphere_to_cartesian([rg_outside, delta, flankpoint_under]),
                                        sphere_to_cartesian([rg_inside, delta, flankpoint_under+gamma]),
                                        sphere_to_cartesian([rg_inside, delta, mirrpoint-flankpoint_under+gamma]),
                                        sphere_to_cartesian([rg_outside, delta, mirrpoint-flankpoint_under]),
                                        sphere_to_cartesian([rg_outside, delta+step, flankpoint_over]),
                                        sphere_to_cartesian([rg_inside, delta+step, flankpoint_over+gamma]),
                                        sphere_to_cartesian([rg_inside, delta+step, mirrpoint-flankpoint_over+gamma]),
                                        sphere_to_cartesian([rg_outside, delta+step, mirrpoint-flankpoint_over])
                                    ],
                                    faces = [[0,1,2],[0,2,3],[0,4,1],[1,4,5],[1,5,2],[2,5,6],[2,6,3],[3,6,7],[0,3,7],[0,7,4],[4,6,5],[4,7,6]],
                                    convexity =1
                                );
                            }
                        }
                    }
                }
            }
        }
    }
}

/*  Bevel Herringbone Gear; uses the Module "bevel_gear"
    modul = Height of the Tooth Tip beyond the Pitch Circle
    tooth_number = Number of Gear Teeth
    partial_cone_angle, tooth_width
    bore = Diameter of the Center Hole
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle, Standard = 0° */
module bevel_herringbone_gear(modul, tooth_number, partial_cone_angle, tooth_width, bore, pressure_angle = 20, helix_angle=0){

    // Dimension Calculations

    tooth_width = tooth_width / 2;

    d_outside = modul * tooth_number;                                // Part Cone Diameter at the Cone Base,
                                                                // corresponds to the Chord in a Spherical Section
    r_outside = d_outside / 2;                                    // Part Cone Radius at the Cone Base
    rg_outside = r_outside/sin(partial_cone_angle);                  // Large-Cone Radius, corresponds to the Length of the Cone-Flank;
    c = modul / 6;                                              // Tip Clearance
    df_outside = d_outside - (modul +c) * 2 * cos(partial_cone_angle);
    rf_outside = df_outside / 2;
    delta_f = asin(rf_outside/rg_outside);
    height_f = rg_outside*cos(delta_f);                           // Height of the Cone from the Root Cone

    // Torsion Angle gamma from Helix Angle
    gamma_g = 2*atan(tooth_width*tan(helix_angle)/(2*rg_outside-tooth_width));
    gamma = 2*asin(rg_outside/r_outside*sin(gamma_g/2));

    echo("Part Cone Diameter at the Cone Base = ", d_outside);

    // Sizes for Complementary Truncated Cone
    height_k = (rg_outside-tooth_width)/cos(partial_cone_angle);      // Height of the Complementary Cone for corrected Tooth Length
    rk = (rg_outside-tooth_width)/sin(partial_cone_angle);           // Foot Radius of the Complementary Cone
    rfk = rk*height_k*tan(delta_f)/(rk+height_k*tan(delta_f));    // Tip Radius of the Cylinders for
                                                                // Complementary Truncated Cone
    height_fk = rk*height_k/(height_k*tan(delta_f)+rk);            // height of the Complementary Truncated Cones

    modul_inside = modul*(1-tooth_width/rg_outside);
    
    lower_cone_angle = partial_cone_angle - 1; // Correct for mirroring misalignment

    union(){
        // Outer ring
        if(1)
        bevel_gear(
            modul,
            tooth_number,
            lower_cone_angle,
            tooth_width,
            bore,
            pressure_angle,
            helix_angle);
        // Inner ring
        if(1)
        translate([0,0,height_f-height_fk])
            rotate(a=-gamma,v=[0,0,1])
                bevel_gear(
                    modul_inside,
                    tooth_number,
                    partial_cone_angle,
                    tooth_width,
                    bore,
                    pressure_angle,
                    -helix_angle);
    }
}

/*  Spiral Bevel Gear; uses the Module "bevel_gear"
    modul = Height of the Tooth Tip beyond the Pitch Circle
    tooth_number = Number of Gear Teeth
    height = Height of Gear Teeth
    bore = Diameter of the Center Hole
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle, Standard = 0° */
module spiral_bevel_gear(modul, tooth_number, partial_cone_angle, tooth_width, bore, pressure_angle = 20, helix_angle=30){

    steps = 16;

    // Dimension Calculations

    b = tooth_width / steps;
    d_outside = modul * tooth_number;                                // Part Cone Diameter at the Cone Base,
                                                                // corresponds to the Chord in a Spherical Section
    r_outside = d_outside / 2;                                    // Part Cone Radius at the Cone Base
    rg_outside = r_outside/sin(partial_cone_angle);                  // Large-Cone Radius, corresponds to the Length of the Cone-Flank;
    rg_center = rg_outside-tooth_width/2;

    echo("Part Cone Diameter at the Cone Base = ", d_outside);

    a=tan(helix_angle)/rg_center;

    union(){
    for(i=[0:1:steps-1]){
        r = rg_outside-i*b;
        helix_angle = a*r;
        modul_r = modul-b*i/rg_outside;
        translate([0,0,b*cos(partial_cone_angle)*i])

            rotate(a=-helix_angle*i,v=[0,0,1])
                bevel_gear(modul_r, tooth_number, partial_cone_angle, b, bore, pressure_angle, helix_angle);   // top Half
        }
    }
}

/*  Bevel Gear Pair with any axis_angle; uses the Module "bevel_gear"
    modul = Height of the Tooth Tip over the Partial Cone; Specification for the Outside of the Cone
    gear_teeth = Number of Gear Teeth on the Gear
    pinion_teeth = Number of Gear Teeth on the Pinion
    axis_angle = Angle between the Axles of the Gear and Pinion
    tooth_width = Width of the Teeth from the Outside toward the apex of the Cone
    gear_bore = Diameter of the Center Hole of the Gear
    pinion_bore = Diameter of the Center Bore of the Gear
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle, Standard = 0°
    together_built = Components assembled for Construction or separated for 3D-Printing */
module bevel_gear_pair(modul, gear_teeth, pinion_teeth, axis_angle=90, tooth_width, gear_bore, pinion_bore, pressure_angle=20, helix_angle=0, together_built=true){

    // Dimension Calculations
    r_gear = modul*gear_teeth/2;                           // Cone Radius of the Gear
    delta_gear = atan(sin(axis_angle)/(pinion_teeth/gear_teeth+cos(axis_angle)));   // Cone Angle of the Gear
    delta_pinion = atan(sin(axis_angle)/(gear_teeth/pinion_teeth+cos(axis_angle)));// Cone Angle of the Pinion
    rg = r_gear/sin(delta_gear);                              // Radius of the Large Sphere
    c = modul / 6;                                          // Tip Clearance
    df_pinion = pi*rg*delta_pinion/90 - 2 * (modul + c);    // Bevel Diameter on the Large Sphere
    rf_pinion = df_pinion / 2;                              // Root Cone Radius on the Large Sphere
    delta_f_pinion = rf_pinion/(pi*rg) * 180;               // Tip Cone Angle
    rkf_pinion = rg*sin(delta_f_pinion);                    // Radius of the Cone Foot
    height_f_pinion = rg*cos(delta_f_pinion);                // Height of the Cone from the Root Cone

    echo("Cone Angle Gear = ", delta_gear);
    echo("Cone Angle Pinion = ", delta_pinion);

    df_gear = pi*rg*delta_gear/90 - 2 * (modul + c);          // Bevel Diameter on the Large Sphere
    rf_gear = df_gear / 2;                                    // Root Cone Radius on the Large Sphere
    delta_f_gear = rf_gear/(pi*rg) * 180;                     // Tip Cone Angle
    rkf_gear = rg*sin(delta_f_gear);                          // Radius of the Cone Foot
    height_f_gear = rg*cos(delta_f_gear);                      // Height of the Cone from the Root Cone

    echo("Gear Height = ", height_f_gear);
    echo("Pinion Height = ", height_f_pinion);

    rotate = is_even(pinion_teeth);

    // Drawing
    // Rad
    rotate([0,0,180*(1-clearance)/gear_teeth*rotate])
        bevel_gear(modul, gear_teeth, delta_gear, tooth_width, gear_bore, pressure_angle, helix_angle);

    // Ritzel
    if (together_built)
        translate([-height_f_pinion*cos(90-axis_angle),0,height_f_gear-height_f_pinion*sin(90-axis_angle)])
            rotate([0,axis_angle,0])
                bevel_gear(modul, pinion_teeth, delta_pinion, tooth_width, pinion_bore, pressure_angle, -helix_angle);
    else
        translate([rkf_pinion*2+modul+rkf_gear,0,0])
            bevel_gear(modul, pinion_teeth, delta_pinion, tooth_width, pinion_bore, pressure_angle, -helix_angle);
 }

/*  Herringbone Bevel Gear Pair with arbitrary axis_angle; uses the Module "bevel_herringbone_gear"
    modul = Height of the Tooth Tip over the Partial Cone; Specification for the Outside of the Cone
    gear_teeth = Number of Gear Teeth on the Gear
    pinion_teeth = Number of Gear Teeth on the Pinion
    axis_angle = Angle between the Axles of the Gear and Pinion
    tooth_width = Width of the Teeth from the Outside toward the apex of the Cone
    gear_bore = Diameter of the Center Hole of the Gear
    pinion_bore = Diameter of the Center Bore of the Gear
    pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
    helix_angle = Helix Angle, Standard = 0°
    together_built = Components assembled for Construction or separated for 3D-Printing */
module bevel_herringbone_gear_pair(modul, gear_teeth, pinion_teeth, axis_angle=90, tooth_width, gear_bore, pinion_bore, pressure_angle = 20, helix_angle=10, together_built=true){

    r_gear = modul*gear_teeth/2;                           // Cone Radius of the Gear
    delta_gear = atan(sin(axis_angle)/(pinion_teeth/gear_teeth+cos(axis_angle)));   // Cone Angle of the Gear
    delta_pinion = atan(sin(axis_angle)/(gear_teeth/pinion_teeth+cos(axis_angle)));// Cone Angle of the Pinion
    rg = r_gear/sin(delta_gear);                              // Radius of the Large Sphere
    c = modul / 6;                                          // Tip Clearance
    df_pinion = pi*rg*delta_pinion/90 - 2 * (modul + c);    // Bevel Diameter on the Large Sphere
    rf_pinion = df_pinion / 2;                              // Root Cone Radius on the Large Sphere
    delta_f_pinion = rf_pinion/(pi*rg) * 180;               // Tip Cone Angle
    rkf_pinion = rg*sin(delta_f_pinion);                    // Radius of the Cone Foot
    height_f_pinion = rg*cos(delta_f_pinion);                // Height of the Cone from the Root Cone

    echo("Cone Angle Gear = ", delta_gear);
    echo("Cone Angle Pinion = ", delta_pinion);

    df_gear = pi*rg*delta_gear/90 - 2 * (modul + c);          // Bevel Diameter on the Large Sphere
    rf_gear = df_gear / 2;                                    // Root Cone Radius on the Large Sphere
    delta_f_gear = rf_gear/(pi*rg) * 180;                     // Tip Cone Angle
    rkf_gear = rg*sin(delta_f_gear);                          // Radius of the Cone Foot
    height_f_gear = rg*cos(delta_f_gear);                      // Height of the Cone from the Root Cone

    echo("Gear Height = ", height_f_gear);
    echo("Pinion Height = ", height_f_pinion);

    rotate = is_even(pinion_teeth);

    // Gear
    rotate([0,0,180*(1-clearance)/gear_teeth*rotate])
        bevel_herringbone_gear(modul, gear_teeth, delta_gear, tooth_width, gear_bore, pressure_angle, helix_angle);

    // Pinion
    if (together_built)
        translate([-height_f_pinion*cos(90-axis_angle),0,height_f_gear-height_f_pinion*sin(90-axis_angle)])
            rotate([0,axis_angle,0])
                bevel_herringbone_gear(modul, pinion_teeth, delta_pinion, tooth_width, pinion_bore, pressure_angle, -helix_angle);
    else
        translate([rkf_pinion*2+modul+rkf_gear,0,0])
            bevel_herringbone_gear(modul, pinion_teeth, delta_pinion, tooth_width, pinion_bore, pressure_angle, -helix_angle);

}

/*
Archimedean screw.
modul = Height of the Screw Head over the Part Cylinder
thread_starts = Number of Starts (Threads) of the Worm
length = Length of the Worm
bore = Diameter of the Center Hole
pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
lead_angle = Lead Angle of the Worm, corresponds to 90° minus Helix Angle. Positive Lead Angle = clockwise.
together_built = Components assembled for Construction or separated for 3D-Printing */
module worm(modul, thread_starts, length, bore, pressure_angle=20, lead_angle, together_built=true){

    // Dimension Calculations
    c = modul / 6;                                              // Tip Clearance
    r = modul*thread_starts/(2*sin(lead_angle));                // Part-Cylinder Radius
    rf = r - modul - c;                                         // Root-Cylinder Radius
    a = modul*thread_starts/(90*tan(pressure_angle));               // Spiralparameter
    tau_max = 180/thread_starts*tan(pressure_angle);                // Angle from Foot to Tip in the Normal Plane
    gamma = -rad*length/((rf+modul+c)*tan(lead_angle));    // Torsion Angle for Extrusion

    step = tau_max/16;

    // Drawing: Extrude with a Twist a Surface enclosed by two Archimedean Spirals
    if (together_built) {
        rotate([0,0,tau_max]){
            linear_extrude(height = length, center = false, convexity = 10, twist = gamma){
                difference(){
                    union(){
                        for(i=[0:1:thread_starts-1]){
                            polygon(
                                concat(
                                    [[0,0]],

                                    // rising Tooth Flank
                                    [for (tau = [0:step:tau_max])
                                        polar_to_cartesian([spiral(a, rf, tau), tau+i*(360/thread_starts)])],

                                    // Tooth Tip
                                    [for (tau = [tau_max:step:180/thread_starts])
                                        polar_to_cartesian([spiral(a, rf, tau_max), tau+i*(360/thread_starts)])],

                                    // descending Tooth Flank
                                    [for (tau = [180/thread_starts:step:(180/thread_starts+tau_max)])
                                        polar_to_cartesian([spiral(a, rf, 180/thread_starts+tau_max-tau), tau+i*(360/thread_starts)])]
                                )
                            );
                        }
                        circle(rf);
                    }
                    circle(bore/2); // Mittelbohrung
                }
            }
        }
    }
    else {
        difference(){
            union(){
                translate([1,r*1.5,0]){
                    rotate([90,0,90])
                        worm(modul, thread_starts, length, bore, pressure_angle, lead_angle, together_built=true);
                }
                translate([length+1,-r*1.5,0]){
                    rotate([90,0,-90])
                        worm(modul, thread_starts, length, bore, pressure_angle, lead_angle, together_built=true);
                    }
                }
            translate([length/2+1,0,-(r+modul+1)/2]){
                    cube([length+2,3*r+2*(r+modul+1),r+modul+1], center = true);
                }
        }
    }
}

/*
Calculates a worm wheel set. The worm wheel is an ordinary spur gear without globoidgeometry.
modul = Height of the screw head above the partial cylinder or the tooth head above the pitch circle
tooth_number = Number of wheel teeth
thread_starts = Number of gears (teeth) of the screw
width = tooth_width
length = Length of the Worm
worm_bore = Diameter of the Center Hole of the Worm
gear_bore = Diameter of the Center Hole of the Spur Gear
pressure_angle = Pressure Angle, Standard = 20° according to DIN 867. Should not exceed 45°.
lead_angle = Pitch angle of the worm corresponds to 90 ° bevel angle. Positive slope angle = clockwise.
optimized = Holes for material / weight savings
together_built =  Components assembled for construction or apart for 3D printing */
module worm_gear(modul, tooth_number, thread_starts, width, length, worm_bore, gear_bore, pressure_angle=20, lead_angle, optimized=true, together_built=true, show_spur=1, show_worm=1){

    c = modul / 6;                                              // Tip Clearance
    r_worm = modul*thread_starts/(2*sin(lead_angle));       // Worm Part-Cylinder Radius
    r_gear = modul*tooth_number/2;                                   // Spur Gear Part-Cone Radius
    rf_worm = r_worm - modul - c;                       // Root-Cylinder Radius
    gamma = -90*width*sin(lead_angle)/(pi*r_gear);         // Spur Gear Rotation Angle
    tooth_distance = modul*pi/cos(lead_angle);                // Tooth Spacing in Transverse Section
    x = is_even(thread_starts)? 0.5 : 1;

    if (together_built) {
        if(show_worm)
        translate([r_worm,(ceil(length/(2*tooth_distance))-x)*tooth_distance,0])
            rotate([90,180/thread_starts,0])
                worm(modul, thread_starts, length, worm_bore, pressure_angle, lead_angle, together_built);

        if(show_spur)
        translate([-r_gear,0,-width/2])
            rotate([0,0,gamma])
                spur_gear (modul, tooth_number, width, gear_bore, pressure_angle, -lead_angle, optimized);
    }
    else {
        if(show_worm)
        worm(modul, thread_starts, length, worm_bore, pressure_angle, lead_angle, together_built);

        if(show_spur)
        translate([-2*r_gear,0,0])
            spur_gear (modul, tooth_number, width, gear_bore, pressure_angle, -lead_angle, optimized);
    }
}

//rack(modul=1, length=60, height=5, width=20, pressure_angle=20, helix_angle=0);

//mountable_rack(modul=1, length=60, height=5, width=20, pressure_angle=20, helix_angle=0, profile=3, head="PH",fastners=3);

//herringbone_rack(modul=1, length=60, height=5, width=20, pressure_angle=20, helix_angle=45);

//mountable_herringbone_rack(modul=1, length=60, height=5, width=20, pressure_angle=20, helix_angle=45, profile=3, head="PH",fastners=3);

//spur_gear (modul=1, tooth_number=30, width=5, bore=4, pressure_angle=20, helix_angle=20, optimized=true);

//herringbone_gear (modul=1, tooth_number=30, width=5, bore=4, pressure_angle=20, helix_angle=30, optimized=true);

//rack_and_pinion (modul=1, rack_length=50, gear_teeth=30, rack_height=4, gear_bore=4, width=5, pressure_angle=20, helix_angle=0, together_built=true, optimized=true);

//ring_gear (modul=1, tooth_number=30, width=5, rim_width=3, pressure_angle=20, helix_angle=20);

//herringbone_ring_gear (modul=1, tooth_number=30, width=5, rim_width=3, pressure_angle=20, helix_angle=30);

//planetary_gear(modul=1, sun_teeth=16, planet_teeth=9, number_planets=5, width=5, rim_width=3, bore=4, pressure_angle=20, helix_angle=30, together_built=true, optimized=true);

//planetary_gear(modul=2, sun_teeth=16, planet_teeth=9, number_planets=5, width=5, rim_width=3, bore=4, pressure_angle=20, helix_angle=30, together_built=true, optimized=false);

//bevel_gear(modul=1, tooth_number=30,  partial_cone_angle=45, tooth_width=5, bore=4, pressure_angle=20, helix_angle=20);

//bevel_herringbone_gear(modul=1, tooth_number=30, partial_cone_angle=45, tooth_width=5, bore=4, pressure_angle=20, helix_angle=30);

//bevel_gear_pair(modul=1, gear_teeth=30, pinion_teeth=11, axis_angle=100, tooth_width=5, gear_bore=4, pinion_bore=4, pressure_angle = 20, helix_angle=20, together_built=true);

/*
bevel_herringbone_gear_pair(
    modul=1,
    gear_teeth=114,
    pinion_teeth=11,
    axis_angle=90,
    tooth_width=5,
    gear_bore=0,
    pinion_bore=4,
    pressure_angle=20,
    helix_angle=20,
    together_built=true);
*/

//worm(modul=1, thread_starts=2, length=15, bore=4, pressure_angle=20, lead_angle=10, together_built=true);

//worm_gear(modul=1, tooth_number=30, thread_starts=2, width=8, length=20, worm_bore=4, gear_bore=4, pressure_angle=20, lead_angle=10, optimized=1, together_built=1, show_spur=1, show_worm=1);
