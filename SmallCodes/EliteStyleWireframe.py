"""
Elite-Style Wireframe: VIPER
================================
Das Raumschiff ist der originale Viper aus Elite (BBC Micro),
mit den Vertex- und Edge-Daten direkt aus dem Quellcode.

Komplett ohne 3D-Bibliotheken - alles selbst implementiert:
  - 3D-Punktdefinition (originale Elite-Koordinaten)
  - Rotationsmatrizen (X, Y, Z)
  - Matrixmultiplikation
  - Perspektivische Projektion (3D -> 2D)
  - Back-Face-Culling über Flächennormalen + Skalarprodukt
  - Wireframe-Zeichenlogik
  - 3D-Sternhimmel mit Streaking

Steuerung:
  Maus links/rechts  -> Rotation um Y-Achse
  Maus oben/unten    -> Rotation um X-Achse
  Q                  -> Beenden
"""

import pygame
import math
import random
import sys

# ---------------------------------------------------------------------------
# 1. VEKTORDEFINITION: Der Elite-Viper
#    Diese Koordinaten stammen DIREKT aus dem originalen Elite-Quellcode
#    (BBC Micro / Acorn Electron Version), aus der SHIP_VIPER Blueprint.
#
#    Im Original werden die Koordinaten als ganzzahlige Bytes gespeichert.
#    Wir normalisieren sie hier durch Division durch 24, damit das Schiff
#    zentriert um den Ursprung liegt und eine angenehme Größe hat.
#
#    Elite nutzt folgende Konvention:
#      +X = rechts, +Y = oben, +Z = nach vorne (Nase)
#
#    Der Viper hat 15 Vertices und 20 Edges – sehr spartan, aber perfekt
#    für Wireframe-Grafik, wie Braben es gewollt hat.
# ---------------------------------------------------------------------------

SCALE = 24.0  # Normalisierungsfaktor aus den Original-Koordinaten

# Originale Viper-Vertices aus dem Elite-Quellcode:
#   VERTEX x, y, z, face1, face2, face3, face4, visibility
# Wir nehmen nur (x, y, z) und normalisieren.
SHIP_POINTS = {
    # Hauptkörper
    0:  ( 0 / SCALE,  0 / SCALE,  72 / SCALE),   # Nase (Spitze vorne)
    1:  ( 0 / SCALE, 16 / SCALE,  24 / SCALE),   # Oben-vorne
    2:  ( 0 / SCALE,-16 / SCALE,  24 / SCALE),   # Unten-vorne
    3:  (48 / SCALE,  0 / SCALE, -24 / SCALE),   # Flügeltip rechts
    4:  (-48/ SCALE,  0 / SCALE, -24 / SCALE),   # Flügeltip links

    # Heck-Kante (untere Reihe)
    5:  (24 / SCALE,-16 / SCALE, -24 / SCALE),   # Heck unten rechts
    6:  (-24/ SCALE,-16 / SCALE, -24 / SCALE),   # Heck unten links

    # Heck-Kante (obere Reihe)
    7:  (24 / SCALE, 16 / SCALE, -24 / SCALE),   # Heck oben rechts
    8:  (-24/ SCALE, 16 / SCALE, -24 / SCALE),   # Heck oben links

    # Heck-Details (äußere Punkte auf der Heckkante)
    9:  (-32/ SCALE,  0 / SCALE, -24 / SCALE),   # Heck links außen
    10: (32 / SCALE,  0 / SCALE, -24 / SCALE),   # Heck rechts außen

    # Cockpit-Fenster (kleine Rechteckfläche auf der Heckkante)
    11: ( 8 / SCALE,  8 / SCALE, -24 / SCALE),   # Cockpit oben rechts
    12: (-8 / SCALE,  8 / SCALE, -24 / SCALE),   # Cockpit oben links
    13: (-8 / SCALE, -8 / SCALE, -24 / SCALE),   # Cockpit unten links
    14: ( 8 / SCALE, -8 / SCALE, -24 / SCALE),   # Cockpit unten rechts
}

