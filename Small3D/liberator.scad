// =============================================================================
//  Sammeldatei – alle Nachkonstruktionen (1 … 15) in einer OpenSCAD-Datei
//  Andre – https://itzwieseltal.wordpress.com · https://zwieselbrau.wordpress.com
//
//  Einheit: alle Teile sind in Zoll konstruiert. EXPORT_MM schaltet ALLE
//  Teile gemeinsam auf mm (Faktor 25.4).
//
//  Benötigt OpenSCAD 2021.01 oder neuer (Teil 5 nutzt p.x / p.y).
// =============================================================================

/* [Auswahl] */
auswahl   = 15;      // 0 = alle nebeneinander, sonst Teilnummer 1..15
EXPORT_MM = false;   // true: Ausgabe in mm, false: in Zoll

u = EXPORT_MM ? 25.4 : 1;   // Faktor für die Anordnung

// Lage der Teile in der Übersicht (Zoll): [Nr, x, y]
layout = [
    [ 1,  0, 0], [ 3,  2, 1], [ 4,  4, 0], [ 6,  5, 0], [ 9,  6, 0],
    [11, 7.5, 0], [12, 8.5, 0],
    [13,  0, 4], [14,  2, 4], [15,  4, 4], [10,  8, 4], [ 7, 11, 4],
    [ 8,  0, 7], [ 5, 9, 8],
    [ 2, 10, 0]
];

module zeige(n) {
    if      (n ==  1) barrel();
    else if (n ==  2) fireingring();
    else if (n ==  3) bottomcover();
    else if (n ==  4) t4();
    else if (n ==  5) frame();
    else if (n ==  6) t6();
    else if (n ==  7) grip();
    else if (n ==  8) hammerbody();
    else if (n ==  9) t9();
    else if (n == 10) hammer();
    else if (n == 11) springconnection();
    else if (n == 12) t12();
    else if (n == 13) spring();
    else if (n == 14) triggerspring();
    else if (n == 15) trigger();
    else echo(str("Teil ", n, " gibt es nicht"));
}

if (auswahl == 0)
    for (p = layout) translate(u * [p[1], p[2], 0]) zeige(p[0]);
else
    zeige(auswahl);


// =============================================================================
//  1 – Hülse mit seitlicher Lasche 
// =============================================================================
module barrel() {
    $fn = 120;

    H          = 2.5;
    R_body     = 0.6;
    R_bot_fil  = 0.125;
    z_cone     = 2.2;
    R_top      = 0.7;
    z_top_cyl  = 2.4;
    R_top_fil  = 0.1;
    R_neck_fil = 0.06;
    R_bore_lo  = 0.185;
    R_bore_hi  = 0.195;
    z_step     = 1.886;
    R_step_fil = 0.02;
    R_bore_fil = 0.15;

    lug_w      = 0.2;
    lug_z0     = 1.6;
    lug_z1     = 2.05;
    lug_end    = 1.0;
    lug_head_y = 0.806;
    web_z0     = 1.7;
    web_z1     = 1.95;
    web_fil_v  = 0.125;
    web_fil_s  = 0.1;
    web_fil_h  = 0.035;

    function arc(c, r, a0, a1, n=24) = [for (i=[0:n]) let(a=a0+(a1-a0)*i/n) [c[0]+r*cos(a), c[1]+r*sin(a)]];

    cone_ang = atan(0.5);
    neck_c   = [R_body + R_neck_fil, z_cone - R_neck_fil*tan(cone_ang/2) + 0];
    neck_t   = R_neck_fil*tan(cone_ang/2);

    module profil() {
        pts = concat(
            arc([R_bore_lo+R_bore_fil, R_bore_fil], R_bore_fil, 180, 270),
            arc([R_body-R_bot_fil, R_bot_fil], R_bot_fil, -90, 0),
            arc([R_body+R_neck_fil, z_cone-neck_t], R_neck_fil, 180, 180-cone_ang, 12),
            [[R_top, z_top_cyl]],
            arc([R_top-R_top_fil, H-R_top_fil], R_top_fil, 0, 90),
            [[R_bore_hi, H]],
            let(a=41.5, dz=R_step_fil*sin(a))
            concat(
                arc([R_bore_hi-R_step_fil, z_step+dz], R_step_fil, 0, -a, 8),
                arc([R_bore_lo+R_step_fil, z_step-dz], R_step_fil, 180-a, 180, 8)
            )
        );
        polygon(pts);
    }

    module grundkoerper() { rotate_extrude() profil(); }

    module lasche() {
        hw = lug_w/2;
        translate([0,0,lug_z0]) linear_extrude(lug_z1-lug_z0)
            hull() {
                translate([-hw,-lug_head_y-0.001]) square([lug_w, 0.001]);
                translate([0,-(lug_end-hw)]) circle(r=hw);
            }
        translate([-hw,-lug_head_y,web_z0]) cube([lug_w, lug_head_y-0.4, web_z1-web_z0]);

        yc = -(R_body + web_fil_v);
        for (s=[[web_z0-web_fil_v, web_z0, 0], [web_z1, web_z1+web_fil_v, 1]])
            difference() {
                translate([-hw, yc, s[0]]) cube([lug_w, web_fil_v+0.2, web_fil_v]);
                translate([0, yc, s[2]==0 ? web_z0-web_fil_v : web_z1+web_fil_v])
                    rotate([0,90,0]) cylinder(r=web_fil_v, h=lug_w+0.02, center=true);
            }

        ys = -sqrt(pow(R_body+web_fil_s,2) - pow(hw+web_fil_s,2));
        for (m=[0,1]) mirror([m,0,0])
            difference() {
                translate([hw, ys, web_z0]) cube([web_fil_s, -ys-0.45, web_z1-web_z0]);
                translate([hw+web_fil_s, ys, web_z0-0.01]) cylinder(r=web_fil_s, h=web_z1-web_z0+0.02);
            }

