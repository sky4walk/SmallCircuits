// =====================================================================
//  TriClamp – parametrische Neufassung (CSG statt Polyhedron-Dump)
//  Maße aus dem Original-Mesh (TriClamp.scad) herausgemessen.
//  Achsen wie im Original: Rohrachse ‖ z, Scharnierachse ‖ z.
// =====================================================================
$fn = 96;

// ---- Bügel (beide Hälften gleich) -----------------------------------
R_in   = 30.5;      // Innenradius Bügel (Ø61)
R_gr   = 35.5;      // Radius Nutgrund (Ø71 → Flanschsitz)
R_out  = 39.9;      // Außenradius (Ø79.8)
H      = 19.0;      // Bügelhöhe (3/4")
F      = 0.635;     // Kantenradius (1/40")
GZ1    = 5.2;       // Nut: Beginn am Innenrand   (z = 5.2 … 13.8)
GZ2    = 7.1;       // Nut: Beginn am Nutgrund    (z = 7.1 … 11.9)
C      = [55.9, 10.1];   // Bügelmittelpunkt (in Hälften-Koordinaten)

// ---- Scharnier ------------------------------------------------------
E      = [10, 10];  // Scharnierauge
R_eye  = 10;        // Auge außen (Ø20)
D_hole = 10;        // Stiftbohrung
FORK   = 5.5;       // Dicke einer Gabelzunge (obere Hälfte: 2 Zungen)
TOL    = 0.1;       // Spiel Zunge/Gabel
CLEAR  = 0.5;       // radiales Spiel um das Gegenauge

// ---- Laschen (Schraubenseite) ---------------------------------------
LUG_X0 = 86;  LUG_X1 = 113;  LUG_R = 1;      // Laschenlänge, Endradius
SLOT_Z = [4.5, 14.5];                         // Gabelschlitz in z
UP_LUG_Y   = [13.5, 23.5];  UP_SLOT_X0 = 97;  // obere Lasche (Schraube schwenkt ein)
DN_LUG_Y   = [11, 23];      DN_SLOT_X  = [98, 108.5]; // untere Lasche (T-Kopf-Lager)
U_C  = [103.5, 20.75];  U_R = 3.75;           // U-Schlitz für T-Kopf

// ---- Schraube / Flügelmutter / Stift --------------------------------
PIN_D = 7.5;  PIN_L = 15;                     // T-Kopf (Querstift)
SHAFT_D = 9.8; SHAFT_L = 12.5;                // glatter Bund
THR_MAJ = 8.9; THR_MIN = 6.2; THR_P = 1.8; THR_L = 31.4;
NUT_TOL = 0.3;

// F5-Vorschau: bei Treiberproblemen (Bügel unsichtbar) auf true setzen –
// die Hälften werden dann per CGAL vorberechnet (einmalig ~10-20 s).
PREVIEW_RENDER = true;
// F5-Vorschau: Gewinde nur als glatter Zylinder zeichnen (schnell); F6 rechnet
// immer das echte Gewinde.
FAST_THREAD = true;
module preview_fix() if (PREVIEW_RENDER && $preview) render(convexity = 10) children(); else children();

// =====================================================================
//  Hilfsmodule
// =====================================================================
module rrect(size, r) offset(r=r) offset(delta=-r) square(size);

// Profil des Bügels (r/z-Ebene): abgerundetes Rechteck minus Trapeznut
module band_profile() difference() {
    translate([R_in, 0]) rrect([R_out - R_in, H], F);
    groove_profile();
}
module groove_profile()
    polygon([[R_in - 1, GZ1], [R_gr, GZ2], [R_gr, H - GZ2], [R_in - 1, H - GZ1]]);

// Ringsektor des Bügels von Winkel a0 bis a1 (um C)
module band_sector(a0, a1)
    translate(C) rotate([0, 0, a0]) rotate_extrude(angle = a1 - a0, convexity = 10) band_profile();
