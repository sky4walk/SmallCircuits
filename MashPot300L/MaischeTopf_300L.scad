// ============================================================
//  Parametrischer Topf mit Tri-Clamp-Anschlüssen
//  Alle Maße in Millimeter
//
//  Anschluss-Gruppe: 3 parallele Stutzen nebeneinander
//    Mitte:  1.5" (DN40)
//    Links:  2"
//    Rechts: 2"
//
//  Alle Stutzen sind parallel, bündig mit der Topfwand.
//  Die Rohrstutzen-Länge wird pro Stutzen geometrisch
//  aus dem Wanddurchschnitt am jeweiligen Y-Versatz berechnet.
// ============================================================

// --- Topf-Parameter ---
topf_id            = 710;    // Innendurchmesser
topf_hoehe         = 800;    // Gesamthöhe
wandstaerke        = 1.5;    // Wandstärke Zylinder
bodenstaerke       = 2.0;    // Bodenstärke

// --- Abgeleitete Topf-Maße ---
topf_od            = topf_id + 2 * wandstaerke;
topf_ir            = topf_id / 2;
topf_or            = topf_od / 2;

// --- Tri-Clamp: gemeinsame Parameter ---
flansch_ueberstand = 15.0;   // Flanschring steht um diesen Betrag außen heraus
// (Rohrstutzen-Länge wird automatisch berechnet, s.u.)

// --- Tri-Clamp Flansch-Typ A: 2" ---
tc_a_flansch_od    = 64.0;
tc_a_rohr_od       = 50.8;
tc_a_rohr_id       = 47.5;
tc_a_flansch_h     = 4.5;
tc_a_nut_tiefe     = 1.5;
tc_a_nut_breite    = 3.5;

// --- Tri-Clamp Flansch-Typ B: 1.5" / DN40 ---
tc_b_flansch_od    = 50.5;
tc_b_rohr_od       = 41.0;
tc_b_rohr_id       = 38.0;
tc_b_flansch_h     = 4.5;
tc_b_nut_tiefe     = 1.5;
tc_b_nut_breite    = 3.5;

// --- Positionierung der Anschluss-Gruppe ---
gruppe_winkel      = 0;      // Drehung der Gruppe um Z-Achse (0° = +X Richtung)
stutzen_abstand    = 150.0;  // Mitte-zu-Mitte Abstand zwischen den Stutzen

// --- Höhe: unteres Stutzen-Trio ---
spiel              = 2.0;    // Mindestabstand Rohrmitte von Bodenkante
stutzen_z   = bodenstaerke + tc_a_rohr_od / 2 + spiel;  // 2"-Paar: so tief wie möglich
stutzen_b_z = bodenstaerke + tc_b_rohr_id / 2;          // 1.5" Mitte: Auslass bodeneben (Innenkante auf Bodenhöhe)

// --- Höhe: oberes 2"-Paar (Rohrmitte von Boden) ---
tc_a_oben_links_z  = 300.0;  // 2" oben links  (parametrisch)
tc_a_oben_rechts_z = 300.0;  // 2" oben rechts (parametrisch)

// --- Temperatursensor-Stutzen: 1.5" mittig, 90° versetzt ---
temp_winkel        = gruppe_winkel + 90;  // 90° zur Hauptgruppe
temp_z             = topf_hoehe / 2;      // Topfmitte (parametrisch)

// --- Oberer 1.5" Stutzen: in Linie mit Hauptgruppe (y=0) ---
oben_rand_abstand  = 10.0;               // Abstand Rohrmitte vom Topfrand (parametrisch)
oben_b_z           = topf_hoehe - oben_rand_abstand - tc_b_rohr_od / 2;

// --- Bügelgriffe (links + rechts, 90° versetzt zur Hauptgruppe) ---
griff_aktiv        = true;    // true = Griffe anzeigen, false = ausblenden
griff_winkel       = gruppe_winkel + 90; // 90° zur Hauptgruppe
griff_rohr_od      = 12.0;   // Außendurchmesser des Griffrohres
griff_rohr_id      = 8.0;    // Innendurchmesser (hohl)
griff_breite       = 80.0;   // Breite des U-Bügels (außen)
griff_tiefe        = 60.0;   // wie weit der Griff nach außen ragt
griff_rand_abstand = 30.0;   // Abstand Griffmitte vom Topfrand nach unten
griff_r            = griff_rohr_od / 2; // Biegeradius der U-Kurve = Rohrradius