        for (s=[[web_z0-web_fil_h, web_z0-web_fil_h], [web_z1, web_z1+web_fil_h]])
            difference() {
                translate([-hw, -lug_head_y, s[0]]) cube([lug_w, web_fil_h, web_fil_h]);
                translate([0, -lug_head_y+web_fil_h, s[1]])
                    rotate([0,90,0]) cylinder(r=web_fil_h, h=lug_w+0.02, center=true, $fn=40);
            }
    }

    module teil() {
        difference() {
            union() { grundkoerper(); lasche(); }
            translate([0,0,-0.01]) cylinder(r=R_bore_lo-0.0001, h=H+0.02);
        }
    }

    scale(EXPORT_MM ? 25.4 : 1) teil();
}


// =============================================================================
//  2 – Ring mit innerer Verrundung (Original-STL in Zoll: Ø0.44 / Ø0.32 x 0.05)
// =============================================================================
module fireingring() {
    d_aussen = 0.44;
    d_innen  = 0.32;
    hoehe    = 0.05;
    r_rund   = 0.04;
    $fn = 360;

    r_a = d_aussen/2;
    r_i = d_innen/2;

    module profil() {
        difference() {
            translate([r_i, 0]) square([r_a - r_i, hoehe]);
            translate([r_i - 0.01, hoehe - r_rund]) square([r_rund + 0.01, r_rund + 0.01]);
        }
        intersection() {
            translate([r_i + r_rund, hoehe - r_rund]) circle(r = r_rund, $fn = 180);
            translate([r_i, hoehe - r_rund]) square([r_rund, r_rund]);
        }
    }

    scale(EXPORT_MM ? 25.4 : 1) rotate_extrude() profil();
}


// =============================================================================
//  3 – Quader 0.99 x 1.19 x 0.1 (hier wie die übrigen Teile als Zoll gewertet)
// =============================================================================
module bottomcover() {
    skala  = EXPORT_MM ? 25.4 : 1;

    breite = 0.99 * skala;
    tiefe  = 1.19 * skala;
    hoehe  = 0.10 * skala;

    translate([0, -tiefe, 0])
        cube([breite, tiefe, hoehe]);
}


// =============================================================================
//  4 – Zylinderstift Ø0.19 x 1.60 
// =============================================================================
module t4() {
    einheit     = EXPORT_MM ? 25.4 : 1;
    durchmesser = 0.19;
    laenge      = 1.60;
    fase        = 0;
    $fn = 76;

    module stift() {
        r = durchmesser / 2;
        if (fase > 0)
            rotate_extrude()
                polygon([
                    [0, 0], [r - fase, 0], [r, fase],
                    [r, laenge - fase], [r - fase, laenge], [0, laenge]
                ]);
        else
            cylinder(d = durchmesser, h = laenge);
    }

    scale(einheit) stift();
}


// =============================================================================
//  5 – gehaeuse 
// =============================================================================
module frame() {
    export_in_mm = EXPORT_MM;
    $fn          = 96;

    L            = 5.155;
    W            = 1.6;
    top_y        = 2.316;
    skin         = 0.2;
    r_top_front  = 0.37;
    slant_x      = -1.75;
    slant_rear_y = 0.6;
    r_slant      = 1.75;
    r_corner     = 0.1;
    r_rear       = 0.85;
    edge_r       = 0.1;
    edge_steps   = 5;

    grip_x0      = -1.4;
    grip_y0      = -1.2;
    grip_wall    = 0.2;
    r_grip_fillet= 0.2;

    post_x       = -4.055;
    floor_y      = 0.25;
    win_z0       = 0.225;
    r_win_fin    = 0.5;
    r_post_top   = 0.12;
    fin_z0       = 0.495;
    fin_x1       = -1.0;
    arc_c        = [-2.0, 1.25];
    arc_r        = 1.0;
    band_drop    = 0.08;

    hole_d       = 0.2;
    holes        = [[-1.6, 0.66], [-1.4, 1.26], [-1.4, 2.026]];

    guard_x0     = -3.655;
    guard_bot    = -1.2;
    guard_wall   = 0.3;
    guard_bar    = 0.15;
    guard_z0     = 0.485;
    post_z0      = 0.36;
    r_guard      = 0.4;
    r_guard_back = 0.2;
    r_post_blend = 0.37;

    tab_z0       = 0.61;
    tab_pts      = [[-4.955, 0], [-4.955, -0.3], [-3.955, -0.9], [-3.655, -0.9], [-3.655, 0]];
    tab_hole     = [-4.055, -0.4];

    c1_z0        = 0.725;
    c1_x         = [-4.58, -1.69];
    c1_y         = 0.1;
    trig_x       = [-2.79, -2.19];
    c2_z0        = 0.625;
    c2_y         = [0.25, 0.45];

    ch_y         = 1.628;
    ch_r         = 0.6;
    bulge_x      = -0.895;
    bulge_r      = 0.702;
    bulge_x0     = -1.0;
    bulge_x1     = -0.69;

    pk_x         = [-0.56, -0.08];
    pk_y0        = 0.611;
    pk_z         = [0.49, 1.11];
    pk_r         = 0.14;
    nub_r        = 0.11;
    nub_y        = 0.912;

    zm = W/2;
    function ys(x) = slant_rear_y + (top_y - slant_rear_y) * (x + L) / (slant_x + L);

    function _u(v) = v / norm(v);
    function _arc(p0, p1, p2, r, n=16) =
        r <= 0 ? [[p1.x, p1.y]] :
        let(u = _u(p0 - p1), v = _u(p2 - p1),
            a = acos(max(-1, min(1, u * v))),
            t = r / tan(a/2),
            c = p1 + _u(u + v) * (r / sin(a/2)),
            A = p1 + u*t, B = p1 + v*t,
            a1 = atan2(A.y - c.y, A.x - c.x),
            a2 = atan2(B.y - c.y, B.x - c.x),
            d  = (a2 - a1 + 540) % 360 - 180)
        [for (i=[0:n]) c + r*[cos(a1 + d*i/n), sin(a1 + d*i/n)]];
    function rpoly(P) = let(n=len(P))
        [for (i=[0:n-1]) each _arc([P[(i+n-1)%n].x, P[(i+n-1)%n].y],
                                   [P[i].x, P[i].y],
                                   [P[(i+1)%n].x, P[(i+1)%n].y], P[i][2])];

