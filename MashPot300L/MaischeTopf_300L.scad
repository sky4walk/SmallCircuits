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
