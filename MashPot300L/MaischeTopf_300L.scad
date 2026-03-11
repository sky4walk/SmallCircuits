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

// ============================================================
//  SCHALTER – hier ein/ausschalten
// ============================================================
topf_podest_aktiv  = true;   // Topf-Podest (Gestell unter dem Topf)
laeuterblech_aktiv = false;   // Läuterblech
podest_aktiv       = false;   // Innenpodest (Läuterblech-Träger)
griff_aktiv        = true;   // Bügelgriffe
boden_stutzen_aktiv = true;  // Boden-Ablassstutzen
deckel_aktiv        = true;  // Deckel
klappe_aktiv        = true;  // Klappe (Einwurfsöffnung)
motor_aktiv         = true;  // Motor (Platzhalter)

 $fn = 128;  // Rendering-Qualität – auskommentiert für schnelles Vorschau-Rendering
//             // Einkommentieren für finales Render

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
griff_winkel       = gruppe_winkel + 90; // 90° zur Hauptgruppe
griff_rohr_od      = 12.0;   // Außendurchmesser des Griffrohres
griff_rohr_id      = 8.0;    // Innendurchmesser (hohl)
griff_breite       = 80.0;   // Breite des U-Bügels (außen)
griff_tiefe        = 60.0;   // wie weit der Griff nach außen ragt
griff_rand_abstand = 30.0;   // Abstand Griffmitte vom Topfrand nach unten
griff_r            = griff_rohr_od / 2; // Biegeradius der U-Kurve = Rohrradius

// --- Deckel ---
deckel_staerke       = 3.0;    // Blechstärke des Deckels
deckel_ueberstand    = 10.0;   // wie weit der Deckel über den Topfrand hinausragt
deckel_r             = topf_or + deckel_ueberstand; // Außenradius Deckel

// Einwurfsöffnung / Klappe
// Klappe als Kreisabschnitt (Sehne = Scharnier, Bogen = freie Kante)
// Kreisabschnitt: Pfeilhöhe = 1/3 des Radius → kompakte Einwurfsöffnung
// Pfeilhöhe h = deckel_r / 3, Sehne bei klappe_tiefe = deckel_r - h = 2/3 * deckel_r
klappe_tiefe       = deckel_r * 2 / 3;  // Abstand Sehne vom Mittelpunkt
klappe_winkel_pos  = gruppe_winkel;      // Klappe zeigt zur Tri-Clamp Gruppe
klappe_staerke     = 3.0;    // Blechstärke der Klappe
klappe_offen       = 0;      // Öffnungswinkel (0=geschlossen, 90=offen)
klappe_offen_aktiv = true;   // true = Öffnung im Deckel sichtbar, false = Deckel geschlossen

// Sehnenlänge: 2 * sqrt(r² - d²)  mit d = klappe_tiefe
// scharnier_l = Länge des Scharnierstabs entlang der Sehne
scharnier_r        = 4.0;    // Radius des Scharnierstabs
scharnier_l        = 2 * sqrt(deckel_r * deckel_r - klappe_tiefe * klappe_tiefe) - 20.0;

// Bügelgriff auf der Klappe
kgriff_rohr_od     = 8.0;    // Außendurchmesser Griffrohr
kgriff_rohr_id     = 5.0;    // Innendurchmesser (hohl)
kgriff_breite      = 60.0;   // Breite des U-Bügels
kgriff_hoehe       = 25.0;   // Höhe des U-Bügels über Klappe
// Griff nahe Außenkante: mittig auf der Klappe in Y, weit außen in X
kgriff_x           = (klappe_tiefe + deckel_r) / 2;  // mittig zwischen Sehne und Bogen

// --- Motor (Platzhalter, mittig auf Deckel) ---
motor_lochkreis     = 80.0;   // Lochabstand der 4 Schrauben (quadratisch)
motor_schraube_d    = 6.0;    // Schraubendurchmesser
motor_welle_d       = 30.0;   // Wellendurchmesser
motor_platte_b      = motor_lochkreis + 30.0;  // Montageplatte Breite
motor_platte_h      = 8.0;    // Montageplatte Stärke
motor_quader_b      = motor_lochkreis + 10.0;  // Motor-Quader Breite
motor_quader_h      = 80.0;   // Motor-Quader Höhe (Platzhalter)

// Arretierungszapfen (greift in den Bügelgriff)
zapfen_r             = griff_rohr_id / 2 - 0.5;  // Radius = Griffinnen-ID minus Spiel
zapfen_h             = griff_rand_abstand + griff_rohr_od + 10.0;  // durch das U + 10mm Überstand
// Zapfen sitzt an der Stelle wo der Griff an der Wand befestigt ist
// → bei ±griff_breite/2 tangential, topf_or radial, topf_hoehe - deckel_staerke Z

