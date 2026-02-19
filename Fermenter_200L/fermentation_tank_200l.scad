// ============================================================
//  200L Biergär-Tank – OpenSCAD Modell v4
//  Basierend auf Assembly Drawing: Ø760 × 1900 mm
//  Maßstab: 1:1 in mm
//
//  v4 neu:
//  - Tri-Clamp Kugelhähne (schematisch) an Stutzen a, d, e, g
//  - Manometer (11) mit Zifferblatt, Gehäuse, Siphon-Rohr
//  - Alle Armaturen korrekt an die Stutzen-Achsen angedockt
// ============================================================

// -----------------------------------------------------------
//  ANSICHTS-SCHALTER
// -----------------------------------------------------------
VIEW = "full";   // "full" oder "section"

// -----------------------------------------------------------
//  PARAMETER
// -----------------------------------------------------------
inner_r       = 380;
wall_inner    = 3.0;
wall_jacket   = 2.0;
insulation    = 80;
cyl_height    = 1200;
head_height   = 120;
cone_half_ang = 30;
cone_h        = inner_r / tan(cone_half_ang);
jacket_gap    = 6;
jacket_height = 700;
leg_od        = 89;
leg_r         = leg_od / 2;
leg_wall      = 5;
leg_count     = 4;
leg_foot_r    = inner_r * 0.60;
clamp_width   = 12;
clamp_thk     = 6;
r_jacket_in   = inner_r + wall_inner + jacket_gap;
r_jacket_out  = r_jacket_in + wall_jacket;

// Z-Koordinaten
z_tip         = 200;
z_base        = z_tip + cone_h;
z_top         = z_base + cyl_height;
z_ht          = z_top + head_height;
z_leg_attach  = z_tip + leg_foot_r / tan(cone_half_ang);

// -----------------------------------------------------------
//  BASISMODULE
// -----------------------------------------------------------

module hollow_cylinder(h, r_out, r_in, fn=120) {
    difference() {
        cylinder(h=h, r=r_out, $fn=fn);
        translate([0,0,-0.1]) cylinder(h=h+0.2, r=r_in, $fn=fn);
    }
}

module dish_head(r, h) {
    intersection() {
        scale([1,1,h/r]) sphere(r=r, $fn=120);
        cylinder(h=h+r, r=r+1, $fn=120);
    }
}

module pipe_nozzle(radius, length, wall=2) {
    difference() {
        cylinder(h=length, r=radius+wall, $fn=48);
        translate([0,0,-0.1]) cylinder(h=length+0.2, r=radius, $fn=48);
    }
}

module triclamp_flange(pipe_r, pipe_wall=2) {
    flange_r = pipe_r + pipe_wall + clamp_thk;
    color("Silver")
    difference() {
        union() {
            cylinder(h=clamp_width, r=flange_r, $fn=60);
            translate([0,0,clamp_width/2-1])
                rotate_extrude($fn=60)
                    translate([flange_r-clamp_thk/2,0])
                        circle(r=clamp_thk/2+1, $fn=20);
        }
        translate([0,0,-0.1]) cylinder(h=clamp_width+0.2, r=pipe_r, $fn=48);
    }
}

module nozzle_with_clamp(pipe_r, length, wall=2, has_clamp=true) {
    pipe_nozzle(pipe_r, length, wall);
    if (has_clamp)
        translate([0,0,length]) triclamp_flange(pipe_r, wall);
}

module threaded_nozzle(pipe_r, length, wall=2) {
    color("DimGray") {
        pipe_nozzle(pipe_r, length, wall);
        translate([0,0,length])
        difference() {
            cylinder(h=12, r=pipe_r+wall+5, $fn=6);
            translate([0,0,-0.1]) cylinder(h=12.2, r=pipe_r, $fn=24);
        }
    }
}

module cleaning_ball(r=25) {
    color("Silver", 0.9) {
        difference() {
            sphere(r=r, $fn=60);
            sphere(r=r-2, $fn=60);
        }
        for (i=[0:5]) for (j=[0:5])
            rotate([i*30,j*60,0])
                translate([0,0,r]) cylinder(h=3, r=1.5, $fn=12);
        translate([0,0,r-2]) cylinder(h=35, r=8, $fn=24);
    }
}