module groove_sector(a0, a1)
    translate(C) rotate([0, 0, a0]) rotate_extrude(angle = a1 - a0, convexity = 10) groove_profile();

// dünne "Stirnfläche" des Bügels bei Winkel a (für hull mit dem Auge)
module band_end_face(a)
    translate(C) rotate([0, 0, a]) translate([R_in, -0.01, 0]) cube([R_out - R_in, 0.02, H]);

module eye(z0, z1) translate([E[0], E[1], z0]) difference() {
    cylinder(r = R_eye, h = z1 - z0);
    translate([0, 0, -1]) cylinder(d = D_hole, h = z1 - z0 + 2);
}

// Einfaches Spitzgewinde: verdrehte "Nocken"-Kontur (r(θ) dreieckig)
module thread(d_maj, d_min, pitch, len)
    if ($preview && FAST_THREAD) cylinder(d = d_maj, h = len);
    else linear_extrude(height = len, twist = -360 * len / pitch,
                   slices = ceil(len / pitch * 24), convexity = 10)
        polygon([for (a = [0 : 5 : 359])
            let(t = 1 - abs(a / 180 - 1))               // 0 → 1 → 0
            (d_min / 2 + t * (d_maj - d_min) / 2) * [cos(a), sin(a)]]);

// =====================================================================
//  Bügelhälfte – gemeinsamer Teil.  a_lug = Winkel, an dem die Lasche
//  beginnt; a_eye = Winkel, an dem der Bügel ins Auge übergeht.
// =====================================================================
module half_body(lug_y) {
    a_lug = asin((lug_y[1] - C[1]) / R_out);   // Außenkante trifft Laschenoberkante
    a_eye = 180 - asin((E[1] + R_eye - C[1]) / R_out); // Außenkante trifft Augenoberseite
    // Kein intersection(): das mag der OpenCSG-Vorschaumodus (Goldfeather)
    // auf manchen Grafiktreibern nicht – difference() ist robuster.
    difference() {
        union() {
            band_sector(a_lug, 180);
            hull() { eye(0, H); band_end_face(a_eye); }
            // Lasche (Rohblock, Details je Hälfte)
            translate([LUG_X0, lug_y[0], 0])
                linear_extrude(H, convexity = 4) rrect([LUG_X1 - LUG_X0, lug_y[1] - lug_y[0]], LUG_R);
        }
        translate([-50, -100, -1]) cube([200, 112, H + 2]); // Steg nur oberhalb y = 12
    }
}

// ---- obere Hälfte: Auge mit 2 Zungen, Lasche mit Einschwenkschlitz ----
module TriClampUp() preview_fix() {
    difference() {
        union() { half_body(UP_LUG_Y); eye(0, H); }
        groove_sector(-5, 185);
        // Gabel im Auge (Mitte frei für Zunge der Unterhälfte)
        translate([E[0], E[1], FORK]) cylinder(r = R_eye + CLEAR, h = H - 2 * FORK);
        // Einschwenkschlitz für den Schraubenschaft
        translate([UP_SLOT_X0, 0, SLOT_Z[0]]) cube([50, 60, SLOT_Z[1] - SLOT_Z[0]]);
    }
    // Rastnase an der Laschenspitze (nur an den Zungen)
    for (z = [[0, SLOT_Z[0]], [SLOT_Z[1], H]])
        translate([109, 11, z[0]]) cube([4, UP_LUG_Y[0] - 11 + 0.01, z[1] - z[0]]);
}

