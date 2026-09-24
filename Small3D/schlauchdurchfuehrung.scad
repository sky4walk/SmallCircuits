// Schlauchdurchführung mit Schnapphaken für 70-mm-Blechloch
// Version 2: Federzungen sind UNTEN (Einführseite) angebunden, das freie
// Ende mit dem Haken liegt am Flansch. Dadurch hat der Haken einen langen
// Hebel zum Einfedern, statt direkt an der starren Flanschwurzel zu sitzen.
//
// Druck: Flansch nach unten aufs Bett, keine Stützen nötig. Material: PETG.
// Die Zungen beginnen kopf_spalt über dem Flansch (bei 0,2-mm-Schichten also
// 2 Leerschichten). Die erste Zungenschicht hängt leicht durch und haftet
// ggf. schwach am Flansch: nach dem Druck jede Zunge einmal nach innen
// drücken oder mit dem Cutter durch den Spalt fahren.

$fn = 120;

/* [Blech] */
loch_d    = 70;     // Lochdurchmesser
blech_min = 2.0;    // dünnste Blechstärke
blech_max = 3.0;    // dickste Blechstärke
spiel     = 0.3;    // radiales Spiel Körper <-> Lochrand

/* [Flansch] */
flansch_d = 84;
flansch_h = 2.5;

/* [Federzungen] */
arm_n        = 10;    // Anzahl Federzungen [2:1:16]
zungen_l     = 24;    // Zungenlänge in mm (länger = weicher, geringere Bruchgefahr) [10:1:40]
zungen_b     = 5;     // Zungenbreite in mm, 0 = automatisch (Rest wird Steg)
arm_wand     = 1.8;   // Wandstärke Rohr / Zungenwurzel
schlitz_b    = 1.5;   // Schlitzbreite neben den Zungen
steg_b       = 4.0;   // Stegbreite in mm, nur bei zungen_b = 0 verwendet
kopf_spalt   = 0.4;   // Spalt zwischen Zungenende und Flansch (≈ 2 Schichten)
fuss_h       = 3.0;   // geschlossener Ring unterhalb der Zungenwurzel
max_dehnung  = 2.0;   // Warnschwelle Biegedehnung in % (PETG, quer zur Schicht)

/* [Test] */
testring     = false; // true: nur Flanschring + Zungen, ohne Nabe (schneller Probedruck)

/* [Haken] */
keil_s       = 1.0;   // Keilsteigung (mm Höhe pro mm radial); 1.0 = 45°, druckt sauberer
haken_rest   = 0.7;   // Resthakenüberdeckung beim dicksten Blech
haken_spitze = 1.5;   // senkrechte Dicke der Hakenspitze (vorher fest 0.8)

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
in_r   = body_r - arm_wand;
bohr_d = schlauch_d - klemm;

z0    = -blech_min + 0.2;                    // Keilhöhe am Lochrand (Ruhelage)
d_max = (blech_max + z0) / keil_s;           // Einfederung beim dicksten Blech
tip   = d_max + haken_rest;                  // Hakenüberstand über Lochrand
function kz(r) = z0 - keil_s * (r - loch_r); // Keilfläche

z_wurzel = -(kopf_spalt + zungen_l);         // Zungenwurzel
rohr_l   = kopf_spalt + zungen_l + fuss_h;
z_spitze = kz(loch_r + tip);

// Winkel (Grad) aus Bogenlänge am Außenradius
function grad(mm) = mm / body_r * 180 / PI;
seg_a    = 360 / arm_n;
schlitz_a = grad(schlitz_b);
zunge_a  = zungen_b > 0 ? grad(zungen_b) : seg_a - grad(steg_b) - 2 * schlitz_a;
steg_ist = (seg_a - zunge_a - 2 * schlitz_a) * body_r * PI / 180;

// Biegedehnung an der Zungenwurzel beim Durchschnappen (Kragbalken, Punktlast)
hebel   = z_spitze - z_wurzel;
dehnung = 3 * arm_wand * tip / (2 * hebel * hebel) * 100;

