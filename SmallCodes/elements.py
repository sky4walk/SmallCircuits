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

    def __repr__(self):
        return (f"TuringMaschine(start=({self.start_zustand},{self.start_position}), "
                f"band={self.band}, n={self.n}, "
                f"zustaende={self.zustaende}, "
                f"transitionen={self.transitionen})")


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
    for titel, args, kwargs, fname in [
        ("ShellB(3, 0)",               (3, 0), {},                          "ShellB_3x_z0.png"),
        ("ShellB(2, 1)",               (2, 1), {},                          "ShellB_2x_z1.png"),
        ("ShellB(4, 0)",               (4, 0), {},                          "ShellB_4x_z0.png"),
        ("ShellB(2,1 s=[0,0,1,1])",    (2, 1), {"schalter":[0,0, 1,1]},    "ShellB_2x_s0011.png"),
        ("ShellB(2,1 s=[1,0,0,1])",    (2, 1), {"schalter":[1,0, 0,1]},    "ShellB_2x_s1001.png"),
        ("ShellB(3,0 s=[0,1,1,0,0,0])",(3, 0), {"schalter":[0,1, 1,0,0,0]},"ShellB_3x_s011000.png"),
    ]:
        print_matrix(ShellB(*args, **kwargs), titel=titel)
        matrix_to_png(ShellB(*args, **kwargs), ausgabe_datei=os.path.join(out_dir, fname), scale=8, koordinaten=True)

    # 8c) ShellB_mit_Kurven
    print("\n[8c] ShellB_mit_Kurven:")
    for titel, args, kwargs, fname in [
        ("ShellB_mit_Kurven(3, 0)",               (3, 0), {},                           "kurven_n3_z0.png"),
        ("ShellB_mit_Kurven(2, 1)",               (2, 1), {},                           "kurven_n2_z1.png"),
        ("ShellB_mit_Kurven(4, 0)",               (4, 0), {},                           "kurven_n4_z0.png"),
        ("ShellB_mit_Kurven(2,1 s=[0,0,1,1])",    (2, 1), {"schalter":[0,0, 1,1]},     "kurven_n2_z1_s0011.png"),
        ("ShellB_mit_Kurven(2,1 s=[1,0,0,1])",    (2, 1), {"schalter":[1,0, 0,1]},     "kurven_n2_z1_s1001.png"),
        ("ShellB_mit_Kurven(3,0 s=[0,1,1,0,0,0])",(3, 0), {"schalter":[0,1, 1,0,0,0]},"kurven_n3_z0_s011000.png"),
    ]:
        print(f"  {titel}")
        m, _ = ShellB_mit_Kurven(*args, **kwargs)
        matrix_to_png(m, ausgabe_datei=os.path.join(out_dir, fname), scale=8, koordinaten=True)

    # 8d) ShellB_mit_Routing
    print("\n[8d] ShellB_mit_Routing:")
    for titel, args, kwargs, fname in [
        ("ShellB_mit_Routing(2,1 LRLR)",         (2,1), {"richtungen":["L","R","L","R"]},                           "routing_n2_z1_LRLR.png"),
        ("ShellB_mit_Routing(2,1 s=0101 LRLR)",  (2,1), {"schalter":[0,1,0,1],"richtungen":["L","R","L","R"]},     "routing_n2_z1_s0101_LRLR.png"),
        ("ShellB_mit_Routing(2,1 LLRR)",         (2,1), {"richtungen":["L","L","R","R"]},                           "routing_n2_z1_LLRR.png"),
        ("ShellB_mit_Routing(3,0 LRLRLR)",       (3,0), {"richtungen":["L","R","L","R","L","R"]},                   "routing_n3_z0_LRLRLR.png"),
    ]:
        print(f"  {titel}")
        m = ShellB_mit_Routing(*args, **kwargs)
        matrix_to_png(m, ausgabe_datei=os.path.join(out_dir, fname), scale=8, koordinaten=True)


    # 8e) ShellA_links
    print("\n[8e] ShellA_links:")
    for titel, args, kwargs, fname in [
        ("ShellA_links(2,1 LRLR)",         (2,1), {"richtungen":["L","R","L","R"]},                       "shellA_n2_z1_LRLR.png"),
        ("ShellA_links(2,1 s=0101 LRLR)",  (2,1), {"schalter":[0,1,0,1],"richtungen":["L","R","L","R"]}, "shellA_n2_z1_s0101_LRLR.png"),
        ("ShellA_links(3,0 LRLRLR)",       (3,0), {"richtungen":["L","R","L","R","L","R"]},               "shellA_n3_z0_LRLRLR.png"),
        ("ShellA_links(6,0)",              (6,0), {"richtungen":["L","R"]*6},                             "shellA_n6_z0.png"),
    ]:
        print(f"  {titel}")
        m, _ = ShellA_links(*args, **kwargs)
        matrix_to_png(m, ausgabe_datei=os.path.join(out_dir, fname), scale=5, koordinaten=True)


    # 8f) ShellA (links + rechts)
    print("\n[8f] ShellA:")
    for titel, args, kwargs, fname in [
        ("ShellA(2,1 LRLR)",        (2,1), {"richtungen":["L","R","L","R"]},                       "shellA_full_n2_z1_LRLR.png"),
        ("ShellA(2,1 s=0101 LRLR)", (2,1), {"schalter":[0,1,0,1],"richtungen":["L","R","L","R"]}, "shellA_full_n2_z1_s0101_LRLR.png"),
        ("ShellA(3,0 LRLRLR)",      (3,0), {"richtungen":["L","R","L","R","L","R"]},               "shellA_full_n3_z0_LRLRLR.png"),
    ]:
        print(f"  {titel}")
        m, _ = ShellA(*args, **kwargs)
        matrix_to_png(m, ausgabe_datei=os.path.join(out_dir, fname), scale=5, koordinaten=True)


    # 8g) ShellA_mit_Bogen
    print("\n[8g] ShellA_mit_Bogen:")
    for titel, args, kwargs, fname in [
        ("ShellA_mit_Bogen(2,1 LRLR)",        (2,1), {"richtungen":["L","R","L","R"]},                       "shellA_bogen_n2_z1_LRLR.png"),
        ("ShellA_mit_Bogen(2,1 s=0101 LRLR)", (2,1), {"schalter":[0,1,0,1],"richtungen":["L","R","L","R"]}, "shellA_bogen_n2_s0101_LRLR.png"),
        ("ShellA_mit_Bogen(3,0 LRLRLR)",      (3,0), {"richtungen":["L","R","L","R","L","R"]},               "shellA_bogen_n3_z0_LRLRLR.png"),
    ]:
        print(f"  {titel}")
        m, _ = ShellA_mit_Bogen(*args, **kwargs)
        matrix_to_png(m, ausgabe_datei=os.path.join(out_dir, fname), scale=5, koordinaten=True)

    # 8b) ShellB + ShellB_mit_Kurven + ShellB_mit_Routing aus TM-Datei
    print("\n[8b] ShellB aus Demo2.tm:")
    tm_pfad = next((p for p in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Demo2.tm"),
        "/mnt/user-data/uploads/Demo2.tm",
    ] if os.path.exists(p)), None)
    tm = TuringMaschine(datei=tm_pfad)
    if tm.transitionen:
        s  = tm.schalter_fuer_shellb()
        rl = [tm.get_transition(z, sym).richtung
              for z in tm.zustaende for sym in [0, 1]]
        band_sym = tm.band[tm.start_position]

        # ShellB (beide Zustände)
        for zsym in [0, 1]:
            print_matrix(ShellB(tm.n, zsym, schalter=s),
                         titel=f"ShellB Demo2 z={zsym} (n={tm.n}, s={s})")
            matrix_to_png(ShellB(tm.n, zsym, schalter=s),
                          ausgabe_datei=os.path.join(out_dir, f"ShellB_Demo2_z{zsym}.png"),
                          scale=8, koordinaten=True)

        # ShellB_mit_Kurven (beide Zustände)
        for zsym in [0, 1]:
            mk, _ = ShellB_mit_Kurven(tm.n, zsym, schalter=s)
            matrix_to_png(mk,
                          ausgabe_datei=os.path.join(out_dir, f"kurven_Demo2_z{zsym}.png"),
                          scale=8, koordinaten=True)

        # ShellB_mit_Routing – nur das aktuelle Bandsymbol
        mr = ShellB_mit_Routing(tm.n, band_sym, schalter=s, richtungen=rl)
        matrix_to_png(mr,
                      ausgabe_datei=os.path.join(out_dir, "routing_Demo2.png"),
                      scale=8, koordinaten=True)

        # ShellA_links – linke Eingangsleitungen
        ma, _ = ShellA_links(tm.n, band_sym, schalter=s, richtungen=rl)
        matrix_to_png(ma,
                      ausgabe_datei=os.path.join(out_dir, "shellA_Demo2.png"),
                      scale=8, koordinaten=True)
        print(f"  Demo2: n={tm.n}, band_sym={band_sym}, s={s}, richtungen={rl}")

        # ShellA_mit_Bogen
        mB, _ = ShellA_mit_Bogen(tm.n, band_sym, schalter=s, richtungen=rl)
        matrix_to_png(mB,
                      ausgabe_datei=os.path.join(out_dir, "shellA_bogen_Demo2.png"),
                      scale=8, koordinaten=True)

    # 9) Kommandozeilen-Modus:
    #    python elements.py <datei.tm> [ausgabe_verzeichnis]
    #    python elements.py <nr> <drehen> <hFlip> <vFlip> [datei]
    if len(sys.argv) >= 2 and sys.argv[1].endswith(".tm"):
        tm_pfad  = sys.argv[1]
        tm_out   = sys.argv[2] if len(sys.argv) >= 3 else out_dir
        if not os.path.exists(tm_pfad):
            print(f"Fehler: '{tm_pfad}' nicht gefunden.")
            sys.exit(1)
        os.makedirs(tm_out, exist_ok=True)
        name = os.path.splitext(os.path.basename(tm_pfad))[0]
        tm2  = TuringMaschine(datei=tm_pfad)
        s2   = tm2.schalter_fuer_shellb()
        rl2  = [tm2.get_transition(z, sym).richtung
                for z in tm2.zustaende for sym in [0, 1]]
        bs2  = tm2.band[tm2.start_position]
        print(f"\n[TM] {tm_pfad}: n={tm2.n}, band_sym={bs2}, s={s2}, richtungen={rl2}")
        for zsym in [0, 1]:
            matrix_to_png(ShellB(tm2.n, zsym, schalter=s2),
                          ausgabe_datei=os.path.join(tm_out, f"{name}_ShellB_z{zsym}.png"),
                          scale=8, koordinaten=True)
            mk, _ = ShellB_mit_Kurven(tm2.n, zsym, schalter=s2)
            matrix_to_png(mk,
                          ausgabe_datei=os.path.join(tm_out, f"{name}_kurven_z{zsym}.png"),
                          scale=8, koordinaten=True)
        mr = ShellB_mit_Routing(tm2.n, bs2, schalter=s2, richtungen=rl2)
        matrix_to_png(mr,
                      ausgabe_datei=os.path.join(tm_out, f"{name}_routing.png"),
                      scale=8, koordinaten=True)
        ma, _ = ShellA_links(tm2.n, bs2, schalter=s2, richtungen=rl2)
        matrix_to_png(ma,
                      ausgabe_datei=os.path.join(tm_out, f"{name}_shellA.png"),
                      scale=8, koordinaten=True)
        mA, _ = ShellA(tm2.n, bs2, schalter=s2, richtungen=rl2)
        matrix_to_png(mA,
                      ausgabe_datei=os.path.join(tm_out, f"{name}_shellA_full.png"),
                      scale=8, koordinaten=True)
        mB, _ = ShellA_mit_Bogen(tm2.n, bs2, schalter=s2, richtungen=rl2)
        matrix_to_png(mB,
                      ausgabe_datei=os.path.join(tm_out, f"{name}_shellA_bogen.png"),
                      scale=8, koordinaten=True)
        print(f"Fertig. Ausgaben in: {tm_out}/")
    elif len(sys.argv) >= 5:
        print("\n[9] Kommandozeilen-Aufruf:")
        nr  = int(sys.argv[1])
        rot = int(sys.argv[2])
        hf  = sys.argv[3].lower() in ("1", "true", "ja", "yes")
        vf  = sys.argv[4].lower() in ("1", "true", "ja", "yes")
        out = sys.argv[5] if len(sys.argv) >= 6 else os.path.join(out_dir, "cmd_output.png")
        img = getElement(nr, rot, hf, vf, ausgabe_datei=out, scale=8)
        print(f"    Element {nr}, Drehen={rot}, hFlip={hf}, vFlip={vf} -> {out}")

    print(f"\nAlle Ausgaben in: ./{out_dir}/")


if __name__ == "__main__":
    main()