// --- Boden-Ablassstutzen: 1.5" nach unten, abschaltbar ---
boden_stutzen_aktiv    = true;           // true = sichtbar, false = ausblenden
boden_stutzen_rand     = 100.0;          // Abstand vom Topfrand (Innenrand) in Richtung Hauptgruppe
boden_stutzen_versatz  = topf_ir - boden_stutzen_rand; // → Abstand von Topfmitte
boden_stutzen_l        = 20.0;           // Länge des Stutzens unter dem Boden

// --- Rendering-Qualität ---
$fn = 128;

// ============================================================
//  Hilfsfunktionen: X-Koordinate auf Innen- bzw. Außenwand
//  bei gegebenem Y-Versatz
// ============================================================
function x_innen(y) = sqrt(max(topf_ir * topf_ir - y * y, 0));
function x_aussen(y) = sqrt(max(topf_or * topf_or - y * y, 0));

// Flansch-Stirnfläche liegt bei allen Stutzen auf gleicher X-Position:
// Außenwand bei y=0 + flansch_ueberstand
flansch_x_ziel = topf_or + flansch_ueberstand;

// Stutzen-Länge pro Stutzen: von Innenwand(y) bis zur gemeinsamen Flansch-X
function stutzen_laenge(y) = flansch_x_ziel - x_innen(y);

// ============================================================
//  MODULE: Tri-Clamp Stutzen (Flansch + Rohr)
//  stutzen_l wird von außen übergeben (pro Stutzen berechnet)
// ============================================================
// ============================================================
//  MODULE: Tri-Clamp Ferrule (ISO 2852 / DIN 32676 Profil)
//
//  Flansch-Stirnflächen-Profil (von innen nach außen):
//    1. Innebohrung (rohr_ir)
//    2. Dichtsteg: leicht erhöhter Ring der auf Dichtung drückt
//    3. Dichtnut: ringförmige Vertiefung für O-Ring / Flachdichtung
//    4. Fase: 20° Abschrägung an der Außenkante des Flansches
//
//  stutzen_l = Gesamtlänge (wird von außen berechnet übergeben)
// ============================================================
module triclamp_stutzen(
    flansch_od, rohr_od, rohr_id,
    flansch_h, stutzen_l,
    nut_tiefe, nut_breite
) {
    rohr_or   = rohr_od / 2;
    rohr_ir   = rohr_id / 2;
    flansch_r = flansch_od / 2;

    // --- Flansch-Profil-Parameter (normgerecht) ---
    // Dichtsteg: schmaler erhabener Ring direkt innen
    steg_breite  = 1.5;    // Breite des Dichtsstegs
    steg_hoehe   = 0.8;    // wie weit der Steg über die Flanschfläche ragt
    // Dichtnut: Ringnut für Dichtung
    nut_r_innen  = rohr_ir + steg_breite;
    nut_r_aussen = flansch_r - 3.0;   // Nut endet 3mm vor Außenkante
    nut_h        = 2.0;    // Tiefe der Nut
    // Fase an der Außenkante: 20° (typisch ISO 2852)
    fase_breite  = 2.5;
    fase_hoehe   = fase_breite * tan(20);

    difference() {
        union() {
            // --- Rohrstutzen ---
            cylinder(h = stutzen_l - flansch_h, r = rohr_or);

            // --- Flanschring: Grundkörper mit Fase an Außenkante ---
            translate([0, 0, stutzen_l - flansch_h])
                rotate_extrude()
                    polygon(points = [
                        // Innen (Rohrwand)
                        [rohr_ir,    0],
                        [rohr_or,    0],
                        [rohr_or,    flansch_h],
                        // Flanschaußen mit 20° Fase
                        [flansch_r,          flansch_h],
                        [flansch_r,          fase_hoehe],
                        [flansch_r - fase_breite, 0],
                        [rohr_ir,    0]
                    ]);

            // --- Dichtsteg: erhabener Ring auf Stirnfläche ---
            translate([0, 0, stutzen_l])
                difference() {
                    cylinder(h = steg_hoehe, r = rohr_ir + steg_breite);
                    cylinder(h = steg_hoehe + 0.01, r = rohr_ir);
                }
        }

        // --- Innenbohrung durchgehend ---
        cylinder(h = stutzen_l + steg_hoehe + 0.1, r = rohr_ir);

        // --- Dichtnut auf Stirnfläche ---
        translate([0, 0, stutzen_l - nut_h])
            difference() {
                cylinder(h = nut_h + 0.01, r = nut_r_aussen);
                cylinder(h = nut_h + 0.02, r = nut_r_innen);
            }
    }
}

