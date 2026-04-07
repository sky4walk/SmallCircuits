// ============================================================
//  Achteck – vollständig parametrisierbar
// ============================================================
//
//  Parameter:
//    breite           – Gesamtbreite des Achtecks (x-Achse), mm
//    hoehe            – Gesamthöhe des Achtecks (y-Achse), mm
//    tiefe            – Extrusionstiefe (z-Achse), mm
//    seite_oben_unten – Länge der oberen und unteren flachen Seite, mm
//    seite_links_rechts – Höhe der linken und rechten flachen Seite, mm
//
//  Bedingungen:
//    seite_oben_unten   < breite
//    seite_links_rechts < hoehe
// ============================================================
variante = 2;

m5                 = 5;
breite             = 140;    // Gesamtbreite, mm
hoehe              = 30;     // Gesamthöhe,   mm
tiefe              = 5;      // Extrusionstiefe (z-Achse), mm
seite_oben_unten   = m5*4;   // Länge der oberen/unteren Seite, mm
seite_links_rechts = m5*4;   // Höhe der linken/rechten Seite, mm
stuhlbein          = 40;
$fn=64;

// ---- Modul -------------------------------------------------
module achteck(b, h, t, su, slr) {
    hb   = b   / 2;   // halbe Breite
    hh   = h   / 2;   // halbe Höhe
    hsu  = su  / 2;   // halbe Länge oben/unten
    hslr = slr / 2;   // halbe Höhe links/rechts

    // 8 Punkte im Uhrzeigersinn, beginnend oben-links
    punkte = [
        [-hsu,   hh    ],   // oben-links
        [ hsu,   hh    ],   // oben-rechts
        [ hb,    hslr  ],   // rechts-oben
        [ hb,   -hslr  ],   // rechts-unten
        [ hsu,  -hh    ],   // unten-rechts
        [-hsu,  -hh    ],   // unten-links
        [-hb,   -hslr  ],   // links-unten
        [-hb,    hslr  ]    // links-oben
    ];

    linear_extrude(height = t, center = false)
        polygon(points = punkte);
}

// ---- Aufruf ------------------------------------------------
if ( 1 == variante ) {
    difference()
    {
        achteck(breite+4*m5, hoehe+4*m5, tiefe, seite_oben_unten, seite_links_rechts);
        translate([-breite/2,0,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
        translate([ breite/2,0,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
        translate([0, hoehe/2,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
        translate([0,-hoehe/2,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
    }
} else {
    difference()
    {
        achteck(breite+4*m5, hoehe+4*m5, tiefe, stuhlbein+m5*2, seite_links_rechts);
        translate([-breite/2,0,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
        translate([ breite/2,0,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
        translate([-stuhlbein/2-m5/2,-hoehe/2,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
        translate([ stuhlbein/2+m5/2,-hoehe/2,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
        translate([-stuhlbein/2-m5/2, hoehe/2,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
        translate([ stuhlbein/2+m5/2, hoehe/2,-.1]) cylinder(tiefe+.2,m5/2,m5/2);
    }
}
