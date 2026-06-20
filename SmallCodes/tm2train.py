"""
TM2Train Bildelement-Bibliothek
================================
Elemente (9x9 Pixel):
  1 = cross       (Kreuzung, schwarz)
  2 = curve1      (Kurve, schwarz)
  3 = FlipFlop1   (FlipFlop Zustand 1, grün diagonal + schwarze Linie)
  4 = FlipFlop2   (FlipFlop Zustand 2, grün horizontal + schwarze Diagonale)
  5 = Lazy1       (Lazy Zustand 1, rot diagonal + schwarze Linie)
  6 = Lazy2       (Lazy Zustand 2, rot horizontal + schwarze Diagonale)
  7 = line1       (gerade Linie, schwarz)
  8 = Sprung1     (Sprung, blau diagonal + schwarze Linie)
  9 = Sprung2     (Sprung, schwarze Diagonale + blaue Linie)

getElement(ElementNr, drehen, horizontalFlip, vertikalFlip)
  drehen: 1=0°, 2=90°, 3=180°, 4=270°
  horizontalFlip: True/False
  vertikalFlip:   True/False
  Rückgabe: PIL.Image (9x9, RGBA)
"""

from PIL import Image, ImageDraw
import numpy as np
import os

# ---------------------------------------------------------------------------
# Farben
# ---------------------------------------------------------------------------
W  = (255, 255, 255, 255)   # Weiß (Hintergrund)
BK = (0,   0,   0,   255)   # Schwarz
GR = (0,   188, 0,   255)   # Grün  (FlipFlop)
RE = (149, 0,   0,   255)   # Rot   (Lazy)
BL = (0,   0,   220, 255)   # Blau  (Sprung)

# ---------------------------------------------------------------------------
# Rohdaten der 8 Elemente  (9 Zeilen × 9 Spalten)
# ---------------------------------------------------------------------------
def _make(rows):
    """Wandelt eine Liste von 9-Tupeln in ein 9×9 RGBA-Array um."""
    arr = np.array(rows, dtype=np.uint8)          # shape (9, 9, 4)
    return arr

# --- 1: cross  (+ Zeichen: vertikale + horizontale schwarze Linie) ---
_cross = _make([
    [W, W, W, W, BK, W, W, W, W],
    [W, W, W, W, BK, W, W, W, W],
    [W, W, W, W, BK, W, W, W, W],
    [W, W, W, W, BK, W, W, W, W],
    [BK,BK,BK,BK,BK,BK,BK,BK,BK],
    [W, W, W, W, BK, W, W, W, W],
    [W, W, W, W, BK, W, W, W, W],
    [W, W, W, W, BK, W, W, W, W],
    [W, W, W, W, BK, W, W, W, W],
])

# --- 2: curve1  (Kurve: horizontale Linie links bis Mitte, dann diagonal nach unten-rechts) ---
_curve1 = _make([
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [BK,BK,BK,W, W, W, W, W, W],
    [W, W, W, BK,W, W, W, W, W],
    [W, W, W, W, BK,W, W, W, W],
    [W, W, W, W, BK,W, W, W, W],
    [W, W, W, W, BK,W, W, W, W],
])

# --- 3: FlipFlop1  (grüne Diagonale NE→SW in oberer Hälfte + horizontale schwarze Linie) ---
_flipflop1 = _make([
    [W, W, W, W, GR,W, W, W, W],
    [W, W, W, GR,W, W, W, W, W],
    [W, W, GR,W, W, W, W, W, W],
    [W, GR,W, W, W, W, W, W, W],
    [BK,BK,BK,BK,BK,BK,BK,BK,BK],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
])

# --- 4: FlipFlop2  (schwarze Diagonale NE→SW in oberer Hälfte + grüne horizontale Linie teilweise) ---
_flipflop2 = _make([
    [W, W, W, W, BK,W, W, W, W],
    [W, W, W, BK,W, W, W, W, W],
    [W, W, BK,W, W, W, W, W, W],
    [W, BK,W, W, W, W, W, W, W],
    [BK,GR,GR,GR,GR,BK,BK,BK,BK],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
])

# --- 5: Lazy1  (rote Diagonale NE→SW in oberer Hälfte + schwarze horizontale Linie) ---
_lazy1 = _make([
    [W, W, W, W, RE,W, W, W, W],
    [W, W, W, RE,W, W, W, W, W],
    [W, W, RE,W, W, W, W, W, W],
    [W, RE,W, W, W, W, W, W, W],
    [BK,BK,BK,BK,BK,BK,BK,BK,BK],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
])

# --- 6: Lazy2  (schwarze Diagonale NE→SW in oberer Hälfte + rote horizontale Linie teilweise) ---
_lazy2 = _make([
    [W, W, W, W, BK,W, W, W, W],
    [W, W, W, BK,W, W, W, W, W],
    [W, W, BK,W, W, W, W, W, W],
    [W, BK,W, W, W, W, W, W, W],
    [BK,RE,RE,RE,RE,BK,BK,BK,BK],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
])

# --- 7: line1  (gerade horizontale schwarze Linie durch die Mitte) ---
_line1 = _make([
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [BK,BK,BK,BK,BK,BK,BK,BK,BK],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
])

# --- 8: Sprung1  (blaue Diagonale NE→SW in oberer Hälfte + schwarze horizontale Linie) ---
_sprung1 = _make([
    [W, W, W, W, BL,W, W, W, W],
    [W, W, W, BL,W, W, W, W, W],
    [W, W, BL,W, W, W, W, W, W],
    [W, BL,W, W, W, W, W, W, W],
    [BK,BK,BK,BK,BK,BK,BK,BK,BK],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
])

# --- 9: Sprung2  (schwarze Diagonale NE→SW in oberer Hälfte + blaue horizontale Linie teilweise) ---
_sprung2 = _make([
    [W, W, W, W, BK,W, W, W, W],
    [W, W, W, BK,W, W, W, W, W],
    [W, W, BK,W, W, W, W, W, W],
    [W, BK,W, W, W, W, W, W, W],
    [BK,BL,BL,BL,BL,BK,BK,BK,BK],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
])

# --- 10: Start  (gerade horizontale Linie mit kleinem Kreis-Ring in der Mitte) ---
_start = _make([
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, BK,BK,BK,W, W, W],
    [W, W, BK,W, W, W, BK,W, W],
    [BK,BK,BK,W, W, W, BK,BK,BK],
    [W, W, BK,W, W, W, BK,W, W],
    [W, W, W, BK,BK,BK,W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
])

# --- 11: Endpuffer / Prellbock  (Gerade von links, Querbalken-Anschlag rechts) ---
_endpuffer = _make([
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, BK,W],
    [W, W, W, W, W, W, W, BK,W],
    [BK,BK,BK,BK,BK,BK,BK,BK,W],
    [W, W, W, W, W, W, W, BK,W],
    [W, W, W, W, W, W, W, BK,W],
    [W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W],
])

# ---------------------------------------------------------------------------
# Mapping: ElementNr → (Array, Name)
# ---------------------------------------------------------------------------
ELEMENTS = {
    1: (_cross,     "cross"),
    2: (_curve1,    "curve1"),
    3: (_flipflop1, "FlipFlop1"),
    4: (_flipflop2, "FlipFlop2"),
    5: (_lazy1,     "Lazy1"),
    6: (_lazy2,     "Lazy2"),
    7: (_line1,     "line1"),
    8: (_sprung1,   "Sprung1"),
    9: (_sprung2,   "Sprung2"),
    10:(_start,     "Start"),
    11:(_endpuffer, "Endpuffer"),
}

# ---------------------------------------------------------------------------
# Haupt-API
# ---------------------------------------------------------------------------
def getElement(
    ElementNr: int,
    drehen: int,
    horizontalFlip: bool,
    vertikalFlip: bool,
    ausgabe_datei: str = None,
    scale: int = 1,
) -> Image.Image:
    """
    Gibt das transformierte Bildelement als PIL.Image zurück
    und speichert es optional als PNG.

    Parameter:
        ElementNr       : 1–9 (siehe Modulkopf)
        drehen          : 1=0°, 2=90°, 3=180°, 4=270°
        horizontalFlip  : True → links/rechts spiegeln
        vertikalFlip    : True → oben/unten spiegeln
        ausgabe_datei   : Pfad zur PNG-Ausgabe (None = kein Speichern)
        scale           : Skalierungsfaktor für die Ausgabe (Standard 1 = 9×9 px)

    Rückgabe:
        PIL.Image (RGBA, 9×9 Pixel × scale)
    """
    if ElementNr not in ELEMENTS:
        raise ValueError(f"Ungültige ElementNr {ElementNr}. Gültig: 1–9")
    if drehen not in (1, 2, 3, 4):
        raise ValueError(f"Ungültiger drehen-Wert {drehen}. Gültig: 1, 2, 3, 4")

    arr, name = ELEMENTS[ElementNr]
    img = Image.fromarray(arr.astype(np.uint8), mode="RGBA")

    # --- Drehung ---
    # PIL rotate dreht gegen den Uhrzeigersinn; wir mappen:
    #   1 = 0°    → keine Drehung
    #   2 = 90°   → 270° im PIL-Koordinatensystem (= 90° im Uhrzeigersinn)
    #   3 = 180°  → 180°
    #   4 = 270°  → 90° im PIL-Koordinatensystem (= 270° im Uhrzeigersinn)
    rotation_map = {1: 0, 2: 270, 3: 180, 4: 90}
    angle = rotation_map[drehen]
    if angle != 0:
        img = img.rotate(angle)

    # --- Spiegelung ---
    if horizontalFlip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if vertikalFlip:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

    # --- Skalierung ---
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)

    # --- Speichern ---
    if ausgabe_datei is not None:
        img.save(ausgabe_datei)
        print(f"Gespeichert: {ausgabe_datei}")

    return img