module leg(angle) {
    ax = leg_foot_r * cos(angle);
    ay = leg_foot_r * sin(angle);
    leg_h = z_leg_attach - leg_r * tan(90-cone_half_ang);
    color("Silver", 0.85)
    translate([ax,ay,0]) {
        hollow_cylinder(leg_h, leg_r, leg_r-leg_wall, fn=48);
        cylinder(h=12, r=leg_r+12, $fn=48);
        translate([0,0,leg_h])
        hull() {
            cylinder(h=2, r=leg_r, $fn=48);
            translate([0,0,z_leg_attach-leg_h]) sphere(r=3, $fn=16);
        }
    }
    color("Silver", 0.80)
    translate([ax,ay,z_leg_attach*0.4])
    rotate([0,0,angle+90])
    linear_extrude(height=4)
        polygon([[-leg_r,0],[leg_r,0],[leg_r*0.3,z_leg_attach*0.55],[-leg_r*0.3,z_leg_attach*0.55]]);
}

// -----------------------------------------------------------
//  ARMATUR-MODULE
// -----------------------------------------------------------

// ── Tri-Clamp Kugelhahn (schematisch) ──────────────────────
//
//  Aufbau (in lokalen Koordinaten, Strömungsrichtung = +Z):
//
//  [Ferrule/Klemmring] → [Gehäuse (Zylinder)] → [Griff oben]
//
//  pipe_r  = Innenradius des Rohres
//  Gesamtlänge ≈ 120mm
//
module ballvalve(pipe_r) {
    wall     = 2.5;
    body_r   = pipe_r + wall + 8;   // Gehäuseradius (dicker als Rohr)
    body_l   = 60;                  // Gehäuselänge
    flange_r = pipe_r + wall + clamp_thk;

    // --- Eingangs-Ferrule (Tri-Clamp, sitzt direkt am Stutzen-Flansch)
    color("Silver")
    difference() {
        union() {
            cylinder(h=clamp_width, r=flange_r, $fn=60);
            translate([0,0,clamp_width/2-1])
                rotate_extrude($fn=60)
                    translate([flange_r-clamp_thk/2,0])
                        circle(r=clamp_thk/2+1, $fn=20);
        }
        translate([0,0,-0.1]) cylinder(h=clamp_width+0.2, r=pipe_r, $fn=48);
    }

    // --- Verbindungsrohr zwischen Ferrule und Gehäuse
    color("DimGray")
    translate([0,0,clamp_width])
        pipe_nozzle(pipe_r, 12, wall);

    // --- Kugelhahngehäuse (runder Körper, erkennbar breiter)
    color("DarkSlateGray")
    translate([0,0,clamp_width+12]) {
        difference() {
            // Außengehäuse (leicht bauchig → Skalierung)
            scale([1,1,1])
                cylinder(h=body_l, r=body_r, $fn=48);
            // Durchbohrung
            translate([0,0,-0.1])
                cylinder(h=body_l+0.2, r=pipe_r, $fn=32);
            // Seitliche Abflachungen (typisch für Kugelhahn-Gehäuse)
            translate([body_r*0.7, -body_r-1, -1])
                cube([body_r*2, body_r*2+2, body_l+2]);
            translate([-body_r*2.7, -body_r-1, -1])
                cube([body_r*2, body_r*2+2, body_l+2]);
        }

        // Kugel andeuten (mittig im Gehäuse, Chrom)
        color("Silver")
        translate([0,0,body_l/2])
            sphere(r=pipe_r+3, $fn=40);

        // --- Griff (Hebel, seitlich abstehend, "offen" = 90° quer)
        // Griffachse sitzt oben auf dem Gehäuse
        color("OrangeRed")
        translate([0,0,body_l]) {
            // Griffsteg (zylindrische Achse)
            cylinder(h=10, r=6, $fn=20);
            // Hebelarm
            translate([-body_r*1.8, -5, 5])
                cube([body_r*3.6, 10, 8]);
            // Griffende (rund)
            translate([body_r*1.8, 0, 9])
                sphere(r=8, $fn=20);
            translate([-body_r*1.8, 0, 9])
                sphere(r=8, $fn=20);
        }
    }

