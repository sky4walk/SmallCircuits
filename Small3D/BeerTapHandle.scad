// ============================================================
// Beer Tap Handle
// ============================================================

// --- Handle ---
handle_height       = 80;
handle_radius       = 10;
sphere_radius       = 20;
neck_height         = 20;

// --- Pillar ---
pillar_height       = 22;   // Höhe des Pillars (mind. 21.5mm für Gewinde)
pillar_radius       = 13;   // Radius des Pillars

// --- Shield ---
shield_width        = 50;
shield_height       = 50;
shield_thickness    = 10;
shield_tilt_angle   = -90;
shield_offset       = shield_height - shield_height / 5;

// --- Rahmen auf der Vorderseite ---
frame_wall          = 3;    // Breite der Rahmenstege (links/rechts/unten)
frame_height        = 4;    // Wie weit der Rahmen von der Shield-Fläche absteht
frame_corner_r      = 8;    // Eckenradius (passend zum Shield)
frame_lip           = 1.5;  // Lippe die innen über den Zettel greift (hält ihn vorne)

// --- 3/8" G-Innengewinde (BSP / Whitworth) ---
thread_designator   = "UNC-3/8"; // Normbezeichnung für threadlib
thread_turns        = 10;       // 10 Gänge × 1.5875mm (UNC-3/8) ≈ 16mm Tiefe
thread_depth_extra  = 2;        // Zusätzlicher Freistich unter dem Gewinde (mm)

// --- Render-Qualität ---
fn = 100;



include <threadlib.scad>

// ============================================================
// Module
// ============================================================

module pillar_to_shaft_transition() {
    hull() {
        translate([0, 0, pillar_height])
            cylinder(r=handle_radius, h=0.1, $fn=fn);
        translate([0, 0, pillar_height / 2])
            cylinder(r=pillar_radius, h=0.1, $fn=fn);
    }
}

module beer_tap_handle() {
    union() {
        hull() {
            translate([0, 0, handle_height + pillar_height])
                sphere(r=sphere_radius, $fn=fn);
            translate([0, 0, pillar_height])
                cylinder(r=handle_radius, h=neck_height, $fn=fn);
        }
        pillar_to_shaft_transition();
        cylinder(r=pillar_radius, h=pillar_height, $fn=fn);
    }
}

module fillet(r, h) {
    translate([r / 2, r / 2, 0])
        difference() {
            cube([r + 0.01, r + 0.01, h], center=true);
            translate([r / 2, r / 2, 0])
                cylinder(r=r, h=h + 1, center=true);
        }
}

module rounded_rect(w, h, r) {
    r_safe = min(r, w/2 - 0.01, h/2 - 0.01);
    hull() {
        translate([ w/2 - r_safe,  h/2 - r_safe]) circle(r=r_safe, $fn=fn);
        translate([-w/2 + r_safe,  h/2 - r_safe]) circle(r=r_safe, $fn=fn);
        translate([ w/2 - r_safe, -h/2 + r_safe]) circle(r=r_safe, $fn=fn);
        translate([-w/2 + r_safe, -h/2 + r_safe]) circle(r=r_safe, $fn=fn);
    }
}

// ----------------------------------------------------------------
// label_frame() – supportfreie Version für aufrechten Druck
//
// Das Schild liegt beim Drucken flach (Vorderseite oben), daher
// zeigt die Z-Achse des Schilds nach oben im Druckraum.
// Der Rahmen wächst in +Z (= weg von der Shield-Fläche) → kein Überhang.
//
// Die Unterseite des Rahmens (Shield-Fläche) ist die Grundfläche →
// keine hängenden Flächen.
// Die Innenkante des Rahmens bekommt eine 45°-Fase (chamfer) an der
// Oberkante, damit auch die innere Wand supportfrei bleibt.
// ----------------------------------------------------------------
module label_frame() {
    z = shield_thickness / 2;

    // Chamfer-Größe: gleich frame_lip, min. 0.8mm
    chamfer = max(frame_lip, 0.8);