# ---------------------------------------------------------------------------
# Hilfsfunktion: Übersichtsbild aller Varianten
# ---------------------------------------------------------------------------
def erzeuge_uebersicht(ausgabe_datei: str = "uebersicht.png", scale: int = 4):
    """
    Erzeugt ein Übersichtsbild mit allen 8 Elementen in allen
    4 Drehungen × 4 Flip-Kombinationen = 16 Varianten pro Element.
    Layout: 8 Zeilen (Elemente), 16 Spalten (Varianten)
    """
    flip_kombinationen = [
        (False, False),
        (True,  False),
        (False, True),
        (True,  True),
    ]
    drehungen = [1, 2, 3, 4]
    varianten = [(d, h, v) for d in drehungen for h, v in flip_kombinationen]

    cell_size   = 9 * scale
    padding     = 2
    label_h     = 14
    row_label_w = 75   # Breite der linken Spalte für "Nr: Name"

    cols = len(varianten)   # 16
    rows = len(ELEMENTS)    # 9

    total_w = row_label_w + cols * (cell_size + padding) + padding
    total_h = rows * (cell_size + padding + label_h) + padding + 20

    canvas = Image.new("RGBA", (total_w, total_h), (220, 220, 220, 255))

    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except Exception:
        font = ImageFont.load_default()

    # Kopfzeile
    draw.text((padding, 2), "Alle Elemente (Zeilen) × alle Varianten (Drehung+Flip)", fill=(0, 0, 0, 255), font=font)

    for row_idx, (elem_nr, (_, elem_name)) in enumerate(sorted(ELEMENTS.items())):
        y_base = 20 + row_idx * (cell_size + padding + label_h) + padding
        # Element-Label in der linken Spalte (Nr + Name)
        draw.text((padding, y_base + label_h + cell_size // 2 - 5),
                  f"{elem_nr}: {elem_name}", fill=(0, 0, 0, 255), font=font)

        for col_idx, (drehen, h_flip, v_flip) in enumerate(varianten):
            x = row_label_w + col_idx * (cell_size + padding)
            y = y_base + label_h

            tile = getElement(elem_nr, drehen, h_flip, v_flip, scale=scale)
            canvas.paste(tile, (x, y))

            # Kleines Label oberhalb des Bildes
            lbl = f"r{drehen}{'H' if h_flip else ''}{'V' if v_flip else ''}"
            draw.text((x, y_base), lbl, fill=(80, 80, 80, 255), font=font)

    canvas.save(ausgabe_datei)
    print(f"Übersicht gespeichert: {ausgabe_datei}")
    return canvas


# ---------------------------------------------------------------------------
# Matrix-Renderer
# ---------------------------------------------------------------------------
def parse_zelle(token: str):
    """
    Parst einen Zellen-Token aus der Matrix-Beschreibung.

    Formate:
        "0"          → leeres Feld
        "3:r4HV"     → ElementNr=3, drehen=4, hFlip=True, vFlip=True
        "2:r1H"      → ElementNr=2, drehen=1, hFlip=True, vFlip=False
        "9:r1"       → ElementNr=9, drehen=1, hFlip=False, vFlip=False

    Rückgabe: (elem_nr, drehen, hFlip, vFlip) oder None bei leerem Feld / Fehler
    """
    token = token.strip()
    if not token or token == "0":
        return None

    try:
        nr_str, rest = token.split(":", 1)
        elem_nr = int(nr_str.strip())
    except ValueError:
        print(f"  [Warnung] Ungültiger Token '{token}' – wird als leeres Feld behandelt")
        return None

    # rest z.B. "r4HV", "r1H", "r1"
    rest = rest.strip()
    if not rest.startswith("r"):
        print(f"  [Warnung] Fehlendes 'r' in '{token}' – wird als leeres Feld behandelt")
        return None

    drehen   = int(rest[1])          # Ziffer nach 'r'
    h_flip   = "H" in rest[2:]
    v_flip   = "V" in rest[2:]

    if elem_nr not in ELEMENTS:
        print(f"  [Warnung] Unbekannte ElementNr {elem_nr} in '{token}' – leeres Feld")
        return None
    if drehen not in (1, 2, 3, 4):
        print(f"  [Warnung] Ungültiges drehen={drehen} in '{token}' – leeres Feld")
        return None

    return (elem_nr, drehen, h_flip, v_flip)


def render_matrix(
    matrix,
    ausgabe_datei: str = None,
    scale: int = 1,
) -> Image.Image:
    """
    Rendert eine Matrix von Element-Tokens zu einem zusammengesetzten Bild.

    Parameter:
        matrix        : 2D-Liste von Strings  ODER  einzelner mehrzeiliger String.
                        Jeder Eintrag hat das Format "Nr:rDHV", z.B. "3:r4HV",
                        oder "0" / "" für ein leeres weißes Feld.
        ausgabe_datei : optionaler Pfad zum Speichern als PNG
        scale         : Skalierungsfaktor (Standard 1 = 9×9 px pro Zelle)

    Rückgabe:
        PIL.Image (RGBA)

    Beispiel-Matrix als String:
        \"\"\"
             0,      0, 3:r4HV, 2:r1
             0, 2:r1H,   9:r1, 1:r1
        8:r1HV,  5:r1,   7:r1, 9:r1
        2:r1HV,  2:r1,   2:r1,    0
        \"\"\"
    """
    # --- Matrix normalisieren (String → 2D-Liste) ---
    if isinstance(matrix, str):
        rows = []
        for line in matrix.strip().splitlines():
            line = line.strip()
            if line:
                rows.append([cell.strip() for cell in line.split(",")])
        matrix = rows

    if not matrix:
        raise ValueError("Leere Matrix übergeben")

    n_rows = len(matrix)
    n_cols = max(len(row) for row in matrix)
    cell   = 9 * scale

    canvas = Image.new("RGBA", (n_cols * cell, n_rows * cell), (255, 255, 255, 255))

    for r_idx, row in enumerate(matrix):
        for c_idx, token in enumerate(row):
            parsed = parse_zelle(token)
            if parsed is None:
                # Leeres weißes Feld – nichts tun, Hintergrund ist schon weiß
                continue
            elem_nr, drehen, h_flip, v_flip = parsed
            tile = getElement(elem_nr, drehen, h_flip, v_flip, scale=scale)
            canvas.paste(tile, (c_idx * cell, r_idx * cell))

    if ausgabe_datei is not None:
        canvas.save(ausgabe_datei)
        print(f"Matrix-Bild gespeichert: {ausgabe_datei}")

    return canvas



# ---------------------------------------------------------------------------
# ShellC – Zell-Element (zwei Zustände)
# ---------------------------------------------------------------------------

# Zustand 0
_SHELLC_MATRIX_0 = """
7:r2,    0,      0, 3:r4HV, 2:r1
7:r2,    0, 2:r1H,   9:r1,  1:r1
7:r2,    0,   7:r2,      0, 7:r2
1:r1, 8:r1HV,  5:r1,   7:r1, 9:r1
7:r2, 2:r1HV,  7:r1,   2:r1,    0
"""

# Zustand 1
_SHELLC_MATRIX_1 = """
7:r2,    0,      0, 4:r4HV, 2:r1
7:r2,    0, 2:r1H,   9:r1,  1:r1
7:r2,    0,   7:r2,      0, 7:r2
1:r1, 8:r1HV,  6:r1,   7:r1, 9:r1
7:r2, 2:r1HV,  7:r1,   2:r1,    0
"""


def ShellC(zustand: int) -> str:
    """
    Gibt die Matrix des Zell-Elements C als String zurück.

    Parameter:
        zustand : 0 = FlipFlop2-Variante (neuer Zustand)
                  1 = FlipFlop1-Variante (alter Zustand)

    Rückgabe:
        Matrix als mehrzeiliger String (verwendbar mit matrix_to_png)
    """
    if zustand not in (0, 1):
        raise ValueError(f"Ungültiger Zustand {zustand}. Gültig: 0 oder 1")

    return _SHELLC_MATRIX_0 if zustand == 0 else _SHELLC_MATRIX_1


def matrix_to_png(
    matrix,
    ausgabe_datei: str = None,
    scale: int = 1,
    koordinaten: bool = False,
) -> Image.Image:
    """
    Wandelt eine Matrix (String oder 2D-Liste) in ein PNG-Bild um.

    Parameter:
        matrix        : mehrzeiliger String oder 2D-Liste von Token-Strings
        ausgabe_datei : optionaler Pfad zum Speichern als PNG
        scale         : Skalierungsfaktor (Standard 1 = 9×9 px pro Zelle)
        koordinaten   : True → Spalten- und Zeilennummern als Rand ins Bild

    Rückgabe:
        PIL.Image (RGBA)

    Beispiel:
        matrix = ShellC(0)
        img    = matrix_to_png(matrix, ausgabe_datei="shellc0.png", scale=8, koordinaten=True)
    """
    img = render_matrix(matrix, ausgabe_datei=None, scale=scale)

    if koordinaten:
        from PIL import ImageDraw, ImageFont
        cell = 9 * scale
        rand = 20          # Pixel für den Rand mit Nummern
        breite  = img.width  + rand
        hoehe   = img.height + rand

        rahmen = Image.new("RGBA", (breite, hoehe), (240, 240, 240, 255))
        rahmen.paste(img, (rand, rand))
        draw = ImageDraw.Draw(rahmen)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(8, scale))
        except Exception:
            font = ImageFont.load_default()

        n_cols = img.width  // cell
        n_rows = img.height // cell

        # Spaltennummern oben
        for c in range(n_cols):
            x = rand + c * cell + cell // 2
            draw.text((x, 2), str(c), fill=(80, 80, 80, 255), font=font, anchor="mt")

        # Zeilennummern links
        for r in range(n_rows):
            y = rand + r * cell + cell // 2
            draw.text((rand - 3, y), str(r), fill=(80, 80, 80, 255), font=font, anchor="rm")

        img = rahmen

    if ausgabe_datei is not None:
        img.save(ausgabe_datei)
        print(f"Matrix-Bild gespeichert: {ausgabe_datei}")

    return img



# ---------------------------------------------------------------------------
# stack_shellc – mehrere ShellC-Matrizen untereinander
# ---------------------------------------------------------------------------

def stack_shellc(anzahl: int, zustand: int) -> list:
    """
    Stapelt mehrere ShellC-Matrizen vertikal und gibt die kombinierte
    Matrix als 2D-Liste zurück.

    Parameter:
        anzahl  : Anzahl der ShellC-Elemente untereinander (>= 1)
        zustand : 0 oder 1 – gilt für alle Elemente im Stapel

    Rückgabe:
        2D-Liste von Token-Strings (verwendbar mit matrix_to_png)

    Beispiel:
        matrix = stack_shellc(3, 0)
        img    = matrix_to_png(matrix, ausgabe_datei="stapel.png", scale=8)
    """
    if anzahl < 1:
        raise ValueError(f"anzahl muss >= 1 sein, got {anzahl}")

    einzel_matrix = ShellC(zustand)

    # String → 2D-Liste parsen
    def parse(s):
        rows = []
        for line in s.strip().splitlines():
            line = line.strip()
            if line:
                rows.append([cell.strip() for cell in line.split(",")])
        return rows

    _HEADER = [
        "2:r1H, 7:r1, 7:r1, 7:r1, 2:r1",
        "7:r2,  0,    0,    2:r1H, 9:r1H",
    ]
    _FOOTER = "2:r1HV, 7:r1, 7:r1, 2:r1V, 0"

    import copy
    einzel  = parse(einzel_matrix)
    header  = [[cell.strip() for cell in row.split(",")] for row in _HEADER]
    footer  = [cell.strip() for cell in _FOOTER.split(",")]

    gestapelt = []
    gestapelt.extend(copy.deepcopy(header))
    for _ in range(anzahl):
        gestapelt.extend(copy.deepcopy(einzel))
    gestapelt.append(copy.deepcopy(footer))
    return gestapelt



# ---------------------------------------------------------------------------
# ShellB – Stack mit verlängertem Header
# ---------------------------------------------------------------------------