    module outline2d() {
        polygon(rpoly([
            [0, grip_y0, r_corner],
            [0, top_y, r_top_front],
            [slant_x, top_y, r_slant],
            [-L, slant_rear_y, r_corner],
            [-L, 0, r_corner],
            [grip_x0, 0, r_grip_fillet],
            [grip_x0, grip_y0, r_corner]
        ]));
    }

    module window2d() {
        polygon(rpoly([
            [post_x, floor_y, 0],
            [slant_x, floor_y, r_win_fin],
            [slant_x, 4, 0],
            [-L-1, 4, 0],
            [-L-1, ys(-L-1), 0],
            [post_x, ys(post_x), r_post_top]
        ]));
    }

    module window_mid2d() {
        window2d();
        translate([arc_c.x, arc_c.y]) square([fin_x1 - arc_c.x, 4]);
        intersection() {
            translate(arc_c) circle(r = arc_r, $fn = 200);
            translate([arc_c.x, floor_y]) square([fin_x1 - arc_c.x, arc_c.y - floor_y]);
        }
    }

    module band2d() {
        x0 = post_x - 0.05;
        polygon([[x0, ys(x0) - band_drop], [slant_x, ys(slant_x) - band_drop],
                 [slant_x, 4], [x0, 4]]);
    }

    module guard2d() {
        hx0 = guard_x0 + guard_wall;
        hx1 = grip_x0;
        hy0 = guard_bot + guard_bar;
        difference() {
            translate([guard_x0, guard_bot]) square([grip_x0 + grip_wall - guard_x0, -guard_bot]);
            polygon(rpoly([
                [hx0, 0, r_guard], [hx0, hy0, r_guard],
                [hx1, hy0, r_guard], [hx1, 0, r_guard_back]
            ]));
            translate([hx0 + r_guard, 0]) square([hx1 - hx0 - r_guard - r_guard_back, 1]);
        }
    }

    module guard_post2d() {
        hx0 = guard_x0 + guard_wall;
        translate([guard_x0, guard_bot]) square([guard_wall, -guard_bot]);
        difference() {
            translate([hx0, -r_guard]) square(r_guard);
            translate([hx0 + r_guard, -r_guard]) circle(r = r_guard);
        }
    }

    module zsym(z0) { translate([0, 0, z0]) linear_extrude(W - 2*z0) children(); }
    module zpair(z0, z1) {
        translate([0, 0, z0]) linear_extrude(z1 - z0) children();
        translate([0, 0, W - z1]) linear_extrude(z1 - z0) children();
    }

    module skin_body() {
        if (edge_r <= 0) linear_extrude(W) outline2d();
        else {
            translate([0, 0, edge_r]) linear_extrude(W - 2*edge_r) outline2d();
            for (i = [0:edge_steps-1]) {
                z1 = edge_r * i / edge_steps;
                z2 = edge_r * (i+1) / edge_steps;
                zc = (z1 + z2) / 2;
                d  = edge_r - sqrt(edge_r*edge_r - (edge_r - zc)*(edge_r - zc));
                for (zz = [z1, W - z2])
                    translate([0, 0, zz]) linear_extrude(z2 - z1) offset(delta = -d) outline2d();
            }
        }
    }

    function bulge_profile() = concat(
        [[0, bulge_x0 - 0.001]],
        [for (i=[0:12]) let(t = i/12, x = bulge_x0 + (bulge_x - bulge_x0)*t,
                            e = (bulge_x - x)/(bulge_x - bulge_x0))
            [ch_r + (bulge_r - ch_r) * sqrt(max(0, 1 - e*e)), x]],
        [[ch_r, bulge_x1], [ch_r, 0.05], [0, 0.05]]);

    module channel() {
        translate([0, ch_y, zm]) rotate([0, 90, 0]) mirror([0,0,1])
            rotate_extrude($fn = 128) polygon([for (p = bulge_profile()) [p.x, -p.y]]);
        translate([0, ch_y, 0]) rotate([-90, 0, 0]) mirror([0,1,0])
            linear_extrude(3) polygon(concat(
                [for (p = bulge_profile()) [p.y, zm + p.x]],
                [for (i = [len(bulge_profile())-1:-1:0]) let(p = bulge_profile()[i]) [p.y, zm - p.x]]));
    }

    module pocket() {
        zc = (pk_z[0] + pk_z[1]) / 2;
        translate([pk_x[0], 0, 0]) rotate([90, 0, 90])
            linear_extrude(pk_x[1] - pk_x[0])
                hull() {
                    translate([pk_y0 + pk_r, pk_z[0] + pk_r]) circle(r = pk_r);
                    translate([pk_y0 + pk_r, pk_z[1] - pk_r]) circle(r = pk_r);
                    translate([1.0, zc - 0.24]) square([0.1, 0.48]);
                }
    }

    module nubs() {
        for (x = pk_x) translate([x, nub_y, zm]) cylinder(r = nub_r, h = pk_z[1] - zm);
    }

