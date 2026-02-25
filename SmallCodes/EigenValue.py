"""
Eigenwert-Berechnung - NUR mit Python-Standard-Bibliothek
==========================================================

Dieses Programm berechnet Eigenwerte und Eigenvektoren einer 2x2-Matrix
OHNE NumPy - jede mathematische Operation wird explizit gezeigt.
"""

import math

def print_step(step_num, title):
    """Druckt einen formatierten Schritt-Header"""
    print(f"\n{'='*70}")
    print(f"SCHRITT {step_num}: {title}")
    print('='*70)

def matrix_mal_vektor(matrix, vektor):
    """
    Multipliziert eine 2x2-Matrix mit einem 2D-Vektor.

    [ a  b ] · [ x ]   [ a*x + b*y ]
    [ c  d ]   [ y ] = [ c*x + d*y ]
    """
    a, b = matrix[0]
    c, d = matrix[1]
    x, y = vektor

    result = [
        a * x + b * y,  # erste Zeile · Vektor
        c * x + d * y   # zweite Zeile · Vektor
    ]

    print(f"\nMatrix-Vektor-Multiplikation:")
    print(f"  [ {a}  {b} ] · [ {x} ]   [ {a}*{x} + {b}*{y} ]   [ {result[0]} ]")
    print(f"  [ {c}  {d} ]   [ {y} ] = [ {c}*{x} + {d}*{y} ] = [ {result[1]} ]")

    return result

def skalar_mal_vektor(skalar, vektor):
    """
    Multipliziert einen Skalar mit einem Vektor.

    λ · [ x ]   [ λ*x ]
        [ y ] = [ λ*y ]
    """
    result = [skalar * vektor[0], skalar * vektor[1]]

    print(f"\nSkalar-Vektor-Multiplikation:")
    print(f"  {skalar} · [ {vektor[0]} ]   [ {skalar}*{vektor[0]} ]   [ {result[0]} ]")
    print(f"          [ {vektor[1]} ] = [ {skalar}*{vektor[1]} ] = [ {result[1]} ]")

    return result

def vektoren_fast_gleich(v1, v2, toleranz=0.0001):
    """Prüft, ob zwei Vektoren fast gleich sind (wegen Rundungsfehlern)"""
    return abs(v1[0] - v2[0]) < toleranz and abs(v1[1] - v2[1]) < toleranz

