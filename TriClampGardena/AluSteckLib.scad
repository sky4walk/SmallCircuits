// ============================================================
//  ALUSTECK® Komplettbibliothek – 25 × 25 mm System
//
//  Teile:
//    0  vierkantrohr()           – Rohr (Länge frei wählbar)
//    1  rechter_winkel()         – L-Form,  2 Zapfen (2D)
//    2  t_stueck()               – T-Form,  3 Zapfen (2D)
//    3  kreuz()                  – +-Form,  4 Zapfen (2D)
//    4  rechter_winkel_abgang()  – 3D-Ecke, 3 Zapfen
//    5  t_verbinder_abgang()     – 3D-T+1,  4 Zapfen
//    6  kreuz_abgang()           – Kreuz+1, 5 Zapfen (3D)
//    7  stern()                  – Alle 6 Seiten, 6 Zapfen (3D)
//    8  rohrverlaengerung()      – Gerade Verlängerung, 2 Zapfen
//
//  Koordinatensystem des Knotens:
//    Querschnitt zentriert in XY, Extrusion in +Z (0 → hub_s)
//    +X-Fläche bei x=+hub_s/2,  -X bei x=-hub_s/2
//    +Y-Fläche bei y=+hub_s/2,  -Y bei y=-hub_s/2
//    +Z-Fläche bei z=hub_s,     -Z bei z=0
//
//  Rotationen (geprüft – Zapfen wächst in +Z, wird auf Achse gedreht):
//    +X: rotate([  0, 90, 0])  →  z→+x
//    -X: rotate([  0,-90, 0])  →  z→-x
//    +Y: rotate([-90,  0, 0])  →  z→+y
//    -Y: rotate([ 90,  0, 0])  →  z→-y
//    +Z: kein rotate            →  z→+z
//    -Z: rotate([180,  0, 0])  →  z→-z
// ============================================================

/* [Anzeige] */
anzeige = 1; // [0:Vierkantrohr, 1:Rechter Winkel, 2:T-Stück, 3:Kreuz, 4:Rechter Winkel 3D, 5:T-Verbinder 3D, 6:Kreuz mit Abgang, 7:Stern, 8:Rohrverlängerung]

/* [Rohr] */
rohr_laenge      = 500;
rohr_innenrillen = true;
rillen_anz       = 28;
rillentiefe      = 0.25;
rillenbreite     = 0.4;

/* [Gemeinsame Maße] */
rohr_aussen   = 25.0;
wandstaerke_r = 1.5;
ecken_r_rohr  = 2.0;

/* [Verbinder-Maße] */
zapfen_laenge = 49.0;
spiel         = 0.15;
wandstaerke_v = 1.8;
ecken_r_v     = 1.6;

/* [Rippen] */
rippen_an  = true;
rippen_anz = 5;
rippen_h   = 0.5;
rippen_b   = 1.0;

// ============================================================
//  Abgeleitete Werte
// ============================================================
rohr_innen   = rohr_aussen - 2 * wandstaerke_r;
innen_r_rohr = max(0.1, ecken_r_rohr - wandstaerke_r);

zapfen_s = rohr_aussen - 2 * spiel;
innen_s  = zapfen_s - 2 * wandstaerke_v;
hub_s    = rohr_aussen;

// ============================================================
//  Hilfsmakro: abgerundetes Quadrat (2D), zentriert
// ============================================================
module sq(s, r) {
    offset(r = r) square(s - 2*r, center = true);
}

// ============================================================
//  VIERKANTROHR
// ============================================================
module vierkantrohr(l = rohr_laenge) {
    difference() {
        linear_extrude(l) sq(rohr_aussen, ecken_r_rohr);
        translate([0, 0, -0.01])
        linear_extrude(l + 0.02)
            sq(rohr_innen, innen_r_rohr);
        if (rohr_innenrillen) {
            for (seite = [0:3]) {
                rotate([0, 0, seite * 90])
                translate([0, 0, -0.01])
                linear_extrude(l + 0.02)
                    rohr_rillen_2d();
            }
        }
    }
}