    module post_blend() {
        for (m = [0, 1]) translate([0, 0, m ? W : 0]) mirror([0, 0, m])
            translate([guard_x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(guard_wall)
                difference() {
                    translate([-r_post_blend, 0]) square([r_post_blend, post_z0]);
                    translate([-r_post_blend - 0.01, 0]) circle(r = r_post_blend - 0.01);
                }
    }

    module rear_round() {
        hull() {
            translate([-L + r_rear, -5, zm]) rotate([-90, 0, 0]) cylinder(r = r_rear, h = 10, $fn = 160);
            translate([-L + r_rear, -5, zm - r_rear]) cube([L, 10, 2*r_rear]);
        }
    }

    module part() {
        intersection() {
            difference() {
                union() {
                    skin_body();
                    zsym(guard_z0) guard2d();
                    zsym(post_z0)  guard_post2d();
                    post_blend();
                    zsym(tab_z0) difference() {
                        polygon(tab_pts);
                        translate(tab_hole) circle(d = hole_d);
                    }
                }
                translate([grip_x0 + grip_wall, grip_y0 - 1, skin])
                    cube([-grip_x0 - 2*grip_wall, 1 - grip_y0, W - 2*skin]);
                zsym(win_z0) window2d();
                zpair(skin, win_z0) band2d();
                zsym(fin_z0) window_mid2d();
                zsym(c1_z0) {
                    translate([c1_x[0], c1_y]) square([c1_x[1] - c1_x[0], 4]);
                    translate([trig_x[0], -0.01]) square([trig_x[1] - trig_x[0], c1_y + 0.02]);
                }
                zsym(c2_z0) translate([c1_x[0], c2_y[0]])
                    square([post_x - c1_x[0], c2_y[1] - c2_y[0]]);
                channel();
                difference() { pocket(); nubs(); }
                for (h = holes) translate([h.x, h.y, -1]) cylinder(d = hole_d, h = W + 2, $fn = 48);
            }
            rear_round();
        }
    }

    if (export_in_mm) scale(25.4) part(); else part();
}


// =============================================================================
//  6 – Zylinderstift Ø0.190 x 0.880
// =============================================================================
module t6() {
    durchmesser_in = 0.190;
    laenge_in      = 0.880;
    in_mm = EXPORT_MM;
    $fn   = 96;

    faktor = in_mm ? 25.4 : 1;

    scale(faktor)
        cylinder(d = durchmesser_in, h = laenge_in);
}


// =============================================================================
//  7 – Griff 
// =============================================================================
module grip() {
    export_in_mm = EXPORT_MM;
    $fn = 64;

    width = 0.875;

    block_back_x   = -0.125;
    block_front_x  = 1.30;
    block_bottom_z = -1.25;
    block_front_round = 0.10;
    block_corner_r = 0.21;

    slot_width   = 0.38;
    slot_back_x  = 0.0;
    slot_z_back  = -0.30;
    slot_ramp_x  = 1.00;
    slot_z_front = -0.90;

    pin_x = 0.91;
    pin_z = -0.39;
    pin_d = 0.20;

    grip_z_ref        = -1.5;
    grip_back_x_ref   = -0.776;
    grip_back_slope   = 0.6506;
    grip_front_x_ref  = 0.997;
    grip_front_slope  = 0.5318;
    grip_corner_r     = 0.33;
    neck_fillet_r     = 0.22;

    wall_y            = 0.20;
    cav_back_x_ref    = -0.580;
    cav_back_slope    = 0.6386;
    cav_front_x_ref   = 0.795;
    cav_front_slope   = 0.538;
    cav_top_z         = -1.25;

    bottom_z0    = -3.9535;
    bottom_slope = -0.2115;
    bottom_round = 0.06;

    eps = 0.001;
    function xb(z)  = grip_back_x_ref  + grip_back_slope  * (z - grip_z_ref);
    function xf(z)  = grip_front_x_ref + grip_front_slope * (z - grip_z_ref);
    function cxb(z) = cav_back_x_ref   + cav_back_slope   * (z - grip_z_ref);
    function cxf(z) = cav_front_x_ref  + cav_front_slope  * (z - grip_z_ref);

    z_low = bottom_z0 + bottom_slope * xb(-4) - 0.5;

    module rrect(x0, x1, y0, y1, r) {
        rr = min(r, (y1 - y0) / 2 - eps, (x1 - x0) / 2 - eps);
        hull() for (x = [x0 + rr, x1 - rr], y = [y0 + rr, y1 - rr])
            translate([x, y]) circle(r = rr);
    }

    module slice(z, x0, x1, y0, y1, r) {
        translate([0, 0, z - eps]) linear_extrude(eps) rrect(x0, x1, y0, y1, r);
    }

    phi   = atan(grip_back_slope);
    z_int = grip_z_ref + (block_back_x - grip_back_x_ref) / grip_back_slope;
    t_len = neck_fillet_r * tan(phi / 2);
    fc    = [block_back_x - neck_fillet_r, z_int + t_len];
    n_arc = 8;
    neck_pts = concat(
        [[xb(block_bottom_z), block_bottom_z, grip_corner_r]],
        [for (i = [n_arc:-1:0]) let(a = phi * i / n_arc)
            [fc[0] + neck_fillet_r * cos(a), fc[1] - neck_fillet_r * sin(a),
             block_corner_r + (grip_corner_r - block_corner_r) * i / n_arc]],
        [[block_back_x, 0, block_corner_r]]
    );
    neck_front = xf(block_bottom_z);

    module above_bottom(d = 0) {
        a = atan(bottom_slope);
        translate([0, 0, bottom_z0 + d * sqrt(1 + bottom_slope * bottom_slope)]) rotate([0, -a, 0])
            translate([-10, -5, 0]) cube([20, 10, 10]);
    }

    module grip_lower(r = 0) {
        db = r / cos(atan(grip_back_slope));
        df = r / cos(atan(grip_front_slope));
        hull() for (z = [z_low, block_bottom_z + r])
            slice(z, xb(z) + db, xf(z) - df, r, width - r, grip_corner_r - r);
    }

    module grip_outer() {
        if (bottom_round > 0)
            minkowski() {
                intersection() { grip_lower(bottom_round); above_bottom(bottom_round); }
                sphere(r = bottom_round, $fn = 24);
            }
        else
            grip_lower(0);
        for (i = [0 : len(neck_pts) - 2]) hull() {
            p = neck_pts[i]; q = neck_pts[i + 1];
            slice(p[1], p[0], neck_front, 0, width, p[2]);
            slice(q[1], q[0], neck_front, 0, width, q[2]);
        }
    }

    module block() {
        bx0 = block_back_x + block_corner_r + 0.05;
        r = block_front_round;
        hull() {
            translate([bx0, 0, block_bottom_z]) cube([block_front_x - bx0, width, -block_bottom_z - r]);
            translate([bx0, 0, -r]) cube([block_front_x - r - bx0, width, r]);
            translate([block_front_x - r, 0, -r]) rotate([-90, 0, 0]) cylinder(r = r, h = width);
        }
    }