def ShellB(anzahl: int, zustand: int, schalter: list = None) -> list:
    """
    Erzeugt einen ShellC-Stack (mit Header und Footer),
    verlängert die zweite Header-Zeile um anzahl*2 mal '6:r1V',
    und fügt für jedes ShellC-Element ein '8:r4HV' / '8:r1'-Paar
    an den rechten Ausgängen an, jeweils um eine Spalte weiter rechts versetzt.

    Parameter:
        anzahl   : Anzahl der ShellC-Elemente im Stack (>= 1)
        zustand  : 0 oder 1 – gilt für alle ShellC-Elemente
        schalter : Liste mit einem Wert (0 oder 1) pro ShellC.
                   0 → 8:r1 wird durch 9:r1 ersetzt
                   1 → 8:r1 bleibt (Standard)
                   None → alle ShellC bekommen 8:r1

    Rückgabe:
        2D-Liste von Token-Strings (verwendbar mit matrix_to_png)

    Beispiel:
        img = matrix_to_png(ShellB(3, 0, schalter=[0, 1, 0]), ausgabe_datei="shellb.png", scale=8)
    """
    if schalter is None:
        schalter = [1] * (anzahl * 2)
    if len(schalter) != anzahl * 2:
        raise ValueError(f"schalter muss genau {anzahl * 2} Werte haben (2 pro ShellC)")

    matrix = stack_shellc(anzahl, zustand)   # enthält bereits Header + Footer

    shellc_hoehe  = 5
    header_zeilen = 2

    # Hilfsfunktion: Zelle setzen, Zeile auffüllen wenn nötig
    def _setze(m, y, x, token):
        row = m[y]
        while len(row) <= x:
            row.append("0")
        row[x] = token

    # -----------------------------------------------------------------------
    # Schritt 1: Header-Zeile 1 – Weichen oder Geraden pro Schalter
    # -----------------------------------------------------------------------
    for i in range(anzahl * 2):
        matrix[1].append("6:r1V" if schalter[i] == 1 else "7:r1")

    # -----------------------------------------------------------------------
    # Schritt 2: Weichen-Paare oder Geraden-Marker setzen
    #   Paar A (schalter[i*2]):   Zeilen basis+0 (8:r4HV) und basis+1 (8:r1)
    #   Paar B (schalter[i*2+1]): Zeilen basis+2 (8:r4HV) und basis+3 (8:r1)
    # -----------------------------------------------------------------------
    for i in range(anzahl):
        basis    = header_zeilen + i * shellc_hoehe
        spalte_a = 5 + 2 * i   # Weichen-Spalte Paar A
        spalte_b = 6 + 2 * i   # Weichen-Spalte Paar B

        if schalter[i * 2] == 1:
            _setze(matrix, basis + 0, spalte_a, "8:r4HV")
            _setze(matrix, basis + 1, spalte_a, "8:r1")
        # schalter=0: Gerade → wird in Schritt 3 behandelt

        if schalter[i * 2 + 1] == 1:
            _setze(matrix, basis + 2, spalte_b, "8:r4HV")
            _setze(matrix, basis + 3, spalte_b, "8:r1")
        # schalter=0: Gerade → wird in Schritt 3 behandelt

    # -----------------------------------------------------------------------
    # Schritt 3: Geraden (schalter=0) – horizontale 7:r1 setzen
    #   Für Paar A (schalter=0) in ShellC i:
    #     - Eigene Ausgangszeile basis+1 in spalte_a: 7:r1
    #     - In den Weichen-Zeilen (basis+0 und basis+2) von ShellC i:
    #       für jede spätere ShellC j mit einer Weiche: 7:r1 in deren Weichen-Spalten
    #   Für Paar B analog
    # -----------------------------------------------------------------------
    gerade_zellen = set()   # (y, x) wo eine schalter=0-Gerade horizontal durchläuft

    def _setze_gerade(m, y, x, token):
        """Wie _setze, merkt sich aber zusätzlich die Zelle als Gerade-Zelle."""
        _setze(m, y, x, token)
        gerade_zellen.add((y, x))

    for i in range(anzahl):
        basis    = header_zeilen + i * shellc_hoehe
        spalte_a = 5 + 2 * i
        spalte_b = 6 + 2 * i

        if schalter[i * 2] == 0:
            # Paar A Gerade: eigene Ausgangszeilen basis+1 und basis+3
            _setze_gerade(matrix, basis + 1, spalte_a, "7:r1")
            _setze_gerade(matrix, basis + 3, spalte_a, "7:r1")
            # Gerade läuft weiter durch alle Ausgangszeilen der späteren ShellCs
            for j in range(i + 1, anzahl):
                basis_j = header_zeilen + j * shellc_hoehe
                _setze_gerade(matrix, basis_j + 1, spalte_a, "7:r1")
                _setze_gerade(matrix, basis_j + 3, spalte_a, "7:r1")
            # In den Weichen-Zeilen (basis+0, basis+2) läuft die vertikale Linie
            # der späteren ShellCs durch → 7:r2 (kein 7:r1 quer)
            for j in range(i + 1, anzahl):
                spalte_ja = 5 + 2 * j
                spalte_jb = 6 + 2 * j
                if schalter[j * 2] == 1:
                    _setze(matrix, basis + 0, spalte_ja, "7:r2")
                    _setze(matrix, basis + 2, spalte_ja, "7:r2")
                if schalter[j * 2 + 1] == 1:
                    _setze(matrix, basis + 0, spalte_jb, "7:r2")
                    _setze(matrix, basis + 2, spalte_jb, "7:r2")

        if schalter[i * 2 + 1] == 0:
            # Paar B Gerade: eigene Ausgangszeile basis+3
            _setze_gerade(matrix, basis + 3, spalte_b, "7:r1")
            # Gerade läuft weiter durch alle Ausgangszeilen der späteren ShellCs
            for j in range(i + 1, anzahl):
                basis_j = header_zeilen + j * shellc_hoehe
                _setze_gerade(matrix, basis_j + 1, spalte_b, "7:r1")
                _setze_gerade(matrix, basis_j + 3, spalte_b, "7:r1")
            # In den Weichen-Zeilen (basis+2) läuft die vertikale Linie durch → 7:r2
            for j in range(i + 1, anzahl):
                spalte_ja = 5 + 2 * j
                spalte_jb = 6 + 2 * j
                if schalter[j * 2] == 1:
                    _setze(matrix, basis + 2, spalte_ja, "7:r2")
                if schalter[j * 2 + 1] == 1:
                    _setze(matrix, basis + 2, spalte_jb, "7:r2")

    # -----------------------------------------------------------------------
    # Schritt 4: max_breite berechnen und alle Zeilen auffüllen
    # -----------------------------------------------------------------------
    max_breite = max(len(row) for row in matrix)

    for y_idx, row in enumerate(matrix):
        hat_weiche = any(c in ("8:r4HV", "8:r1", "9:r1") for c in row[5:])
        hat_gerade = (not hat_weiche) and any(c == "7:r1" for c in row[5:])

        if hat_weiche:
            pos_4hv = next((j for j in range(5, len(row)) if row[j] == "8:r4HV"), None)
            pos_r1  = next((j for j in range(5, len(row)) if row[j] in ("8:r1", "9:r1")), None)
            if pos_r1 is not None:
                # 7:r1 vor dem 8:r1 auffüllen
                for j in range(5, pos_r1):
                    if row[j] == "0":
                        row[j] = "7:r1"
                # Tail rechts vom 8:r1: nur füllen wenn Gerade-Verbindungen dort vorhanden
                del row[pos_r1 + 1:]
                while len(row) < max_breite:
                    x = len(row)
                    if (y_idx, x) in gerade_zellen:
                        row.append("7:r1")
                    else:
                        row.append("0")
            elif pos_4hv is not None:
                del row[pos_4hv + 1:]
                while len(row) < max_breite:
                    row.append("7:r1")
        elif hat_gerade:
            # Gerade: ab x=5 durchziehen bis rechts, 7:r2 nicht überschreiben
            for j in range(5, len(row)):
                if row[j] == "0":
                    row[j] = "7:r1"
                    gerade_zellen.add((y_idx, j))
                elif row[j] == "7:r1":
                    gerade_zellen.add((y_idx, j))
                # 7:r2 bleibt stehen
            while len(row) < max_breite:
                row.append("7:r1")
                gerade_zellen.add((y_idx, len(row) - 1))
        else:
            while len(row) < max_breite:
                row.append("0")

    # -----------------------------------------------------------------------
    # Schritt 5: Innere Trennzeilen mit 7:r2 auffüllen
    # Nur Spalten wo tatsächlich eine vertikale 8:r4HV-Verbindung läuft
    # -----------------------------------------------------------------------
    # Sammle alle Spalten mit 8:r4HV (= aktive Vertikalen)
    weichen_spalten = {
        x
        for row in matrix
        for x, cell in enumerate(row)
        if cell == "8:r4HV"
    }

    for i in range(anzahl - 1):
        zeile_idx     = header_zeilen + i * shellc_hoehe + (shellc_hoehe - 1)
        naechste_basis = header_zeilen + (i + 1) * shellc_hoehe
        start_spalte  = next(
            (j for j, cell in enumerate(matrix[naechste_basis]) if cell == "8:r4HV"),
            max_breite
        )
        row = matrix[zeile_idx]
        while len(row) < max_breite:
            row.append("0")
        for j in range(start_spalte, max_breite):
            if row[j] == "0" and j in weichen_spalten:
                row[j] = "7:r2"

    # -----------------------------------------------------------------------
    # Schritt 6: Vertikale Verbindungen von jedem 8:r4HV bis Zeile 1
    #            Kreuzung (1:r1) nur in echten Ausgangszeilen (haben 1:r1 oder 9:r1
    #            in Spalten 0..4). Weichen-Zeilen und Trennzeilen bleiben 7:r1/7:r2.
    # -----------------------------------------------------------------------
    # Bestimme welche Zeilen echte Ausgangszeilen sind
    ausgangszeilen = set()
    for y, row in enumerate(matrix):
        for x in range(min(5, len(row))):
            if row[x] in ("1:r1", "9:r1"):
                ausgangszeilen.add(y)
                break

    pos_4hv_liste = [
        (y, x)
        for y, row in enumerate(matrix)
        for x, cell in enumerate(row)
        if cell == "8:r4HV"
    ]
    for y_start, x in pos_4hv_liste:
        for y in range(y_start - 1, 0, -1):
            while len(matrix[y]) <= x:
                matrix[y].append("0")
            cell = matrix[y][x]
            if cell == "0":
                # Leere Zelle: vertikale Linie zieht durch → 7:r2
                matrix[y][x] = "7:r2"
            elif cell == "7:r1":
                row = matrix[y]
                pos_r1_zeile = next(
                    (j for j in range(5, len(row)) if row[j] in ("8:r1", "9:r1")),
                    None
                )
                pos_4hv_zeile = next(
                    (j for j in range(5, len(row)) if row[j] == "8:r4HV"),
                    None
                )
                if (y, x) in gerade_zellen:
                    matrix[y][x] = "1:r1"
                elif y in ausgangszeilen:
                    below = matrix[y + 1][x] if (y + 1 < len(matrix) and x < len(matrix[y + 1])) else "0"
                    if below == "8:r4HV":
                        matrix[y][x] = "7:r2"
                    else:
                        matrix[y][x] = "1:r1"
                elif pos_r1_zeile is not None and x > pos_r1_zeile:
                    matrix[y][x] = "7:r2"
                elif pos_4hv_zeile is not None and x > pos_4hv_zeile:
                    matrix[y][x] = "1:r1"
                # sonst: 7:r1 bleibt
            # 7:r2 bleibt, 1:r1 bleibt, 6:r1V bleibt

    return matrix




# ---------------------------------------------------------------------------
# ShellB_mit_Kurven – ShellB mit gestaffelten U-Kurven nach unten
# ---------------------------------------------------------------------------

def ShellB_mit_Kurven(anzahl: int, zustand: int, schalter: list = None) -> tuple:
    """
    Erweitert ShellB um 2*anzahl U-Kurven nach unten rechts.

    Pro ShellC zwei Kurven:
      Paar A: startet in der 4:r4HV-Zeile (basis+0)
      Paar B: startet zwei Zeilen tiefer (basis+2)

    Kurven gestaffelt von rechts nach links:
      k=0 (ShellC 0 Paar A) → ganz rechts, k=2n-1 → ganz links

    Rückgabe: (matrix, kurven_zeilen)
    """
    m = ShellB(anzahl, zustand, schalter=schalter)

    breite_alt  = len(m[0])
    hoehe_alt   = len(m)
    neue_breite = breite_alt + 2 * anzahl

    for row in m:
        while len(row) < neue_breite:
            row.append('0')

    def _z(y, x):
        if 0 <= y < len(m) and 0 <= x < len(m[y]):
            return m[y][x]
        return '0'

    weichen_zeilen = [y for y, row in enumerate(m) for v in row if v in ('3:r4HV', '4:r4HV')]

    # Schalter-Liste normalisieren (None → alle 1)
    schalter_norm = schalter if schalter is not None else [1] * (2 * anzahl)

    # Kurvenzeilen: schalter=1 → Weichen-Zeile (basis+0/+2)
    #               schalter=0 → Ausgangszeile (basis+1/+3), eine Zeile tiefer
    kurven_zeilen = []
    for i, wy in enumerate(weichen_zeilen):
        paar_a = wy      + (0 if schalter_norm[i * 2]     == 1 else 1)
        paar_b = wy + 2  + (0 if schalter_norm[i * 2 + 1] == 1 else 1)
        kurven_zeilen.append(paar_a)
        kurven_zeilen.append(paar_b)

    kurven = [
        (k, ky, breite_alt + (2 * anzahl - 1 - k))
        for k, ky in enumerate(kurven_zeilen)
    ]

    for k, knick_y, kurven_x in kurven:
        for x in range(breite_alt, kurven_x):
            c = _z(knick_y, x)
            if c == '0':      m[knick_y][x] = '7:r1'
            elif c == '7:r2': m[knick_y][x] = '1:r1'
        m[knick_y][kurven_x] = '2:r1'
        for y in range(knick_y + 1, hoehe_alt):
            c = _z(y, kurven_x)
            if c == '0':      m[y][kurven_x] = '7:r2'
            elif c == '7:r1': m[y][kurven_x] = '1:r1'

    return m, kurven_zeilen


# ---------------------------------------------------------------------------
# ShellB_mit_Routing – ShellB_mit_Kurven + horizontales Ausgangsrouting L/R
# ---------------------------------------------------------------------------