// --- Topf-Podest (Gestell unter dem Topf, abschaltbar) ---
topf_podest_b        = topf_id - 20;  // Breite des Podests (X) → innerhalb des Topf-ID
topf_podest_t        = topf_id - 20;  // Tiefe des Podests (Y) → innerhalb des Topf-ID
topf_podest_h        = 310.0;  // Höhe der Füsse
topf_podest_fuss_b   = 40.0;   // Querschnitt Fuss (Breite)
topf_podest_fuss_t   = 40.0;   // Querschnitt Fuss (Tiefe)
topf_podest_strebe_b = 10.0;   // Dicke der Streben
topf_podest_strebe_h = 40.0;   // Höhe der Streben (hochkant)

// --- Läuterblech (abschaltbar) ---
blech_od           = 708.0;          // Außendurchmesser Läuterblech (parametrisch)
blech_staerke      = 1.5;            // Blechstärke
// blech_z wird nach podest_hoehe berechnet (siehe unten)

// Schlitzparameter
schlitz_breite     = 1.5;
schlitz_laenge     = 40.0;
schlitz_abstand    = 1.5;
reihen_abstand     = 1.5;
reihen_versatz     = (schlitz_breite + schlitz_abstand) / 2;
rand_breite        = 10.0;

// Abgeleitete Blech-Maße
blech_r            = blech_od / 2;
nutzbereich_r      = blech_r - rand_breite;
schlitz_pitch_x    = schlitz_breite + schlitz_abstand;
reihen_pitch_y     = schlitz_laenge + reihen_abstand;
n_schlitze         = ceil(2 * nutzbereich_r / schlitz_pitch_x) + 2;
n_reihen           = ceil(2 * nutzbereich_r / reihen_pitch_y) + 2;

// --- Podest (abschaltbar) ---
podest_hoehe       = 65.0;
podest_fuss_r      = 15.0;
podest_mitte_r     = 20.0;
podest_radius      = blech_r - 40.0;
podest_winkel      = 45.0;
strebe_breite      = 8.0;
strebe_staerke     = 3.0;

// Läuterblech liegt auf Oberkante Podest (Füsse + Streben)
blech_z            = bodenstaerke + podest_hoehe;

// --- Boden-Ablassstutzen: 1.5" nach unten, abschaltbar ---
boden_stutzen_rand     = 100.0;          // Abstand vom Topfrand (Innenrand) in Richtung Hauptgruppe
boden_stutzen_versatz  = topf_ir - boden_stutzen_rand; // → Abstand von Topfmitte
boden_stutzen_l        = 20.0;           // Länge des Stutzens unter dem Boden

// --- Rendering-Qualität ---


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
//  MODULE: Einzelner Schlitz
// ============================================================
module schlitz() {
    r = schlitz_breite / 2;
    hull() {
        translate([0,  schlitz_laenge/2 - r, 0]) cylinder(h = blech_staerke + 0.1, r = r);
        translate([0, -schlitz_laenge/2 + r, 0]) cylinder(h = blech_staerke + 0.1, r = r);
    }
}

// ============================================================
//  MODULE: Schlitzmuster (Negativ)
// ============================================================
module schlitzmuster() {
    for (row = [-n_reihen : n_reihen]) {
        x_off = (row % 2 == 0) ? 0 : reihen_versatz;
        y_pos = row * reihen_pitch_y;
        for (col = [-n_schlitze : n_schlitze]) {
            x_pos = col * schlitz_pitch_x + x_off;
            if (sqrt(x_pos*x_pos + y_pos*y_pos) < nutzbereich_r + schlitz_laenge)
                translate([x_pos, y_pos, -0.05]) schlitz();
        }
    }
}

// ============================================================
//  MODULE: Nutzbereich-Maske
// ============================================================
module nutzbereich_maske() {
    cylinder(h = blech_staerke + 0.2, r = nutzbereich_r);
}

// ============================================================
//  MODULE: Läuterblech
// ============================================================
module laeuterblech() {
    translate([0, 0, blech_z])
        difference() {
            cylinder(h = blech_staerke, r = blech_r);
            intersection() {
                translate([0, 0, -0.05]) nutzbereich_maske();
                schlitzmuster();
            }
        }
}

// ============================================================
//  MODULE: Podest-Strebe
// ============================================================
module strebe(x1, y1, x2, y2) {
    dx     = x2 - x1;
    dy     = y2 - y1;
    len    = sqrt(dx*dx + dy*dy);
    winkel = atan2(dy, dx);
    translate([x1, y1, 0])
        rotate([0, 0, winkel])
            translate([0, -strebe_staerke/2, 0])
                cube([len, strebe_staerke, strebe_breite]);
}