# Kanten: (vertex1, vertex2, face1, face2)
#   Direkt aus SHIP_VIPER_EDGES – face1 und face2 sind die beiden
#   Flächen, die sich an dieser Kante treffen.
#   Eine Kante wird nur gezeichnet, wenn MINDESTENS eine ihrer
#   beiden Flächen zur Kamera zeigt (Back-Face-Culling).
SHIP_EDGES = [
    (0,  3, 2, 4),   # Edge 0:  Nase -> Flügeltip rechts
    (0,  1, 1, 2),   # Edge 1:  Nase -> Oben-vorne
    (0,  2, 3, 4),   # Edge 2:  Nase -> Unten-vorne
    (0,  4, 1, 3),   # Edge 3:  Nase -> Flügeltip links
    (1,  7, 0, 2),   # Edge 4:  Oben-vorne -> Heck oben rechts
    (1,  8, 0, 1),   # Edge 5:  Oben-vorne -> Heck oben links
    (2,  5, 4, 5),   # Edge 6:  Unten-vorne -> Heck unten rechts
    (2,  6, 3, 5),   # Edge 7:  Unten-vorne -> Heck unten links
    (7,  8, 0, 6),   # Edge 8:  Heck oben rechts -> Heck oben links
    (5,  6, 5, 6),   # Edge 9:  Heck unten rechts -> Heck unten links
    (4,  8, 1, 6),   # Edge 10: Flügeltip links -> Heck oben links
    (4,  6, 3, 6),   # Edge 11: Flügeltip links -> Heck unten links
    (3,  7, 2, 6),   # Edge 12: Flügeltip rechts -> Heck oben rechts
    (3,  5, 6, 4),   # Edge 13: Flügeltip rechts -> Heck unten rechts
    (9, 12, 6, 6),   # Edge 14: Heck links außen -> Cockpit oben links
    (9, 13, 6, 6),   # Edge 15: Heck links außen -> Cockpit unten links
    (10,11, 6, 6),   # Edge 16: Heck rechts außen -> Cockpit oben rechts
    (10,14, 6, 6),   # Edge 17: Heck rechts außen -> Cockpit unten rechts
    (11,14, 6, 6),   # Edge 18: Cockpit oben rechts -> Cockpit unten rechts
    (12,13, 6, 6),   # Edge 19: Cockpit oben links -> Cockpit unten links
]

# ---------------------------------------------------------------------------
# 1b. FLÄCHEN-DEFINITIONEN FÜR CULLING
#     Jede Fläche wird durch 3 Vertices definiert (Triangle).
#     Diese werden pro Frame nach Rotation benutzt um die Normale
#     via Kreuzprodukt zu berechnen.
#
#     Die Winding-Order (Reihenfolge) ist so gewählt, dass das
#     Kreuzprodukt (b-a)×(c-a) eine Normale ergibt, die nach
#     AUSSEN vom Schiff zeigt. Diese wurde geometrisch verifiziert.
# ---------------------------------------------------------------------------
FACE_TRIS = {
    0: (1, 7, 8),     # Oberseite
    1: (0, 1, 8),     # Obere Linksseite
    2: (0, 7, 1),     # Obere Rechtsseite
    3: (0, 6, 2),     # Untere Linksseite
    4: (0, 2, 5),     # Untere Rechtsseite
    5: (2, 6, 5),     # Unterseite
    6: (7, 4, 8),     # Heckkante
}

# ---------------------------------------------------------------------------
# 2. ROTATIONSMATRIZEN
#    Eine 3x3-Matrix wird als Liste von 3 Zeilen dargestellt:
#    [[m00, m01, m02],
#     [m10, m11, m12],
#     [m20, m21, m22]]
#
#    Die Rotation um eine Achse um den Winkel θ (theta) nutzt sin/cos.
# ---------------------------------------------------------------------------