// ---- untere Hälfte: eine Mittelzunge, Lasche mit U-Lager für T-Kopf ----
module TriClampDown() preview_fix() translate([0, 50, 0]) mirror([0, 1, 0]) difference() {
    union() { half_body(DN_LUG_Y); eye(FORK + TOL, H - FORK - TOL); }
    groove_sector(-5, 185);
    // oben und unten frei für die Zungen der Oberhälfte
    for (z = [[-1, FORK + TOL], [H - FORK - TOL, H + 1]])
        translate([E[0], E[1], z[0]]) cylinder(r = R_eye + CLEAR, h = z[1] - z[0]);
    // Gabelschlitz (vorn geschlossen, damit der T-Kopf nicht herausrutscht)
    translate([DN_SLOT_X[0], 0, SLOT_Z[0]])
        cube([DN_SLOT_X[1] - DN_SLOT_X[0], 60, SLOT_Z[1] - SLOT_Z[0]]);
    // U-Schlitz für den Querstift, nach innen offen
    translate([U_C[0], U_C[1], -1]) linear_extrude(H + 2, convexity = 4) union() {
        circle(r = U_R);
        translate([-U_R, 0]) square([2 * U_R, 10]);
    }
}

// ---- Scharnierstift mit Kopf und Rast-Kuppe (Achse z, Kopf bei z<0) ----
module TriClampHinge() preview_fix() {
    translate([0, 0, -2.24]) rotate_extrude(convexity = 4) rrect([7.5, 2.24], F); // Kopf Ø15
    cylinder(d = 9.4, h = 21.5);                                     // Schaft
    translate([0, 0, 21.5]) intersection() {                         // Rastkuppe Ø10.4
        scale([1, 1, 0.4]) sphere(r = 5.2);
        cylinder(r = 6, h = 3);
    }
}

// ---- T-Kopf-Schraube: Querstift ‖ z, Schaft ‖ +y ----------------------
module TriClampScrew() preview_fix() {
    translate([0, 0, -PIN_L / 2]) cylinder(d = PIN_D, h = PIN_L);
    rotate([-90, 0, 0]) {
        cylinder(d = SHAFT_D, h = PIN_D / 2 + SHAFT_L);
        translate([0, 0, PIN_D / 2 + SHAFT_L]) intersection() {
            thread(THR_MAJ, THR_MIN, THR_P, THR_L);
            cylinder(d1 = THR_MAJ + 2 * THR_L, d2 = 0, h = THR_L + 1); // kleine Fase am Ende
        }
    }
}

// ---- Flügelmutter: Achse ‖ +y, Fuß bei y = 0 ---------------------------
module TriClampWingnut() preview_fix() rotate([-90, 0, 0]) difference() {
    union() {
        difference() { cylinder(d = 17.8, h = 8.35); translate([0,0,-1]) cylinder(d = 15.8, h = 9.35 + 1); } // Schürze
        translate([0, 0, 8.35]) cylinder(d = 26, h = 2);                          // Bund
        rotate([90, 0, 0]) linear_extrude(height = 12.2, center = true, convexity = 6)           // Flügel
            wing_outline();
    }
    translate([0, 0, 8]) thread(THR_MAJ + NUT_TOL, THR_MIN + NUT_TOL, THR_P, 22.5); // Innengewinde
    translate([0, 0, 7]) cylinder(d = THR_MIN + NUT_TOL, h = 24);
}
module wing_outline() {
    half = [[8.9, 10.35], [9.0, 12.35], [9.7, 15.35], [10.2, 16.35], [10.8, 17.35],
            [12.5, 19.35], [13.9, 20.35], [15.8, 21.35], [19.8, 22.35], [19.9, 25.35], [19.6, 28.35]];
    arc = [for (a = [30 : -2 : 0]) 38.9 * [sin(a), cos(a)] + [0, -5.25]]; // Oberkante, R38.9
    pts = concat(half, arc, [for (i = [len(arc) - 1 : -1 : 0]) [-arc[i][0], arc[i][1]]],
                 [for (i = [len(half) - 1 : -1 : 0]) [-half[i][0], half[i][1]]]);
    polygon(pts);
}

// =====================================================================
//  Zusammenbau (Rohrachse bei x = 55.9, y = 40)
// =====================================================================
TriClampDown();
translate([0, 30, 0])                    TriClampUp();
translate([E[0], 40, 0])                 TriClampHinge();
translate([U_C[0], 50 - U_C[1], H / 2])  TriClampScrew();
translate([U_C[0], 30 + UP_LUG_Y[1], H / 2]) TriClampWingnut();