module rohr_rillen_2d() {
    rasterb = rohr_innen / rillen_anz;
    for (i = [0 : rillen_anz - 1]) {
        x = -rohr_innen/2 + i * rasterb + rasterb/2;
        translate([x, rohr_innen/2 - rillentiefe * 0.75])
        polygon([
            [-rillenbreite/2,  0],
            [ rillenbreite/2,  0],
            [ 0,               rillentiefe * 1.5]
        ]);
    }
}

// ============================================================
//  ZAPFEN
//  Wächst in +Z ab Ursprung, Querschnitt zentriert in XY.
//  Rippen auf allen 4 Außenflächen.
// ============================================================
module zapfen(l = zapfen_laenge) {
    z0  = l * 0.12;
    zl  = l * 0.70;
    nb  = zapfen_s * 0.72;
    gap = (rippen_anz > 1) ? nb / (rippen_anz - 1) : 0;
    h   = rippen_h;
    b   = rippen_b;
    s   = zapfen_s;

    union() {
        // Hohlkörper
        difference() {
            linear_extrude(l) sq(s, ecken_r_v);
            translate([0, 0, -0.01])
            linear_extrude(l + 0.02)
                sq(innen_s, max(0.1, ecken_r_v - wandstaerke_v));
        }

        // Rippen ±Y (über X verteilt)
        for (i = [0 : rippen_anz - 1]) {
            x = -nb/2 + i * gap;
            translate([x,  s/2,       z0 + zl/2]) cube([b, h, zl], center=true);
            translate([x, -s/2 - h/2, z0 + zl/2]) cube([b, h, zl], center=true);
        }

        // Rippen ±X (über Y verteilt)
        for (i = [0 : rippen_anz - 1]) {
            y = -nb/2 + i * gap;
            translate([ s/2,       y, z0 + zl/2]) cube([h, b, zl], center=true);
            translate([-s/2 - h/2, y, z0 + zl/2]) cube([h, b, zl], center=true);
        }
    }
}

// ============================================================
//  KNOTEN
// ============================================================
module knoten() {
    linear_extrude(hub_s) sq(hub_s, ecken_r_v);
}

// ============================================================
//  zapfen_rot: dreht Zapfen (+Z) auf gewünschte Achse
//
//  Geprüfte Rotationsmatrix für rotate([a,b,c]) um Y-Achse:
//    rotate([0, 90,0]): (x,y,z)→( z, y,-x)  → z wächst in +X ✓
//    rotate([0,-90,0]): (x,y,z)→(-z, y, x)  → z wächst in -X ✓
//    rotate([-90,0,0]): (x,y,z)→( x, z,-y)  → z wächst in +Y ✓
//    rotate([ 90,0,0]): (x,y,z)→( x,-z, y)  → z wächst in -Y ✓
// ============================================================
module zapfen_rot(dir) {
    if      (dir == [ 1, 0, 0]) rotate([  0, 90, 0]) zapfen();
    else if (dir == [-1, 0, 0]) rotate([  0,-90, 0]) zapfen();
    else if (dir == [ 0, 1, 0]) rotate([-90,  0, 0]) zapfen();
    else if (dir == [ 0,-1, 0]) rotate([ 90,  0, 0]) zapfen();
    else if (dir == [ 0, 0, 1])                       zapfen();
    else if (dir == [ 0, 0,-1]) rotate([180,  0, 0]) zapfen();
}

// ============================================================
//  zapfen_an: Zapfen bündig an Knotenaußenfläche
//
//  Knotengeometrie (zentriert XY, +Z-Extrusion 0→hub_s):
//    Flächenmittelpunkte:
//      +X → ( hub_s/2,      0, hub_s/2)
//      -X → (-hub_s/2,      0, hub_s/2)
//      +Y → (       0,  hub_s/2, hub_s/2)
//      -Y → (       0, -hub_s/2, hub_s/2)
//      +Z → (       0,       0,  hub_s  )
//      -Z → (       0,       0,  0      )
//
//  Formel: pos = dir * hub_s/2 + [0, 0, hub_s/2]
// ============================================================
module zapfen_an(dir) {
    pos = dir * (hub_s/2) + [0, 0, hub_s/2];
    translate(pos) zapfen_rot(dir);
}