    module slot() {
        y0 = (width - slot_width) / 2;
        translate([0, y0, 0]) rotate([90, 0, 0]) mirror([0, 0, 1])
            linear_extrude(slot_width)
                polygon([
                    [slot_back_x, 1],
                    [slot_back_x, slot_z_back],
                    [slot_ramp_x, slot_z_front],
                    [block_front_x + 1, slot_z_front],
                    [block_front_x + 1, 1]
                ]);
    }

    module pin_hole() {
        translate([pin_x, -1, pin_z]) rotate([-90, 0, 0]) cylinder(d = pin_d, h = width + 2);
    }

    module cavity() {
        y0 = wall_y; y1 = width - wall_y;
        r = (y1 - y0) / 2;
        hull() {
            slice(z_low - 1, cxb(z_low - 1), cxf(z_low - 1), y0, y1, r);
            slice(cav_top_z, cxb(cav_top_z), cxf(cav_top_z), y0, y1, r);
        }
    }

    module bottom_cut() {
        a = atan(bottom_slope);
        translate([0, 0, bottom_z0]) rotate([0, -a, 0])
            translate([-10, -5, -10]) cube([20, 10, 10]);
    }

    module nerf_grip() {
        difference() {
            union() { grip_outer(); block(); }
            slot();
            pin_hole();
            cavity();
            bottom_cut();
        }
    }

    scale(export_in_mm ? 25.4 : 1) nerf_grip();
}


// =============================================================================
//  8 – Gabelteil mit Scharnierauge und Zapfen
// =============================================================================
module hammerbody() {
    $fn = 96;

    T        = 0.61;
    LASCHE   = 0.10;
    W_TOP    = 2.10;
    Y_STUFE  = 1.00;
    STEG_B   = 0.125;
    R_GROSS  = 1.00;
    R_LASCHE = 1.00;
    R_KEHLE_L= 0.125;
    R_KEHLE_S= 0.153;

    AX       = 1.381;
    AZ       = -T/2;
    R_AUGE   = T/2;
    Y_SCHULT = 1.35;
    R_AUSSEN = 0.75;
    R_KEHLE_A= 0.11;
    R_RUND_A = 0.30;
    D_STIFT  = 0.14;
    D_SENK   = 0.44;
    T_SENK   = 0.19;

    ZP       = [0.617, 0.700];
    D_BUND   = 0.43;  H_BUND  = 0.02;
    D_ZAPFEN = 0.31;  H_ZAPFEN= 0.21;
    D_FLACH  = 0.10;

    BOHR_200 = [[0.40, 1.50], [1.00, 1.70], [1.7662, 1.70]];
    BOHR_125 = [[0.278, 0.847]];

    module kehle(r) { offset(r = -r) offset(delta = r) children(); }

    module oberteil2d() {
        intersection() {
            translate([0, Y_STUFE]) square([AX, W_TOP - Y_STUFE]);
            union() {
                translate([0, Y_STUFE]) square([AX, W_TOP - Y_STUFE - R_GROSS + 0.0001]);
                translate([R_GROSS, Y_STUFE]) square([AX, W_TOP]);
                translate([R_GROSS, W_TOP - R_GROSS]) circle(r = R_GROSS, $fn = 256);
            }
        }
    }

    module mitte2d() {
        intersection() {
            square([AX, W_TOP]);
            kehle(R_KEHLE_S) union() {
                oberteil2d();
                square([STEG_B, W_TOP - R_GROSS]);
            }
        }
    }

    module lasche2d() {
        intersection() {
            square([AX, W_TOP]);
            kehle(R_KEHLE_L) union() {
                mitte2d();
                intersection() {
                    translate([STEG_B, Y_STUFE]) circle(r = R_LASCHE, $fn = 256);
                    translate([0, 0]) square([STEG_B + R_LASCHE, Y_STUFE + 0.0001]);
                }
                square([STEG_B + 0.0001, Y_STUFE]);
            }
        }
    }

    module auge_profil() {
        intersection() {
            translate([0, Y_STUFE]) square([R_AUSSEN, W_TOP - Y_STUFE]);
            offset(r = R_RUND_A) offset(delta = -R_RUND_A)
            kehle(R_KEHLE_A) union() {
                translate([-1, 0]) square([1 + R_AUGE, 3]);
                translate([-1, Y_SCHULT]) square([1 + R_AUSSEN, 3]);
            }
        }
    }

    module auge3d() {
        intersection() {
            translate([AX, 0, AZ]) rotate([-90, 0, 0])
                rotate_extrude($fn = 192) auge_profil();
            translate([AX - 0.01, 0, -T]) cube([1, W_TOP, T]);
        }
    }

    module zapfen() {
        translate([0, 0, -0.005]) cylinder(d = D_BUND, h = H_BUND + 0.005);
        intersection() {
            cylinder(d = D_ZAPFEN, h = H_BUND + H_ZAPFEN);
            translate([-D_ZAPFEN, -D_ZAPFEN, 0]) cube([2 * D_ZAPFEN, D_ZAPFEN + D_FLACH, 1]);
        }
    }

    module teil() {
        difference() {
            union() {
                translate([0, 0, -T]) linear_extrude(LASCHE) lasche2d();
                translate([0, 0, -T + LASCHE]) linear_extrude(T - 2 * LASCHE) mitte2d();
                translate([0, 0, -LASCHE]) linear_extrude(LASCHE) lasche2d();
                auge3d();
                translate([ZP[0], ZP[1], 0]) zapfen();
                translate([ZP[0], ZP[1], -T]) mirror([0, 0, 1]) zapfen();
            }
            translate([AX, Y_STUFE - 0.01, AZ]) rotate([-90, 0, 0]) {
                cylinder(d = D_STIFT, h = W_TOP);
                cylinder(d = D_SENK, h = T_SENK + 0.01);
            }
            for (p = BOHR_200) translate([p[0], p[1], -T - 1]) cylinder(d = 0.20, h = T + 2);
            for (p = BOHR_125) translate([p[0], p[1], -T - 1]) cylinder(d = 0.125, h = T + 2);
        }
    }