def rot_x(theta):
    """Rotationsmatrix um die X-Achse (Nicken / Pitch)."""
    c, s = math.cos(theta), math.sin(theta)
    return [
        [1,  0,  0],
        [0,  c, -s],
        [0,  s,  c],
    ]

def rot_y(theta):
    """Rotationsmatrix um die Y-Achse (Gieren / Yaw)."""
    c, s = math.cos(theta), math.sin(theta)
    return [
        [ c, 0, s],
        [ 0, 1, 0],
        [-s, 0, c],
    ]

def rot_z(theta):
    """Rotationsmatrix um die Z-Achse (Rollen / Roll)."""
    c, s = math.cos(theta), math.sin(theta)
    return [
        [c, -s, 0],
        [s,  c, 0],
        [0,  0, 1],
    ]


# ---------------------------------------------------------------------------
# 3. MATRIXMULTIPLIKATION
#    Zwei 3x3-Matrizen multiplizieren (A * B)
#    Wichtig: Die Reihenfolge ist entscheidend!
# ---------------------------------------------------------------------------

def mat_mul(A, B):
    """Multipliziert zwei 3x3-Matrizen."""
    result = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                result[i][j] += A[i][k] * B[k][j]
    return result


# ---------------------------------------------------------------------------
# 4. MATRIX-VEKTOR-MULTIPLIKATION
#    Einen 3D-Punkt (Vektor) mit einer 3x3-Matrix transformieren.
# ---------------------------------------------------------------------------

def mat_vec_mul(M, v):
    """Multipliziert eine 3x3-Matrix mit einem 3D-Vektor (x, y, z)."""
    return (
        M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2],
        M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2],
        M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2],
    )


# ---------------------------------------------------------------------------
# 4b. VEKTOROPERATIONEN FÜR CULLING
# ---------------------------------------------------------------------------

def sub3(a, b):
    """Vektorsubtraktion a - b."""
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def cross3(a, b):
    """Kreuzprodukt a × b. Ergibt einen Vektor senkrecht zu beiden."""
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )

def dot3(a, b):
    """Skalarprodukt a · b."""
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


# ---------------------------------------------------------------------------
# 5. PERSPEKTIVISCHE PROJEKTION (3D -> 2D)
#    Das Herzstück der 3D-Darstellung!
#
#    Die Kamera sitzt bei (0, 0, +d) und schaut in Richtung -Z auf das Schiff.
#    Ein Punkt (x, y, z) wird auf eine Bildebene bei z = 0 projiziert.
#
#    Der Abstand des Punktes zur Kamera ist (d - z):
#      - Nase bei z=+3: Abstand = d-3  (klein  -> nahe  -> groß auf Bildschirm)
#      - Heck bei z=-1: Abstand = d+1  (groß   -> weit  -> klein auf Bildschirm)
#
#    Formel (Central Projection):
#        x_2d = (x * d) / (d - z)
#        y_2d = (y * d) / (d - z)
#
#    Je näher ein Punkt zur Kamera (kleines d-z), desto größer er auf dem Bild.
# ---------------------------------------------------------------------------

def project(point, d=5.0):
    """
    Projiziert einen 3D-Punkt auf 2D.
    d = Brennweite / Kameraabstand.
    Gibt (x_2d, y_2d) zurück oder None, wenn der Punkt hinter der Kamera ist.
    """
    x, y, z = point
    denom = d - z          # Abstand zum Betrachter
    if denom <= 0.1:       # Punkt hinter oder an der Kamera -> nicht zeichnen
        return None
    x_2d = (x * d) / denom
    y_2d = (y * d) / denom
    return (x_2d, y_2d)


# ---------------------------------------------------------------------------
# 6. POLYGON-CLIPPING (Sutherland-Hodgman)
#    Die konvexe Hülle des Schiffes kann Vertices außerhalb des Bildschirms
#    haben (z.B. die Nase bei seitlicher Ansicht durch die Perspektive).
#    pygame.draw.polygon füllt solche Polygone nicht korrekt.
#    Daher wird die Hull vor dem Zeichnen gegen das Bildschirm-Rechteck
#    geclippt: Außerhalb liegende Teile werden abgeschnitten und durch
#    Schnittpunkte auf dem Rand ersetzt.
# ---------------------------------------------------------------------------