def ShellB_mit_Routing(anzahl: int, zustand: int,
                        schalter: list = None,
                        richtungen: list = None) -> list:
    """
    Erweitert ShellB_mit_Kurven um das horizontale Ausgangsrouting.

    Pro Ausgang k (0..2n-1) wird eine eigene neue Zeile unter ShellB angelegt.
    Die Kurven-Vertikale läuft bis in diese Zeile, biegt dort um und führt
    horizontal nach links (L) oder rechts (R) weiter.

    Parameter:
        anzahl    : Anzahl Zustände (n)
        zustand   : aktuelles Bandsymbol (0 oder 1)
        schalter  : [0/1] × 2n – Band geändert?
        richtungen: ['L'/'R'] × 2n – Bewegungsrichtung pro Ausgang
                    Reihenfolge: [(z1,sym0), (z1,sym1), (z2,sym0), ...]

    Rückgabe: erweiterte 2D-Matrix
    """
    m, kurven_zeilen = ShellB_mit_Kurven(anzahl, zustand, schalter=schalter)

    if richtungen is None:
        richtungen = ['R'] * (2 * anzahl)

    hoehe_alt     = len(m)
    breite_alt    = len(m[0])
    breite_shellb = breite_alt - 2 * anzahl

    for row in m:
        while len(row) < breite_alt:
            row.append('0')
    for _ in range(2 * anzahl):
        m.append(['0'] * breite_alt)

    def _z(y, x):
        if 0 <= y < len(m) and 0 <= x < len(m[y]):
            return m[y][x]
        return '0'

    # kurven_x: k=0 ganz rechts, k=2n-1 ganz links
    kurven_xs = [breite_shellb + (2 * anzahl - 1 - k) for k in range(2 * anzahl)]

    for k in range(2 * anzahl):
        kx       = kurven_xs[k]
        boden_y  = hoehe_alt + (2 * anzahl - 1 - k)
        richtung = richtungen[k]

        # Vertikale verlängern bis boden_y
        for y in range(hoehe_alt, boden_y):
            c = _z(y, kx)
            if c == '0':      m[y][kx] = '7:r2'
            elif c == '7:r1': m[y][kx] = '1:r1'

        # Kurve + horizontale Weiterführung
        if richtung == 'L':
            m[boden_y][kx] = '2:r1V'
            for x in range(kx - 1, -1, -1):
                c = _z(boden_y, x)
                if c == '0':      m[boden_y][x] = '7:r1'
                elif c == '7:r2': m[boden_y][x] = '1:r1'
        else:
            m[boden_y][kx] = '2:r1HV'
            for x in range(kx + 1, breite_alt):
                c = _z(boden_y, x)
                if c == '0':      m[boden_y][x] = '7:r1'
                elif c == '7:r2': m[boden_y][x] = '1:r1'

    return m


# ---------------------------------------------------------------------------
# ShellA_links – ShellB_mit_Routing + linke Eingangsleitungen
# ---------------------------------------------------------------------------

def ShellA_links(anzahl: int, zustand: int,
                 schalter: list = None,
                 richtungen: list = None) -> tuple:
    """
    Erweitert ShellB_mit_Routing um die linken Eingangsleitungen.

    Pro Zustand i (0-basiert) wird ein Block von 2n+1 Spalten links eingefügt:
      - 9:r1H  : Eingang von rechts (für Zug der von der rechten Seite kommt)
      - 2n x 9:r1V : Kreuzungspunkte für die 2n Ausgangskanäle von ShellB
    In den Eingangszeilen (y=5, 10, 15, ...) läuft zwischen den Blöcken 7:r1.

    Parameter:
        anzahl    : Anzahl Zustände (n)
        zustand   : aktuelles Bandsymbol (0 oder 1)
        schalter  : [0/1] × 2n
        richtungen: ['L'/'R'] × 2n

    Rückgabe: (matrix, eingangszeilen)
        matrix       : erweiterte 2D-Matrix
        eingangszeilen: Liste der y-Positionen der Eingänge [5, 10, 15, ...]
    """
    m = ShellB_mit_Routing(anzahl, zustand, schalter=schalter, richtungen=richtungen)

    eingangszeilen = [5 * i for i in range(1, anzahl + 1)]
    versatz        = 2 * anzahl + 1   # 1x 9:r1H + 2n x 9:r1V
    links_breite   = anzahl * versatz

    neue_breite = links_breite + len(m[0])
    for row in m:
        for _ in range(links_breite):
            row.insert(0, '0')
        while len(row) < neue_breite:
            row.append('0')

    def _s(y, x, v):
        m[y][x] = v

    for i, y in enumerate(eingangszeilen):
        x0 = i * versatz
        # 7:r1 über gesamte links_breite (Durchfahrt für andere Zustände)
        for x in range(links_breite):
            if m[y][x] == '0':
                _s(y, x, '7:r1')
        # 9:r1H + 2n x 9:r1V ab x0 (überschreibt 7:r1)
        _s(y, x0, '9:r1H')
        for k in range(2 * anzahl):
            _s(y, x0 + 1 + k, '9:r1V')

    return m, eingangszeilen


# ---------------------------------------------------------------------------
# ShellA – vollständige ShellA mit linken und rechten Eingangsleitungen
# ---------------------------------------------------------------------------

def ShellA(anzahl: int, zustand: int,
           schalter: list = None,
           richtungen: list = None) -> tuple:
    """
    Vollständige ShellA: ShellA_links + rechte Eingangsleitungen.

    Links:  n Blöcke à (2n+1) Spalten: 9:r1H + 2n×9:r1V
            (Eingang von links, Zustand 1 ganz außen)
    Rechts: n Blöcke à (2n+1) Spalten: 2:r1HV + 2n×9:r1HV
            (Eingang von rechts, Zustand n ganz außen, umgekehrte Reihenfolge)

    Parameter:
        anzahl    : Anzahl Zustände (n)
        zustand   : aktuelles Bandsymbol (0 oder 1)
        schalter  : [0/1] × 2n
        richtungen: ['L'/'R'] × 2n

    Rückgabe: (matrix, eingangszeilen)
    """
    m, eingangszeilen = ShellA_links(anzahl, zustand,
                                      schalter=schalter,
                                      richtungen=richtungen)

    versatz       = 2 * anzahl + 1
    rechts_breite = anzahl * versatz
    alte_breite   = len(m[0])
    neue_breite   = alte_breite + rechts_breite

    for row in m:
        while len(row) < neue_breite:
            row.append('0')

    def _s(y, x, v):
        m[y][x] = v

    # Rechte Eingänge: umgekehrte Reihenfolge (Zustand n zuerst = ganz innen)
    for i, y in enumerate(reversed(eingangszeilen)):
        x0 = alte_breite + i * versatz
        # 2:r1HV + 2n × 9:r1HV
        _s(y, x0, '2:r1HV')
        for k in range(2 * anzahl):
            _s(y, x0 + 1 + k, '9:r1HV')
        # 7:r1 rechts vom Block bis zum Rand
        for x in range(x0 + versatz, neue_breite):
            if m[y][x] == '0':
                _s(y, x, '7:r1')

    return m, eingangszeilen


# ---------------------------------------------------------------------------
# ShellA_mit_Bogen – ShellA + Verbindungsbögen rechts→links oben
# ---------------------------------------------------------------------------

def ShellA_mit_Bogen(anzahl: int, zustand: int,
                     schalter: list = None,
                     richtungen: list = None) -> tuple:
    """
    Vollständige ShellA mit Verbindungsbögen von den rechten Eingängen
    oben über ShellB zu den linken Eingangsweichen.

    Pro Zustand i wird ein Bogen gezeichnet:
      - Senkrecht hoch vom rechten 2:r1HV
      - Waagrecht über ShellB
      - Senkrecht runter zur linken 9:r1H des gleichen Zustands

    Parameter:
        anzahl    : Anzahl Zustände (n)
        zustand   : aktuelles Bandsymbol (0 oder 1)
        schalter  : [0/1] × 2n
        richtungen: ['L'/'R'] × 2n

    Rückgabe: (matrix, eingangszeilen)
    """
    m, eingangszeilen = ShellA(anzahl, zustand,
                                schalter=schalter,
                                richtungen=richtungen)

    versatz       = 2 * anzahl + 1
    rechts_breite = anzahl * versatz
    alte_breite   = len(m[0])  # nach ShellA bereits erweitert
    # Originale ShellB+Routing Breite rekonstruieren
    links_breite  = anzahl * versatz

    # Neu aufbauen mit Bögen – daher von vorne mit ShellA_links
    m, eingangszeilen = ShellA_links(anzahl, zustand,
                                      schalter=schalter,
                                      richtungen=richtungen)
    rechts_breite = anzahl * versatz
    alte_breite   = len(m[0])
    neue_breite   = alte_breite + rechts_breite
    for row in m:
        while len(row) < neue_breite:
            row.append('0')

    def _z(y, x):
        if 0 <= y < len(m) and 0 <= x < len(m[y]): return m[y][x]
        return '0'
    def _s(y, x, v): m[y][x] = v

    rechts_positionen = []
    for i, y in enumerate(reversed(eingangszeilen)):
        x0 = alte_breite + i * versatz
        rechts_positionen.append((y, x0))
        _s(y, x0, '2:r1HV')
        for k in range(2 * anzahl): _s(y, x0 + 1 + k, '9:r1HV')
        for x in range(x0 + versatz, neue_breite):
            if m[y][x] == '0': _s(y, x, '7:r1')

    links_positionen = [(y, i * versatz) for i, y in enumerate(eingangszeilen)]

    n_bogen_zeilen = anzahl
    for row in m:
        for _ in range(n_bogen_zeilen): row.insert(0, '0')
    for _ in range(n_bogen_zeilen): m.insert(0, ['0'] * neue_breite)

    eingangszeilen    = [y + n_bogen_zeilen for y in eingangszeilen]
    rechts_positionen = [(y + n_bogen_zeilen, x) for y,x in rechts_positionen]
    links_positionen  = [(y + n_bogen_zeilen, x) for y,x in links_positionen]

    neun_r1h = {(y, x) for y, row in enumerate(m) for x, v in enumerate(row) if v == '9:r1H'}

    lx_offset       = anzahl
    rx_vert_offset  = anzahl
    bogen_rx_offset = anzahl
    schnitt         = anzahl

    for i in range(anzahl):
        bogen_y  = n_bogen_zeilen - 1 - i
        ry, rx   = rechts_positionen[i]
        ly, lx   = links_positionen[anzahl - 1 - i]
        bogen_lx = lx + lx_offset
        rx_vert  = rx + rx_vert_offset
        bogen_rx = rx + bogen_rx_offset

        # Linke Kurve + Vertikale
        m[bogen_y][bogen_lx] = '2:r1H'
        for y in range(bogen_y + 1, ly):
            c = _z(y, bogen_lx)
            if (y, bogen_lx) in neun_r1h:
                m[y][bogen_lx] = '1:r1'
            elif c == '0':      m[y][bogen_lx] = '7:r2'
            elif c == '7:r1':   m[y][bogen_lx] = '1:r1'

        # Rechte Vertikale
        for y in range(ry - 1, bogen_y, -1):
            c = _z(y, rx_vert)
            if c == '0':      m[y][rx_vert] = '7:r2'
            elif c == '7:r1': m[y][rx_vert] = '1:r1'

        # Kurve oben rechts
        m[bogen_y][bogen_rx] = '2:r1'

        # Waagrecht
        for x in range(bogen_rx - 1, bogen_lx, -1):
            c = _z(bogen_y, x)
            if c == '0':      m[bogen_y][x] = '7:r1'
            elif c == '7:r2': m[bogen_y][x] = '1:r1'

    m = [row[schnitt:] for row in m]
    return m, eingangszeilen


# ---------------------------------------------------------------------------
# ShellA_verbunden – ShellA_mit_Bogen + Verbindung der ShellB-Ausgänge
# ---------------------------------------------------------------------------