    if (EXPORT_MM) scale(25.4) teil(); else teil();
}


// =============================================================================
//  9 – Stift Ø0.125 x 0.61, liegend (Achse X)
// =============================================================================
module t9() {
    d_orig = 0.125;
    l_orig = 0.61;
    fase   = 0;          // in Ausgabeeinheit
    liegend = true;
    $fn = 96;

    f = EXPORT_MM ? 25.4 : 1;
    d = d_orig * f;
    l = l_orig * f;

    module stift() {
        if (fase > 0) {
            rotate_extrude()
                polygon([[0,0],[d/2-fase,0],[d/2,fase],[d/2,l-fase],[d/2-fase,l],[0,l]]);
        } else {
            cylinder(d = d, h = l);
        }
    }

    if (liegend)
        rotate([0, 90, 0]) stift();
    else
        stift();
}


// =============================================================================
//  10 – Hebel mit Schlitzkopf, Querbohrung und Zapfen
// =============================================================================
module hammer() {
    export_mm = EXPORT_MM;

    dicke_fuss  = 0.400;
    dicke_kopf  = 0.200;
    arm_breite  = 0.300;
    arm_unten   = -1.103;
    bohrung_d   = 0.130;

    kopf_unten  = 0.1732;
    kopf_oben   = 0.6732;
    kopf_links  = -0.475;
    schlitz_x0  = -0.250;
    schlitz_x1  = 0.000;
    schlitz_z   = 0.3732;
    r_links     = 0.225;
    r_rechts    = 0.300;
    nase_x      = 0.180;
    r_hohlkehle = 0.250;
    r_uebergang = 0.200;

    zapfen_d    = 0.250;
    zapfen_l    = 0.150;
    zapfen_r    = 0.020;

    $fn = 96;
    eps = 0.001;

    module teil() {
        difference() {
            union() {
                translate([0, (dicke_fuss + dicke_kopf) / 2, 0])
                    profil_y(dicke_kopf);
                intersection() {
                    translate([0, dicke_fuss, 0]) profil_y(dicke_fuss);
                    union() {
                        translate([-1, -1, -2]) cube([2, 2, 2]);
                        translate([-1, dicke_fuss / 2, 0])
                            rotate([0, 90, 0]) cylinder(r = r_uebergang, h = 2);
                    }
                }
                zapfen();
            }
            translate([arm_breite / 2, -eps, arm_unten])
                rotate([-90, 0, 0]) cylinder(d = bohrung_d, h = dicke_fuss + 2 * eps, $fn = 64);
        }
    }

    module profil_y(h) {
        rotate([90, 0, 0]) linear_extrude(height = h) profil();
    }

    module profil() {
        union() {
            translate([0, arm_unten]) square([arm_breite, kopf_unten - arm_unten + eps]);
            translate([arm_breite / 2, arm_unten]) circle(d = arm_breite);
            difference() {
                union() {
                    translate([kopf_links, kopf_unten])
                        square([arm_breite - kopf_links, schlitz_z - kopf_unten]);
                    intersection() {
                        translate([0, schlitz_z]) circle(r = r_rechts, $fn = 192);
                        translate([0, schlitz_z]) square([r_rechts, kopf_oben - schlitz_z]);
                    }
                    polygon([[0, schlitz_z], [0, kopf_oben], [nase_x, kopf_oben],
                             [r_rechts * cos(60), schlitz_z + r_rechts * sin(60)]]);
                    intersection() {
                        translate([schlitz_x0, schlitz_z]) circle(r = r_links, $fn = 192);
                        translate([kopf_links, schlitz_z]) square([r_links, r_links]);
                    }
                }
                translate([schlitz_x0, schlitz_z]) square([schlitz_x1 - schlitz_x0, 1]);
            }
            difference() {
                translate([-r_hohlkehle, kopf_unten - r_hohlkehle]) square([r_hohlkehle + eps, r_hohlkehle + eps]);
                translate([-r_hohlkehle, kopf_unten - r_hohlkehle]) circle(r = r_hohlkehle, $fn = 192);
            }
        }
    }

    module zapfen() {
        r = zapfen_d / 2;
        translate([arm_breite - eps, dicke_fuss / 2, 0]) rotate([0, 90, 0])
            rotate_extrude($fn = 96) union() {
                hull() {
                    square([r - zapfen_r, zapfen_l + eps]);
                    square([r, eps]);
                    translate([r - zapfen_r, zapfen_l + eps - zapfen_r]) circle(r = zapfen_r, $fn = 24);
                    translate([0, 0]) square([r, zapfen_l + eps - zapfen_r]);
                }
                difference() {
                    square([r + zapfen_r, zapfen_r + eps]);
                    translate([r + zapfen_r, zapfen_r + eps]) circle(r = zapfen_r, $fn = 24);
                }
            }
    }

    scale(export_mm ? 25.4 : 1) teil();
}


// =============================================================================
//  11 – Röhrchen Ø0.24 / Ø0.16 x 0.63
// =============================================================================
module springconnection() {
    od     = 0.24;
    id     = 0.16;
    height = 0.63;
    mm = EXPORT_MM;
    $fn = 96;

    scale(mm ? 25.4 : 1)
    difference() {
        cylinder(d = od, h = height);
        translate([0, 0, -0.01]) cylinder(d = id, h = height + 0.02);
    }
}


// =============================================================================
//  12 – Stift Ø0.130 x 1.050
// =============================================================================
module t12() {
    durchmesser = 0.130;
    laenge      = 1.050;
    fase        = 0.000;
    inch_to_mm  = EXPORT_MM;
    $fn = 96;

    module stift(d = durchmesser, l = laenge, c = fase) {
        if (c > 0) {
            hull() {
                translate([0, 0, c])     cylinder(d = d, h = l - 2*c);
                                         cylinder(d = d - 2*c, h = l);
            }
        } else {
            cylinder(d = d, h = l);
        }
    }

    scale(inch_to_mm ? 25.4 : 1) stift();
}


// =============================================================================
//  13 – Spiralfeder (Uhrfeder) 
// =============================================================================
module spring() {
    mm = EXPORT_MM;

