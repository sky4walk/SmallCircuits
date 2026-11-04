// ============================================================
//  Tri-Clamp-Rohrbogen 1.5"  –  parametrisch
//  Nachkonstruktion nach Foto vom 31.10.2026
//
//  Aus dem Foto abgelesen (Maßstab = Ferrule-Ø 50,5 mm):
//   - EIN Knick, ca. 90°, Bogen mit engem Radius (~1,5×D)
//   - langer senkrechter Schenkel, kurzer Schenkel
//   - KEIN T-Stück (Option unten trotzdem vorhanden)
//   - Rohr deutlich dünner als der Ferrule-Hals -> vermutlich
//     32-mm-Rohr mit 1.5"-Ferrule (Ø-Verhältnis im Bild ~0,63)
//  Alle Maße sind Schätzungen – bitte nachmessen und eintragen.
// ============================================================
 
$fn = 96;
 
/* [Rohr] */
rohr_da   = 32;     // Außendurchmesser Rohr [mm]  (38.1 wäre echtes 1.5"-Rohr)
rohr_wand = 1.5;    // Wandstärke [mm]
 
/* [Geometrie] */
knick     = true;   // false = gerades Rohr
knick_w   = 90;     // Knickwinkel [°] (0 < w < 180)
knick_r   = 48;     // Biegeradius bezogen auf Rohrmitte [mm]
l_gerade  = 225;    // langer Schenkel: Dichtfläche oben -> Bogenbeginn [mm]
                    // (ohne Knick: Dichtfläche zu Dichtfläche)
l_kurz    = 27;     // kurzer Schenkel: Bogenende -> Dichtfläche [mm]
 
/* [Ferrule 1.5" (DIN 32676 / ISO 2852, Flansch-Ø 50,5)] */
fl_da      = 50.5;  // Flansch-Außendurchmesser
fl_l       = 12.7;  // Ferrule-Länge (kurz 12.7 / lang 21.5)
fl_dicke   = 2.85;  // Flanschrand-Dicke
fl_winkel  = 20;    // Neigung der Flanschrückseite (Klemmkonus) [°]
buendig    = true;  // true = Ferrule-Hals so dick wie das Rohr (kein Absatz)
hals_da_x  = 38.1;  // nur bei buendig=false: Außen-Ø des Ferrule-Halses
hals_di_x  = 34.8;  // nur bei buendig=false: Innen-Ø des Ferrule-Halses
uebergang_x = 3;    // nur bei buendig=false: Konus Rohr -> Ferrule-Hals [mm]
hals_da    = buendig ? rohr_da               : hals_da_x;
hals_di    = buendig ? rohr_da - 2*rohr_wand : hals_di_x;
uebergang  = buendig ? 0                     : uebergang_x;
nut_d      = 43.6;  // Mitten-Ø der Dichtungsnut
nut_r      = 1.3;   // Radius der Dichtungsnut
 
/* [T-Stück (optional)] */
t_stueck   = false; // im Foto nicht vorhanden
t_pos      = 110;   // Abstand Dichtfläche oben -> Abzweigachse [mm]
t_mass     = 70;    // Hauptrohrachse -> Dichtfläche Abzweig [mm]
t_dreh     = 90;    // Drehung des Abzweigs um die Hauptachse [°]
 
// ---------------- abgeleitete Werte ----------------
ri    = rohr_da/2;
rii   = ri - rohr_wand;
hr    = hals_da/2;
fr    = fl_da/2;
fl_lg = fl_l + uebergang;                     // Platzbedarf Ferrule + Übergang
th    = (fr - hr) * tan(fl_winkel);           // Höhe Klemmkonus
l_oben = knick ? l_gerade : l_gerade/2;
 
assert(rohr_wand < ri, "Wand zu dick");
assert(l_oben >= fl_lg, "langer Schenkel kürzer als Ferrule");
assert(!knick || l_kurz >= fl_lg, "kurzer Schenkel kürzer als Ferrule");
assert(!knick || (knick_w > 0 && knick_w < 180), "Winkel 0..180");
assert(!knick || knick_r > ri, "Biegeradius kleiner als Rohrradius");
 
// ---------------- Ferrule ----------------
// lokal: z=0 Rohrseite, z=fl_lg Dichtfläche
module ferrule_aussen() {
    rotate_extrude()
        polygon(concat([[0,0],[ri,0]],
                 uebergang > 0 ? [[hr,uebergang]] : [],
                 [[hr, fl_lg-fl_dicke-th],[fr, fl_lg-fl_dicke],
                  [fr, fl_lg],[0, fl_lg]]));
}
module ferrule_innen() {
    if (uebergang > 0)
        translate([0,0,-0.01]) cylinder(h=uebergang+0.02, r1=rii, r2=hals_di/2);
    translate([0,0,uebergang-0.01]) cylinder(h=fl_l+1, r=hals_di/2);
    translate([0,0,fl_lg])                     // Dichtungsnut
        rotate_extrude() translate([nut_d/2,0]) circle(r=nut_r);
}
 
// gerader Schenkel entlang +z, Dichtfläche bei z=l
module schenkel(l, innen) {
    if (innen) {
        translate([0,0,-0.01]) cylinder(h=l-fl_lg+0.02, r=rii);
        translate([0,0,l-fl_lg]) ferrule_innen();
    } else {
        cylinder(h=l-fl_lg, r=ri);
        translate([0,0,l-fl_lg]) ferrule_aussen();
    }
}
 
// Bogen: startet im Ursprung, Richtung -z, biegt Richtung -x
module bogen(innen) {
    translate([-knick_r,0,0]) rotate([-90,0,0])
        rotate_extrude(angle=knick_w)
            translate([knick_r,0]) circle(r = innen ? rii : ri);
}
bogen_ende = [-knick_r + knick_r*cos(knick_w), 0, -knick_r*sin(knick_w)];
 
module teil(innen) {
    schenkel(l_oben, innen);
    if (knick) {
        bogen(innen);
        translate(bogen_ende) rotate([0,180+knick_w,0]) schenkel(l_kurz, innen);
    } else {
        rotate([180,0,0]) schenkel(l_oben, innen);
    }
    if (t_stueck)
        translate([0,0,l_oben - t_pos]) rotate([0,0,t_dreh]) rotate([0,90,0])
            schenkel(t_mass, innen);
}
 
difference() { teil(false); teil(true); }
 
// ---------------- Kontrollmaße (Konsole) ----------------
if (knick) {
    v = knick_r * tan(knick_w/2);   // Bogenbeginn -> Schnittpunkt der Achsen
    echo(str("Bogenlänge (Rohrmitte): ", 2*PI*knick_r*knick_w/360, " mm"));
    echo(str("Dichtfläche oben -> Achsschnittpunkt: ", l_gerade + v, " mm"));
    echo(str("Dichtfläche unten -> Achsschnittpunkt: ", l_kurz + v, " mm"));
    echo(str("Gestreckte Rohrlänge (Mitte, Fläche-Fläche): ",
             l_gerade + l_kurz + 2*PI*knick_r*knick_w/360, " mm"));
}