// ============================================================
//  MODULE: Parallelen Stutzen bündig an der Topfwand platzieren
//  Startpunkt = Innenwand bei y_offset
//  Länge      = Wanddicke(y_offset) + flansch_ueberstand
// ============================================================
module stutzen_parallel(
    y_offset, z_pos,
    flansch_od, rohr_od, rohr_id,
    flansch_h, nut_tiefe, nut_breite
) {
    // Startpunkt wird um rohr_od/2 nach innen verschoben,
    // damit der runde Stutzen die gekrümmte Wand vollständig durchdringt
    einzug  = rohr_od / 2;
    xi      = x_innen(y_offset) - einzug;
    sl      = stutzen_laenge(y_offset) + einzug;

    translate([xi, y_offset, z_pos])
        rotate([0, 90, 0])
            triclamp_stutzen(
                flansch_od = flansch_od,
                rohr_od    = rohr_od,
                rohr_id    = rohr_id,
                flansch_h  = flansch_h,
                stutzen_l  = sl,
                nut_tiefe  = nut_tiefe,
                nut_breite = nut_breite
            );
}

// ============================================================
//  MODULE: Wanddurchbruch für parallelen Stutzen
//  Bohrung von Mitte des Topfes nach außen, mit Übermaß
// ============================================================
module durchbruch_parallel(y_offset, z_pos, rohr_id) {
    translate([0, y_offset, z_pos])
        rotate([0, 90, 0])
            cylinder(h = topf_or + 1, r = rohr_id / 2);
}

// ============================================================
//  MODULE: Bügelgriff (U-Form, radial nach außen)
//
//  Aufbau in der XY-Ebene (bei Z = z_base):
//
//        Querrohr (oben)
//    ___________________________
//   |                           |
//   | linker          rechter   |
//   | Schenkel        Schenkel  |
//   |                           |
//  [L]  ←— Topfwand —→        [R]
//
//  X = radial nach außen
//  Y = tangential (±halb_b)
//  Z = Höhe
//
//  Befestigungslasche liegt bündig an der Topfwand an.
// ============================================================
module buegelgriff() {
    r      = griff_rohr_od / 2;
    ri     = griff_rohr_id / 2;
    br     = griff_rohr_od * 1.5;  // Biegeradius der Ecken
    z_base = topf_hoehe - griff_rand_abstand;
    halb_b = griff_breite / 2;
    x0     = topf_or;               // Start X (Topfwand)
    x1     = topf_or + griff_tiefe; // Ende X (Außenkante Querrohr)

    // Punkte des U-Bügels:
    // P_LL = linke Befestigung an Wand
    // P_LO = linke obere Ecke
    // P_RO = rechte obere Ecke
    // P_RL = rechte Befestigung an Wand
    P_LL = [x0, -halb_b, z_base];
    P_LO = [x1, -halb_b, z_base];
    P_RO = [x1,  halb_b, z_base];
    P_RL = [x0,  halb_b, z_base];

    module seg(p1, p2) {
        hull() {
            translate(p1) sphere(r = r);
            translate(p2) sphere(r = r);
        }
    }
    module seg_i(p1, p2) {
        hull() {
            translate(p1) sphere(r = ri);
            translate(p2) sphere(r = ri);
        }
    }

    difference() {
        union() {
            // U-Bügel: 3 Segmente
            seg(P_LL, P_LO);   // linker Schenkel
            seg(P_LO, P_RO);   // Querrohr oben
            seg(P_RO, P_RL);   // rechter Schenkel

            // Befestigungslasche links (bündig an Topfwand)
            hull() {
                translate(P_LL) sphere(r = r);
                translate([x0 - r, -halb_b, z_base - griff_rohr_od]) sphere(r = r);
                translate([x0 - r, -halb_b + griff_rohr_od, z_base]) sphere(r = r);
                translate([x0 - r, -halb_b + griff_rohr_od, z_base - griff_rohr_od]) sphere(r = r);
            }

            // Befestigungslasche rechts (bündig an Topfwand)
            hull() {
                translate(P_RL) sphere(r = r);
                translate([x0 - r, halb_b, z_base - griff_rohr_od]) sphere(r = r);
                translate([x0 - r, halb_b - griff_rohr_od, z_base]) sphere(r = r);
                translate([x0 - r, halb_b - griff_rohr_od, z_base - griff_rohr_od]) sphere(r = r);
            }
        }

        // Innenbohrung (hohles Rohr)
        seg_i(P_LL, P_LO);
        seg_i(P_LO, P_RO);
        seg_i(P_RO, P_RL);
    }
}

