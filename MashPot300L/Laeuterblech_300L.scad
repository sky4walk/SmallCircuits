// ============================================================
//  Läuterblech für Braukessel
//  Runde Platte mit parallelen Schlitzen, bündig im Topf
//  Alle Maße in Millimeter
// ============================================================

// --- Hauptparameter ---
blech_od         = 708.0;   // Außendurchmesser (= Topf-Innendurchmesser)
blech_staerke    = 1.5;     // Blechstärke

// --- Schlitzparameter ---
schlitz_breite   = 1.5;     // Breite der Schlitze
schlitz_laenge   = 40.0;    // Länge der einzelnen Schlitze
schlitz_abstand  = 1.5;     // Stegbreite zwischen den Schlitzen (Mitte-zu-Mitte Abstand = schlitz_breite + schlitz_abstand)
reihen_abstand   = 1.5;     // Abstand zwischen den Schlitzreihen (Stegbreite)

// Versatz jeder zweiten Reihe (für versetztes Muster, 0 = keine Versetzung)
reihen_versatz   = (schlitz_breite + schlitz_abstand) / 2;

// Randbereich ohne Schlitze (umlaufender Steg)
rand_breite      = 10.0;    // Breite des geschlossenen Randes

// --- Abgeleitete Maße ---
blech_r          = blech_od / 2;
nutzbereich_r    = blech_r - rand_breite;   // Radius des Schlitzbereichs

// Abstand Mitte-zu-Mitte der Schlitze in X-Richtung
schlitz_pitch_x  = schlitz_breite + schlitz_abstand;
// Abstand Mitte-zu-Mitte der Reihen in Y-Richtung
reihen_pitch_y   = schlitz_laenge + reihen_abstand;

// Anzahl Schlitze und Reihen (großzügig, wird durch Kreismaske beschnitten)
n_schlitze       = ceil(2 * nutzbereich_r / schlitz_pitch_x) + 2;
n_reihen         = ceil(2 * nutzbereich_r / reihen_pitch_y) + 2;

// --- Rendering-Qualität ---
$fn = 256;

// ============================================================
//  MODULE: Einzelner Schlitz (als Negativ-Körper)
// ============================================================
module schlitz() {
    // Schlitz mit abgerundeten Enden (Stadionform)
    r = schlitz_breite / 2;
    hull() {
        translate([0,  schlitz_laenge/2 - r, 0]) cylinder(h = blech_staerke + 0.1, r = r, center = false);
        translate([0, -schlitz_laenge/2 + r, 0]) cylinder(h = blech_staerke + 0.1, r = r, center = false);
    }
}

// ============================================================
//  MODULE: Gesamtes Schlitzmuster (als Negativ)
// ============================================================
module schlitzmuster() {
    for (row = [-n_reihen : n_reihen]) {
        // Jede zweite Reihe um reihen_versatz versetzen
        x_off = (row % 2 == 0) ? 0 : reihen_versatz;
        y_pos = row * reihen_pitch_y;

        for (col = [-n_schlitze : n_schlitze]) {
            x_pos = col * schlitz_pitch_x + x_off;

            // Nur Schlitze innerhalb des Nutzbereichs zeichnen
            // (grobe Vorauswahl, feine Beschneidung durch Maske)
            if (sqrt(x_pos*x_pos + y_pos*y_pos) < nutzbereich_r + schlitz_laenge) {
                translate([x_pos, y_pos, -0.05])
                    schlitz();
            }
        }
    }
}

// ============================================================
//  MODULE: Kreismaske für Nutzbereich
//  Schneidet Schlitze außerhalb des Nutzbereichs weg
// ============================================================
module nutzbereich_maske() {
    cylinder(h = blech_staerke + 0.2, r = nutzbereich_r, center = false);
}

// ============================================================
//  Podest-Parameter
//  podest_aktiv = true  → Podest wird angezeigt
//  podest_aktiv = false → nur Läuterblech
// ============================================================
podest_aktiv       = true;           // Ein/Ausschalten des Podests
podest_hoehe       = 65.0;           // Höhe aller Füsse
podest_fuss_r      = 15.0;           // Radius der äußeren Füsse (rund)
podest_mitte_r     = 20.0;           // Radius des Mittelfusses
podest_radius      = blech_r - 40.0; // Abstand äußere Fussmitte von Topfachse
podest_winkel      = 45.0;           // Startwinkel (45° = zwischen Tri-Clamp Anschlüssen)

// Streben-Parameter
strebe_breite      = 8.0;            // Breite der Strebe (hochkant = sichtbare Dimension)
strebe_staerke     = 3.0;            // Dicke der Strebe

// ============================================================
//  MODULE: Äußerer Fuss (Vollzylinder)
// ============================================================
module fuss_aussen() {
    cylinder(h = podest_hoehe, r = podest_fuss_r, center = false);
}

// ============================================================
//  MODULE: Mittelfuss (größerer Vollzylinder)
// ============================================================
module fuss_mitte() {
    cylinder(h = podest_hoehe, r = podest_mitte_r, center = false);
}

// ============================================================
//  MODULE: Strebe zwischen zwei Punkten (hochkant)
//  von [x1,y1] nach [x2,y2], Höhe = podest_hoehe
// ============================================================
module strebe(x1, y1, x2, y2) {
    dx   = x2 - x1;
    dy   = y2 - y1;
    len  = sqrt(dx*dx + dy*dy);
    winkel = atan2(dy, dx);

    translate([x1, y1, 0])
        rotate([0, 0, winkel])
            translate([0, -strebe_staerke/2, 0])
                cube([len, strebe_staerke, strebe_breite]);
}

// ============================================================
//  MODULE: Komplettes Podest
//  - 4 äußere runde Füsse (90° versetzt, 45° zur Gruppe)
//  - 1 Mittelfuss
//  - Streben: jeder äußere Fuss → Mittelfuss
//  - Streben: äußere Füsse untereinander (Ring)
// ============================================================
module podest() {
    z_off = -(podest_hoehe + blech_staerke);  // Füsse hängen unter dem Blech

    // Positionen der 4 äußeren Füsse
    fuss_pos = [
        for (i = [0:3])
            [podest_radius * cos(podest_winkel + i*90),
             podest_radius * sin(podest_winkel + i*90)]
    ];

    // Füsse hängen unter dem Blech
    translate([0, 0, z_off]) {
        // --- 4 äußere Füsse ---
        for (p = fuss_pos)
            translate([p[0], p[1], 0])
                fuss_aussen();

        // --- Mittelfuss ---
        fuss_mitte();
    }

    // Streben direkt unterhalb des Läuterbleches
    translate([0, 0, -strebe_breite]) {
        // --- Streben: jeder äußere Fuss → Mitte ---
        for (p = fuss_pos)
            strebe(0, 0, p[0], p[1]);

        // --- Streben: äußere Füsse untereinander (Ring) ---
        for (i = [0:3]) {
            p1 = fuss_pos[i];
            p2 = fuss_pos[(i+1) % 4];
            strebe(p1[0], p1[1], p2[0], p2[1]);
        }
    }
}

// ============================================================
//  HAUPTKONSTRUKTION
// ============================================================
// Läuterblech (immer sichtbar)
difference() {
    cylinder(h = blech_staerke, r = blech_r);
    intersection() {
        translate([0, 0, -0.05])
            nutzbereich_maske();
        schlitzmuster();
    }
}

// Podest (ein/ausschaltbar)
if (podest_aktiv) {
    podest();
}