def ShellA_verbunden(anzahl: int, zustand: int,
                     schalter: list = None,
                     richtungen: list = None,
                     zustaende: list = None,
                     transitionen_map: dict = None,
                     halt: list = None) -> tuple:
    """
    Vollständige ShellA mit verbundenen ShellB-Ausgängen.

    Die 2n Routing-Ausgänge von ShellB werden über vertikale und horizontale
    Leitungen mit den 9:r1V/9:r1HV-Kreuzungspunkten der Eingangsweichen verbunden.

    Slot-Indizes (generisch für beliebiges n):
      L-Ausgang k (zi=k//2, sym=k%2): slot = (n-1-zi)*2 + sym  in neun_v[ez[zi]]
      R-Ausgang k:                     slot = zi*2               in neun_hv[ez[zi]]

    Verbindungszeile:
      L-Ausgang: ry+1 (eine Zeile unter dem Routing-Ausgang)
      R-Ausgang: ry-1 (eine Zeile über dem Routing-Ausgang)

    Parameter:
        anzahl          : Anzahl Zustände (n)
        zustand         : aktuelles Bandsymbol (0 oder 1)
        schalter        : [0/1] × 2n
        richtungen      : ['L'/'R'] × 2n
        zustaende       : Liste der Zustands-IDs (für Haltezustand-Erkennung)
        transitionen_map: dict (zustand, symbol) → Transition (für Haltezustand-Check)

    Rückgabe: (matrix, eingangszeilen)
    """
    m, eingangszeilen = ShellA_mit_Bogen(anzahl, zustand,
                                          schalter=schalter,
                                          richtungen=richtungen)
    n = anzahl

    # 9:r1V (links) und 9:r1HV (rechts) pro Eingangszeile
    neun_v  = {y: sorted([x for x,v in enumerate(row) if v == '9:r1V'])
               for y, row in enumerate(m) if any(v == '9:r1V' for v in row)}
    neun_hv = {}
    for y, row in enumerate(m):
        cols = sorted([x for x, v in enumerate(row) if v == '9:r1HV'])
        if cols:
            neun_hv[y] = cols

    # Die 2n Routing-Ausgänge (letzte 2n 2:r1V/2:r1HV unterhalb der Eingangszeilen)
    routing = [(y, x, v)
               for y, row in enumerate(m)
               for x, v in enumerate(row)
               if v in ('2:r1V', '2:r1HV') and y > eingangszeilen[-1]][-2*n:]

    def _z(y, x):
        if 0 <= y < len(m) and 0 <= x < len(m[y]): return m[y][x]
        return '0'
    def _s(y, x, v):
        # Matrix nach unten erweitern falls nötig
        while y >= len(m):
            m.append(['0'] * len(m[0]))
        while x >= len(m[y]):
            m[y].append('0')
        m[y][x] = v

    # routing umdrehen, damit k=(zi,sym) dem physischen Ausgang entspricht
    # (k=0=(z1,f) am rechtesten Ausgang, k=2n-1=(zn,t) am linkesten).
    routing = list(reversed(routing))

    # Verbindungsregel (von Andre): für Transition (qz,gelesen,ziel,geschr,richtung)
    # geht die Linie aus ShellC von qz (Ausgang=geschr) zur Sprungweiche an
    # Position (qz,gelesen) auf der Zustandsleitung von ziel, Seite=richtung.
    # Positions-Kodierung auf der Zielleitung von links: 1f 1t 2f 2t 3f 3t.

    # Zwei-Phasen-Verlegung (verhindert Fehlrouting durch Kollisionen):
    #   Phase 1: horizontale Linien auf der jeweiligen Kurven-Zeile bis zur Zielspalte
    #   Phase 2: vertikale Linien von dort hoch zur Zielzustands-Leitung
    # Kreuzt eine neue Linie eine bestehende, wird ein Kreuz (1:r1) gesetzt.

    verbindungen = []  # (ry, rx, ziel_y, vx, richt, sym, halt)
    for k, (ry, rx, rv) in enumerate(routing):
        zi  = k // 2
        sym = k % 2

        # Transition nachschlagen
        if zustaende is not None and transitionen_map is not None:
            z = zustaende[zi]
            t = transitionen_map.get((z, sym))
            halt = (t is None or t.neuer_zustand not in zustaende)
        else:
            t = None
            halt = False

        if halt:
            # Halt-Slot: Richtung der vorhandenen L/R-Kurve merken (rv),
            # damit der Puffer in Fahrtrichtung gesetzt werden kann.
            halt_richt = 'L' if rv == '2:r1V' else 'R'
            verbindungen.append((ry, rx, None, None, halt_richt, sym, True))
            continue

        if t is not None:
            ziel_idx = zustaende.index(t.neuer_zustand)
            richt = t.richtung
        else:
            ziel_idx = zi
            richt = richtungen[k] if richtungen else ('L' if rv == '2:r1HV' else 'R')

        ziel_y = eingangszeilen[ziel_idx]
        pos_links = zi * 2 + sym
        if richt == 'L':
            if ziel_y not in neun_v or pos_links >= len(neun_v[ziel_y]):
                continue
            vx = neun_v[ziel_y][pos_links]
        else:
            idx = (2 * n - 1) - pos_links
            if ziel_y not in neun_hv or idx < 0 or idx >= len(neun_hv[ziel_y]):
                continue
            vx = neun_hv[ziel_y][idx]
        verbindungen.append((ry, rx, ziel_y, vx, richt, sym, False))

    # --- Phase 1: horizontale Linien auf der Kurven-Zeile bis VOR die Zielspalte ---
    def kreuz_h(y, x):
        # Horizontale Linie legen; bestehende Vertikale -> Kreuz
        c = _z(y, x)
        if c == '0':                 _s(y, x, '7:r1')
        elif c == '7:r2':            _s(y, x, '1:r1')   # kreuzt Vertikale
        # 7:r1/1:r1/Weichen: bereits horizontal befahrbar, nichts tun

    for (ry, rx, ziel_y, vx, richt, sym, halt) in verbindungen:
        if halt:
            # Halt: direkt nach der L/R-Kurve den Endpuffer setzen
            # (keine horizontale Linie, kein toter Strang).
            if richt == 'L':
                _s(ry, rx - 1, '11:r3')   # Puffer links der Kurve
            else:
                _s(ry, rx + 1, '11:r1')   # Puffer rechts der Kurve
            continue
        # horizontale Strecke von rx bis VOR vx (Zielspalte bleibt frei für Kurve)
        if vx > rx:
            for x in range(rx + 1, vx):
                kreuz_h(ry, x)
        elif vx < rx:
            for x in range(rx - 1, vx, -1):
                kreuz_h(ry, x)

    # Endstück: Kurve nach oben an der Zielspalte.
    # Seite R (von links angefahren) -> 2:r1V (lenkt nach N);
    # Seite L (von rechts angefahren) -> 2:r1HV (lenkt nach N).
    for (ry, rx, ziel_y, vx, richt, sym, halt) in verbindungen:
        if halt:
            continue
        _s(ry, vx, '2:r1V' if richt == 'R' else '2:r1HV')

    # --- Phase 2: vertikale Linien von der Kurven-Zeile hoch zur Zielleitung ---
    def kreuz_v(y, x):
        c = _z(y, x)
        if c == '0':                 _s(y, x, '7:r2')
        elif c == '7:r1':            _s(y, x, '1:r1')   # kreuzt Horizontale
        elif c in ('9:r1V', '9:r1HV'):  pass            # Zielweiche: stehen lassen

    for (ry, rx, ziel_y, vx, richt, sym, halt) in verbindungen:
        if halt:
            continue
        # vertikale Strecke von ry-1 hoch bis ziel_y (exklusiv, Weiche bleibt)
        for y in range(ry - 1, ziel_y, -1):
            kreuz_v(y, vx)

    # --- Cleanup: verwaiste Routing-Tails und Kreuzungen bereinigen ---
    # Zustandsleitungen (eingangszeilen) müssen links aus der ShellA herauslaufen
    # und werden daher vom Cleanup ausgenommen.
    cleanup_start_y = 5 * n + 3  # unterhalb der letzten ShellB-Hauptzeile
    geschuetzt = set(eingangszeilen)
    changed = True
    while changed:
        changed = False
        for y in range(cleanup_start_y, len(m)):
            if y in geschuetzt:
                continue  # Zustandsleitung nicht antasten
            w = len(m[y])
            # 7:r1 ohne horizontale Anbindung links → 0
            for x in range(w):
                if m[y][x] == '7:r1':
                    has_h_left = False
                    for xl in range(x - 1, -1, -1):
                        if m[y][xl] in ('0', '7:r2'):
                            continue
                        has_h_left = True
                        break
                    if not has_h_left:
                        m[y][x] = '0'
                        changed = True
            # 1:r1 Kreuzungen ohne Horizontalverkehr → 7:r2
            for x in range(1, w - 1):
                if m[y][x] == '1:r1':
                    left = m[y][x - 1]
                    right = m[y][x + 1] if x + 1 < w else '0'
                    if left in ('0', '7:r2') or right in ('0', '7:r2'):
                        m[y][x] = '7:r2'
                        changed = True

    # Alle Zeilen auf einheitliche Breite auffüllen
    max_w = max(len(row) for row in m)
    for row in m:
        while len(row) < max_w:
            row.append('0')

    return m, eingangszeilen


def _setze_halt_puffer(m, eingangszeilen, halt_slots,
                       anzahl, schalter, richtungen):
    """
    Ersetzt für jeden Halt-Slot die Abbiegekurve durch den Endpuffer und
    entfernt den toten Verbindungsstrang, der früher zur Zielzustands-Leitung
    führte.

    Da alle ShellAs strukturell identisch sind, sitzt der Halt-Puffer in JEDER
    ShellA an derselben Stelle. Position und toter Strang werden per Simulation
    auf einer Referenz-ShellA (mit passendem Symbol, ohne Halt) ermittelt:
      - Der Zug fährt von der Eingangszeile des Slot-Zustands los.
      - Die letzte S->W/O-Abbiegung ist die Stelle für den Puffer.
      - Alles NACH dieser Abbiegung ist der tote Strang.
    Tote Zellen, die KEIN anderer (Nicht-Halt-)Pfad mitbenutzt, werden entfernt;
    geteilte Zellen (Kreuzungen, Zustandsleitungen) bleiben erhalten.
    """
    # 1) Alle Zellen sammeln, die Nicht-Halt-Pfade benutzen (pro Symbol)
    benutzt_andere = set()
    for symbol in (0, 1):
        m_ref, ez_ref = ShellA_verbunden(anzahl, symbol,
                                         schalter=schalter, richtungen=richtungen)
        for zi in range(anzahl):
            k = zi * 2 + symbol
            if k < len(halt_slots) and halt_slots[k]:
                continue  # Halt-Pfad nicht mitzählen
            p = TrainSimulation(m_ref).fahre(ez_ref[zi], 0, 'O', max_schritte=1000)
            for (yy, xx, _f) in p:
                benutzt_andere.add((yy, xx))

    # 2) Pro Halt-Slot: Puffer setzen und toten Strang entfernen
    for k, ist_halt in enumerate(halt_slots):
        if not ist_halt:
            continue
        zi, sym = k // 2, k % 2

        m_ref, ez_ref = ShellA_verbunden(anzahl, sym,
                                         schalter=schalter, richtungen=richtungen)
        pfad = TrainSimulation(m_ref).fahre(ez_ref[zi], 0, 'O', max_schritte=1000)

        # Letzte S->W/O-Abbiegung finden (Index der Kurve)
        abb_idx = None
        for i in range(1, len(pfad)):
            if pfad[i - 1][2] == 'S' and pfad[i][2] in ('W', 'O'):
                abb_idx = i - 1
        if abb_idx is None:
            continue

        ay, ax = pfad[abb_idx][0], pfad[abb_idx][1]
        # Puffer an die Abbiegekurve setzen (vertikaler Strang von oben, Anschlag unten)
        if 0 <= ay < len(m) and 0 <= ax < len(m[ay]):
            m[ay][ax] = '11:r2'

        # Toten Strang (alles nach der Abbiegung) entfernen, sofern exklusiv
        for (ty, tx, _f) in pfad[abb_idx + 1:]:
            if (ty, tx) in benutzt_andere:
                continue  # von anderem Pfad genutzt -> behalten
            if 0 <= ty < len(m) and 0 <= tx < len(m[ty]):
                m[ty][tx] = '0'

        # Verwaiste Kreuzungen entlang des toten Strangs bereinigen:
        # Eine 1:r1-Kreuzung, die durch das Entfernen nur noch EINE Achse hat,
        # wird zur reinen Durchgangsleitung (horizontal 7:r1 / vertikal 7:r2).
        for (ty, tx, _f) in pfad[abb_idx:]:
            for (cy, cx) in ((ty, tx),
                             (ty, tx - 1), (ty, tx + 1),
                             (ty - 1, tx), (ty + 1, tx)):
                if not (0 <= cy < len(m) and 0 <= cx < len(m[cy])):
                    continue
                if m[cy][cx] != '1:r1':
                    continue
                left  = m[cy][cx - 1] if cx > 0 else '0'
                right = m[cy][cx + 1] if cx + 1 < len(m[cy]) else '0'
                up    = m[cy - 1][cx] if cy > 0 else '0'
                down  = m[cy + 1][cx] if cy + 1 < len(m) else '0'
                h_belegt = left not in ('0', '7:r2') or right not in ('0', '7:r2')
                v_belegt = up not in ('0', '7:r1') or down not in ('0', '7:r1')
                if h_belegt and not v_belegt:
                    m[cy][cx] = '7:r1'   # nur noch horizontal
                elif v_belegt and not h_belegt:
                    m[cy][cx] = '7:r2'   # nur noch vertikal

    return m