// ============================================================
//  MODULE: Boden-Ablassstutzen (zeigt nach unten)
// ============================================================
module boden_stutzen() {
    rotate([0, 0, gruppe_winkel])
    translate([boden_stutzen_versatz, 0, 0])
    difference() {
        union() {
            // Rohrstutzen nach unten
            translate([0, 0, -(boden_stutzen_l + bodenstaerke)])
                cylinder(h = boden_stutzen_l + bodenstaerke, r = tc_b_rohr_od / 2);
            // Flanschring am unteren Ende
            translate([0, 0, -(boden_stutzen_l + bodenstaerke)])
                translate([0, 0, -(tc_b_flansch_h)])
                    rotate_extrude()
                        polygon(points = [
                            [tc_b_rohr_id/2,       0],
                            [tc_b_rohr_od/2,       0],
                            [tc_b_rohr_od/2,       tc_b_flansch_h],
                            [tc_b_flansch_od/2,    tc_b_flansch_h],
                            [tc_b_flansch_od/2,    tc_b_flansch_h - 2.5*tan(20)],
                            [tc_b_flansch_od/2 - 2.5, 0],
                            [tc_b_rohr_id/2,       0]
                        ]);
            // Dichtsteg
            translate([0, 0, -(boden_stutzen_l + bodenstaerke + tc_b_flansch_h) - 0.8])
                difference() {
                    cylinder(h = 0.8, r = tc_b_rohr_id/2 + 1.5);
                    cylinder(h = 0.9, r = tc_b_rohr_id/2);
                }
        }
        // Innenbohrung durchgehend
        translate([0, 0, -(boden_stutzen_l + bodenstaerke + tc_b_flansch_h + 1)])
            cylinder(h = boden_stutzen_l + bodenstaerke + tc_b_flansch_h + 2, r = tc_b_rohr_id/2);
        // Dichtnut
        translate([0, 0, -(boden_stutzen_l + bodenstaerke + tc_b_flansch_h - tc_b_nut_breite)])
            difference() {
                cylinder(h = tc_b_nut_breite + 0.01, r = tc_b_flansch_od/2 - tc_b_nut_tiefe);
                cylinder(h = tc_b_nut_breite + 0.02, r = tc_b_rohr_id/2);
            }
    }
}