    // --- Ausgangs-Ferrule
    color("Silver")
    translate([0,0,clamp_width+12+body_l])
    difference() {
        union() {
            cylinder(h=clamp_width, r=flange_r, $fn=60);
            translate([0,0,clamp_width/2-1])
                rotate_extrude($fn=60)
                    translate([flange_r-clamp_thk/2,0])
                        circle(r=clamp_thk/2+1, $fn=20);
        }
        translate([0,0,-0.1]) cylinder(h=clamp_width+0.2, r=pipe_r, $fn=48);
    }
}

// ── Manometer (schematisch) ────────────────────────────────
//
//  Aufbau (in +Z-Richtung ab Stutzenende):
//  Siphon-Rohr (U-Form) → Manometer-Gehäuse → Zifferblatt
//
module pressure_gauge(pipe_r) {
    gauge_r  = 40;     // Zifferblatt-Radius (Ø80 Manometer)
    gauge_h  = 22;     // Gehäusetiefe
    siphon_h = 50;     // Siphonrohr-Länge

    // --- Anschluss-Ferrule
    color("Silver")
    difference() {
        union() {
            cylinder(h=clamp_width, r=pipe_r+2+clamp_thk, $fn=60);
            translate([0,0,clamp_width/2-1])
                rotate_extrude($fn=60)
                    translate([pipe_r+2+clamp_thk-clamp_thk/2,0])
                        circle(r=clamp_thk/2+1, $fn=20);
        }
        translate([0,0,-0.1]) cylinder(h=clamp_width+0.2, r=pipe_r, $fn=48);
    }

    // --- Siphon-Rohr (kleines Steigrohr, typisch für Manometer)
    color("DimGray")
    translate([0,0,clamp_width]) {
        // Gerader Teil
        pipe_nozzle(6, siphon_h, 1.5);
        // U-Bogen andeuten
        translate([0,0,siphon_h])
        rotate_extrude(angle=180, $fn=40)
            translate([10,0])
                circle(r=4, $fn=20);
        // Rückführung
        translate([20,0,siphon_h])
            pipe_nozzle(6, 20, 1.5);
    }

    // --- Manometergehäuse
    color("LightGray")
    translate([20, 0, clamp_width + siphon_h + 20]) {
        // Gehäuse (Zylinder)
        difference() {
            cylinder(h=gauge_h, r=gauge_r, $fn=60);
            translate([0,0,-0.1]) cylinder(h=gauge_h+0.2, r=gauge_r-3, $fn=60);
        }
        // Rückwand
        cylinder(h=3, r=gauge_r, $fn=60);

        // --- Zifferblatt (weiße Scheibe mit Skala)
        color("WhiteSmoke")
        translate([0,0,gauge_h-2])
            cylinder(h=2.5, r=gauge_r-3.5, $fn=60);

        // Skalenteilstriche (12 Stück)
        color("DarkGray")
        for (a=[0:30:330])
            rotate([0,0,a])
            translate([gauge_r-10, 0, gauge_h])
                cylinder(h=1.5,
                    r = (a % 90 == 0) ? 2 : 1,
                    $fn=10);

        // Zeiger (zeigt auf ca. 30° – typisch Betriebsdruck ~1.5 Bar)
        color("Red")
        translate([0,0,gauge_h+1])
        rotate([0,0,120])     // 0 Bar = 225°, 3 Bar = -45° → 1.5 Bar ≈ 120°
        linear_extrude(height=1.5)
            polygon([[0,-1.5],[gauge_r-14,0],[0,1.5]]);

        // Zentralschraube (Zeigerlager)
        color("Silver")
        translate([0,0,gauge_h+1]) cylinder(h=3, r=3.5, $fn=20);

        // Schutzglas (leicht transparent)
        color("LightCyan", 0.25)
        translate([0,0,gauge_h-0.5])
            cylinder(h=3, r=gauge_r-1, $fn=60);
    }
}

// -----------------------------------------------------------
//  TANK HAUPTMODUL
// -----------------------------------------------------------

module tank_body() {

    // Standbeine – 4 Stück an den Ecken eines Quadrats (45°, 135°, 225°, 315°)
    for (i=[0:leg_count-1]) leg(45 + i*90);

    // Konus
    color("Silver", 0.88)
    translate([0,0,z_tip])
        difference() {
            cylinder(h=cone_h, r1=0, r2=inner_r+wall_inner, $fn=120);
            translate([0,0,-0.1]) cylinder(h=cone_h+0.2, r1=0, r2=inner_r, $fn=120);
        }

