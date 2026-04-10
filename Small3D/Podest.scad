// ============================================================
//  Podest – parametrisch
//  Alle Maße in Millimetern
//  Ursprung: Mitte der Grundfläche, Unterkante Z=0
// ============================================================

// --- Parameter ---
hoehe      = 100;  // Gesamthöhe des Podests
flaeche    = 160;  // Seitenlänge der quadratischen Grundfläche
oeffnung   = 110;  // Seitenlänge der quadratischen Öffnung in der Deckplatte

// --- Abgeleitete Werte ---
fuss_dicke =  (flaeche - oeffnung) /  2;  // Quadratischer Querschnitt der vier Füsse
wandstaerke = (flaeche - oeffnung) / 2 ;
deckel_h    = max(20, hoehe * 0.04);
fuss_h      = hoehe - deckel_h;

// Außenkante der Füsse bündig mit Außenkante der Grundfläche.
// Mittelpunkt jedes Fusses in XY:
fuss_mitte  = flaeche / 2 - fuss_dicke / 2;

// ============================================================
//  Hilfsfunktion: Quader, zentriert in XY, Z startet bei z_base
// ============================================================
module quader(cx, cy, z_base, w, d, h) {
    translate([cx - w/2, cy - d/2, z_base])
        cube([w, d, h]);
}

// ============================================================
//  Fuesse – vier Ecken, Aussenkanten bündig mit Grundflaeche
// ============================================================
module fuesse() {
    for (sx = [-1, 1], sy = [-1, 1]) {
        quader(sx * fuss_mitte, sy * fuss_mitte, 0,
               fuss_dicke, fuss_dicke, fuss_h);
    }
}

// ============================================================
//  Deckplatte mit quadratischer Oeffnung
//  4 Planken, lueckenlos, keine Ueberlappungen:
//    vorne/hinten : volle Breite (flaeche), Tiefe = wandstaerke
//    links/rechts : Breite = wandstaerke, Tiefe = oeffnung
// ============================================================
module deckplatte() {
    // Vordere Planke  (Aussenkante bei Y = +flaeche/2)
    quader(0,  flaeche/2 - wandstaerke/2, fuss_h,
           flaeche, wandstaerke, deckel_h);

    // Hintere Planke  (Aussenkante bei Y = -flaeche/2)
    quader(0, -flaeche/2 + wandstaerke/2, fuss_h,
           flaeche, wandstaerke, deckel_h);

    // Rechte Planke   (Aussenkante bei X = +flaeche/2)
    quader( flaeche/2 - wandstaerke/2, 0, fuss_h,
            wandstaerke, oeffnung, deckel_h);

    // Linke Planke    (Aussenkante bei X = -flaeche/2)
    quader(-flaeche/2 + wandstaerke/2, 0, fuss_h,
            wandstaerke, oeffnung, deckel_h);
}

// ============================================================
//  Zusammenbau
// ============================================================
fuesse();
deckplatte();