def clip_polygon_to_rect(polygon, x_min, y_min, x_max, y_max):
    """Sutherland-Hodgman: Clippt ein Polygon gegen ein Rechteck.
    Funktioniert für beliebige Winding-Richtung."""

    def clip_against_edge(poly, edge_normal, edge_point):
        """Clippt gegen eine Halbebene.
        Behält Punkte wo dot(p - edge_point, normal) >= 0 (Innenseite)."""
        if not poly:
            return []

        def inside(p):
            return ((p[0]-edge_point[0])*edge_normal[0] +
                    (p[1]-edge_point[1])*edge_normal[1]) >= 0

        def intersect(p1, p2):
            d1 = ((p1[0]-edge_point[0])*edge_normal[0] +
                  (p1[1]-edge_point[1])*edge_normal[1])
            d2 = ((p2[0]-edge_point[0])*edge_normal[0] +
                  (p2[1]-edge_point[1])*edge_normal[1])
            t = d1 / (d1 - d2)
            return (p1[0] + t*(p2[0]-p1[0]),
                    p1[1] + t*(p2[1]-p1[1]))

        output = []
        for i in range(len(poly)):
            cur  = poly[i]
            nxt  = poly[(i+1) % len(poly)]
            c_in = inside(cur)
            n_in = inside(nxt)
            if c_in:
                output.append(cur)
                if not n_in:
                    output.append(intersect(cur, nxt))
            elif n_in:
                output.append(intersect(cur, nxt))
        return output

    poly = list(polygon)
    # Normale zeigt nach INNEN zum Rechteck
    poly = clip_against_edge(poly, ( 1,  0), (x_min, 0))   # links
    poly = clip_against_edge(poly, (-1,  0), (x_max, 0))   # rechts
    poly = clip_against_edge(poly, ( 0,  1), (0, y_min))   # oben
    poly = clip_against_edge(poly, ( 0, -1), (0, y_max))   # unten
    return poly
#    In Elite leben die Sterne im 3D-Raum – sie sind keine 2D-Punkte auf
#    einem Bildschirm, sondern echte 3D-Positionen, die durch dieselbe
#    Perspektivprojektion wie das Schiff dargestellt werden.
#
#    Das Prinzip:
#      - Jeder Stern hat eine 3D-Position (x, y, z).
#      - Pro Frame wird z um einen Geschwindigkeitswert verringert
#        (Stern bewegt sich Richtung Kamera).
#      - Die Projektion (x*d/(z+d)) macht nahe Sterne schneller und
#        größer – das erzeugt automatisch den "Streaking"-Effekt.
#      - Wenn ein Stern hinter die Kamera fällt (z < -d), wird er
#        weit hinten neu platziert (z = Z_FAR).
#
#    Helligkeit: Sterne werden je nach Z-Abstand heller/dunkelr,
#    damit die Tiefe noch spürbar wird.
# ---------------------------------------------------------------------------