// ============================================================
//  MODULE: Podest (Füsse + Streben, steht auf Topfboden)
// ============================================================
module podest() {
    // Füsse stehen auf dem Topfinnenboden
    // Streben liegen direkt unter dem Läuterblech (blech_z - strebe_breite)
    z_fuesse   = bodenstaerke;
    z_streben  = blech_z - strebe_breite;

    fuss_pos = [
        for (i = [0:3])
            [podest_radius * cos(podest_winkel + i*90),
             podest_radius * sin(podest_winkel + i*90)]
    ];

    // Streben direkt unter dem Blech
    translate([0, 0, z_streben]) {
        for (p = fuss_pos) strebe(0, 0, p[0], p[1]);
        for (i = [0:3]) {
            p1 = fuss_pos[i];
            p2 = fuss_pos[(i+1) % 4];
            strebe(p1[0], p1[1], p2[0], p2[1]);
        }
    }

    // Füsse vom Innenboden bis zur Strebenunterkante
    fuss_h = z_streben - z_fuesse;
    translate([0, 0, z_fuesse]) {
        for (p = fuss_pos)
            translate([p[0], p[1], 0])
                cylinder(h = fuss_h, r = podest_fuss_r);
        cylinder(h = fuss_h, r = podest_mitte_r);
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
    }  // end difference
}  // end topf_koerper

// ============================================================
//  MODULE: Topf-Podest (4 Eckfüsse + oberer Rahmen)
// ============================================================
module topf_podest() {
    hb = topf_podest_b / 2;   // halbe Breite
    ht = topf_podest_t / 2;   // halbe Tiefe
    fuss_b = topf_podest_fuss_b;
    fuss_t = topf_podest_fuss_t;
    fuss_h = topf_podest_h;
    str_b  = topf_podest_strebe_b;
    str_h  = topf_podest_strebe_h;

    // Eckpositionen der 4 Füsse (Mitte jedes Fusses)
    ecken = [
        [-hb + fuss_b/2, -ht + fuss_t/2],
        [ hb - fuss_b/2, -ht + fuss_t/2],
        [ hb - fuss_b/2,  ht - fuss_t/2],
        [-hb + fuss_b/2,  ht - fuss_t/2]
    ];

    // Podest liegt unter dem Topf → Z geht von -(fuss_h) bis 0
    translate([0, 0, -fuss_h]) {

        // --- 4 Eckfüsse ---
        for (e = ecken)
            translate([e[0] - fuss_b/2, e[1] - fuss_t/2, 0])
                cube([fuss_b, fuss_t, fuss_h]);

        // --- Oberer Rahmen: 4 Streben zwischen den Ecken ---
        // Streben oben bündig mit Fuss-Oberkante (z = fuss_h - str_h)
        z_str = fuss_h - str_h;

        // Strebe vorne (Y = -ht): von Ecke [0] nach Ecke [1]
        translate([-hb + fuss_b, -ht, z_str])
            cube([topf_podest_b - 2*fuss_b, str_b, str_h]);

        // Strebe hinten (Y = +ht - str_b): von Ecke [3] nach Ecke [2]
        translate([-hb + fuss_b, ht - str_b, z_str])
            cube([topf_podest_b - 2*fuss_b, str_b, str_h]);

        // Strebe links (X = -hb): von Ecke [0] nach Ecke [3]
        translate([-hb, -ht + fuss_t, z_str])
            cube([str_b, topf_podest_t - 2*fuss_t, str_h]);

        // Strebe rechts (X = +hb - str_b): von Ecke [1] nach Ecke [2]
        translate([hb - str_b, -ht + fuss_t, z_str])
            cube([str_b, topf_podest_t - 2*fuss_t, str_h]);

        // Diagonale Querstreben (X-Form): Ecke zu Ecke
        // Verlängerung in beide Richtungen um halben Fuss-Querschnitt
        verlaengerung = sqrt(fuss_b*fuss_b + fuss_t*fuss_t) / 2;
        diag_dx  = topf_podest_b - 2*fuss_b;
        diag_dy  = topf_podest_t - 2*fuss_t;
        diag_len = sqrt(diag_dx*diag_dx + diag_dy*diag_dy) + 2*verlaengerung;
        diag_winkel = atan2(diag_dy, diag_dx);

        // Diagonale 1: von Ecke vorne-links nach Ecke hinten-rechts
        translate([-hb + fuss_b, -ht + fuss_t, z_str])
            rotate([0, 0, diag_winkel])
                translate([-verlaengerung, -str_b/2, 0])
                    cube([diag_len, str_b, str_h]);

        // Diagonale 2: von Ecke vorne-rechts nach Ecke hinten-links
        translate([hb - fuss_b, -ht + fuss_t, z_str])
            rotate([0, 0, 180 - diag_winkel])
                translate([-verlaengerung, -str_b/2, 0])
                    cube([diag_len, str_b, str_h]);
    }
}

