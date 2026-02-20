// ============================================================
// OpenSCAD Rekonstruktion: 42003_fixed.stl
// Lego Technic Winkelverbinder (Angle Connector / L-Beam)
// ============================================================
//
// Koordinatensystem:
//   X = Längsachse des linken Arms
//   Y = Breite
//   Z = Höhe
//
// Bohrungen 1+2: Achse in Y-Richtung (horizontal durchgehend)
// Bohrung 3:     Achshalter in Z-Richtung (90° verdreht),
//                Kreuzprofil wie Lego Technic Bush
// ============================================================

// --- KÖRPERMASSE ---
body_width   = 7.2;               // Y
body_height  = 8.0;               // Z
body_half_w  = body_width  / 2;   // 3.6
body_half_h  = body_height / 2;   // 4.0
left_cap_r   = body_half_w;       // 3.6
right_cap_r  = body_half_h;       // 4.0

// --- BOHRUNGEN 1 + 2 (rund, Y-Richtung) ---
bore_r       = 2.4;    // Radius Ø4.8mm (Lego Technic Standard)
boss_r       = 3.15;   // Außenradius des inneren Wulstrings
boss_h       = 0.8;    // Breite des inneren Wulstrings (ragt ins Innere)
pin_recess_r = 3.15;   // Radius der Pinaufnahme-Aussenkung (um die Bohrung)
pin_recess_d = 0.9;    // Tiefe der Pinaufnahme-Aussenkung

// --- BOHRUNG 3: Lego Technic Bush / Achshalter (Z-Richtung) ---
// Der Bush-Sitz besteht aus:
//   - Kreuzprofil innen: 4.8 x 1.8mm  (hält die Achse)
//   - Zylindrischer Außensitz: Ø4.8mm  (= gleich wie Bohrung 1+2,
//     damit Bush bündig sitzt; Abflachungen verhindern Verdrehen)
// Die Abflachungen schneiden den Zylinder auf bush_flat ab.
cross_arm_l  = 4.8;   // Länge Kreuzarm
cross_arm_w  = 1.8;   // Breite Kreuzarm
bush_r       = 2.4;   // Außenradius Bush-Zylinder (= bore_r, Ø4.8mm)
bush_flat    = 1.6;   // Halbbreite der Abflachung (schneidet Zylinder ab)
              //  -> Abflachung bei Y = ±1.6mm vom Zentrum

// --- POSITIONEN ---
bore1_x  = 4.2;
bore2_x  = 12.2;
bore3_x  = 20.2;
arm_len  = bore3_x;   // Körper endet am rechten Cap-Mittelpunkt

$fn = 64;

// ============================================================
// HAUPTMODELL
// ============================================================
module lego_angle_connector() {
    difference() {
        union() {
            body_solid();
            boss_y(bore1_x);
            boss_y(bore2_x);
            boss_z(bore3_x);
        }
        bore_y(bore1_x);
        bore_y(bore2_x);
        bush_z(bore3_x);
    }
}

// ============================================================
// KÖRPER
// ============================================================
module body_solid() {
    // Quader Mittelteil
    translate([0, -body_half_w, 0])
        cube([arm_len, body_width, body_height]);
    // Linke Endkappe (Halbzylinder in XY)
    intersection() {
        cylinder(h = body_height, r = left_cap_r);
        translate([-(left_cap_r+1), -(left_cap_r+1), -0.1])
            cube([left_cap_r+1, (left_cap_r+1)*2, body_height+0.2]);
    }
    // Rechte Endkappe (Halbzylinder in XZ)
    translate([arm_len, 0, body_half_h])
        intersection() {
            rotate([90,0,0])
                cylinder(h = body_width+0.2, r = right_cap_r, center=true);
            translate([0, -(body_half_w+0.1), -(right_cap_r+1)])
                cube([right_cap_r+1, body_width+0.2, (right_cap_r+1)*2]);
        }
}

// ============================================================
// BOSS-BUNDE
// ============================================================
module boss_y(xpos) {
    // Innerer Wulstring: sitzt bündig mit der Außenfläche,
    // ragt als schmaler Ring ins Körperinnere (je eine Seite pro Y-Fläche)
    for (s = [-1, 1])
        translate([xpos, s * (body_half_w - boss_h), body_half_h])
            rotate([90, 0, 0])
                difference() {
                    cylinder(h = boss_h, r = boss_r, center = false);
                    translate([0, 0, -0.01])
                        cylinder(h = boss_h + 0.02, r = bore_r, center = false);
                }
}

module boss_z(xpos) {
    // Innerer Wulstring: bündig mit Ober-/Unterseite, ragt ins Körperinnere
    // s=+1: bei Z = body_height - boss_h (von oben nach innen)
    // s=-1: bei Z = 0 (von unten nach innen)
    for (s = [-1, 1])
        translate([xpos, 0, s > 0 ? body_height - boss_h : 0])
            difference() {
                cylinder(h = boss_h, r = boss_r, center = false);
                translate([0, 0, -0.01])
                    cylinder(h = boss_h + 0.02, r = bush_r, center = false);
            }
}

// ============================================================
// BOHRUNGEN
// ============================================================

// Runde Durchgangsbohrung in Y-Richtung mit Pinaufnahme-Aussenkung
module bore_y(xpos) {
    len = body_width + 2;
    translate([xpos, 0, body_half_h])
        rotate([90, 0, 0]) {
            // Hauptbohrung
            cylinder(h = len, r = bore_r, center = true);
            // Pinaufnahme: flache Kreisaussenkung auf beiden Seiten
            // s=+1: Aussenkung von +body_half_w nach innen (nach -Z)
            // s=-1: Aussenkung von -body_half_w nach innen (nach +Z)
            for (s = [-1, 1])
                translate([0, 0, s * body_half_w - (s > 0 ? pin_recess_d : 0)])
                    cylinder(h = pin_recess_d + 0.01,
                             r = pin_recess_r,
                             center = false);
        }
}

// Achshalter in Z-Richtung: Kreuzprofil mit abgerundeten Enden
module bush_z(xpos) {
    len = body_height + 2;
    translate([xpos, 0, body_half_h]) {
        // Kreuzprofil: je zwei Zylinder entlang X und Y
        // -> abgerundete Enden wie das echte Lego-Achsprofil
        for (rot = [0, 90])
            rotate([0, 0, rot])
                hull() {
                    translate([ cross_arm_l/2 - cross_arm_w/2, 0, 0])
                        cylinder(h = len, r = cross_arm_w/2, center = true);
                    translate([-cross_arm_l/2 + cross_arm_w/2, 0, 0])
                        cylinder(h = len, r = cross_arm_w/2, center = true);
                }
    }
}

// ============================================================
// RENDER
// ============================================================
lego_angle_connector();


//include <Technic.scad>;

//color( "yellow" ) 
/*
difference() {

    difference() {
        technic_beam( length = 3, height = 1 );
        translate([-7.1,-3.1,-1]) cube([10,6.2,10]);
    }
    translate([-10,-5,-1]) cube([10,10,10]);
}
//translate([0,3.9,4]) rotate([90,0,0]) technic_bush( height = 1, stud_cutouts = false );
*/