// ============================================================
//  MODULE: Topf-Körper
// ============================================================
module topf_koerper() {
    rotate([0, 0, gruppe_winkel])
    difference() {
        union() {
            // Außenzylinder
            cylinder(h = topf_hoehe, r = topf_or);

            // Stutzen 2" LINKS  (y = +stutzen_abstand)
            stutzen_parallel(
                y_offset   =  stutzen_abstand,
                z_pos      = stutzen_z,
                flansch_od = tc_a_flansch_od,
                rohr_od    = tc_a_rohr_od,
                rohr_id    = tc_a_rohr_id,
                flansch_h  = tc_a_flansch_h,
                nut_tiefe  = tc_a_nut_tiefe,
                nut_breite = tc_a_nut_breite
            );

            // Stutzen 1.5" MITTE (y = 0)
            stutzen_parallel(
                y_offset   =  0,
                z_pos      = stutzen_b_z,
                flansch_od = tc_b_flansch_od,
                rohr_od    = tc_b_rohr_od,
                rohr_id    = tc_b_rohr_id,
                flansch_h  = tc_b_flansch_h,
                nut_tiefe  = tc_b_nut_tiefe,
                nut_breite = tc_b_nut_breite
            );

            // Stutzen 2" RECHTS (y = -stutzen_abstand)
            stutzen_parallel(
                y_offset   = -stutzen_abstand,
                z_pos      = stutzen_z,
                flansch_od = tc_a_flansch_od,
                rohr_od    = tc_a_rohr_od,
                rohr_id    = tc_a_rohr_id,
                flansch_h  = tc_a_flansch_h,
                nut_tiefe  = tc_a_nut_tiefe,
                nut_breite = tc_a_nut_breite
            );
            // Stutzen 2\" OBEN LINKS  (y = +stutzen_abstand)
            stutzen_parallel(
                y_offset   =  stutzen_abstand,
                z_pos      = tc_a_oben_links_z,
                flansch_od = tc_a_flansch_od,
                rohr_od    = tc_a_rohr_od,
                rohr_id    = tc_a_rohr_id,
                flansch_h  = tc_a_flansch_h,
                nut_tiefe  = tc_a_nut_tiefe,
                nut_breite = tc_a_nut_breite
            );

            // Stutzen 2\" OBEN RECHTS (y = -stutzen_abstand)
            stutzen_parallel(
                y_offset   = -stutzen_abstand,
                z_pos      = tc_a_oben_rechts_z,
                flansch_od = tc_a_flansch_od,
                rohr_od    = tc_a_rohr_od,
                rohr_id    = tc_a_rohr_id,
                flansch_h  = tc_a_flansch_h,
                nut_tiefe  = tc_a_nut_tiefe,
                nut_breite = tc_a_nut_breite
            );

            // --- Temperatursensor: 1.5" mittig, 90° versetzt ---
            rotate([0, 0, temp_winkel - gruppe_winkel])
                stutzen_parallel(
                    y_offset   = 0,
                    z_pos      = temp_z,
                    flansch_od = tc_b_flansch_od,
                    rohr_od    = tc_b_rohr_od,
                    rohr_id    = tc_b_rohr_id,
                    flansch_h  = tc_b_flansch_h,
                    nut_tiefe  = tc_b_nut_tiefe,
                    nut_breite = tc_b_nut_breite
                );

            // --- Oberer 1.5" Stutzen: in Linie mit Hauptgruppe, nahe Topfrand ---
            stutzen_parallel(
                y_offset   = 0,
                z_pos      = oben_b_z,
                flansch_od = tc_b_flansch_od,
                rohr_od    = tc_b_rohr_od,
                rohr_id    = tc_b_rohr_id,
                flansch_h  = tc_b_flansch_h,
                nut_tiefe  = tc_b_nut_tiefe,
                nut_breite = tc_b_nut_breite
            );

            // --- Boden-Ablassstutzen (nach unten, abschaltbar) ---
            if (boden_stutzen_aktiv)
                boden_stutzen();

            // --- Bügelgriffe links + rechts (abschaltbar) ---
            if (griff_aktiv) {
                rotate([0, 0,  griff_winkel]) buegelgriff();
                rotate([0, 0, -griff_winkel]) buegelgriff();
            }
        }

        // Innenraum ausschneiden
        translate([0, 0, bodenstaerke])
            cylinder(h = topf_hoehe, r = topf_ir);

        // Wanddurchbrüche unteres Trio
        durchbruch_parallel( stutzen_abstand, stutzen_z,          tc_a_rohr_id);
        durchbruch_parallel( 0,               stutzen_b_z,        tc_b_rohr_id);
        durchbruch_parallel(-stutzen_abstand, stutzen_z,          tc_a_rohr_id);

        // Wanddurchbrüche oberes 2"-Paar
        durchbruch_parallel( stutzen_abstand, tc_a_oben_links_z,  tc_a_rohr_id);
        durchbruch_parallel(-stutzen_abstand, tc_a_oben_rechts_z, tc_a_rohr_id);

        // Wanddurchbruch Temperatursensor
        rotate([0, 0, temp_winkel - gruppe_winkel])
            durchbruch_parallel(0, temp_z, tc_b_rohr_id);

        // Wanddurchbruch oberer 1.5" Stutzen
        durchbruch_parallel(0, oben_b_z, tc_b_rohr_id);

        // Bodendurchbruch Ablassstutzen
        if (boden_stutzen_aktiv)
            rotate([0, 0, gruppe_winkel])
                translate([boden_stutzen_versatz, 0, -0.1])
                    cylinder(h = bodenstaerke + 0.2, r = tc_b_rohr_id / 2);
    }
}

// ============================================================
//  HAUPTKONSTRUKTION
// ============================================================
topf_koerper();

// ============================================================
//  DEBUG: Einzelnen Stutzen isoliert (auskommentieren zum Testen)
// ============================================================
// triclamp_stutzen(tc_a_flansch_od, tc_a_rohr_od, tc_a_rohr_id,
//                  tc_a_flansch_h, stutzen_laenge(stutzen_abstand),
//                  tc_a_nut_tiefe, tc_a_nut_breite);