// ============================================================
//  MODULE: Deckel (flach, mit Überstand + Arretierung)
//
//  Arretierung pro Griff-Seite:
//    - Rechteckige Lasche die vom Deckelrand bis über die Griffrohre ragt
//    - Zwei Zapfen hängen von der Lasche nach unten in die Griffrohre
//    → verhindert Rotation des Deckels wenn Motor dreht
// ============================================================
module deckel() {
    z_deckel  = topf_hoehe;
    halb_b    = griff_breite / 2;
    lasche_b  = griff_breite + griff_rohr_od * 2;
    lasche_t  = griff_tiefe + griff_rohr_od;
    lasche_h  = deckel_staerke;
    x_zapfen  = topf_or + griff_tiefe / 2;

    difference() {
        union() {
            // --- Grundplatte: flache Scheibe ---
            translate([0, 0, z_deckel])
                cylinder(h = deckel_staerke, r = deckel_r);

            // --- Arretierung: je eine Lasche + 2 Zapfen pro Griff-Seite ---
            // gruppe_winkel mitdrehen damit Laschen exakt auf den Griffen sitzen
            rotate([0, 0, gruppe_winkel])
            for (seite = [1, -1]) {
                rotate([0, 0, seite * 90]) {
                    // Rechteckige Lasche
                    translate([topf_or - griff_rohr_od,
                               -lasche_b / 2,
                               z_deckel])
                        cube([lasche_t, lasche_b, lasche_h]);

                    // Zapfen links
                    translate([x_zapfen,  halb_b / 2, z_deckel - zapfen_h])
                        cylinder(h = zapfen_h, r = zapfen_r);

                    // Zapfen rechts
                    translate([x_zapfen, -halb_b / 2, z_deckel - zapfen_h])
                        cylinder(h = zapfen_h, r = zapfen_r);
                }
            }
        }

        // --- Wellenöffnung für Motor mittig im Deckel ---
        if (motor_aktiv)
            translate([0, 0, topf_hoehe - 0.1])
                cylinder(h = deckel_staerke + 0.2, r = motor_welle_d / 2);

        // --- Öffnung für Klappe (Kreisabschnitt) ausschneiden, abschaltbar ---
        if (klappe_offen_aktiv)
            rotate([0, 0, klappe_winkel_pos])
                translate([0, 0, topf_hoehe - 0.1])
                    linear_extrude(height = deckel_staerke + 0.2)
                        intersection() {
                            circle(r = deckel_r + 0.1);
                            translate([klappe_tiefe, -(deckel_r + 0.1)])
                                square([deckel_r - klappe_tiefe + 0.1, (deckel_r + 0.1) * 2]);
                        }
    }
}

// ============================================================
//  MODULE: Motor (Platzhalter mit Montageplatte + Quader)
//  - Montageplatte mit 4 Schraubenlöchern
//  - Wellenöffnung im Deckel
//  - Motor-Quader als Platzhalter
// ============================================================
module motor() {
    halb_lk  = motor_lochkreis / 2;
    halb_pb  = motor_platte_b / 2;
    halb_qb  = motor_quader_b / 2;
    z_deckel = topf_hoehe + deckel_staerke;

    union() {
        // --- Montageplatte ---
        translate([-halb_pb, -halb_pb, z_deckel])
            difference() {
                cube([motor_platte_b, motor_platte_b, motor_platte_h]);

                // Wellenöffnung mittig
                translate([halb_pb, halb_pb, -0.1])
                    cylinder(h = motor_platte_h + 0.2, r = motor_welle_d / 2);

                // 4 Schraubenlöcher an den Ecken des Lochkreises
                for (dx = [-1, 1], dy = [-1, 1])
                    translate([halb_pb + dx * halb_lk,
                               halb_pb + dy * halb_lk,
                               -0.1])
                        cylinder(h = motor_platte_h + 0.2,
                                 r = motor_schraube_d / 2);
            }

        // --- Motor-Quader als Platzhalter (sitzt auf der Montageplatte) ---
        translate([-halb_qb, -halb_qb, z_deckel + motor_platte_h])
            difference() {
                cube([motor_quader_b, motor_quader_b, motor_quader_h]);
                // Wellenöffnung durchgehend
                translate([halb_qb, halb_qb, -0.1])
                    cylinder(h = motor_quader_h + 0.2, r = motor_welle_d / 2);
            }
    }
}