# ---------------------------------------------------------------------------
# print_matrix – Matrix übersichtlich ausgeben
# ---------------------------------------------------------------------------

def print_matrix(matrix, titel: str = None):
    """
    Gibt eine Matrix übersichtlich als Tabelle auf der Konsole aus.

    Parameter:
        matrix : 2D-Liste oder mehrzeiliger String
        titel  : optionaler Titeltext
    """
    # String → 2D-Liste
    if isinstance(matrix, str):
        rows = []
        for line in matrix.strip().splitlines():
            line = line.strip()
            if line:
                rows.append([c.strip() for c in line.split(",")])
        matrix = rows

    if titel:
        print(f"\n=== {titel} ===")

    # Spaltenbreiten ermitteln
    max_cols = max(len(row) for row in matrix)
    col_w = [0] * max_cols
    for row in matrix:
        for j, cell in enumerate(row):
            col_w[j] = max(col_w[j], len(cell))

    # Trennlinie
    sep = "+" + "+".join("-" * (w + 2) for w in col_w) + "+"

    print(sep)
    for i, row in enumerate(matrix):
        # Zeile mit Leerzeilen auffüllen falls kürzer
        padded = row + [""] * (max_cols - len(row))
        line = "|" + "|".join(f" {cell:<{col_w[j]}} " for j, cell in enumerate(padded)) + "|"
        print(f"{i:2d} {line}")
        print(f"   {sep}")



# ---------------------------------------------------------------------------
# Turing-Maschinen Parser
# ---------------------------------------------------------------------------

class Transition:
    """Eine einzelne Transition der Turingmaschine."""
    def __init__(self, zustand, symbol, neuer_zustand, schreib_symbol, richtung):
        self.zustand       = zustand        # int: aktueller Zustand
        self.symbol        = symbol         # int: gelesenes Symbol (0=f, 1=t)
        self.neuer_zustand = neuer_zustand  # int: Folgezustand
        self.schreib       = schreib_symbol # int: zu schreibendes Symbol (0=f, 1=t)
        self.richtung      = richtung       # str: 'L' oder 'R'

    def __repr__(self):
        sym  = 't' if self.symbol  == 1 else 'f'
        schr = 't' if self.schreib == 1 else 'f'
        return f"({self.zustand},{sym},{self.neuer_zustand},{schr},{self.richtung})"


class TuringMaschine:
    """Parsed eine .tm Datei und stellt die Daten bereit."""

    def __init__(self, datei: str = None, text: str = None):
        self.start_zustand  = None
        self.start_position = None
        self.band           = []
        self.transitionen   = []   # Liste von Transition
        self._zustaende     = None

        if datei:
            with open(datei, 'r') as f:
                text = f.read()
        if text:
            self._parse(text)

    def _parse(self, text: str):
        import re
        lines = [l.strip() for l in text.splitlines()]
        for line in lines:
            if not line or line.startswith('#'):
                continue

            # Startposition: (zustand,position)
            m = re.fullmatch(r'\((\d+),(\d+)\)', line)
            if m:
                self.start_zustand  = int(m.group(1))
                self.start_position = int(m.group(2))
                continue

            # Band: (tt), (ff), (tft), etc.
            m = re.fullmatch(r'\(([tf]+)\)', line)
            if m:
                self.band = [1 if c == 't' else 0 for c in m.group(1)]
                continue

            # Transitionen: beliebig viele pro Zeile
            for m in re.finditer(r'\((\d+),([tf]),(\d+),([tf]),([LR])\)', line):
                self.transitionen.append(Transition(
                    zustand       = int(m.group(1)),
                    symbol        = 1 if m.group(2) == 't' else 0,
                    neuer_zustand = int(m.group(3)),
                    schreib_symbol= 1 if m.group(4) == 't' else 0,
                    richtung      = m.group(5),
                ))

    @property
    def zustaende(self):
        """Alle Zustände mit ausgehenden Transitionen (sortiert)."""
        if self._zustaende is None:
            self._zustaende = sorted(set(t.zustand for t in self.transitionen))
        return self._zustaende

    @property
    def n(self):
        """Anzahl Zustände mit ausgehenden Transitionen."""
        return len(self.zustaende)

    def get_transition(self, zustand: int, symbol: int):
        """Gibt die Transition für (zustand, symbol) zurück, oder None."""
        for t in self.transitionen:
            if t.zustand == zustand and t.symbol == symbol:
                return t
        return None

    def schalter_fuer_shellb(self):
        """
        Gibt die Schalter-Liste für ShellB zurück.
        Pro Zustand 2 Schalter: [schalter_sym0, schalter_sym1]
        Schalter = 1 wenn Band geändert wird (gelesen != geschrieben)
        Schalter = 0 wenn Band nicht geändert wird (gelesen == geschrieben)
        Kein Übergang → Schalter = 0
        """
        schalter = []
        for z in self.zustaende:
            for sym in [0, 1]:
                t = self.get_transition(z, sym)
                if t is None:
                    schalter.append(0)
                else:
                    schalter.append(1 if t.symbol != t.schreib else 0)
        return schalter

    def richtungen_fuer_shellb(self):
        """
        Gibt die Richtungs-Liste für ShellB zurück.
        Pro Zustand 2 Richtungen: [richtung_sym0, richtung_sym1]
        Kein Übergang → 'L' als Default.
        """
        richtungen = []
        for z in self.zustaende:
            for sym in [0, 1]:
                t = self.get_transition(z, sym)
                richtungen.append(t.richtung if t is not None else 'L')
        return richtungen

    def halt_fuer_shellb(self):
        """
        Gibt pro Slot True zurück, wenn der Übergang in einen Haltezustand führt
        (Ziel-Zustand hat selbst keine ausgehenden Transitionen / existiert nicht
        in self.zustaende). Reihenfolge wie schalter/richtungen: pro Zustand
        [sym0, sym1].
        """
        halt = []
        for z in self.zustaende:
            for sym in [0, 1]:
                t = self.get_transition(z, sym)
                if t is None:
                    halt.append(False)
                else:
                    halt.append(t.neuer_zustand not in self.zustaende)
        return halt

    def __repr__(self):
        return (f"TuringMaschine(start=({self.start_zustand},{self.start_position}), "
                f"band={self.band}, n={self.n}, "
                f"zustaende={self.zustaende}, "
                f"transitionen={self.transitionen})")


# ---------------------------------------------------------------------------
# kaskadiere_TM – mehrere ShellA horizontal zur kompletten TM verbinden
# ---------------------------------------------------------------------------
def kaskadiere_TM(tm, spalt: int = 3) -> tuple:
    """
    Erzeugt das vollständige TM-Layout: pro Bandzelle eine ShellA,
    horizontal nebeneinander, verbunden durch n gerade Leitungen.

    Jede ShellA speichert das Bandsymbol ihrer Zelle (tm.band[i]).
    Alle ShellA sind strukturell identisch (gleiche Schalter/Richtungen),
    nur das gespeicherte Symbol unterscheidet sich.

    Verbindung: Eingangszeile i (Zustand i) der linken ShellA wird auf
    gleicher Höhe mit Eingangszeile i der rechten ShellA verbunden
    (n gerade horizontale Leitungen pro Spalt).

    Vor der ersten ShellA wird zusätzlich ein Spalt eingefügt, damit das
    Startsymbol auch bei bandPos=0 davor platziert werden kann.

    Startsymbol (10:r1): wird im Spalt LINKS von ShellA[start_position]
    auf der Eingangszeile des Startzustands (start_zustand) gesetzt.

    Parameter:
        tm    : TuringMaschine
        spalt : Anzahl Spalten zwischen benachbarten ShellA (und vor der ersten)

    Rückgabe: (matrix, info)
    """
    n = tm.n
    s = tm.schalter_fuer_shellb()
    r = tm.richtungen_fuer_shellb()
    h = tm.halt_fuer_shellb()
    tmap = {(t.zustand, t.symbol): t for t in tm.transitionen}

    # Eine ShellA pro Bandzelle erzeugen
    shells = []
    for symbol in tm.band:
        m_a, ez = ShellA_verbunden(n, symbol, schalter=s, richtungen=r, halt=h,
                                   zustaende=tm.zustaende, transitionen_map=tmap)
        shells.append(m_a)

    if not shells:
        return [], {}

    hoehe       = len(shells[0])
    a_breite    = len(shells[0][0])
    eingangszeilen = ez  # identisch für alle (gleiche Struktur)

    # Gesamtbreite: führender Spalt + k ShellA + (k-1) Spalte
    k = len(shells)
    gesamt_breite = spalt + k * a_breite + (k - 1) * spalt

    # Leere Gesamtmatrix
    m = [['0'] * gesamt_breite for _ in range(hoehe)]

    # ShellA einsetzen (alle um den führenden Spalt nach rechts verschoben)
    x_offsets = []
    for idx, shell in enumerate(shells):
        x0 = spalt + idx * (a_breite + spalt)
        x_offsets.append(x0)
        for y in range(hoehe):
            for x in range(a_breite):
                if shell[y][x] != '0':
                    m[y][x0 + x] = shell[y][x]

    # Verbindungsleitungen in den Spalten zwischen den ShellA
    for idx in range(k - 1):
        x_gap_start = x_offsets[idx] + a_breite       # erste Spalt-Spalte
        x_gap_end   = x_offsets[idx + 1]              # exklusiv
        for ey in eingangszeilen:                     # n gerade Leitungen
            for x in range(x_gap_start, x_gap_end):
                m[ey][x] = '7:r1'

    # Startsymbol im Spalt links von ShellA[start_position]
    start_pos = tm.start_position if tm.start_position is not None else 0
    start_z   = tm.start_zustand   if tm.start_zustand   is not None else tm.zustaende[0]
    if 0 <= start_pos < k and start_z in tm.zustaende:
        zi = tm.zustaende.index(start_z)         # Index des Startzustands
        start_y = eingangszeilen[zi]
        # x-Bereich des Spalts links von ShellA[start_pos]
        gap_start = x_offsets[start_pos] - spalt
        gap_end   = x_offsets[start_pos]
        # gerade Leitung im Spalt füllen, Symbol in die Mitte
        for x in range(gap_start, gap_end):
            m[start_y][x] = '7:r1'
        mitte = (gap_start + gap_end) // 2
        m[start_y][mitte] = '10:r1'

    info = {
        'shellA_breite':  a_breite,
        'eingangszeilen': eingangszeilen,
        'spalt':          spalt,
        'x_offsets':      x_offsets,
        'start_position': start_pos,
        'start_zustand':  start_z,
    }
    return m, info


# ===========================================================================
# ZUG-SIMULATION
# ===========================================================================
# Eine "grüne Kugel" (der Zug) fährt von Matrixzelle zu Matrixzelle über das
# Schienen-Gitter. Jedes Tile lenkt den Zug entsprechend seiner Geometrie und
# (bei Weichen) seinem Schaltzustand ab. Lazy- und FlipFlop-Weichen ändern
# ihren Zustand während der Fahrt – das ist die Turingmaschinen-Berechnung.
#
# Richtungs-Konvention (Bild-Koordinaten, y wächst nach UNTEN):
#     N=oben (dy=-1), S=unten (dy=+1), W=links (dx=-1), O=rechts (dx=+1)
#
# Weichen-Semantik (aus TMTrain.odt), Grundstellung r1:
#     F = W(links), S1 = N(oben), S2 = O(rechts)
#     Variante 1 (xxx1): Strecke F<->S1 aktiv (Diagonale)
#     Variante 2 (xxx2): Strecke F<->S2 aktiv (Horizontale)
#     LAZY:     F->S folgt Stellung. S->F stellt um (S1->Var1, S2->Var2).
#     SPRUNG:   feste Stellung, ändert sich nie.
#     FLIPFLOP: nur von F benutzt. F->S folgt Stellung, dann Toggle.
# ---------------------------------------------------------------------------

