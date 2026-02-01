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
  - Wireframe-Zeichenlogik

Steuerung:
  Maus links/rechts  -> Rotation um Y-Achse
  Maus oben/unten    -> Rotation um X-Achse
  Q                  -> Beenden
"""

import pygame
import math
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

# Kanten: Paare von Vertex-Indizes (direkt aus SHIP_VIPER_EDGES)
#   EDGE vertex1, vertex2, face1, face2, visibility
# Wir nehmen nur (vertex1, vertex2).
SHIP_EDGES = [
    (0,  3),   # Edge 0:  Nase -> Flügeltip rechts
    (0,  1),   # Edge 1:  Nase -> Oben-vorne
    (0,  2),   # Edge 2:  Nase -> Unten-vorne
    (0,  4),   # Edge 3:  Nase -> Flügeltip links
    (1,  7),   # Edge 4:  Oben-vorne -> Heck oben rechts
    (1,  8),   # Edge 5:  Oben-vorne -> Heck oben links
    (2,  5),   # Edge 6:  Unten-vorne -> Heck unten rechts
    (2,  6),   # Edge 7:  Unten-vorne -> Heck unten links
    (7,  8),   # Edge 8:  Heck oben rechts -> Heck oben links
    (5,  6),   # Edge 9:  Heck unten rechts -> Heck unten links
    (4,  8),   # Edge 10: Flügeltip links -> Heck oben links
    (4,  6),   # Edge 11: Flügeltip links -> Heck unten links
    (3,  7),   # Edge 12: Flügeltip rechts -> Heck oben rechts
    (3,  5),   # Edge 13: Flügeltip rechts -> Heck unten rechts
    (9, 12),   # Edge 14: Heck links außen -> Cockpit oben links
    (9, 13),   # Edge 15: Heck links außen -> Cockpit unten links
    (10,11),   # Edge 16: Heck rechts außen -> Cockpit oben rechts
    (10,14),   # Edge 17: Heck rechts außen -> Cockpit unten rechts
    (11,14),   # Edge 18: Cockpit oben rechts -> Cockpit unten rechts
    (12,13),   # Edge 19: Cockpit oben links -> Cockpit unten links
]


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
# 5. PERSPEKTIVISCHE PROJEKTION (3D -> 2D)
#    Das Herzstück der 3D-Darstellung!
#
#    Die Kamera sitzt bei (0, 0, -d) und schaut in Richtung +Z.
#    Ein Punkt (x, y, z) wird auf eine Bildebene bei z = -d projiziert.
#
#    Formel (Central Projection):
#        x_2d = (x * d) / (z + d)
#        y_2d = (y * d) / (z + d)
#
#    Dabei:
#      d = Abstand der Kamera zum Ursprung (Brennweite)
#      z + d = Abstand des Punktes zur Kamera
#
#    Je näher ein Punkt zur Kamera (kleines z+d), desto größer er auf dem Bild.
#    Das erzeugt den "Tiefeneffekt".
# ---------------------------------------------------------------------------

def project(point, d=5.0):
    """
    Projiziert einen 3D-Punkt auf 2D.
    d = Brennweite / Kameraabstand.
    Gibt (x_2d, y_2d) zurück oder None, wenn der Punkt hinter der Kamera ist.
    """
    x, y, z = point
    denom = z + d          # Abstand zum Betrachter
    if denom <= 0.1:       # Punkt hinter oder an der Kamera -> nicht zeichnen
        return None
    x_2d = (x * d) / denom
    y_2d = (y * d) / denom
    return (x_2d, y_2d)


# ---------------------------------------------------------------------------
# 6. HAUPTPROGRAMM
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
    cockpit_edges = [e for e in SHIP_EDGES if e[0] in cockpit_vertices or e[1] in cockpit_vertices]
    body_edges    = [e for e in SHIP_EDGES if e not in cockpit_edges]

    font = pygame.font.SysFont("monospace", 16)

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
        projected = {}
        for name, pt in SHIP_POINTS.items():
            # Schritt 1: Rotation anwenden
            rotated = mat_vec_mul(M, pt)
            # Schritt 2: Perspektivische Projektion
            proj = project(rotated, d=5.0)
            if proj:
                # Auf Bildschirmkoordinaten umrechnen
                # (0,0) ist oben-links bei pygame, also y umdrehen
                sx = proj[0] * scale + WIDTH  / 2
                sy = -proj[1] * scale + HEIGHT / 2
                projected[name] = (int(sx), int(sy))

        # --- Zeichnen ---
        screen.fill(BG_COLOR)

        # Sterne im Hintergrund (statisch, zufällig aber reproduzierbar)
        # (werden einmal generiert – hier vereinfacht mit einem Trick)

        # Wireframe zeichnen
        def draw_edges(edges, color, width=2):
            for a, b in edges:
                if a in projected and b in projected:
                    pygame.draw.line(screen, color, projected[a], projected[b], width)

        draw_edges(body_edges, WIRE_COLOR, 2)
        draw_edges(cockpit_edges, COCKPIT_COL, 2)

        # Punkte als kleine Kreise markieren (optional, zum Studieren)
        for name, pos in projected.items():
            pygame.draw.circle(screen, WIRE_COLOR, pos, 2)

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