    // Zylinder
    color("Silver", 0.90)
    translate([0,0,z_base])
        hollow_cylinder(cyl_height, inner_r+wall_inner, inner_r);

    // Kühlmantel
    color("SteelBlue", 0.50)
    translate([0,0,z_top-jacket_height])
        hollow_cylinder(jacket_height, r_jacket_out, r_jacket_in);
    color("Silver", 0.85)
    for (dz=[0,jacket_height])
        translate([0,0,z_top-jacket_height+dz])
            hollow_cylinder(5, r_jacket_out+3, r_jacket_in-1);

    // Deckel
    color("Silver", 0.92)
    translate([0,0,z_top])
        difference() {
            dish_head(inner_r+wall_inner, head_height);
            translate([0,0,-0.1]) dish_head(inner_r, head_height-wall_inner+0.1);
        }
    color("Silver", 0.85)
    translate([0,0,z_top-5])
        hollow_cylinder(8, inner_r+wall_inner+3, inner_r+wall_inner-2);

    // Isolierung
    color("SandyBrown", 0.15)
    translate([0,0,z_base])
        hollow_cylinder(cyl_height, r_jacket_out+insulation, r_jacket_out);

    // Reinigungsball
    color("Silver", 0.85)
    translate([0,0,z_top+head_height*0.45-28])
        cleaning_ball(r=28);

    // ==========================================================
    //  STUTZEN + ARMATUREN
    //
    //  Prinzip: Stutzen wächst von Tankwand nach außen in +Z.
    //  Kugelhahn/Manometer dockt direkt am Stutzenende an
    //  (translate um Stutzenlänge, gleiche Rotation).
    // ==========================================================

    // ----------------------------------------------------------
    //  a: Drainage Ø36 – senkrecht nach unten, Konusspitze
    //     Kugelhahn hängt unter dem Stutzen (Richtung -Z)
    // ----------------------------------------------------------
    color("DimGray")
    translate([0,0,z_tip-90])
        nozzle_with_clamp(18, 90, 2, true);
    color("DimGray")
    translate([0,0,z_tip-5])
        cylinder(h=8, r=20, $fn=36);

    // Kugelhahn a – hängt unterhalb des Stutzens
    // Stutzen geht von z_tip-90 nach z_tip, Kugelhahn nach unten
    translate([0, 0, z_tip - 90])
    rotate([180, 0, 0])           // umdrehen: wächst nach unten
        ballvalve(18);

    // ----------------------------------------------------------
    //  d: Beer outlet Ø32 – Konus bei 315°, z_tip+280
    //     Kugelhahn schließt sich nach außen an
    // ----------------------------------------------------------
    {
        d_ang      = 315;
        d_z        = z_tip + 280;
        d_cone_r   = (d_z - z_tip) * tan(cone_half_ang);
        d_nozzle_l = 90;

        color("DimGray")
        translate([d_cone_r*cos(d_ang), d_cone_r*sin(d_ang), d_z])
        rotate([0,90,d_ang])
            nozzle_with_clamp(16, d_nozzle_l, 2, true);

        // Kugelhahn: startet am Ende des Stutzens
        translate([d_cone_r*cos(d_ang), d_cone_r*sin(d_ang), d_z])
        rotate([0,90,d_ang])
        translate([0,0,d_nozzle_l+clamp_width])
            ballvalve(16);
    }

    // ----------------------------------------------------------
    //  e: Sampling Ø25 – Zylinder 90°, z_base+120
    // ----------------------------------------------------------
    {
        e_ang      = 90;
        e_z        = z_base + 120;
        e_nozzle_l = 75;

        color("DimGray")
        translate([(inner_r+wall_inner)*cos(e_ang),
                   (inner_r+wall_inner)*sin(e_ang), e_z])
        rotate([0,90,e_ang])
            nozzle_with_clamp(12.5, e_nozzle_l, 2, true);

        translate([(inner_r+wall_inner)*cos(e_ang),
                   (inner_r+wall_inner)*sin(e_ang), e_z])
        rotate([0,90,e_ang])
        translate([0,0,e_nozzle_l+clamp_width])
            ballvalve(12.5);
    }