    dicke     = 0.20;
    nabe_r    = 0.25;
    loch_r    = 0.15;
    loch_flach= 0.15*cos(50);
    steigung  = 0.22;
    band      = 0.10;
    windungen = 2;
    oese_r    = 0.14;
    oese_loch = 0.065;
    fillet_r  = 0.125;

    $fn = 96;
    seg = 360;

    function ri(f)  = nabe_r + steigung*f;
    function ra(f)  = ri(f) + band;
    function P(r,f) = [r*cos(360*f), r*sin(360*f)];

    oese_c = P(ri(windungen) + oese_r, windungen);

    function nrm(f) = let(r = ra(f), dr = steigung/(2*PI),
                          v = [r*cos(360*f) + dr*sin(360*f),  r*sin(360*f) - dr*cos(360*f)])
                      v / norm(v);
    function fc(f)  = P(ra(f), f) + fillet_r*nrm(f);

    function solve(a, b, i=0) =
        let(m = (a+b)/2, d = norm(fc(m) - oese_c) - (oese_r + fillet_r))
        i > 40 ? m : (d > 0 ? solve(m, b, i+1) : solve(a, m, i+1));
    ft    = solve(windungen - 0.25, windungen);
    F     = fc(ft);
    T_band= P(ra(ft), ft);
    T_oese= oese_c + oese_r*(F - oese_c)/norm(F - oese_c);

    module spirale() {
        n = ceil(windungen*seg);
        polygon(concat([for (i=[0:n]) P(ri(windungen*i/n), windungen*i/n)],
                       [for (i=[n:-1:0]) P(ra(windungen*i/n), windungen*i/n)]));
    }

    Q      = P(ra(0), 0);
    nQ     = nrm(0);
    blend_R= (Q*Q - nabe_r*nabe_r) / (2*(Q*nQ) - 2*nabe_r);
    blend_C= Q - blend_R*nQ;
    blend_a= atan2(-blend_C[1], -blend_C[0]) + 360;

    module nabe() {
        circle(r = nabe_r);
        intersection() {
            translate(blend_C) circle(r = blend_R, $fn = 192);
            polygon(concat([[0,0]], [for (a=[blend_a:1:360.5]) 2*[cos(a), sin(a)]], [2*[cos(360.5), sin(360.5)]]));
        }
    }

    module oese() {
        translate(oese_c) circle(r = oese_r);
        difference() {
            polygon([T_band, T_oese, oese_c, P(ri(ft), ft)]);
            translate(F) circle(r = fillet_r);
        }
    }

    module kontur() {
        difference() {
            union() { nabe(); spirale(); oese(); }
            intersection() {
                circle(r = loch_r);
                translate([-loch_r-1, -loch_r-1]) square([loch_r+1+loch_flach, 2*loch_r+2]);
            }
            translate(oese_c) circle(r = oese_loch);
        }
    }

    scale(mm ? 25.4 : 1)
        linear_extrude(height = dicke) kontur();
}


// =============================================================================
//  14 – Biegefeder-Element (Mäanderfeder mit Anschlussblock)
// =============================================================================
module triggerspring() {
    einheit = EXPORT_MM ? 25.4 : 1;

    w      = 0.05;
    p      = 0.15;
    dicke  = 0.15;
    ansatz = 0.01;

    x0     = 0.20;
    z_bot  = -0.37;
    z_top  = -0.13;
    z_top2 = -0.23;
    z_sym  = 0.065;

    blk_x0 = 0.925;
    blk_x1 = 1.125;
    bogen_r = 0.20;
    lang_x  = [0.90, 0.98];
    lang_r  = 0.065;

    $fn = 96;

    r_c   = p/2;
    r_out = r_c + w/2;
    r_in  = r_c - w/2;
    y_min = 0.14;

    module steg(x, y1, y2)
        translate([x - w/2, min(y1,y2)]) square([w, abs(y2-y1)]);

    module bogen(cx, cy, dir, eckig_links=false, eckig_rechts=false) {
        difference() {
            union() {
                intersection() {
                    translate([cx, cy]) circle(r_out);
                    translate([cx - r_out, dir < 0 ? cy - r_out : cy]) square([2*r_out, r_out]);
                }
                if (eckig_links)
                    translate([cx - r_out, dir < 0 ? cy - r_out : cy]) square([r_out, r_out]);
                if (eckig_rechts)
                    translate([cx, dir < 0 ? cy - r_out : cy]) square([r_out, r_out]);
            }
            translate([cx, cy]) circle(r_in);
        }
    }

    module feder_unten() {
        xs = [for (i = [0:5]) x0 + i*p];
        steg(xs[0], z_bot, z_top);
        steg(xs[1], z_bot, z_top);
        steg(xs[2], z_bot, z_top);
        steg(xs[3], z_bot, z_top2);
        steg(xs[4], z_bot, z_top2);
        bogen(xs[0] + r_c, z_bot,  -1, eckig_links = true);
        bogen(xs[1] + r_c, z_top,  +1);
        bogen(xs[2] + r_c, z_bot,  -1);
        bogen(xs[3] + r_c, z_top2, +1);
        bogen(xs[4] + r_c, z_bot,  -1, eckig_rechts = true);
    }

    module profil() {
        difference() {
            union() {
                feder_unten();
                translate([0, 2*z_sym]) mirror([0,1]) feder_unten();
                translate([blk_x0, z_bot - r_out])
                    square([blk_x1 - blk_x0, 2*(z_sym - (z_bot - r_out))]);
                intersection() {
                    translate([blk_x0, z_sym]) circle(bogen_r, $fn = 192);
                    translate([blk_x0 - bogen_r, z_sym - bogen_r]) square([bogen_r, 2*bogen_r]);
                }
            }
            hull() for (x = lang_x) translate([x, z_sym]) circle(lang_r);
        }
    }

    module ansatz_profil()
        difference() {
            translate([lang_x[1], z_sym - lang_r]) square([blk_x1 - lang_x[1], 2*lang_r]);
            translate([lang_x[1], z_sym]) circle(lang_r);
        }

