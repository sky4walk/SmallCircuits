// Schlauchdurchführung mit Schnapphaken für 70-mm-Blechloch
// Druck: Flansch nach unten aufs Bett, keine Stützen nötig. Material: PETG

$fn = 120;

/* [Blech] */
loch_d    = 70;     // Lochdurchmesser
blech_min = 2.0;    // dünnste Blechstärke
blech_max = 3.0;    // dickste Blechstärke
spiel     = 0.3;    // radiales Spiel Körper <-> Lochrand

/* [Flansch] */
flansch_d = 84;
flansch_h = 2.5;

/* [Schnapphaken] */
arm_n      = 12;    // Anzahl Federarme
arm_l      = 20;    // Armlänge unter dem Flansch
arm_wand   = 1.8;   // Wandstärke der Arme
schlitz_b  = 2.5;   // Schlitz zwischen den Armen
keil_s     = 0.7;   // Keilsteigung (mm Höhe pro mm radial)
haken_rest = 0.7;   // Resthakenüberdeckung beim dicksten Blech

/* [Schlauch] */
schlauch_d     = 12.5;
klemm          = 0.3;   // Bohrung so viel kleiner als Schlauch
nabe_d         = 20;
nabe_l         = 18;
nabe_schlitze  = 4;
nabe_schlitz_b = 1.5;
kb_b           = 4.5;   // Kabelbindernut Breite
kb_t           = 1.0;   // Kabelbindernut Tiefe

// ---------- abgeleitete Werte ----------
loch_r = loch_d / 2;
body_r = loch_r - spiel;
bohr_d = schlauch_d - klemm;

z0    = -blech_min + 0.2;                    // Keilhöhe am Lochrand (Ruhelage)
d_max = (blech_max + z0) / keil_s;           // Einfederung beim dicksten Blech
tip   = d_max + haken_rest;                  // Hakenüberstand über Lochrand
function kz(r) = z0 - keil_s * (r - loch_r); // Keilfläche

// ---------- Teile ----------
module flansch() {
    cylinder(h = flansch_h, d1 = flansch_d, d2 = flansch_d - 2);
}

module arme() {
    haken = [
        [body_r - 0.5,   kz(body_r)],
        [body_r,         kz(body_r)],
        [loch_r + tip,   kz(loch_r + tip)],
        [loch_r + tip,   kz(loch_r + tip) - 0.8],
        [body_r,         -arm_l + 1],           // Einführschräge
        [body_r - 0.5,   -arm_l + 1]
    ];
    difference() {
        union() {
            translate([0, 0, -arm_l])
                difference() {
                    cylinder(r = body_r, h = arm_l + 0.01);
                    translate([0, 0, -1])
                        cylinder(r = body_r - arm_wand, h = arm_l + 2);
                }
            rotate_extrude() polygon(haken);
        }
        // Schlitze -> einzelne Federarme
        for (i = [0 : arm_n - 1])
            rotate([0, 0, i * 360 / arm_n])
                translate([body_r - arm_wand - 1, -schlitz_b / 2, -arm_l - 1])
                    cube([tip + arm_wand + spiel + 3, schlitz_b, arm_l + 1]);
    }
}

module nabe() {
    translate([0, 0, -nabe_l])
    difference() {
        cylinder(d = nabe_d, h = nabe_l + 0.01);
        // Spannzangen-Schlitze (oben 4 mm massiv lassen)
        for (i = [0 : nabe_schlitze - 1])
            rotate([0, 0, i * 360 / nabe_schlitze])
                translate([0, -nabe_schlitz_b / 2, -1])
                    cube([nabe_d, nabe_schlitz_b, nabe_l - 4 + 1]);
        // Kabelbindernut
        translate([0, 0, 3])
            rotate_extrude()
                translate([nabe_d / 2 - kb_t, 0]) square([kb_t + 1, kb_b]);
    }
}

// ---------- Zusammenbau ----------
difference() {
    union() {
        flansch();
        arme();
        nabe();
    }
    // Schlauchbohrung
    translate([0, 0, -nabe_l - 1])
        cylinder(d = bohr_d, h = nabe_l + flansch_h + 2);
    // Fase oben am Schlaucheinlauf
    translate([0, 0, flansch_h - 1])
        cylinder(h = 1.01, d1 = bohr_d, d2 = bohr_d + 2);
}
