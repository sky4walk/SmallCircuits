// =====================================================================
//  CIP-Sprühkugel (Reinigungskugel) – parametrisch
//  Nachkonstruktion von cipball1.stl, erweitert um Tri-Clamp-Anschluss
//  Anschluss unten auf z=0 (Dichtfläche nach unten), Kugel oben.
//  https://itzwieseltal.wordpress.com  ·  https://zwieselbrau.wordpress.com
// =====================================================================

/* [Anschluss] */
anschluss    = "triclamp";   // [triclamp, gewinde, keiner]

/* [Kugel] */
kugel_d      = 42;     // Außendurchmesser Kugel (x/y)
kugel_h      = 42;     // Höhe der Kugel in z (> kugel_d = in die Länge gezogen)
wand         = 1;      // Wandstärke Kugel

/* [Zulaufrohr] */
rohr_di      = 20;     // Innendurchmesser Zulaufrohr (bei Gewinde = Kern-Ø)
rohr_wand    = 2.5;    // Wandstärke Zulaufrohr
rohr_laenge  = 10;     // gerades Rohrstück zwischen Anschluss und Kugel

/* [Tri-Clamp 1,5" (DIN 32676 / ISO 2852, Flansch 50,5)] */
tc_flansch_d = 50.5;   // Flansch-Außendurchmesser
tc_rand      = 2.85;   // Flanschdicke am Außenrand
tc_winkel    = 20;     // Klemmwinkel der Flanschrückseite
tc_gerade    = true;   // true: Schräge läuft direkt ins Rohr, Rohr gerade bis zur Kugel
                       // false: Normhals Ø38,1 x 12,7 mm, dann 45°-Konus aufs Rohr
tc_hals_d    = 38.1;   // Halsdurchmesser Norm (nur tc_gerade = false)
tc_hoehe     = 12.7;   // Ferrule-Höhe Norm (nur tc_gerade = false)
tc_nut_d     = 43.5;   // Durchmesser Mitte Dichtungsnut
tc_nut_r     = 1.3;    // Radius Nut
tc_nut_tiefe = 1.0;    // Tiefe Nut

/* [Gewinde (nur anschluss = gewinde; ~M22x2 innen mit Spiel)] */
gew_major_d  = 22.25;  // Gewindegrund
gew_minor_d  = 20;     // (wird durch rohr_di ersetzt)
gew_p        = 2;      // Steigung
gew_kopf     = 0.55;   // Breite Zahnspitze
gew_fuss     = 1.83;   // Breite Zahnfuß
gew_phase    = 0.5;    // axiale Lage Zahnmitte bei Winkel 0
gew_laenge   = 23.6;   // Gewindestutzen-Länge (Original: 23,6)
gew_seg      = 72;

/* [Sprühbohrungen] */
loch_muster  = "gleichmaessig";  // [gleichmaessig, original]
loch_d       = 2;
loch_raster  = 10;     // Lochabstand auf der Oberfläche (nur gleichmaessig)
loch_abstand = 1.2;    // Mindestabstand Lochrand zur Rohrkante

$fn = 96;

// ------------------------------------------------- abgeleitete Größen
R       = kugel_d/2;
Ri      = R - wand;
Rz      = kugel_h/2;          // Halbachse in z
Rzi     = Rz - wand;
rohr_ad = rohr_di + 2*rohr_wand;     // bei "gewinde" ist rohr_di = Kern-Ø
bohr_d  = (anschluss == "gewinde") ? gew_major_d : rohr_di;
gew_minor_eff = (anschluss == "gewinde") ? rohr_di : gew_minor_d;

// Höhe des Anschlussteils (inkl. Konus vom TC-Hals auf das Rohr)
hals_r   = tc_gerade ? rohr_ad/2 : tc_hals_d/2;
// Höhe, bei der die 20°-Schräge den Hals erreicht
tc_schraeg_h = tc_rand + (tc_flansch_d/2 - hals_r)*tan(tc_winkel);
konus_h  = (anschluss == "triclamp" && !tc_gerade) ? max(0, (tc_hals_d - rohr_ad)/2) : 0;   // 45°
unten_h  = (anschluss == "triclamp") ? (tc_gerade ? tc_schraeg_h : tc_hoehe + konus_h)
         : (anschluss == "gewinde")  ? gew_laenge : 0;
