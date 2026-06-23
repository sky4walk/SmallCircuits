// ============================================================
//  Lüfterhalterung für KN10 / KG DN100 Rohr
//  Lüfter: 120x120mm (Standard 12V PC-Lüfter)
//
//  Aufbau:
//   - Muffe (Steckende) für das KN10-Rohr
//   - Übergangsrohr
//   - Lüfterhalterung (120x120mm mit 4 Schraubenlöchern)
// ============================================================

// ---- Anpassbare Parameter ----

// KN10 / KG DN100 Rohr
rohr_aussen_d    = 100;   // Außendurchmesser KN10-Rohr [mm]
muffe_spiel      = 0.1;   // Spiel für den Stecksitz [mm]
muffe_laenge     = 60;    // Tiefe der Muffe [mm]
muffe_wandstaerke = 3;    // Wandstärke der Muffe [mm]

// Übergang
uebergang_laenge = 30;    // Länge des Übergangsbereichs [mm]

// Lüfter (120x120mm)
lue_breite       = 120;   // Lüfter Breite [mm]
lue_hoehe        = 120;   // Lüfter Höhe [mm]
lue_loch_abstand = 105;   // Lochabstand (Mitte-Mitte) [mm]
lue_schraube_d   = 4.3;   // Schraubenloch-Durchmesser M4 [mm]
lue_rahmen_breite = 8;    // Breite des Rahmens um den Lüfter [mm]
lue_rahmen_dicke  = 4;    // Dicke des Lüfterrahmens [mm]

// Luftöffnung im Lüfterrahmen
lue_oeffnung_d   = 116;   // Freier Durchmesser der Luftöffnung [mm]

//nur muffe
muffe_only = false;

// Allgemein
$fn = 128;                 // Auflösung (Segmente für Kreise)

// ---- Berechnete Werte ----
muffe_innen_d    = rohr_aussen_d + muffe_spiel * 2;
muffe_aussen_d   = muffe_innen_d + muffe_wandstaerke * 2;

// Diagonale des Lüfter-Quadrats (für kreisförmigen Übergang)
lue_diag         = sqrt(2) * lue_breite / 2;


// ============================================================
//  HAUPTKÖRPER
// ============================================================

union() {
    // 1) Muffe (Steckende für das KN10-Rohr)
    muffe();

    if ( false == muffe_only ) {
        // 2) Übergang: Zylinder → quadratischer Rahmen
        translate([0, 0, muffe_laenge])
            uebergang();

        // 3) Lüfterrahmen
        translate([0, 0, muffe_laenge + uebergang_laenge])
            lueifterrahmen();
    }
}


// ============================================================
//  MODULE
// ============================================================

// --- Muffe ---
module muffe() {
    difference() {
        // Außenhülle
        cylinder(d = muffe_aussen_d, h = muffe_laenge);
        // Hohlraum für das Rohr
        translate([0, 0, -0.1])
            cylinder(d = muffe_innen_d, h = muffe_laenge + 0.2);
    }
}

// --- Übergang von rund zu quadratisch ---
module uebergang() {
    difference() {
        // Außenform: Zylinder → Quader (lineare Extrusion mit Skalierung)
        hull() {
            // Unten: Kreis (passend zur Muffe)
            cylinder(d = muffe_aussen_d, h = 0.1);
            // Oben: Rechteck (passend zum Lüfterrahmen)
            translate([0, 0, uebergang_laenge - 0.1])
                linear_extrude(height = 0.1)
                    square([lue_breite, lue_hoehe], center = true);
        }

        // Innenhohlraum (Luftkanal)
        translate([0, 0, -0.1])
        hull() {
            cylinder(d = muffe_innen_d, h = 0.1);
            translate([0, 0, uebergang_laenge + 0.1])
                linear_extrude(height = 0.1)
                    square([lue_breite - lue_rahmen_breite * 2,
                            lue_hoehe - lue_rahmen_breite * 2],
                           center = true);
        }
    }
}

// --- Lüfterrahmen ---
module lueifterrahmen() {
    difference() {
        // Vollquader
        translate([-lue_breite/2, -lue_hoehe/2, 0])
            cube([lue_breite, lue_hoehe, lue_rahmen_dicke]);

        // Luftöffnung (rund, passend zum Lüfterdurchmesser)
        translate([0, 0, -0.1])
            cylinder(d = lue_oeffnung_d, h = lue_rahmen_dicke + 0.2);

        // 4 Schraubenlöcher (M4, 105mm Lochabstand)
        lue_lochpositionen()
            translate([0, 0, -0.1])
                cylinder(d = lue_schraube_d, h = lue_rahmen_dicke + 0.2);
    }
}

// --- Hilfsfunktion: Schraubenloch-Positionen ---
module lue_lochpositionen() {
    offset = lue_loch_abstand / 2;
    for (x = [-offset, offset])
        for (y = [-offset, offset])
            translate([x, y, 0])
                children();
}