    scale(einheit)
        translate([0, y_min + ansatz + dicke, 0])
            rotate([90, 0, 0]) {
                linear_extrude(dicke) profil();
                translate([0, 0, dicke]) linear_extrude(ansatz) ansatz_profil();
            }
}


// =============================================================================
//  15 – Abzugshebel 
// =============================================================================
module trigger() {
    MM_EXPORT = EXPORT_MM;
    $fn = 96;

    T        = 0.13;
    BAR_L    = 2.54;
    BAR_H    = 0.14;
    BAR_R    = 0.0625;
    LEG_W    = 0.225;
    TOP_Y0   = 0.69;
    TOP_Y1   = 0.915;
    TOP_X1   = 0.525;
    TOP_R    = 0.125;
    IN_R_TOP = 0.0625;
    IN_R_BOT = 0.125;
    TAB_X0   = 0.8355;
    TAB_X1   = 1.0448;
    TAB_Y1   = 0.32;
    TRG_X0   = 1.79;
    TRG_X1   = 2.09;
    TRG_CR   = 0.03;
    TIP_Y    = -0.853;
    BLK_Y0   = 0.15;
    BLK_Y1   = 0.33;
    BLK_Z0   = -0.08;
    BLK_Z1   = 0.21;
    BLK_W    = 0.225;
    BLK_R    = 0.125;
    FL_R     = 0.13;
    FL_YC    = 0.262;

    function ang(c, p) = atan2(p[1]-c[1], p[0]-c[0]);
    function arc(c, p0, p1, n = 24) =
        let(r  = (norm(p0-c) + norm(p1-c)) / 2,
            a0 = ang(c, p0),
            d0 = ang(c, p1) - a0,
            d  = d0 > 180 ? d0-360 : (d0 < -180 ? d0+360 : d0))
        [for (i = [0:n]) c + r*[cos(a0 + d*i/n), sin(a0 + d*i/n)]];

    module fillet_concave(corner, r, qx, qy) {
        translate(corner)
            difference() {
                scale([qx, qy]) square(r);
                translate([qx*r, qy*r]) circle(r);
            }
    }

    module trigger2d() {
        pts = concat(
            [[TRG_X0, 0]],
            arc([1.76,   -0.0726], [TRG_X0, -0.0726], [1.7627, -0.1012], 8),
            arc([1.7902, -0.4038], [1.7627, -0.1012], [1.5048, -0.2996], 24),
            arc([1.9269, -0.4948], [1.5048, -0.2996], [1.6216, -0.8456], 40),
            arc([1.641,  TIP_Y+TRG_CR], [1.6216, -0.8456], [1.641, TIP_Y], 8),
            arc([1.669,  TIP_Y+TRG_CR], [1.669, TIP_Y], [1.6939, -0.8072], 10),
            arc([1.9943, -0.6065], [1.6939, -0.8072], [1.8703, -0.2673], 40),
            arc([1.6754,  0.2166], [1.8703, -0.2673], [2.0835, -0.1084], 20),
            arc([TRG_X1-TRG_CR, -0.0897], [2.0835, -0.1084], [TRG_X1, -0.0897], 6),
            [[TRG_X1, 0]]
        );
        polygon(pts);
    }

    module plate2d() {
        union() {
            hull() {
                translate([BAR_R, BAR_R]) circle(BAR_R);
                translate([BAR_L-0.001, 0]) square([0.001, BAR_H]);
                translate([0, BAR_H-0.001]) square([0.001, 0.001]);
            }
            translate([0, BAR_R]) square([LEG_W, TOP_Y0 - BAR_R + 0.01]);
            intersection() {
                translate([0, TOP_Y0]) square([TOP_X1, TOP_Y1-TOP_Y0]);
                hull() {
                    translate([TOP_R, TOP_Y1-TOP_R])        circle(TOP_R);
                    translate([TOP_X1-TOP_R, TOP_Y1-TOP_R]) circle(TOP_R);
                    translate([0, TOP_Y0]) square([TOP_X1, 0.01]);
                }
            }
            fillet_concave([LEG_W, BAR_H], IN_R_BOT, 1, 1);
            fillet_concave([LEG_W, TOP_Y0], IN_R_TOP, 1, -1);
            trigger2d();
        }
    }

    module block_profile() {
        h = BLK_Z1 - BLK_Z0;
        intersection() {
            translate([0, BLK_Z0]) square([BLK_W, h]);
            hull() {
                translate([0, BLK_Z0]) square([0.001, h]);
                translate([BLK_W-BLK_R, BLK_Z0+BLK_R]) circle(BLK_R);
                translate([BLK_W-BLK_R, BLK_Z1-BLK_R]) circle(BLK_R);
            }
        }
    }

    function blk_s(y) = y >= FL_YC ? 1 :
        1 + (FL_R - sqrt(FL_R*FL_R - (FL_YC-y)*(FL_YC-y))) / BLK_W;

    module block() {
        N  = 12;
        ys = [for (i = [0:N]) BLK_Y0 + (FL_YC-BLK_Y0)*i/N];
        multmatrix([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]]) {
            for (i = [0:N-1])
                translate([0, 0, ys[i]])
                    linear_extrude(height = ys[i+1]-ys[i] + 0.0005,
                                   scale  = [blk_s(ys[i+1])/blk_s(ys[i]), 1])
                        scale([blk_s(ys[i]), 1]) block_profile();
            translate([0, 0, FL_YC])
                linear_extrude(height = BLK_Y1 - FL_YC) block_profile();
        }
    }

    module tab() {
        multmatrix([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
            translate([0, 0, BAR_H - 0.01])
                linear_extrude(height = TAB_Y1 - BAR_H + 0.01)
                    hull() {
                        translate([TAB_X0 + T/2, T/2]) circle(T/2);
                        translate([TAB_X1 - T/2, T/2]) circle(T/2);
                    }
    }

    module part() {
        union() {
            linear_extrude(height = T) plate2d();
            tab();
            block();
        }
    }

    scale(MM_EXPORT ? 25.4 : 1) part();
}