echo(str("Zungen: ", arm_n, " × ", round(zunge_a * body_r * PI / 180 * 10) / 10,
         " mm breit, ", zungen_l, " mm lang; Stege ", round(steg_ist * 10) / 10, " mm"));
echo(str("Hakenüberstand: ", tip, " mm, Hebel: ", hebel, " mm, Wurzeldehnung: ",
         round(dehnung * 100) / 100, " %"));
if (dehnung > max_dehnung)
    echo(str("WARNUNG: Dehnung über ", max_dehnung,
             " % – zungen_l erhöhen oder arm_wand verringern"));

assert(zunge_a > 5, "Zungen zu schmal: arm_n, steg_b oder schlitz_b verkleinern");
assert(steg_ist >= 2, "Stege unter 2 mm: zungen_b verkleinern oder arm_n reduzieren");
assert(kz(body_r) < -kopf_spalt - 0.3, "Haken kollidiert mit dem Kopfspalt");
assert(z_spitze - haken_spitze > z_wurzel + 2, "Zunge zu kurz für den Haken");

// ---------- Hilfsformen ----------
// Kreissektor, mittig um die X-Achse, zwischen r1..r2 und z1..z2
module sektor(a, r1, r2, z1, z2) {
    rotate([0, 0, -a / 2])
        rotate_extrude(angle = a)
            translate([r1, z1]) square([r2 - r1, z2 - z1]);
}

// ---------- Teile ----------
module flansch() {
    cylinder(h = flansch_h, d1 = flansch_d, d2 = flansch_d - 2);
}

module rohr() {
    difference() {
        translate([0, 0, -rohr_l])
            difference() {
                cylinder(r = body_r, h = rohr_l + 0.01);
                translate([0, 0, -1]) cylinder(r = in_r, h = rohr_l + 2);
            }
        for (i = [0 : arm_n - 1])
            rotate([0, 0, i * seg_a]) {
                // Spalt unter dem Flansch -> freies Zungenende
                sektor(zunge_a + 2 * schlitz_a, in_r - 1, body_r + 1,
                       -kopf_spalt, 0.02);
                // seitliche Schlitze mit runder Wurzel (Kerbentlastung)
                for (s = [-1, 1])
                    rotate([0, 0, s * (zunge_a + schlitz_a) / 2]) {
                        translate([in_r - 1, -schlitz_b / 2, z_wurzel])
                            cube([arm_wand + 2, schlitz_b, -z_wurzel + 0.02]);
                        translate([in_r - 1, 0, z_wurzel])
                            rotate([0, 90, 0])
                                cylinder(d = schlitz_b, h = arm_wand + 2, $fn = 24);
                    }
            }
    }
}

module haken() {
    haken = [
        [body_r - 0.5,   kz(body_r)],
        [body_r,         kz(body_r)],
        [loch_r + tip,   z_spitze],
        [loch_r + tip,   z_spitze - haken_spitze],
        [body_r,         z_wurzel + 0.5],      // Einführschräge bis zur Wurzel
        [body_r - 0.5,   z_wurzel + 0.5]
    ];
    intersection() {
        rotate_extrude() polygon(haken);
        // nur auf den Zungen, nicht auf den Stegen
        for (i = [0 : arm_n - 1])
            rotate([0, 0, i * seg_a])
                sektor(zunge_a, 0, loch_r + tip + 1, z_wurzel - 1, 0);
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
        if (testring)
            difference() { flansch(); translate([0, 0, -1]) cylinder(r = in_r - 3, h = flansch_h + 2); }
        else
            flansch();
        rohr();
        haken();
        if (!testring) nabe();
    }
    // Schlauchbohrung
    translate([0, 0, -nabe_l - 1])
        cylinder(d = bohr_d, h = nabe_l + flansch_h + 2);
    // Fase oben am Schlaucheinlauf
    translate([0, 0, flansch_h - 1])
        cylinder(h = 1.01, d1 = bohr_d, d2 = bohr_d + 2);
}