def berechne_eigenwerte_schritt_fuer_schritt(matrix):
    """
    Berechnet Eigenwerte einer 2x2-Matrix mit allen Zwischenschritten
    """
    a, b = matrix[0]
    c, d = matrix[1]

    print("\n" + "="*70)
    print("EIGENWERT-BERECHNUNG - NUR MIT PYTHON-STANDARD")
    print("="*70)
    print(f"\nGegebene Matrix A:")
    print(f"    [ {a}  {b} ]")
    print(f"    [ {c}  {d} ]")

    # SCHRITT 1
    print_step(1, "Grundgleichung aufstellen")
    print("Wir suchen λ und v mit: A·v = λ·v")
    print("Umgeformt: (A - λI)·v = 0")

    # SCHRITT 2
    print_step(2, "A - λI berechnen")
    print(f"Einheitsmatrix I:")
    print(f"    [ 1  0 ]")
    print(f"    [ 0  1 ]")
    print(f"\nλI (λ mal Einheitsmatrix):")
    print(f"    [ λ  0 ]")
    print(f"    [ 0  λ ]")
    print(f"\nA - λI (komponentenweise Subtraktion):")
    print(f"    [ {a}  {b} ]   [ λ  0 ]   [ {a}-λ    {b}   ]")
    print(f"    [ {c}  {d} ] - [ 0  λ ] = [  {c}    {d}-λ ]")

    # SCHRITT 3
    print_step(3, "Determinante berechnen")
    print(f"Für eine 2×2-Matrix [ a  b ] gilt die Determinante:")
    print(f"                     [ c  d ]")
    print(f"\ndet = a·d - b·c")
    print(f"      ↑       ↑")
    print(f"  Hauptdiagonale mal zusammen minus Nebendiagonale mal zusammen")
    print(f"\nFür unsere Matrix A - λI:")
    print(f"  a = {a}-λ")
    print(f"  b = {b}")
    print(f"  c = {c}")
    print(f"  d = {d}-λ")
    print(f"\ndet(A - λI) = ({a}-λ)·({d}-λ) - {b}·{c}")

    # SCHRITT 4
    print_step(4, "Ausmultiplizieren (jeder Schritt einzeln)")
    print(f"\nErster Term: ({a}-λ)·({d}-λ)")
    print(f"  = {a}·{d} + {a}·(-λ) + (-λ)·{d} + (-λ)·(-λ)")
    print(f"  = {a*d} - {a}λ - {d}λ + λ²")
    print(f"  = {a*d} - {a+d}λ + λ²")

    print(f"\nZweiter Term: {b}·{c}")
    print(f"  = {b*c}")

    print(f"\nGesamte Determinante:")
    print(f"  det = ({a*d} - {a+d}λ + λ²) - {b*c}")
    print(f"      = λ² - {a+d}λ + {a*d - b*c}")

    # Das ist jetzt in der Form: λ² + pλ + q = 0
    # Wir bringen es in Normalform
    p = -(a + d)
    q = a*d - b*c

    print(f"\nCharakteristisches Polynom in Normalform:")
    print(f"  λ² + ({p})λ + {q} = 0")
    print(f"\nDas bedeutet:")
    print(f"  p = {p}")
    print(f"  q = {q}")

    # SCHRITT 5
    print_step(5, "Nullstellen mit pq-Formel berechnen")
    print(f"\npq-Formel: λ = -p/2 ± √((p/2)² - q)")
    print(f"\nWas bedeutet das?")
    print(f"  1. Hälfte von p nehmen und Vorzeichen umkehren: -p/2")
    print(f"  2. Diese Hälfte quadrieren: (p/2)²")
    print(f"  3. q davon abziehen: (p/2)² - q")
    print(f"  4. Wurzel ziehen: √(...)")
    print(f"  5. Zu -p/2 addieren UND subtrahieren (± gibt 2 Lösungen)")

    print(f"\n--- Schritt 5a: p/2 berechnen ---")
    p_halb = p / 2
    print(f"  p/2 = {p}/2 = {p_halb}")

    print(f"\n--- Schritt 5b: -p/2 berechnen (Vorzeichen umkehren) ---")
    minus_p_halb = -p_halb
    print(f"  -p/2 = -({p_halb}) = {minus_p_halb}")

    print(f"\n--- Schritt 5c: (p/2)² berechnen ---")
    p_halb_quadrat = p_halb ** 2
    print(f"  (p/2)² = ({p_halb})²")
    print(f"         = {p_halb} · {p_halb}")
    print(f"         = {p_halb_quadrat}")

    print(f"\n--- Schritt 5d: (p/2)² - q berechnen ---")
    diskriminante = p_halb_quadrat - q
    print(f"  (p/2)² - q = {p_halb_quadrat} - {q}")
    print(f"             = {diskriminante}")
    print(f"\nDas nennt man die 'Diskriminante'.")

    print(f"\n--- Schritt 5e: Wurzel ziehen ---")
    wurzel = math.sqrt(diskriminante)
    print(f"  √{diskriminante} = {wurzel}")
    print(f"\nWie rechnet man das?")
    print(f"  Die Wurzel ist die Zahl, die mit sich selbst multipliziert {diskriminante} ergibt.")
    print(f"  {wurzel} · {wurzel} = {wurzel * wurzel} ✓")

    print(f"\n--- Schritt 5f: Beide Lösungen berechnen ---")
    print(f"\nErste Lösung (mit +):")
    print(f"  λ₁ = -p/2 + √(...)")
    print(f"     = {minus_p_halb} + {wurzel}")
    lambda1 = minus_p_halb + wurzel
    print(f"     = {lambda1}")

    print(f"\nZweite Lösung (mit -):")
    print(f"  λ₂ = -p/2 - √(...)")
    print(f"     = {minus_p_halb} - {wurzel}")
    lambda2 = minus_p_halb - wurzel
    print(f"     = {lambda2}")

    print(f"\n{'>'*70}")
    print(f">>> EIGENWERTE GEFUNDEN: λ₁ = {lambda1}, λ₂ = {lambda2}")
    print(f"{'>'*70}")

    return lambda1, lambda2