gerade_h = (anschluss == "gewinde") ? 0 : rohr_laenge;
uebergang = unten_h + gerade_h;                       // Rohr trifft Kugel
kugel_z  = uebergang + Rz*sqrt(1 - (rohr_ad/2/R)*(rohr_ad/2/R));

assert(anschluss != "gewinde" || rohr_ad > gew_major_d + 1, "Wand zu dünn für das Gewinde");
assert(kugel_h > 2*wand + 2, "Kugel zu flach");
assert(rohr_ad < kugel_d - 4, "Zulaufrohr zu dick für die Kugel");
assert(anschluss != "triclamp" || rohr_ad < tc_flansch_d - 2, "Rohr zu dick für den Flansch");
assert(anschluss != "triclamp" || rohr_di/2 < tc_nut_d/2 - tc_nut_r - 1,
       "Rohr-Innen-Ø zu groß für die Tri-Clamp-Dichtfläche");
assert(anschluss != "triclamp" || tc_gerade || rohr_ad <= tc_hals_d + 0.01,
       "Rohr-Außen-Ø größer als Tri-Clamp-Hals");

// Lochringe: [Elevation, Startwinkel, Schritt, Anzahl] (um die Querachse,
// Winkel 0 = Kugelscheitel). Löcher im Bereich des Rohrs entfallen automatisch.
loch_ringe = [
    [  0.00, -147.2, 32.80, 11 ],
    [ 31.33, -144.35, 32.45, 11 ],
    [-29.47, -144.35, 32.45, 11 ],
    [ 62.63, -124.25, 50.65, 7 ],
    [-58.98, -124.25, 50.65, 7 ],
    [ 86.10,    0.00,  0.00, 1 ],
    [-88.40,  180.00,  0.00, 1 ]
];
// minimaler Winkel eines Lochs zur Rohrachse (nach unten)
// Abstand (radial) eines Lochrands von der Rohrachse für Lochrichtung mit z-Anteil dz
// achsnächste Mantellinie der Bohrung mit der Außenfläche schneiden → Abstand zur Rohrkante
// (2D-Schnitt: x radial, z axial, Ursprung = Kugelmitte, al = Winkel zur Rohrachse nach unten)
function loch_rand_r(dz) = let(al = acos(-dz), rl = loch_d/2,
        ux = sin(al), uz = -cos(al), wx = -cos(al), wz = -sin(al),
        A = ux*ux/(R*R) + uz*uz/(Rz*Rz),
        B = 2*rl*(ux*wx/(R*R) + uz*wz/(Rz*Rz)),
        C = rl*rl*(wx*wx/(R*R) + wz*wz/(Rz*Rz)) - 1,
        sp = (-B + sqrt(B*B - 4*A*C))/(2*A))
    let(x = sp*ux + rl*wx, z = sp*uz + rl*wz,
        xj = rohr_ad/2, zj = -Rz*sqrt(1 - (xj/R)*(xj/R)))      // Rohr/Kugel-Kante
    (x <= xj) ? -1 : norm([x - xj, z - zj]);                  // Abstand Lochrand → Rohrkante

// ---------------------------------------------------------------------
module aussen() translate([0, 0, kugel_z]) scale([1, 1, Rz/R])   sphere(r = R);
module innen()  translate([0, 0, kugel_z]) scale([1, 1, Rzi/Ri]) sphere(r = Ri);

module loch(elev, theta) {
    translate([0, 0, kugel_z])
        rotate([0, theta, 0]) rotate([elev, 0, 0])
            translate([0, 0, min(Ri, Rzi) - 3]) cylinder(d = loch_d, h = abs(Rz - R) + wand + 6, $fn = 24);
}

// ---------- gleichmäßiges Muster: Ringe mit festem Bogenabstand um die Hochachse
// Meridian-Parameter t (Grad): t = 0 oben, Punkt (rho, z) = (R sin t, Rz cos t)
function ds_dt(t)  = sqrt(pow(R*cos(t), 2) + pow(Rz*sin(t), 2)) * PI/180;
function bogen(t, n = 90) = let(h = t/n) h * [for (i = [0:n-1]) ds_dt((i + 0.5)*h)] * [for (i = [0:n-1]) 1];
function t_zu_bogen(sz, lo = 0, hi = 180, it = 30) =
    it == 0 ? (lo + hi)/2 :
    let(m = (lo + hi)/2) (bogen(m) < sz) ? t_zu_bogen(sz, m, hi, it - 1) : t_zu_bogen(sz, lo, m, it - 1);