class Starfield:
    NUM_STARS = 200          # Anzahl der Sterne
    # Kamera bei z=+5, Schiff von z=-1 (Heck) bis z=+3 (Nase).
    # Sterne müssen im negativen Z-Bereich bleiben (hinter das Schiff).
    # Sie fliegen in +Z Richtung (auf die Kamera zu) und werden bei
    # Z_NEAR zurückgesetzt auf Z_FAR.
    Z_NEAR   = -1.5          # Nahe Grenze: knapp hinter dem Heck (z=-1)
    Z_FAR    = -40.0         # Weite Grenze: weit hinter das Schiff
    SPREAD_X = 8.0           # Breite des Sternfeldes (X)
    SPREAD_Y = 6.0           # Höhe des Sternfeldes (Y)
    SPEED    = 12.0          # Bewegungsgeschwindigkeit Richtung Kamera (+Z)

    def __init__(self):
        random.seed(42)      # Reproduzierbar für konsistentes Aussehen
        self.stars = []
        for _ in range(self.NUM_STARS):
            self.stars.append(self._new_star())

    def _new_star(self):
        """Erzeugt einen neuen Stern im negativen Z-Bereich (hinter das Schiff)."""
        return [
            random.uniform(-self.SPREAD_X, self.SPREAD_X),
            random.uniform(-self.SPREAD_Y, self.SPREAD_Y),
            random.uniform(self.Z_FAR, self.Z_NEAR),         # z zwischen -40 und -1.5
        ]

    def update(self, dt):
        """Bewegt Sterne in +Z Richtung (auf Kamera zu), setzt bei Z_NEAR zurück."""
        for star in self.stars:
            star[2] += self.SPEED * dt          # Z zunehmen (auf Kamera zu)
            if star[2] > self.Z_NEAR:           # Zu nah geworden?
                star[0] = random.uniform(-self.SPREAD_X, self.SPREAD_X)
                star[1] = random.uniform(-self.SPREAD_Y, self.SPREAD_Y)
                star[2] = self.Z_FAR

    def draw(self, surface, width, height, scale, d=5.0):
        """Projiziert und zeichnet alle Sterne."""
        cx, cy = width // 2, height // 2

        for star in self.stars:
            x, y, z = star

            # Gleiche Projektion wie für das Schiff: denom = d - z
            denom = d - z
            if denom <= 0.1:
                continue                        # Stern nicht sichtbar

            sx = (x * d) / denom * scale + cx
            sy = -(y * d) / denom * scale + cy

            # Bildschirmgrenzen prüfen
            if sx < 0 or sx >= width or sy < 0 or sy >= height:
                continue

            # --- Helligkeit nach Tiefe ---
            # Abstand zur Kamera = d - z. Nahe Sterne (z nahe 0) haben
            # kleinen Abstand -> hell. Weit entfernte (z nahe -40) haben
            # großen Abstand -> dunkel.
            dist_to_cam = d - z                  # immer positiv, da z < 0 < d
            # Normalisieren auf 0..1: dist läuft von ~6.5 (nah) bis ~45 (weit)
            t = (dist_to_cam - (d - self.Z_NEAR)) / ((d - self.Z_FAR) - (d - self.Z_NEAR))
            t = max(0.0, min(1.0, t))            # Klamp
            # t=0 -> nah -> hell, t=1 -> weit -> dunkel
            brightness = int(255 - 195 * t)      # Bereich 255..60

            # --- Streaking ---
            # Vorheriges Frame: Stern war bei z - SPEED*dt (noch weiter weg)
            z_prev = z - self.SPEED * (1.0 / 60.0)
            denom_prev = d - z_prev
            if denom_prev > 0.1:
                sx_prev = (x * d) / denom_prev * scale + cx
                sy_prev = -(y * d) / denom_prev * scale + cy
            else:
                sx_prev, sy_prev = sx, sy

            # Farbe: leichtes Blauweiss wie im Original
            color = (brightness, brightness, min(255, brightness + 20))

            # Streak-Länge begrenzen (bei sehr nahen Sternen)
            dist = math.sqrt((sx - sx_prev)**2 + (sy - sy_prev)**2)
            if dist > 1.5:
                pygame.draw.line(surface, color, (int(sx_prev), int(sy_prev)),
                                 (int(sx), int(sy)), 1)
            else:
                pygame.draw.circle(surface, color, (int(sx), int(sy)), 1)


# ---------------------------------------------------------------------------
# 7. HAUPTPROGRAMM
# ---------------------------------------------------------------------------