// ============================================================
//  MODULE: Abgerundetes Rechteck (2D)
// ============================================================
module rundrechteck(b, t, r) {
    hull() {
        translate([ b/2 - r,  t/2 - r]) circle(r = r);
        translate([-b/2 + r,  t/2 - r]) circle(r = r);
        translate([ b/2 - r, -t/2 + r]) circle(r = r);
        translate([-b/2 + r, -t/2 + r]) circle(r = r);
    }
}

// ============================================================
//  MODULE: Einwurfsklappe mit Scharnier
//  - Rechteckige Öffnung im Deckel
//  - Klappe liegt auf oder klappt auf (klappe_offen = 0..90°)
//  - Einfaches Stabscharnier an der hinteren Kante
// ============================================================
module klappe() {
    // Kreisabschnitt: Sehne bei x = klappe_tiefe (Scharnier), Bogen = freie Kante
    // Klappe klappt um die Sehne (Y-Achse bei x = klappe_tiefe) nach oben auf

    gr          = kgriff_rohr_od / 2;
    gr_i        = kgriff_rohr_id / 2;
    halb_kb     = kgriff_breite / 2;
    z_deckel    = topf_hoehe + deckel_staerke;
    z_scharnier = z_deckel - scharnier_r;
    // Sehnenlänge (halbe Sehne für Y-Berechnung)
    halb_sehne  = sqrt(deckel_r * deckel_r - klappe_tiefe * klappe_tiefe);

    rotate([0, 0, klappe_winkel_pos])
    union() {
        // --- Scharnierstab entlang der Sehne (Y-Richtung bei x = klappe_tiefe) ---
        translate([klappe_tiefe, -scharnier_l / 2, z_scharnier])
            rotate([-90, 0, 0])
                cylinder(h = scharnier_l, r = scharnier_r);

        // --- Klappe dreht um Scharnier (Y-Achse bei x = klappe_tiefe) ---
        translate([klappe_tiefe, 0, z_deckel])
            rotate([0, -klappe_offen, 0])
            translate([-klappe_tiefe, 0, -z_deckel])
            union() {
                // Kreisabschnitt-Platte
                translate([0, 0, z_deckel])
                    linear_extrude(height = klappe_staerke)
                        intersection() {
                            circle(r = deckel_r);
                            translate([klappe_tiefe, -halb_sehne])
                                square([deckel_r - klappe_tiefe + 0.1, halb_sehne * 2]);
                        }

                // Bügelgriff: mittig in Y=0, nahe Außenbogen in X
                z_top = z_deckel + klappe_staerke;

                // Schenkel links
                translate([kgriff_x, halb_kb, z_top])
                    difference() {
                        cylinder(h = kgriff_hoehe, r = gr);
                        cylinder(h = kgriff_hoehe + 1, r = gr_i);
                    }
                // Schenkel rechts
                translate([kgriff_x, -halb_kb, z_top])
                    difference() {
                        cylinder(h = kgriff_hoehe, r = gr);
                        cylinder(h = kgriff_hoehe + 1, r = gr_i);
                    }
                // Querrohr oben
                translate([kgriff_x, -halb_kb, z_top + kgriff_hoehe - gr])
                    rotate([-90, 0, 0])
                        difference() {
                            cylinder(h = kgriff_breite, r = gr);
                            cylinder(h = kgriff_breite + 1, r = gr_i);
                        }
                // Verrundungen
                translate([kgriff_x,  halb_kb, z_top + kgriff_hoehe - gr]) sphere(r = gr);
                translate([kgriff_x, -halb_kb, z_top + kgriff_hoehe - gr]) sphere(r = gr);
            }
    }
}


// ============================================================
//  HAUPTKONSTRUKTION
// ============================================================
topf_koerper();

if (deckel_aktiv) {
    deckel();
    if (klappe_aktiv) klappe();
    if (motor_aktiv)  motor();
}
if (topf_podest_aktiv)  topf_podest();
if (laeuterblech_aktiv) laeuterblech();
if (podest_aktiv)       podest();

// ============================================================
//  DEBUG: Einzelnen Stutzen isoliert (auskommentieren zum Testen)
// ============================================================
// triclamp_stutzen(tc_a_flansch_od, tc_a_rohr_od, tc_a_rohr_id,
//                  tc_a_flansch_h, stutzen_laenge(stutzen_abstand),
//                  tc_a_nut_tiefe, tc_a_nut_breite);