    // ----------------------------------------------------------
    //  g: CIP port Ø32 – Zylinder 180°, z_base+350
    // ----------------------------------------------------------
    {
        g_ang      = 180;
        g_z        = z_base + 350;
        g_nozzle_l = 85;

        color("DimGray")
        translate([(inner_r+wall_inner)*cos(g_ang),
                   (inner_r+wall_inner)*sin(g_ang), g_z])
        rotate([0,90,g_ang])
            nozzle_with_clamp(16, g_nozzle_l, 2, true);

        translate([(inner_r+wall_inner)*cos(g_ang),
                   (inner_r+wall_inner)*sin(g_ang), g_z])
        rotate([0,90,g_ang])
        translate([0,0,g_nozzle_l+clamp_width])
            ballvalve(16);
    }

    // ----------------------------------------------------------
    //  h: Dry hops Ø51 – Deckel schräg 135°
    // ----------------------------------------------------------
    color("DimGray") {
        h_ang = 135; h_rr = 150;
        h_z   = z_top + head_height * 0.50;
        translate([h_rr*cos(h_ang), h_rr*sin(h_ang), h_z])
        rotate([0,-55,h_ang])
            nozzle_with_clamp(25.5, 75, 2, true);
    }

    // ----------------------------------------------------------
    //  b/c: Kühlmantelanschlüsse G3/4
    // ----------------------------------------------------------
    color("DimGray") {
        b_ang = 135; b_z = z_top - 60;
        translate([r_jacket_out*cos(b_ang), r_jacket_out*sin(b_ang), b_z])
        rotate([0,90,b_ang]) threaded_nozzle(10, 60, 2);
    }
    color("DimGray") {
        c_ang = 45; c_z = z_top - jacket_height + 60;
        translate([r_jacket_out*cos(c_ang), r_jacket_out*sin(c_ang), c_z])
        rotate([0,90,c_ang]) threaded_nozzle(10, 60, 2);
    }

    // ----------------------------------------------------------
    //  f: Mannloch Ø400
    // ----------------------------------------------------------
    color("Silver", 0.85)
    translate([0,0,z_top+head_height-10])
    difference() {
        union() {
            cylinder(h=38, r=222, $fn=80);
            translate([0,0,38]) cylinder(h=14, r=217, $fn=80);
            translate([210,0,18]) cube([35,22,32], center=true);
            for (a=[0:60:300])
                rotate([0,0,a]) translate([217,0,22]) sphere(r=9, $fn=20);
        }
        translate([0,0,-0.1]) cylinder(h=60, r=200, $fn=80);
    }

    // ----------------------------------------------------------
    //  10: Wasserschloss
    // ----------------------------------------------------------
    color("DimGray") {
        ws_ang = 270; ws_rr = 120;
        ws_z   = z_top + head_height * 0.65;
        translate([ws_rr*cos(ws_ang), ws_rr*sin(ws_ang), ws_z])
        rotate([0,-50,ws_ang])
            nozzle_with_clamp(16, 65, 2, true);
    }

    // ----------------------------------------------------------
    //  11: Manometer – auf Deckel, 0°, r=120
    //      Stutzen + Siphon-Rohr + Manometergehäuse
    // ----------------------------------------------------------
    {
        pg_ang      = 0;
        pg_rr       = 120;
        pg_z        = z_top + head_height * 0.65;
        pg_nozzle_l = 65;

        // Stutzen
        color("DimGray")
        translate([pg_rr*cos(pg_ang), pg_rr*sin(pg_ang), pg_z])
        rotate([0,-50,pg_ang])
            nozzle_with_clamp(16, pg_nozzle_l, 2, true);

        // Manometer dockt am Ende des Stutzens an
        translate([pg_rr*cos(pg_ang), pg_rr*sin(pg_ang), pg_z])
        rotate([0,-50,pg_ang])
        translate([0,0,pg_nozzle_l+clamp_width])
            pressure_gauge(16);
    }

}  // end tank_body

// -----------------------------------------------------------
//  HAUPTAUSGABE
// -----------------------------------------------------------
if (VIEW == "section") {
    difference() {
        tank_body();
        translate([-2000,0,-50])
            cube([4000,4000,z_ht+200]);
    }
} else {
    tank_body();
}