def main():
    pygame.init()

    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Elite – Viper Wireframe")
    clock = pygame.time.Clock()

    # Farben
    BG_COLOR    = (10, 10, 20)       # Dunkles Weltraum-Schwarz
    WIRE_COLOR  = (0, 220, 180)      # Cyan-Grün (Classic Elite)
    COCKPIT_COL = (180, 220, 255)    # Leichtes Blau für Cockpit
    TEXT_COLOR  = (100, 200, 160)

    # Aktuelle Rotation (Winkel in Radiant)
    angle_y = 0.0
    angle_x = 0.0

    # Maussteuerung: Referenzposition beim Drücken
    mouse_start = None
    angle_y_start = 0.0
    angle_x_start = 0.0

    # Auto-Rotation (wenn Maus nicht gedrückt)
    auto_rotate = True
    auto_speed_y = 0.4   # Radiant pro Sekunde
    auto_speed_x = 0.15

    # Skalierfaktor für die Bildschirm-Projektion
    scale = 160.0

    # Cockpit-Kanten separat für andere Farbe
    # Im originalen Viper sind Vertices 9-14 die Heck- und Cockpit-Details
    cockpit_vertices = {9, 10, 11, 12, 13, 14}
    cockpit_edge_set = set()
    for i, (v1, v2, f1, f2) in enumerate(SHIP_EDGES):
        if v1 in cockpit_vertices or v2 in cockpit_vertices:
            cockpit_edge_set.add(i)

    font = pygame.font.SysFont("monospace", 16)

    # Sternhimmel initialisieren
    starfield = Starfield()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Zeitdifferenz in Sekunden

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_start = pygame.mouse.get_pos()
                angle_y_start = angle_y
                angle_x_start = angle_x
                auto_rotate = False
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_start = None
                auto_rotate = True

        # --- Rotation aktualisieren ---
        if mouse_start and auto_rotate is False:
            mx, my = pygame.mouse.get_pos()
            dx = mx - mouse_start[0]
            dy = my - mouse_start[1]
            # Mausbewegung -> Winkel (sensitivität anpassen)
            angle_y = angle_y_start + dx * 0.01
            angle_x = angle_x_start + dy * 0.01
        elif auto_rotate:
            angle_y += auto_speed_y * dt
            angle_x += auto_speed_x * dt

        # --- Kombinierte Rotationsmatrix berechnen ---
        # Reihenfolge: erst X, dann Y rotieren
        M = mat_mul(rot_y(angle_y), rot_x(angle_x))

        # --- Alle Punkte transformieren und projizieren ---
        projected = {}      # 2D-Bildschirmkoordinaten
        rotated_pts = {}    # 3D nach Rotation, vor Projektion (für Culling)
        for name, pt in SHIP_POINTS.items():
            rot = mat_vec_mul(M, pt)
            rotated_pts[name] = rot
            proj = project(rot, d=5.0)
            if proj:
                sx = proj[0] * scale + WIDTH  / 2
                sy = -proj[1] * scale + HEIGHT / 2
                projected[name] = (int(sx), int(sy))

        # --- Zeichnen ---
        screen.fill(BG_COLOR)

        # Sternhimmel: update + zeichnen (vor dem Schiff)
        starfield.update(dt)
        starfield.draw(screen, WIDTH, HEIGHT, scale)

        # --- Back-Face-Culling (Vertex-basiert) ---
        # Funktioniert ohne vordefinierte Normals:
        #   1. Jede Fläche ist durch 3 Vertices definiert (FACE_TRIS).
        #   2. Diese werden durch die Rotationsmatrix M transformiert.
        #   3. Kreuzprodukt (b-a)×(c-a) gibt die Flächennormale.
        #      Die Winding-Order sorgt dafür, dass sie nach AUSSEN zeigt.
        #   4. Vektor vom Flächenmittelpunkt zur Kamera berechnen.
        #   5. Dot-Produkt Normale · ZurKamera:
        #        > 0  ->  Normale zeigt zur Kamera  ->  Fläche SICHTBAR
        #        <= 0 ->  Normale zeigt weg          ->  Fläche VERSTECKT
        #   6. Kante wird gezeichnet wenn mindestens eine ihrer
        #      beiden Flächen sichtbar ist.
        CAMERA_POS = (0.0, 0.0, 5.0)   # Kamera bei (0, 0, +d)

        visible_faces = set()
        for fi, (a, b, c) in FACE_TRIS.items():
            va = rotated_pts[a]
            vb = rotated_pts[b]
            vc = rotated_pts[c]
            # Normale: Kreuzprodukt der beiden Kantenvektoren
            normal = cross3(sub3(vb, va), sub3(vc, va))
            # Mittelpunkt der Fläche
            mid = ((va[0]+vb[0]+vc[0]) / 3.0,
                   (va[1]+vb[1]+vc[1]) / 3.0,
                   (va[2]+vb[2]+vc[2]) / 3.0)
            # Vektor vom Mittelpunkt zur Kamera
            to_cam = sub3(CAMERA_POS, mid)
            # Sichtbar wenn Normale zum Betrachter zeigt
            if dot3(normal, to_cam) > 0:
                visible_faces.add(fi)

        # --- Silhouette-Fill: Außenumriss des Schiffes schwarz füllen ---
        # Der Viper ist ein konvexer Körper. Die konvexe Hülle (Convex Hull)
        # aller projizierten Vertices gibt exakt die Außensilhouette.
        # Diese wird als einzelnes schwarzes Polygon gefüllt, damit keine
        # Sterne durch das Schiff scheinen – unabhängig vom Blickwinkel.
        #
        # Konvexe Hülle via Graham-Scan:
        #   1. Unterster Punkt als Startpunkt wählen
        #   2. Alle anderen Punkte nach Winkel zum Startpunkt sortieren
        #   3. Punkte durchgehen, dabei nur Links-Abbiegungen behalten
        if len(projected) >= 3:
            # Duplikate entfernen (int()-Rundung kann Punkte auf gleichen Pixel mappen)
            pts = list(set(projected.values()))

            # Startpunkt: unterster Punkt (höchstes y in pygame)
            # Bei Gleichstand: der linkeste (kleinstes x)
            start = max(pts, key=lambda p: (p[1], -p[0]))

            def angle_key(p):
                return math.atan2(p[1] - start[1], p[0] - start[0])

            sorted_pts = sorted([p for p in pts if p != start], key=angle_key)

            def cross(o, a, b):
                """Kreuzprodukt (a-o) x (b-o). Positiv = Links-Abbiegung."""
                return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

            hull = [start]
            for p in sorted_pts:
                # Solange der letzte Schritt eine Rechts-Abbiegung ist, entfernen
                while len(hull) > 1 and cross(hull[-2], hull[-1], p) <= 0:
                    hull.pop()
                hull.append(p)

            if len(hull) >= 3:
                # Hull gegen Bildschirm clippen – Vertices können durch
                # die Perspektive außerhalb des Bildschirms liegen
                clipped_hull = clip_polygon_to_rect(hull, 0, 0, WIDTH, HEIGHT)
                if len(clipped_hull) >= 3:
                    pygame.draw.polygon(screen, BG_COLOR, clipped_hull)

        # Wireframe zeichnen – nur Kanten, deren mindestens eine Fläche sichtbar ist
        for i, (v1, v2, f1, f2) in enumerate(SHIP_EDGES):
            if v1 not in projected or v2 not in projected:
                continue
            # Kante nur zeichnen wenn face1 ODER face2 sichtbar
            if f1 not in visible_faces and f2 not in visible_faces:
                continue
            color = COCKPIT_COL if i in cockpit_edge_set else WIRE_COLOR
            pygame.draw.line(screen, color, projected[v1], projected[v2], 2)

        # --- HUD / Info-Text ---
        info_lines = [
            "ELITE  –  VIPER",
            f"Rot Y: {math.degrees(angle_y):>7.1f}°   Rot X: {math.degrees(angle_x):>7.1f}°",
            "",
            "Maus ziehen -> Rotation",
            "Q -> Beenden",
        ]
        for i, line in enumerate(info_lines):
            surf = font.render(line, True, TEXT_COLOR)
            screen.blit(surf, (12, 12 + i * 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
