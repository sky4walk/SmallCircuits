// ============================================================
//  Namensschilder – 4 Varianten, alle gleichzeitig
//  Jedes Wort in einer eigenen Zeile
//  Text erhaben oder vertieft, abgerundete Ecken
// ============================================================

// --- Schilder-Definitionen [zeile1, zeile2] ---
schilder = [
    ["WASSER", "EIN"],
    ["WASSER", "AUS"],
    ["WÜRZE",  "EIN"],
    ["WÜRZE",  "AUS"]
];

// --- Text-Modus ---
// "erhaben"  → Text steht vor der Platte heraus
// "vertieft" → Text ist in die Platte eingraviert
text_modus = "vertieft";

// --- Plattenmaße ---
platten_breite = 60;   // mm
platten_hoehe  = 40;   // mm
platten_dicke  =  3;   // mm
eck_radius     =  5;   // mm

// --- Textparameter ---
schriftgroesse = 9.0;  // mm – beide Zeilen gleich groß
text_tiefe     = 1.2;  // mm – Reliefhöhe bzw. Gravurtiefe
text_abstand_y = 2.5;  // mm – Abstand zwischen den Zeilen
font_name      = "Liberation Sans:style=Bold";

// --- Anordnung der Schilder auf dem Druckbett ---
abstand_x = 10;  // mm Abstand zwischen den Schildern

// --- Montage ---
loch_aktiv   = false;
loch_abstand = 8;     // mm vom Rand zur Lochmitte
loch_dm      = 3.2;   // Lochdurchmesser (M3)

// ============================================================
//  Interne Berechnungen
// ============================================================
$fn = 64;

// Y-Positionen der zwei Zeilen (Plattenmitte = 0)
y1 =  text_abstand_y / 2 + schriftgroesse / 2;
y2 = -(text_abstand_y / 2 + schriftgroesse / 2);

// ============================================================
//  Module
// ============================================================
module abgerundetes_rechteck(b, h, r) {
    hull() {
        translate([ b/2 - r,  h/2 - r, 0]) circle(r = r);
        translate([-b/2 + r,  h/2 - r, 0]) circle(r = r);
        translate([ b/2 - r, -h/2 + r, 0]) circle(r = r);
        translate([-b/2 + r, -h/2 + r, 0]) circle(r = r);
    }
}

module grundplatte() {
    linear_extrude(height = platten_dicke)
        abgerundetes_rechteck(platten_breite, platten_hoehe, eck_radius);
}

module text_zeile(txt, y_pos) {
    translate([0, y_pos, 0])
        linear_extrude(height = text_tiefe + 0.01)
            text(txt,
                 size   = schriftgroesse,
                 font   = font_name,
                 halign = "center",
                 valign = "center");
}

module texte(z1, z2) {
    text_zeile(z1, y1);
    text_zeile(z2, y2);
}

module montageloecher() {
    if (loch_aktiv) {
        for (x_sign = [-1, 1])
            translate([x_sign * (platten_breite / 2 - loch_abstand), 0, -0.1])
                cylinder(h = platten_dicke + 0.2, d = loch_dm);
    }
}

module schild(z1, z2) {
    difference() {
        union() {
            difference() {
                grundplatte();
                montageloecher();
            }
            if (text_modus == "erhaben")
                translate([0, 0, platten_dicke])
                    texte(z1, z2);
        }
        if (text_modus == "vertieft")
            translate([0, 0, platten_dicke - text_tiefe])
                texte(z1, z2);
    }
}

// ============================================================
//  Alle 4 Schilder als 2x2 Raster auf dem Druckbett
// ============================================================
schritt_x = platten_breite + abstand_x;
schritt_y = platten_hoehe  + abstand_x;

for (i = [0 : len(schilder) - 1]) {
    col = i % 2;        // 0 = links,  1 = rechts
    row = floor(i / 2); // 0 = oben,   1 = unten
    translate([
        (col - 0.5) * schritt_x,
        (0.5 - row) * schritt_y,
        0
    ])
        schild(schilder[i][0], schilder[i][1]);
}