// ============================================================
//  VERBINDER
// ============================================================

module rechter_winkel() {
    knoten();
    zapfen_an([-1, 0, 0]);   // nach links  (-X)  ← Knoten sitzt in der Ecke
    zapfen_an([ 0, 0,-1]);   // nach unten  (-Z)
}

module t_stueck() {
    knoten();
    zapfen_an([ 1, 0, 0]);
    zapfen_an([-1, 0, 0]);
    zapfen_an([ 0, 0,-1]);
}

module kreuz() {
    knoten();
    zapfen_an([ 1, 0, 0]);
    zapfen_an([-1, 0, 0]);
    zapfen_an([ 0, 0, 1]);
    zapfen_an([ 0, 0,-1]);
}

module rechter_winkel_abgang() {
    knoten();
    zapfen_an([ 1, 0, 0]);
    zapfen_an([ 0, 0,-1]);
    zapfen_an([ 0, 1, 0]);
}

module t_verbinder_abgang() {
    knoten();
    zapfen_an([ 1, 0, 0]);
    zapfen_an([-1, 0, 0]);
    zapfen_an([ 0, 0,-1]);
    zapfen_an([ 0, 1, 0]);
}

// ============================================================
//  8. ROHRVERLÄNGERUNG  (gerade, 2 Zapfen gegenüber: +Z und -Z)
// ============================================================
module rohrverlaengerung() {
    knoten();
    zapfen_an([ 0, 0, 1]);
    zapfen_an([ 0, 0,-1]);
}

// ============================================================
//  RENDER  (Kreuz in XZ + 1 Zapfen nach +Y)
//     5 Zapfen: +X, -X, +Z, -Z, +Y
// ============================================================
module kreuz_abgang() {
    knoten();
    zapfen_an([ 1, 0, 0]);
    zapfen_an([-1, 0, 0]);
    zapfen_an([ 0, 0, 1]);
    zapfen_an([ 0, 0,-1]);
    zapfen_an([ 0, 1, 0]);
}

// ============================================================
//  7. STERN  (alle 6 Seiten belegt)
//     6 Zapfen: +X, -X, +Y, -Y, +Z, -Z
// ============================================================
module stern() {
    knoten();
    zapfen_an([ 1, 0, 0]);
    zapfen_an([-1, 0, 0]);
    zapfen_an([ 0, 1, 0]);
    zapfen_an([ 0,-1, 0]);
    zapfen_an([ 0, 0, 1]);
    zapfen_an([ 0, 0,-1]);
}

// ============================================================
//  RENDER
// ============================================================
if      (anzeige == 0) vierkantrohr(rohr_laenge);
else if (anzeige == 1) rechter_winkel();
else if (anzeige == 2) t_stueck();
else if (anzeige == 3) kreuz();
else if (anzeige == 4) rechter_winkel_abgang();
else if (anzeige == 5) t_verbinder_abgang();
else if (anzeige == 6) kreuz_abgang();
else if (anzeige == 7) stern();
else if (anzeige == 8) rohrverlaengerung();

// ============================================================
//  Alle Teile nebeneinander (zum Testen auskommentieren):
//
//  gap = 120;
//  vierkantrohr(200);
//  translate([gap,   0, 0]) rechter_winkel();
//  translate([gap*2, 0, 0]) t_stueck();
//  translate([gap*3, 0, 0]) kreuz();
//  translate([gap*4, 0, 0]) rechter_winkel_abgang();
//  translate([gap*5, 0, 0]) t_verbinder_abgang();
//  translate([gap*6, 0, 0]) kreuz_abgang();
//  translate([gap*7, 0, 0]) stern();
//  translate([gap*8, 0, 0]) rohrverlaengerung();
// ============================================================
