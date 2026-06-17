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

from PIL import Image
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

    # zweite Header-Zeile (Index 1) um anzahl*2 × '6:r1V' verlängern
    matrix[1] = matrix[1] + ["6:r1V"] * (anzahl * 2)

    # Jedes ShellC belegt 5 Zeilen, Header belegt 2 Zeilen (Indizes 0+1)
    # Innerhalb jedes ShellC: Ausgang 1:r1 = relative Zeile 1, 9:r1 = relative Zeile 3
    shellc_hoehe = 5
    header_zeilen = 2

    def _setze(matrix, zeile_idx, spalte, token):
        zeile = matrix[zeile_idx]
        while len(zeile) <= spalte:
            zeile.append("0")
        zeile[spalte] = token

    for i in range(anzahl):
        # Globale Basiszeile dieser ShellC (relativ zu Zeile 0 der ShellC)
        basis = header_zeilen + i * shellc_hoehe

        # Paar A: relative Zeilen 0+1, jede ShellC um 2 nach rechts versetzt
        spalte_a = 5 + 2 * i
        _setze(matrix, basis + 0, spalte_a, "8:r4HV")
        _setze(matrix, basis + 1, spalte_a, "8:r1")

        # Paar B: zwei nach unten und eins nach rechts von Paar A
        spalte_b = 6 + 2 * i
        _setze(matrix, basis + 2, spalte_b, "8:r4HV")
        _setze(matrix, basis + 3, spalte_b, "8:r1")

        # Schalter: 0 → 8:r1 durch 9:r1 ersetzen (2 pro ShellC)
        # schalter[i*2]   → Paar A (basis+1, Zeile mit 1:r1-Ausgang)
        # schalter[i*2+1] → Paar B (basis+3, Zeile mit 9:r1-Ausgang)
        if schalter[i * 2] == 0:
            if matrix[basis + 1][spalte_a] == "8:r1":
                matrix[basis + 1][spalte_a] = "9:r1"
        if schalter[i * 2 + 1] == 0:
            if matrix[basis + 3][spalte_b] == "8:r1":
                matrix[basis + 3][spalte_b] = "9:r1"

    # Maximale Zeilenbreite ermitteln
    max_breite = max(len(row) for row in matrix)

    # Nur Zeilen mit 8:r4HV oder 8:r1 bekommen 7:r1 als Verbindung und Auffüllung.
    # Alle anderen Zeilen werden auf max_breite mit "0" aufgefüllt.
    for row in matrix:
        hat_8er = any(c in ("8:r4HV", "8:r1", "9:r1") for c in row[5:])
        if hat_8er:
            pos_4hv = next((j for j in range(5, len(row)) if row[j] == "8:r4HV"), None)
            pos_r1  = next((j for j in range(5, len(row)) if row[j] in ("8:r1", "9:r1")), None)

            if pos_r1 is not None:
                # Zeile mit 8:r1: 7:r1 von Spalte 5 bis 8:r1, dann 7:r1 bis rechts
                for j in range(5, pos_r1):
                    if row[j] == "0":
                        row[j] = "7:r1"
                del row[pos_r1 + 1:]
                while len(row) < max_breite:
                    row.append("7:r1")
            elif pos_4hv is not None:
                # Zeile mit nur 8:r4HV: 7:r1 ab 8:r4HV bis zum rechten Rand
                del row[pos_4hv + 1:]
                while len(row) < max_breite:
                    row.append("7:r1")
        else:
            # Keine Verbindung – mit 0 auffüllen
            while len(row) < max_breite:
                row.append("0")


    # Innere ShellC-Trennzeilen mit 7:r2 auffüllen – aber erst ab der Spalte
    # des 8:r4HV der nächsten ShellC (nicht ab Spalte 5)
    for i in range(anzahl - 1):
        zeile_idx = header_zeilen + i * shellc_hoehe + (shellc_hoehe - 1)
        # 8:r4HV der nächsten ShellC liegt in Zeile basis+0 der nächsten ShellC
        naechste_basis = header_zeilen + (i + 1) * shellc_hoehe
        # Spalte des 8:r4HV der nächsten ShellC
        start_spalte = next(
            (j for j, cell in enumerate(matrix[naechste_basis]) if cell == "8:r4HV"),
            max_breite
        )
        row = matrix[zeile_idx]
        while len(row) < max_breite:
            row.append("0")
        for j in range(start_spalte, max_breite):
            if row[j] == "0":
                row[j] = "7:r2"

    # Vertikale Verbindungen: von jedem 8:r4HV bis Zeile 1 hochziehen
    # Nur wo 7:r1 liegt → 1:r1 (Kreuz), 0 bleibt 0
    pos_4hv_liste = [
        (i, j)
        for i, row in enumerate(matrix)
        for j, cell in enumerate(row)
        if cell == "8:r4HV"
    ]

    for y_start, x in pos_4hv_liste:
        for y in range(y_start - 1, 0, -1):
            while len(matrix[y]) <= x:
                matrix[y].append("0")
            if matrix[y][x] in ("7:r1", "9:r1"):
                matrix[y][x] = "1:r1"

    return matrix



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
# main – Test aller Elemente
# ---------------------------------------------------------------------------
def main():
    import sys

    out_dir = "element_output"
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 60)
    print("TM2Train Bildelement-Bibliothek – Testlauf")
    print("=" * 60)

    # 1) Alle 8 Elemente, alle 4 Drehungen, kein Flip → 32 Dateien
    print("\n[1] Alle Elemente in allen Drehungen (kein Flip):")
    for nr, (_, name) in sorted(ELEMENTS.items()):
        for d in [1, 2, 3, 4]:
            fname = os.path.join(out_dir, f"el{nr}_{name}_rot{d}.png")
            getElement(nr, d, False, False, ausgabe_datei=fname, scale=8)

    # 2) Flip-Kombinationen für Element 2 (Kurve) – gut sichtbarer Effekt
    print("\n[2] Element 2 (Kurve) – alle Flip-Kombinationen:")
    combos = [
        (False, False, "noFlip"),
        (True,  False, "hFlip"),
        (False, True,  "vFlip"),
        (True,  True,  "hvFlip"),
    ]
    for h, v, tag in combos:
        fname = os.path.join(out_dir, f"el2_curve_{tag}.png")
        getElement(2, 1, h, v, ausgabe_datei=fname, scale=8)

    # 3) Einzelner Aufruf wie gewünscht
    print("\n[3] Beispiel: getElement(5, 2, True, False)")
    img = getElement(5, 2, True, False,
                     ausgabe_datei=os.path.join(out_dir, "beispiel_el5_rot2_hflip.png"),
                     scale=8)
    print(f"    Bildgröße: {img.size}, Modus: {img.mode}")

    # 4) Übersichtsbild
    print("\n[4] Erzeuge Übersichtsbild:")
    erzeuge_uebersicht(os.path.join(out_dir, "uebersicht.png"), scale=6)

    # 5) Matrix-Renderer – Beispiel (entspricht ShellC Zustand 1)
    print("\n[5] Matrix-Renderer:")
    render_matrix(
        _SHELLC_MATRIX_1,
        ausgabe_datei=os.path.join(out_dir, "matrix_beispiel.png"),
        scale=8,
    )

    # 6) ShellC + matrix_to_png – beide Zustände
    print("\n[6] ShellC + matrix_to_png:")
    matrix_to_png(ShellC(0), ausgabe_datei=os.path.join(out_dir, "ShellC_zustand0.png"), scale=8)
    matrix_to_png(ShellC(1), ausgabe_datei=os.path.join(out_dir, "ShellC_zustand1.png"), scale=8)

    # 7) stack_shellc
    print("\n[7] stack_shellc:")
    matrix_to_png(stack_shellc(3, 0), ausgabe_datei=os.path.join(out_dir, "stack_3x_zustand0.png"), scale=8)
    matrix_to_png(stack_shellc(2, 1), ausgabe_datei=os.path.join(out_dir, "stack_2x_zustand1.png"), scale=8)

    # 8) ShellB
    print("\n[8] ShellB:")
    print_matrix(ShellB(3, 0), titel="ShellB(3, 0)")
    matrix_to_png(ShellB(3, 0), ausgabe_datei=os.path.join(out_dir, "ShellB_3x_z0.png"), scale=8, koordinaten=True)
    print_matrix(ShellB(2, 1), titel="ShellB(2, 1)")
    matrix_to_png(ShellB(2, 1), ausgabe_datei=os.path.join(out_dir, "ShellB_2x_z1.png"), scale=8, koordinaten=True)
    matrix_to_png(ShellB(4, 0), ausgabe_datei=os.path.join(out_dir, "ShellB_4x_z0.png"), scale=8, koordinaten=True)

    # 8b) ShellB mit Schaltern
    print("\n[8b] ShellB mit Schaltern:")
    # 2x: [A1,B1, A2,B2]
    matrix_to_png(ShellB(2, 1, schalter=[0,0, 1,1]),
                  ausgabe_datei=os.path.join(out_dir, "ShellB_2x_s0011.png"), scale=8, koordinaten=True)
    matrix_to_png(ShellB(2, 1, schalter=[1,0, 0,1]),
                  ausgabe_datei=os.path.join(out_dir, "ShellB_2x_s1001.png"), scale=8, koordinaten=True)
    # 3x: [A1,B1, A2,B2, A3,B3]
    matrix_to_png(ShellB(3, 0, schalter=[0,1, 1,0, 0,0]),
                  ausgabe_datei=os.path.join(out_dir, "ShellB_3x_s011000.png"), scale=8, koordinaten=True)

    # 9) Kommandozeilen-Modus: python elements.py <nr> <drehen> <hFlip> <vFlip> [datei]
    if len(sys.argv) >= 5:
        print("\n[7] Kommandozeilen-Aufruf:")
        nr  = int(sys.argv[1])
        rot = int(sys.argv[2])
        hf  = sys.argv[3].lower() in ("1", "true", "ja", "yes")
        vf  = sys.argv[4].lower() in ("1", "true", "ja", "yes")
        out = sys.argv[5] if len(sys.argv) >= 6 else os.path.join(out_dir, "cmd_output.png")
        img = getElement(nr, rot, hf, vf, ausgabe_datei=out, scale=8)
        print(f"    Element {nr}, Drehen={rot}, hFlip={hf}, vFlip={vf} → {out}")

    print(f"\nAlle Ausgaben in: ./{out_dir}/")


if __name__ == "__main__":
    main()