    translate([0, 0, z]) {

        // --- Hauptrahmen (links, rechts, unten; oben offen) ---
        // Außenprofil minus Innenprofil, als Polygon mit 45°-Fase oben innen
        linear_extrude(height = frame_height - chamfer) {
            difference() {
                intersection() {
                    rounded_rect(shield_width, shield_height, frame_corner_r);
                    translate([0, frame_wall/2])
                        square([shield_width, shield_height - frame_wall], center=true);
                }
                translate([0, -frame_wall/2])
                    square([shield_width  - 2*frame_wall,
                            shield_height - frame_wall], center=true);
            }
        }

        // --- Chamfer-Ring oben innen (45°-Fase) ---
        // Schräger Ring: außen auf Rahmen-Außenkontur, innen läuft nach innen
        translate([0, 0, frame_height - chamfer])
            linear_extrude(height = chamfer, scale = 1) {
                // Schritt für Schritt: Außenprofil bleibt, Innenprofil schrumpft
                // → wird mit hull() von Vollprofil auf äußeres Profil interpoliert
                difference() {
                    intersection() {
                        rounded_rect(shield_width, shield_height, frame_corner_r);
                        translate([0, frame_wall/2])
                            square([shield_width, shield_height - frame_wall], center=true);
                    }
                    // Innenöffnung schrumpft um chamfer → ergibt 45°-Fase
                    translate([0, -frame_wall/2])
                        square([shield_width  - 2*frame_wall - 0,
                                shield_height - frame_wall  - 0], center=true);
                }
            }

        // --- Lippe (hält Zettel) ---
        // Liegt direkt auf dem Hauptrahmen, wächst nach oben → kein Überhang
        translate([0, 0, frame_height - frame_lip])
            linear_extrude(height = frame_lip) {
                difference() {
                    intersection() {
                        rounded_rect(shield_width, shield_height, frame_corner_r);
                        translate([0, frame_wall/2])
                            square([shield_width, shield_height - frame_wall], center=true);
                    }
                    translate([0, -frame_wall/2])
                        square([shield_width  - 2*frame_wall - 2*frame_lip,
                                shield_height - frame_wall  -   frame_lip], center=true);
                }
            }
    }
}

// ----------------------------------------------------------------
// shield() – mit 45-Fase an der Druckbett-zugewandten Unterseite
//
// Beim aufrechten Druck (Pillar unten) zeigt -Z des Shields nach
// unten (Ueberhang). Eine 45-Fase an allen vier unteren Kanten
// macht die Unterseite supportfrei druckbar.
// ----------------------------------------------------------------
module shield(w, h, t) {
    corner_r = w / 4;
    shield_chamfer = min(t / 2, 4);

    difference() {
        union() {
            // Hauptkoerper (ohne unterste shield_chamfer mm)
            translate([0, 0, shield_chamfer / 2])
                cube([w, h, t - shield_chamfer], center=true);

            // 45-Fase unten: hull von schmalem Boden zu vollem Querschnitt
            hull() {
                translate([0, 0, -t/2])
                    cube([w - 2*shield_chamfer, h - 2*shield_chamfer, 0.01], center=true);
                translate([0, 0, -t/2 + shield_chamfer])
                    cube([w, h, 0.01], center=true);
            }
        }

        // Ecken-Fillets (XY-Ebene)
        translate([-w/2, -h/2, 0]) rotate([0,0,  0]) fillet(corner_r, t+1);
        translate([-w/2,  h/2, 0]) rotate([0,0,-90]) fillet(corner_r, t+1);
        translate([ w/2, -h/2, 0]) rotate([0,0, 90]) fillet(corner_r, t+1);
        translate([ w/2,  h/2, 0]) rotate([0,0,180]) fillet(corner_r, t+1);
    }

    // Einlaufschraege oben (unter der Zettel-Lippe):
    // fillet() waechst im +X/+Y-Quadranten. Mit translate auf (-w/2, h/2)
    // und (+w/2, h/2) liegt die Rundung bündig unter der Oberkante des Shields.
    translate([  .8, h/2, 7])                fillet(w/3, 4);
    translate([ -.8, h/2, 7]) mirror([1,0,0]) fillet(w/3, 4);

    label_frame();
}

// tap() aus threadlib liefert ein positives Objekt:
// Kernzylinder mit eingeschnittenen Gewinderippen (fertiges Negativ-Werkzeug).
// Dieses wird als Ganzes aus dem Hauptkörper herausgeschnitten.
module inner_thread_pocket() {
    specs    = thread_specs(str(thread_designator, "-int"));
    P        = specs[0];
    Dsupport = specs[2];
    chamfer  = 0.8;

    union() {
        // tap() = Kernzylinder minus Gewinderippen
        tap(thread_designator,
            turns      = thread_turns,
            higbee_arc = 20,
            fn         = fn);

        // Fase am Eingang (Unterseite Pillar = Z=0)
        translate([0, 0, -P / 2 - chamfer])
            cylinder(h  = chamfer + 0.01,
                     d1 = Dsupport + 2 * chamfer,
                     d2 = Dsupport,
                     $fn = fn);

        // Freistich unterhalb des Gewindes
        translate([0, 0, -P / 2 - chamfer - thread_depth_extra])
            cylinder(h  = thread_depth_extra + 0.01,
                     d  = Dsupport,
                     $fn = fn);
    }
}

module main() {
    rotate([shield_tilt_angle, 0, 0])
        translate([0, -(handle_height + pillar_height + shield_offset), 0])
            shield(shield_width, shield_height, shield_thickness);

    // Handle mit UNC-3/8-Innengewinde unten.
    // tap() liefert bereits den fertigen Negativ-Körper (Zylinder + Gewinde),
    // der direkt aus dem Hauptkörper herausgeschnitten wird.
    difference() {
        beer_tap_handle();
        inner_thread_pocket();
    }
}

main();
