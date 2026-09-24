// Parametrischer Schlauchhalter – mehrfach, offen (Clip) oder geschlossen
// Basis: schlauchhalter2.scad (Zwick-Modell von vorne)
//
// Koordinaten: Wand liegt bei X = -basis_dicke, Schläuche zeigen in +X,
// die Halter werden entlang Y nebeneinander gereiht, Z = Höhe (Druckrichtung).
$fn = 100;

// ================= EINSTELLBARE PARAMETER (in mm) =================

// --- Schlauch ---
schlauch_dm   = 11;     // Außendurchmesser des Schlauchs
spiel         = 0.5;    // Zugabe auf den Durchmesser (negativ = Klemmsitz)

// --- Anzahl / Anordnung ---
anzahl        = 5;      // Anzahl gleicher Schläuche nebeneinander
ring_abstand  = 2;      // Lücke zwischen zwei Ringen außen (0 = gemeinsame Wand)

// --- Höhe / Form ---
hoehe         = 15;     // Höhe des Halters (Extrusion in Z)
wandstaerke   = 4;      // Wanddicke des Rings
wandabstand   = 0;      // Zusätzlicher Abstand Ring <-> Montageplatte

// --- Ring offen oder geschlossen ---
offen         = true;   // true = Clip zum Einhaken/Einklemmen, false = geschlossener Ring
oeffnung_mass = 0;      // Breite der Öffnung; 0 = automatisch (75 % vom Schlauch-Ø)
lippen_rund   = true;   // Kanten der Öffnung abrunden (schont den Schlauch, klipst leichter)

// --- Montageplatte ---
basis_dicke   = 5;      // Dicke der Montageplatte
lasche        = 12;     // Breite der Schraubenlaschen links/rechts neben den Ringen
schrauben_dm  = 4.5;    // Durchmesser der Schraubenlöcher
senkkopf      = true;   // Senkung für Senkkopfschrauben
senkkopf_dm   = 9;      // Kopfdurchmesser Senkkopfschraube

// ================= ABGELEITETE WERTE =================
innen_dm  = schlauch_dm + spiel;
r_i       = innen_dm / 2;
r_a       = r_i + wandstaerke;
teilung   = 2 * r_a + ring_abstand - (ring_abstand == 0 ? wandstaerke : 0);
ring_x    = wandabstand + r_a;                 // Ringmitte in X
ringspan  = (anzahl - 1) * teilung + 2 * r_a;  // Breite aller Ringe zusammen
basis_breite = ringspan + 2 * lasche;
oeffnung  = oeffnung_mass > 0 ? oeffnung_mass : innen_dm * 0.75;
steg_b    = min(innen_dm * 0.6, 2 * r_a);      // Breite des Verbindungsstegs zur Platte

assert(anzahl >= 1, "anzahl muss mindestens 1 sein");
assert(!offen || oeffnung < innen_dm, "oeffnung_mass muss kleiner als der Schlauch-Ø sein");
assert(lasche > schrauben_dm + 2, "lasche zu schmal für die Schraube");

echo(str("Gesamtbreite: ", basis_breite, " mm, Teilung: ", teilung,
         " mm, Öffnung: ", offen ? oeffnung : 0, " mm"));

// Y-Position des i-ten Rings (zentriert um Y = 0)
function ring_y(i) = (i - (anzahl - 1) / 2) * teilung;

// ================= MODULE =================

// 2D-Querschnitt eines Rings (C-Form oder geschlossen), Öffnungskanten optional gerundet
module ring_profil() {
    rr = wandstaerke * 0.45;
    module roh() {
        difference() {
            circle(r = r_a);
            circle(r = r_i);
            if (offen)
                translate([0, -oeffnung / 2]) square([r_a + 1, oeffnung]);
        }
    }
    if (offen && lippen_rund)
        offset(r = rr) offset(r = -rr) roh();
    else
        roh();
}

// Positivform eines Rings inkl. Steg zur Platte
module ring_positiv() {
    translate([ring_x, 0, 0])
        linear_extrude(height = hoehe) ring_profil();
    // Steg: sorgt für eine flächige Verbindung zur Platte (Bohrung wird ausgespart)
    difference() {
        translate([-0.01, -steg_b / 2, 0])
            cube([ring_x + 0.01, steg_b, hoehe]);
        translate([ring_x, 0, -1])
            cylinder(h = hoehe + 2, r = r_i);
    }
}

module schraubenloch() {
    translate([-basis_dicke - 1, 0, hoehe / 2])
        rotate([0, 90, 0])
            cylinder(h = basis_dicke + 2, d = schrauben_dm);
    if (senkkopf) {
        tiefe = (senkkopf_dm - schrauben_dm) / 2;   // 90°-Senkung
        translate([0.01 - tiefe, 0, hoehe / 2])
            rotate([0, 90, 0])
                cylinder(h = tiefe, d1 = schrauben_dm, d2 = senkkopf_dm);
        // Freiraum für den Schraubendreher vor der Senkung
        translate([0, 0, hoehe / 2])
            rotate([0, 90, 0])
                cylinder(h = 1, d = senkkopf_dm);
    }
}

module schlauchhalter() {
    difference() {
        union() {
            // Montageplatte
            translate([-basis_dicke, -basis_breite / 2, 0])
                cube([basis_dicke, basis_breite, hoehe]);
            // Ringe
            for (i = [0 : anzahl - 1])
                translate([0, ring_y(i), 0]) ring_positiv();
        }
        // Schraubenlöcher in den Laschen außen
        for (s = [-1, 1])
            translate([0, s * (ringspan / 2 + lasche / 2), 0]) schraubenloch();
    }
}

schlauchhalter();