t_rohr   = 180 - asin(rohr_ad/2/R);             // Meridianwinkel der Rohrkante
s_rohr   = bogen(t_rohr);
n_ringe  = floor((s_rohr - loch_d/2 - loch_abstand) / loch_raster);

module loch_normal(t, phi) {
    rho = R*sin(t);  zz = Rz*cos(t);
    nv  = [rho/(R*R), 0, zz/(Rz*Rz)];           // Flächennormale (in Meridianebene)
    tilt = atan2(nv[0], nv[2]);
    translate([0, 0, kugel_z]) rotate([0, 0, phi])
        translate([rho, 0, zz]) rotate([0, tilt, 0])
            translate([0, 0, -(wand + 3)]) cylinder(d = loch_d, h = 2*wand + 6, $fn = 24);
}

module loecher_gleichmaessig() {
    loch_normal(0, 0);                            // Scheitelloch
    for (k = [1 : n_ringe]) {
        t   = t_zu_bogen(k*loch_raster);
        n   = max(1, round(2*PI*R*sin(t) / loch_raster));
        for (i = [0 : n-1]) loch_normal(t, (i + (k % 2)*0.5) * 360/n);
    }
}

module alle_loecher() {
    if (loch_muster == "original") loecher_original(); else loecher_gleichmaessig();
}

module loecher_original() {
    for (r = loch_ringe)
        for (k = [0 : r[3]-1]) {
            th = r[1] + k*r[2];
            dz = cos(r[0]) * cos(th);           // z-Komponente der Lochrichtung
            if (dz >= 0 || loch_rand_r(dz) > loch_abstand) loch(r[0], th);
        }
}

// Tri-Clamp-Ferrule (Vollkörper, Bohrung wird später abgezogen)
module triclamp() {
    rf = tc_flansch_d/2;
    rh = hals_r;
    z_taper = tc_schraeg_h;
    z_hals  = tc_gerade ? z_taper : tc_hoehe;
    difference() {
        rotate_extrude($fn = 128)
            polygon([ [0, 0], [rf, 0], [rf, tc_rand], [rh, z_taper],
                      [rh, z_hals], [rohr_ad/2, z_hals + konus_h],
                      [0, z_hals + konus_h] ]);
        // Dichtungsnut in der Stirnfläche
        rotate_extrude($fn = 128)
            translate([tc_nut_d/2, tc_nut_tiefe - tc_nut_r]) circle(r = tc_nut_r, $fn = 32);
    }
}

// Gewindezahn als Helix-Polyeder (Rechtsgewinde)
module gewindezaehne(h) {
    r_k = gew_minor_eff/2;
    r_g = gew_major_d/2;
    r_a = r_g + 0.3;
    prof = [ [r_a, -gew_fuss/2], [r_g, -gew_fuss/2], [r_k, -gew_kopf/2],
             [r_k,  gew_kopf/2], [r_g,  gew_fuss/2], [r_a,  gew_fuss/2] ];
    np   = len(prof);
    z0   = gew_phase - 2*gew_p;
    turns = ceil((h - z0)/gew_p) + 1;
    n    = turns * gew_seg;
    pts = [ for (i = [0:n]) let(a = 360*i/gew_seg, dz = z0 + gew_p*i/gew_seg)
              for (p = prof) [ p[0]*cos(a), p[0]*sin(a), dz + p[1] ] ];
    seite = [ for (i = [0:n-1]) for (j = [0:np-1])
                let(a = i*np + j, b = i*np + (j+1)%np, c = (i+1)*np + (j+1)%np, d = (i+1)*np + j)
                [d, c, b, a] ];
    deckel = [ [ for (j = [0:np-1]) j ], [ for (j = [np-1:-1:0]) n*np + j ] ];
    polyhedron(points = pts, faces = concat(seite, deckel), convexity = 10);
}

// ---------------------------------------------------------------------
module cipball() {
    difference() {
        union() {
            aussen();
            cylinder(d = rohr_ad, h = uebergang + 1);
            if (anschluss == "triclamp") triclamp();
        }
        innen();
        translate([0, 0, -1]) cylinder(d = bohr_d, h = kugel_z + 1);
        alle_loecher();
    }
    if (anschluss == "gewinde")
        intersection() {
            gewindezaehne(uebergang + gew_p);
            difference() {
                cylinder(d = gew_major_d + 0.4, h = uebergang + 1);
                innen();
            }
        }
}

cipball();
