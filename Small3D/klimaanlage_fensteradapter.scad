// ============================================================
//  Klimaanlage Fenster-Durchführungsadapter
// ============================================================

// --- Schlauch ---
schlauch_aussen_d = 99.5;  // Außen-Ø Klimaanlagen-Schlauch
wandstaerke       = 3.0;
aufsteck_tiefe    = 40;
spiel             = 0.5;

// --- Kanalquerschnitt ---
kanal_breite   = 160;
kanal_hoehe    = 30;
kanal_laenge   = 30;
uebergang_hoehe = 80;

// --- Fenster-Maße ---
rahmen_dicke    = 95;   // Dicke des Fensterrahmens [mm]
ueberhang_tiefe = 20;   // Tiefe der Klemmnase (greift hinter Rahmen) [mm]
spaltbreite     = 60;   // Spaltbreite beim gekippten Fenster [mm]

// --- Bogen + Auslass ---
// biegeradius wird automatisch aus rahmen_dicke berechnet:
// Innenmaß des U = 2*br - (kh+2ws) >= rahmen_dicke  → br >= (rahmen_dicke + kh + 2ws)/2
// +3mm Spiel damit der Adapter leicht aufgesteckt werden kann
biegeradius    = (rahmen_dicke + kanal_hoehe + 2*wandstaerke) / 2 + 3;
auslauf_laenge = 30;   // gerades Stück am Auslass (außen, zeigt nach unten)
nasen_dicke    = 8;    // Dicke der Klemmnase [mm]
fuss_hoehe     = 13;   // Höhe des Druckfußes am Bogenscheitel [mm]

$fn = 64;

// --- Berechnete Hilfswerte ---
adapter_innen_r = (schlauch_aussen_d + spiel) / 2;
adapter_aussen_r = adapter_innen_r + wandstaerke;
kw = kanal_breite;
kh = kanal_hoehe;
ws = wandstaerke;
br = biegeradius;

z_uebergang = aufsteck_tiefe;
z_kanal     = aufsteck_tiefe + uebergang_hoehe;
z_knick     = z_kanal + kanal_laenge;

// Sicherheits-Prüfung: Spaltbreite muss >= Kanaltiefe sein
// (kh + 2*ws = 36mm muss durch den Spalt von 60mm passen ✓)

// ============================================================
union() {
    aufsteck_muffe();
    translate([0, 0, z_uebergang]) uebergang_rund_flach();
    translate([0, 0, z_kanal])     senkrechter_kanal();
    translate([0, 0, z_knick])     l_haken();
}

// ============================================================
module aufsteck_muffe() {
    difference() {
        cylinder(r = adapter_aussen_r, h = aufsteck_tiefe);
        translate([0, 0, -0.1])
            cylinder(r = adapter_innen_r, h = aufsteck_tiefe + 0.2);
    }
}

module uebergang_rund_flach() {
    difference() {
        hull() {
            cylinder(r = adapter_aussen_r, h = 1);
            translate([-(kw/2), -(kh/2 + ws), uebergang_hoehe - 1])
                cube([kw, kh + 2*ws, 1]);
        }
        hull() {
            translate([0, 0, -0.1]) cylinder(r = adapter_innen_r, h = 1);
            translate([-(kw/2 - ws), -(kh/2), uebergang_hoehe - 1])
                cube([kw - 2*ws, kh, 1.2]);
        }
    }
}

module senkrechter_kanal() {
    difference() {
        translate([-(kw/2), -(kh/2 + ws), 0])
            cube([kw, kh + 2*ws, kanal_laenge]);
        translate([-(kw/2 - ws), -(kh/2), -0.1])
            cube([kw - 2*ws, kh, kanal_laenge + 0.2]);
    }
}

// ============================================================
// 180°-Bogen + gerades Auslaufstück + Klemmnase
//
// Geometrie (lokal, Z=0 = Oberkante senkrechter Kanal):
//
//   End 1: (0,   0,  0)  Richtung +Z  → Anschluss senkrechter Kanal (innen)
//   End 2: (0, 2*br, 0)  Richtung -Z  → Auslass zeigt nach unten (außen)
//
//   Innenmaß des U = 2*br - (kh+2ws) = rahmen_dicke + Spiel
//
//   Klemmnase: dünne Lippe am Ende des Auslaufs,
//   greift ueberhang_tiefe mm hinter den Fensterrahmen

module l_haken() {
    arc_size = br + kh/2 + ws + 2;
    y_innen  = 2*br - (kh/2 + ws);  // Innenfläche des Außenschenkels

    difference() {
        union() {
            // 1) 180°-Bogen
            translate([0, br, 0])
            rotate([90, 0, -90])
            intersection() {
                rotate_extrude($fn = $fn)
                    translate([br, 0])
                        square([kh + 2*ws, kw], center = true);
                translate([-arc_size, 0, -(kw/2 + 1)])
                    cube([2 * arc_size, arc_size, kw + 2]);
            }

            // 2) Gerades Auslaufstück
            translate([-(kw/2), y_innen, -auslauf_laenge])
                cube([kw, kh + 2*ws, auslauf_laenge]);

            // 3) Druckfuß am Bogenscheitel
            //    Gibt eine flache Standfläche beim umgekehrten Drucken (kein Brim nötig)
            //    Sitzt am höchsten Punkt des Bogens: Y=br, Z=br+(kh/2+ws)
            translate([-(kw/2), br - (kh/2 + ws) - 20, br + (kh/2) - fuss_hoehe/2-3])
                cube([kw, kh + 2*ws + 40, fuss_hoehe]);

            // 4) Keilförmige Klemmnase (45°-Keil → kein steiler Überhang beim Druck)
            //    hull() zwischen voller Basis (am Auslauf) und Spitze (ueberhang_tiefe entfernt)
            //    Beim umgekehrten Druck: die geneigte Fläche ist selbsttragend
            hull() {
                // Basis: volle Höhe nasen_dicke, direkt an der Auslaufwand
                translate([-(kw/2), y_innen - 0.01, -auslauf_laenge])
                    cube([kw, 0.01, nasen_dicke]);
                // Spitze: Höhe 0, nasen_dicke entfernt → 45° Winkel
                translate([-(kw/2), y_innen - nasen_dicke, -auslauf_laenge])
                    cube([kw, 0.01, 0.01]);
            }
        }

        union() {
            // Bogen-Hohlraum
            translate([0, br, 0])
            rotate([90, 0, -90])
            intersection() {
                rotate_extrude($fn = $fn)
                    translate([br, 0])
                        square([kh, kw - 2*ws], center = true);
                translate([-arc_size, 0, -(kw/2 + 1)])
                    cube([2 * arc_size, arc_size, kw + 2]);
            }

            // Auslauf-Hohlraum
            translate([-(kw/2 - ws), 2*br - kh/2, -auslauf_laenge - 0.1])
                cube([kw - 2*ws, kh, auslauf_laenge + 0.2]);
        }
    }
}