def berechne_eigenvektor(matrix, eigenvalue):
    """Berechnet den Eigenvektor für einen gegebenen Eigenwert"""
    a, b = matrix[0]
    c, d = matrix[1]

    print(f"\n{'─'*70}")
    print(f"EIGENVEKTOR für λ = {eigenvalue}")
    print('─'*70)

    print(f"\nWir müssen lösen: (A - λI)·v = 0")
    print(f"\nDas bedeutet: Welcher Vektor v wird von (A - λI) auf Null abgebildet?")

    print(f"\n--- Schritt 1: (A - λI) berechnen ---")
    print(f"\nA - {eigenvalue}I:")
    m11 = a - eigenvalue
    m12 = b
    m21 = c
    m22 = d - eigenvalue

    print(f"  [ {a} - {eigenvalue}      {b}        ]   [ {m11}  {m12} ]")
    print(f"  [  {c}         {d} - {eigenvalue} ] = [ {m21}  {m22} ]")

    print(f"\n--- Schritt 2: Gleichungssystem aufstellen ---")
    print(f"\n(A - λI)·v = 0  wird zu:")
    print(f"\n  [ {m11}  {m12} ] · [ v₁ ]   [ 0 ]")
    print(f"  [ {m21}  {m22} ]   [ v₂ ] = [ 0 ]")
    print(f"\nAusgeschrieben:")
    print(f"  Zeile 1: {m11}·v₁ + {m12}·v₂ = 0")
    print(f"  Zeile 2: {m21}·v₁ + {m22}·v₂ = 0")

    print(f"\n--- Schritt 3: Eine Gleichung nach v₂ auflösen ---")

    # Erste Gleichung nach v₂ auflösen
    if m11 != 0:
        print(f"\nNehmen wir Zeile 1: {m11}·v₁ + {m12}·v₂ = 0")
        print(f"\n  {m11}·v₁ = -{m12}·v₂")

        if m12 != 0:
            ratio = -m11 / m12
            print(f"  v₁ = -{m12}·v₂ / {m11}")
            print(f"  v₁ = {ratio}·v₂")

            print(f"\n--- Schritt 4: Einen konkreten Wert wählen ---")
            print(f"\nWir können v₂ frei wählen (außer 0).")
            print(f"Wählen wir v₂ = 1 (einfachste Wahl), dann:")
            print(f"  v₁ = {ratio} · 1 = {ratio}")

            v1, v2 = ratio, 1
        else:
            print(f"  {m11}·v₁ = 0")
            print(f"  v₁ = 0")
            print(f"\nWählen wir v₂ = 1, dann v₁ = 0")
            v1, v2 = 0, 1
    else:
        print(f"\nZeile 1 liefert 0 = 0 (keine Info)")
        print(f"Nehmen wir Zeile 2: {m21}·v₁ + {m22}·v₂ = 0")
        if m22 != 0:
            ratio = -m21 / m22
            print(f"  v₁ = {ratio}·v₂")
            print(f"\nWählen wir v₂ = 1, dann v₁ = {ratio}")
            v1, v2 = ratio, 1
        else:
            v1, v2 = 1, 0

    print(f"\n{'>'*70}")
    print(f">>> EIGENVEKTOR: v = [{v1}, {v2}]")
    print(f"{'>'*70}")

    return [v1, v2]

# ========== HAUPTPROGRAMM ==========

if __name__ == "__main__":
    # Beispiel-Matrix
    matrix = [
        [3, 1],
        [1, 3]
    ]

    # Eigenwerte berechnen (Schritt für Schritt)
    lambda1, lambda2 = berechne_eigenwerte_schritt_fuer_schritt(matrix)

    # Eigenvektoren berechnen
    print("\n\n" + "="*70)
    print("EIGENVEKTOREN BERECHNEN")
    print("="*70)

    v1 = berechne_eigenvektor(matrix, lambda1)
    v2 = berechne_eigenvektor(matrix, lambda2)

    # Verifikation
    print("\n\n" + "="*70)
    print("VERIFIKATION - PRÜFEN OB ES WIRKLICH STIMMT")
    print("="*70)

    print(f"\n{'─'*70}")
    print("Test 1: A·v₁ sollte gleich λ₁·v₁ sein")
    print('─'*70)

    Av1 = matrix_mal_vektor(matrix, v1)
    lam_v1 = skalar_mal_vektor(lambda1, v1)

    if vektoren_fast_gleich(Av1, lam_v1):
        print(f"\nDie Vektoren sind identisch!")
        print(f"    A·v₁ = λ₁·v₁ ist erfüllt!")
    else:
        print(f"\n✗ Fehler - die Vektoren unterscheiden sich")

    print(f"\n{'─'*70}")
    print("Test 2: A·v₂ sollte gleich λ₂·v₂ sein")
    print('─'*70)

    Av2 = matrix_mal_vektor(matrix, v2)
    lam_v2 = skalar_mal_vektor(lambda2, v2)

    if vektoren_fast_gleich(Av2, lam_v2):
        print(f"\nDie Vektoren sind identisch!")
        print(f"    A·v₂ = λ₂·v₂ ist erfüllt!")
    else:
        print(f"\nFehler - die Vektoren unterscheiden sich")

    # Zusammenfassung
    print("\n\n" + "="*70)
    print("ZUSAMMENFASSUNG")
    print("="*70)
    print(f"\nMatrix A:")
    print(f"  [ {matrix[0][0]}  {matrix[0][1]} ]")
    print(f"  [ {matrix[1][0]}  {matrix[1][1]} ]")
    print(f"\nEigenwert λ₁ = {lambda1}")
    print(f"Eigenvektor v₁ = [{v1[0]}, {v1[1]}]")
    print(f"\nEigenwert λ₂ = {lambda2}")
    print(f"Eigenvektor v₂ = [{v2[0]}, {v2[1]}]")

    print("\n" + "="*70)
    print("FERTIG!")
    print("="*70)