GEGEN = {'N': 'S', 'S': 'N', 'W': 'O', 'O': 'W'}
DELTA = {'N': (0, -1), 'S': (0, 1), 'W': (-1, 0), 'O': (1, 0)}  # (dx, dy)

_CW = ['N', 'O', 'S', 'W']               # Reihenfolge im Uhrzeigersinn
_DREHEN_CW = {1: 0, 2: 1, 3: 2, 4: 3}    # drehen-Wert -> Anzahl 90°-CW-Schritte


def _rot_cw(d, times):
    return _CW[(_CW.index(d) + times) % 4]


def _flip_h_dir(d):
    return {'O': 'W', 'W': 'O', 'N': 'N', 'S': 'S'}[d]


def _flip_v_dir(d):
    return {'N': 'S', 'S': 'N', 'O': 'O', 'W': 'W'}[d]


def lokal_zu_welt(d, drehen, h_flip, v_flip):
    """Lokale Richtung (r1) -> Welt-Richtung nach getElement-Transformation."""
    d = _rot_cw(d, _DREHEN_CW[drehen])
    if h_flip:
        d = _flip_h_dir(d)
    if v_flip:
        d = _flip_v_dir(d)
    return d


def welt_zu_lokal(d, drehen, h_flip, v_flip):
    """Welt-Richtung -> lokale Richtung (Umkehrung von lokal_zu_welt)."""
    if v_flip:
        d = _flip_v_dir(d)
    if h_flip:
        d = _flip_h_dir(d)
    d = _rot_cw(d, (-_DREHEN_CW[drehen]) % 4)
    return d


# Tile-Typen
PORT_F, PORT_S1, PORT_S2 = 'W', 'N', 'O'   # Weichen-Ports in lokalen Richtungen
WEICHEN_TYP = {3: 'flipflop', 4: 'flipflop',
               5: 'lazy',     6: 'lazy',
               8: 'sprung',   9: 'sprung'}
WEICHEN_VAR = {3: 1, 4: 2, 5: 1, 6: 2, 8: 1, 9: 2}  # 1=Diag aktiv, 2=Horiz aktiv

# Umkehrung: (Typ, Variante) -> ElementNr  (zum Aktualisieren des Tile-Symbols)
TYP_VAR_ZU_NR = {
    ('flipflop', 1): 3, ('flipflop', 2): 4,
    ('lazy', 1): 5,     ('lazy', 2): 6,
    ('sprung', 1): 8,   ('sprung', 2): 9,
}


def _token_mit_nr(alter_token, neue_nr):
    """Ersetzt nur die ElementNr im Token, behält Drehung/Flips: '4:r4HV' -> '3:r4HV'."""
    rest = alter_token.split(':', 1)[1]
    return f"{neue_nr}:{rest}"


class TrainSimulation:
    """Simuliert einen Zug, der über das Tile-Gitter fährt."""

    def __init__(self, matrix):
        self.matrix = [list(row) for row in matrix]
        self.hoehe = len(self.matrix)
        self.breite = len(self.matrix[0]) if self.matrix else 0
        self.switch_state = {}
        for y in range(self.hoehe):
            for x in range(self.breite):
                p = parse_zelle(self.matrix[y][x])
                if p and p[0] in WEICHEN_TYP:
                    self.switch_state[(y, x)] = WEICHEN_VAR[p[0]]

    def _tile(self, y, x):
        if 0 <= y < self.hoehe and 0 <= x < self.breite:
            return parse_zelle(self.matrix[y][x])
        return None

    def schritt(self, y, x, fahrt):
        """
        Zug betritt Tile (y,x) fahrend in Richtung 'fahrt'.
        Gibt (neue_fahrt, beschreibung) oder (None, grund) zurück.
        Modifiziert ggf. switch_state.
        """
        p = self._tile(y, x)
        if p is None:
            return None, 'leeres Feld / außerhalb'

        elem_nr, drehen, h_flip, v_flip = p
        entry_welt = GEGEN[fahrt]
        entry_lok = welt_zu_lokal(entry_welt, drehen, h_flip, v_flip)

        # LINIE / START: gerade durch (W<->O)
        if elem_nr in (7, 10):
            exit_lok = {'W': 'O', 'O': 'W'}.get(entry_lok)
            if exit_lok is None:
                return None, f'Linie: ungültige Einfahrt {entry_lok}'
            return lokal_zu_welt(exit_lok, drehen, h_flip, v_flip), 'Linie'

        # KURVE: W<->S (lokal)
        if elem_nr == 2:
            exit_lok = {'W': 'S', 'S': 'W'}.get(entry_lok)
            if exit_lok is None:
                return None, f'Kurve: ungültige Einfahrt {entry_lok}'
            return lokal_zu_welt(exit_lok, drehen, h_flip, v_flip), 'Kurve'

        # KREUZUNG: W<->O und N<->S unabhängig
        if elem_nr == 1:
            exit_lok = {'W': 'O', 'O': 'W', 'N': 'S', 'S': 'N'}.get(entry_lok)
            if exit_lok is None:
                return None, f'Kreuzung: ungültige Einfahrt {entry_lok}'
            return lokal_zu_welt(exit_lok, drehen, h_flip, v_flip), 'Kreuzung'

        # WEICHEN
        if elem_nr in WEICHEN_TYP:
            typ = WEICHEN_TYP[elem_nr]
            var = self.switch_state[(y, x)]

            if entry_lok == PORT_F:
                port = 'F'
            elif entry_lok == PORT_S1:
                port = 'S1'
            elif entry_lok == PORT_S2:
                port = 'S2'
            else:
                return None, f'Weiche: ungültige Einfahrt {entry_lok}'

            if typ == 'sprung':
                exit_lok = (PORT_S1 if var == 1 else PORT_S2) if port == 'F' else PORT_F
                return lokal_zu_welt(exit_lok, drehen, h_flip, v_flip), \
                    f'Sprung(Var{var}) {port}->{exit_lok}'

            if typ == 'lazy':
                if port == 'F':
                    exit_lok = PORT_S1 if var == 1 else PORT_S2
                    return lokal_zu_welt(exit_lok, drehen, h_flip, v_flip), \
                        f'Lazy F->{exit_lok}(Var{var})'
                else:
                    self.switch_state[(y, x)] = 1 if port == 'S1' else 2
                    return lokal_zu_welt(PORT_F, drehen, h_flip, v_flip), \
                        f'Lazy {port}->F(stellt Var{self.switch_state[(y,x)]})'

            if typ == 'flipflop':
                if port == 'F':
                    exit_lok = PORT_S1 if var == 1 else PORT_S2
                    self.switch_state[(y, x)] = 2 if var == 1 else 1
                    return lokal_zu_welt(exit_lok, drehen, h_flip, v_flip), \
                        f'FlipFlop F->{exit_lok}(jetzt Var{self.switch_state[(y,x)]})'
                else:
                    return lokal_zu_welt(PORT_F, drehen, h_flip, v_flip), \
                        f'FlipFlop {port}->F'

        return None, f'unbekanntes Element {elem_nr}'

    def fahre(self, start_y, start_x, start_fahrt, max_schritte=10000,
              verbose=False, mit_zustand=False):
        """
        Lässt den Zug fahren, bis er das Gitter verlässt oder max_schritte erreicht.

        Gibt die Liste [(y, x, fahrt), ...] zurück.
        Bei mit_zustand=True zusätzlich eine parallele Liste von Schaltzustands-
        Schnappschüssen (dict-Kopie NACH dem jeweiligen Schritt).
        """
        pfad = []
        zustaende = []
        y, x, fahrt = start_y, start_x, start_fahrt
        for schritt_nr in range(max_schritte):
            if not (0 <= y < self.hoehe and 0 <= x < self.breite):
                if verbose:
                    print(f"  STOPP: außerhalb bei ({y},{x})")
                break
            neue_fahrt, beschr = self.schritt(y, x, fahrt)
            pfad.append((y, x, fahrt))
            if mit_zustand:
                zustaende.append(dict(self.switch_state))
            if verbose:
                print(f"  [{schritt_nr:3d}] ({y:2d},{x:2d}) "
                      f"{self.matrix[y][x]:8s} {fahrt} -> {beschr}")
            if neue_fahrt is None:
                if verbose:
                    print(f"  STOPP: {beschr}")
                break
            dx, dy = DELTA[neue_fahrt]
            y, x, fahrt = y + dy, x + dx, neue_fahrt
        if mit_zustand:
            return pfad, zustaende
        return pfad


def finde_start(matrix):
    """Sucht das Startsymbol (10:...) und gibt (y, x) zurück, oder None."""
    for y, row in enumerate(matrix):
        for x, tok in enumerate(row):
            if tok.startswith('10:'):
                return (y, x)
    return None


def erzeuge_einzelbilder(matrix, pfad, ausgabe_prefix, anzahl_schritte, scale=10,
                         zustaende=None):
    """
    Erzeugt einzelne PNG-Bilder, eines pro Schritt (ohne Spur), in der
    angegebenen Skalierung. Dateien: <prefix>_step_000.png, _001.png, ...

    Wenn 'zustaende' (Liste von switch_state-Schnappschüssen pro Schritt)
    übergeben wird, zeigen die Weichen-Symbole ihre AKTUELLE Stellung
    (FlipFlop/Lazy springen im Bild um).

    Rückgabe: Liste der erzeugten Dateinamen
    """
    cell = 9 * scale
    kugel_r = max(3, scale)

    n = min(anzahl_schritte, len(pfad))
    dateien = []
    breite = max(3, len(str(max(n - 1, 0))))

    # Basis-Bild nur einmal rendern, wenn keine Zustandsänderung visualisiert wird
    base_static = None
    if zustaende is None:
        base_static = render_matrix(matrix, scale=scale).convert('RGBA')

    for i in range(n):
        y, x, _ = pfad[i]

        if zustaende is not None:
            # Matrix-Kopie mit aktualisierten Weichen-Symbolen für diesen Schritt
            akt = [row[:] for row in matrix]
            for (wy, wx), var in zustaende[i].items():
                alter = akt[wy][wx]
                p = parse_zelle(alter)
                if p and p[0] in WEICHEN_TYP:
                    typ = WEICHEN_TYP[p[0]]
                    neue_nr = TYP_VAR_ZU_NR[(typ, var)]
                    akt[wy][wx] = _token_mit_nr(alter, neue_nr)
            frame = render_matrix(akt, scale=scale).convert('RGBA')
        else:
            frame = base_static.copy()

        draw = ImageDraw.Draw(frame, 'RGBA')
        cx, cy = x * cell + cell // 2, y * cell + cell // 2
        draw.ellipse([cx - kugel_r, cy - kugel_r, cx + kugel_r, cy + kugel_r],
                     fill=(0, 220, 0, 255), outline=(0, 100, 0, 255))
        datei = f"{ausgabe_prefix}_step_{i:0{breite}d}.png"
        frame.save(datei)
        dateien.append(datei)

    return dateien


def erzeuge_gif(matrix, pfad, ausgabe_datei, scale=8, duration=80,
                jeder_schritt=1, spur=False):
    """
    Erzeugt ein animiertes GIF: die grüne Kugel rollt Schritt für Schritt
    über die Schienen (ohne Spur, sofern spur=False).
    """
    base = render_matrix(matrix, scale=scale).convert('RGBA')
    cell = 9 * scale
    kugel_r = max(3, scale)
    schritte = pfad[::jeder_schritt]

    frames = []
    for i, (y, x, _) in enumerate(schritte):
        frame = base.copy()
        draw = ImageDraw.Draw(frame, 'RGBA')
        if spur and i > 0:
            pts = [(px * cell + cell // 2, py * cell + cell // 2)
                   for (py, px, _) in schritte[:i + 1]]
            draw.line(pts, fill=(0, 180, 0, 120), width=max(2, scale // 2))
        cx, cy = x * cell + cell // 2, y * cell + cell // 2
        draw.ellipse([cx - kugel_r, cy - kugel_r, cx + kugel_r, cy + kugel_r],
                     fill=(0, 220, 0, 255), outline=(0, 100, 0, 255))
        frames.append(frame.convert('P', palette=Image.ADAPTIVE))

    if frames:
        frames[0].save(ausgabe_datei, save_all=True, append_images=frames[1:],
                       duration=duration, loop=0, optimize=True)
    return len(frames)


def simuliere_tm_einzelbilder(tm_datei, anzahl_schritte, scale=10,
                              ausgabe_prefix=None, spalt=3):
    """
    Komplett-Pipeline: liest .tm-Datei, baut Layout, simuliert den Zug und
    erzeugt einzelne PNG-Bilder (eins pro Schritt) in Originalskalierung.

    Rückgabe: (matrix, pfad, dateien, info)
    """
    tm = TuringMaschine(datei=tm_datei)
    matrix, info = kaskadiere_TM(tm, spalt=spalt)

    start = finde_start(matrix)
    if start is None:
        raise ValueError("Kein Startsymbol (10:...) in der Matrix gefunden")

    sim = TrainSimulation(matrix)
    pfad, zustaende = sim.fahre(start[0], start[1], 'O',
                                max_schritte=max(anzahl_schritte, 1),
                                mit_zustand=True)

    if ausgabe_prefix is None:
        ausgabe_prefix = os.path.splitext(os.path.basename(tm_datei))[0]
    dateien = erzeuge_einzelbilder(matrix, pfad, ausgabe_prefix,
                                   anzahl_schritte, scale=scale,
                                   zustaende=zustaende)
    return matrix, pfad, dateien, info


# ===========================================================================
# VERIFIKATOR – Bahn-Simulation gegen unabhängigen TM-Interpreter prüfen
# ===========================================================================
# Vergleicht die Bahn-Anlage gegen einen unabhängigen Interpreter, der direkt
# die Transitionstabelle anwendet und keine Geometrie kennt. So lässt sich
# objektiv prüfen, ob die Anlage wirklich die TM berechnet – für beliebige n.
#
# Repräsentation im Layout:
#   Bandsymbol  = Stellung der Lazy-Weiche auf einer Zustandsleitung
#                 (Var1=f/0, Var2=t/1)
#   Richtung    = Abbiegung in der L/R-Kurve unterhalb von ShellB
#   Folgezustand= Zustandsleitung, auf der der Zug die ShellA verlässt
#   Ein TM-Schritt = ein kompletter ShellA-Durchlauf
# ---------------------------------------------------------------------------

def tm_interpret(tm, max_schritte=1000):
    """
    Unabhängiger TM-Interpreter (kennt nur die Transitionstabelle).
    Gibt die Liste der Konfigurationen (zustand, kopfposition, band-tupel) zurück.
    """
    z = tm.start_zustand
    pos = tm.start_position
    band = list(tm.band)
    konfigs = [(z, pos, tuple(band))]
    for _ in range(max_schritte):
        if not (0 <= pos < len(band)):
            break
        t = tm.get_transition(z, band[pos])
        if t is None:
            break
        band[pos] = t.schreib
        z = t.neuer_zustand
        pos += 1 if t.richtung == 'R' else -1
        konfigs.append((z, pos, tuple(band)))
        if z not in tm.zustaende:
            break
    return konfigs


def lies_band_aus_switches(sim, info, anzahl_zellen):
    """
    Liest den Bandinhalt aus den Symbol-Lazy-Weichen der Simulation.
    Die Symbol-Lazy-Weiche ist generisch die Lazy-Weiche AUF einer Zustands-
    leitung (Position aus Geometrie, nicht hartkodiert). Var1->0(f), Var2->1(t).
    """
    ez = info['eingangszeilen']
    xoffs = info['x_offsets']
    bw = info['shellA_breite']
    m = sim.matrix
    band = []
    for c in range(anzahl_zellen):
        sym = None
        for ey in ez:
            for x in range(xoffs[c], xoffs[c] + bw):
                p = parse_zelle(m[ey][x])
                if p and p[0] in (5, 6):
                    var = sim.switch_state.get((ey, x))
                    if var is not None:
                        sym = 0 if var == 1 else 1
                    break
            if sym is not None:
                break
        band.append(sym)
    return band


def verifiziere(tm, max_schritte=2000, verbose=False):
    """
    Lässt den Zug durch die Kaskade fahren, liest das Endband aus den Weichen
    und vergleicht es mit dem unabhängigen Interpreter.
    Rückgabe: dict mit 'ok', 'band_sim', 'band_interp', ...
    """
    m, info = kaskadiere_TM(tm)
    start = finde_start(m)
    if start is None:
        return {'ok': False, 'fehler': 'kein Startsymbol'}

    sim = TrainSimulation(m)
    pfad = sim.fahre(start[0], start[1], 'O', max_schritte=max_schritte)

    band_sim = lies_band_aus_switches(sim, info, len(tm.band))
    konfigs = tm_interpret(tm)
    band_interp = list(konfigs[-1][2])
    ok = (band_sim == band_interp)

    if verbose:
        bs = ''.join('t' if x == 1 else ('f' if x == 0 else '?') for x in band_sim)
        bi = ''.join('t' if x == 1 else 'f' for x in band_interp)
        print(f"  Band Simulation:  {bs}")
        print(f"  Band Interpreter: {bi}")
        print(f"  Übereinstimmung:  {'JA ✓' if ok else 'NEIN ✗'}")
        print(f"  Interpreter-Schritte: {len(konfigs)-1}, Zug-Pfad: {len(pfad)} Zellen")

    return {'ok': ok, 'band_sim': band_sim, 'band_interp': band_interp,
            'interp_schritte': len(konfigs) - 1, 'pfad_laenge': len(pfad)}


def teste_einzeluebergaenge(tm, verbose=True):
    """
    Testet jeden Übergang (zustand, symbol) isoliert: ShellA bauen, Zug auf der
    Zustandsleitung eintreten lassen, Folgezustand + Richtung gegen die
    Transitionstabelle prüfen. Lokalisiert Konstruktionsfehler pro Übergang.
    Rückgabe: Liste von dicts mit 'ok'.
    """
    n = tm.n
    s = tm.schalter_fuer_shellb()
    r = tm.richtungen_fuer_shellb()
    tmap = {(t.zustand, t.symbol): t for t in tm.transitionen}

    ergebnisse = []
    for symbol in (0, 1):
        m, ez = ShellA_verbunden(n, symbol, schalter=s, richtungen=r,
                                 zustaende=tm.zustaende, transitionen_map=tmap)
        z_aus = {ez[i]: tm.zustaende[i] for i in range(n)}
        for zi in range(n):
            z = tm.zustaende[zi]
            t = tm.get_transition(z, symbol)
            pfad = TrainSimulation(m).fahre(ez[zi], 0, 'O', max_schritte=1000)
            ende = pfad[-1]
            if ende[0] in z_aus:
                ist = (z_aus[ende[0]], 'R' if ende[2] == 'O' else 'L')
            else:
                ist = None
            if t is not None and t.neuer_zustand in tm.zustaende:
                erw = (t.neuer_zustand, t.richtung)
            else:
                erw = 'HALT'
            ok = (ist == erw) or (erw == 'HALT' and ist is None)
            ergebnisse.append({'zustand': z, 'symbol': symbol,
                               'erwartet': erw, 'tatsaechlich': ist, 'ok': ok})

    if verbose:
        print(f"  {'(Zustand,Sym)':14s} {'Erwartet':10s} {'Tatsächlich':12s} OK")
        for e in ergebnisse:
            sym_s = 't' if e['symbol'] else 'f'
            erw = 'HALT' if e['erwartet'] == 'HALT' else f"z{e['erwartet'][0]},{e['erwartet'][1]}"
            ist = '-' if e['tatsaechlich'] is None else f"z{e['tatsaechlich'][0]},{e['tatsaechlich'][1]}"
            print(f"  (z{e['zustand']},{sym_s})          {erw:10s} {ist:12s} {'✓' if e['ok'] else '✗'}")
        n_ok = sum(1 for e in ergebnisse if e['ok'])
        print(f"  -> {n_ok}/{len(ergebnisse)} Übergänge korrekt")

    return ergebnisse


# ---------------------------------------------------------------------------
# main – Test aller Elemente
# ---------------------------------------------------------------------------
def main():
    """Erzeugt alle Element-Bilder: Übersicht, Einzelelemente und n=2-Varianten."""
    import os
    out_dir = "element_output"
    os.makedirs(out_dir, exist_ok=True)

    # 1) Übersichtsbild: alle 10 Elemente in allen Drehungen/Flips
    erzeuge_uebersicht(ausgabe_datei=os.path.join(out_dir, "uebersicht.png"), scale=6)
    print(f"Übersicht gespeichert: {os.path.join(out_dir, 'uebersicht.png')}")

    # 2) Einzelne Element-Bilder (Grundstellung r1), inkl. Weichen + Start
    for elem_nr, (_, elem_name) in sorted(ELEMENTS.items()):
        datei = os.path.join(out_dir, f"element_{elem_nr:02d}_{elem_name}.png")
        getElement(elem_nr, 1, False, False, ausgabe_datei=datei, scale=16)

    # 3) Alle 16 ShellA-Varianten für n=2
    varianten = [
        ('LLLL', [0,0,0,0], ['L','L','L','L']),
        ('LLLR', [0,0,0,1], ['L','L','L','R']),
        ('LLRL', [0,0,1,0], ['L','L','R','L']),
        ('LLRR', [0,0,1,1], ['L','L','R','R']),
        ('LRLL', [0,1,0,0], ['L','R','L','L']),
        ('LRLR', [0,1,0,1], ['L','R','L','R']),
        ('LRRL', [0,1,1,0], ['L','R','R','L']),
        ('LRRR', [0,1,1,1], ['L','R','R','R']),
        ('RLLL', [1,0,0,0], ['R','L','L','L']),
        ('RLLR', [1,0,0,1], ['R','L','L','R']),
        ('RLRL', [1,0,1,0], ['R','L','R','L']),
        ('RLRR', [1,0,1,1], ['R','L','R','R']),
        ('RRLL', [1,1,0,0], ['R','R','L','L']),
        ('RRLR', [1,1,0,1], ['R','R','L','R']),
        ('RRRL', [1,1,1,0], ['R','R','R','L']),
        ('RRRR', [1,1,1,1], ['R','R','R','R']),
    ]

    for name, schalter, richtungen in varianten:
        m, _ = ShellA_verbunden(2, 1, schalter=schalter, richtungen=richtungen)
        matrix_to_png(m,
                      ausgabe_datei=os.path.join(out_dir, f"n2_{name}.png"),
                      scale=6, koordinaten=True)

    print(f"Alle Bilder in '{out_dir}/' erzeugt "
          f"({len(ELEMENTS)} Elemente + Übersicht + {len(varianten)} ShellA-Varianten)")


if __name__ == "__main__":
    import sys

    # Modus: Verifikator  ->  elements.py --verify <turingmachine.tm>
    if len(sys.argv) >= 3 and sys.argv[1] in ('--verify', '-v'):
        tm_datei = sys.argv[2]
        tm = TuringMaschine(datei=tm_datei)
        band_str = ''.join('t' if x else 'f' for x in tm.band)
        print(f"Verifiziere {tm_datei} "
              f"(start z{tm.start_zustand} pos{tm.start_position} band {band_str}):")
        print("\n[1] Endband-Vergleich (komplette Kaskade):")
        verifiziere(tm, verbose=True)
        print("\n[2] Einzelübergang-Test (pro Zustand/Symbol):")
        teste_einzeluebergaenge(tm, verbose=True)

    # Modus: Simulation  ->  elements.py <turingmachine.tm> <anzahl schritte>
    elif len(sys.argv) >= 3 and sys.argv[1].endswith('.tm'):
        tm_datei = sys.argv[1]
        try:
            anzahl_schritte = int(sys.argv[2])
        except ValueError:
            print(f"Fehler: '{sys.argv[2]}' ist keine gültige Schrittzahl")
            sys.exit(1)

        SCALE = 10  # Originalskalierung der Einzelbilder
        print(f"Simuliere {tm_datei} ({anzahl_schritte} Schritte) ...")
        matrix, pfad, dateien, info = simuliere_tm_einzelbilder(
            tm_datei, anzahl_schritte, scale=SCALE)
        print(f"  Layout:  {len(matrix)}x{len(matrix[0])}")
        print(f"  Start:   Zustand {info['start_zustand']}, Bandposition {info['start_position']}")
        print(f"  Pfad:    {len(pfad)} Schritte verfügbar")
        print(f"  Bilder:  {len(dateien)} PNGs erzeugt (scale {SCALE})")
        if dateien:
            print(f"           {dateien[0]} ... {dateien[-1]}")
    else:
        # Modus: ohne Argument -> Element-Testbilder erzeugen
        main()
