"""
Dirac-Notation Visualisierung - NUR mit Python-Standard
========================================================

Dieses Programm zeigt Dirac-Notation-Rechnungen Schritt für Schritt
OHNE NumPy - jede mathematische Operation wird explizit gezeigt.
"""

import math  # Nur für sqrt() bei reellen Zahlen

def print_header(title):
    """Schöner Header für Abschnitte"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_step(step_num, description):
    """Nummerierte Schritte"""
    print(f"\n[Schritt {step_num}] {description}")
    print("-" * 70)

def vektor_addieren(v1, v2):
    """Addiert zwei Vektoren (Listen) komponentenweise"""
    return [v1[0] + v2[0], v1[1] + v2[1]]

def skalar_mal_vektor(skalar, vektor):
    """Multipliziert jeden Eintrag des Vektors mit dem Skalar"""
    return [skalar * vektor[0], skalar * vektor[1]]

def skalarprodukt(v1, v2):
    """
    Berechnet das Skalarprodukt zweier Vektoren.
    Bei komplexen Zahlen: v1 wird konjugiert!
    """
    # Konjugiere v1 (falls komplex)
    v1_konj = [komplex_konjugieren(v1[0]), komplex_konjugieren(v1[1])]
    
    # Multipliziere komponentenweise und addiere
    return v1_konj[0] * v2[0] + v1_konj[1] * v2[1]

def komplex_konjugieren(z):
    """Konjugiert eine (möglicherweise komplexe) Zahl"""
    if isinstance(z, complex):
        return z.conjugate()  # a+bi → a-bi
    else:
        return z  # Reelle Zahlen bleiben gleich

def vektor_norm(vektor):
    """Berechnet die Länge (Norm) eines Vektors"""
    # |v| = √(|v₀|² + |v₁|²)
    # Bei komplexen Zahlen: |z|² = z · z*
    
    betrag_0_quadrat = abs(vektor[0])**2
    betrag_1_quadrat = abs(vektor[1])**2
    
    return math.sqrt(betrag_0_quadrat + betrag_1_quadrat)

def zeige_basis_vektoren():
    """Zeigt die Basis-Vektoren |0⟩ und |1⟩"""
    print_header("Die Basis-Vektoren")
    
    ket0 = [1, 0]  # Einfache Python-Liste!
    ket1 = [0, 1]
    
    print("\n|0⟩ = [1]  ← Der erste Einheitsvektor")
    print("      [0]")
    print("\n|1⟩ = [0]  ← Der zweite Einheitsvektor")
    print("      [1]")
    
    print("\nDas sind einfache Python-Listen mit zwei Zahlen!")
    
    return ket0, ket1

def zeige_skalar_multiplikation():
    """Zeigt α|0⟩ Schritt für Schritt"""
    print_header("Skalar-Multiplikation: α|0⟩")
    
    alpha = 3
    ket0 = [1, 0]
    
    print_step(1, f"Gegeben: α = {alpha} und |0⟩ = [1, 0]")
    
    print_step(2, "Multipliziere jeden Eintrag mit α")
    print("\nIn Python:")
    print(f"  result = [{alpha} * {ket0[0]}, {alpha} * {ket0[1]}]")
    
    result = skalar_mal_vektor(alpha, ket0)
    
    print(f"\nSchritt für Schritt:")
    print(f"  Erste Komponente:  {alpha} × {ket0[0]} = {result[0]}")
    print(f"  Zweite Komponente: {alpha} × {ket0[1]} = {result[1]}")
    
    print(f"\n✓ Ergebnis: {alpha}|0⟩ = {result}")
    
    return result

def zeige_linearkombination():
    """Zeigt α|0⟩ + β|1⟩"""
    print_header("Linearkombination: α|0⟩ + β|1⟩")
    
    alpha = 1/math.sqrt(2)  # Python's math.sqrt
    beta = 1/math.sqrt(2)
    
    ket0 = [1, 0]
    ket1 = [0, 1]
    
    print_step(1, f"Gegeben: α = 1/√2 ≈ {alpha:.3f}, β = 1/√2 ≈ {beta:.3f}")
    
    print_step(2, "Berechne α|0⟩")
    print(f"\n  α|0⟩ = [{alpha:.3f} × {ket0[0]}, {alpha:.3f} × {ket0[1]}]")
    part1 = skalar_mal_vektor(alpha, ket0)
    print(f"       = [{part1[0]:.3f}, {part1[1]:.3f}]")
    
    print_step(3, "Berechne β|1⟩")
    print(f"\n  β|1⟩ = [{beta:.3f} × {ket1[0]}, {beta:.3f} × {ket1[1]}]")
    part2 = skalar_mal_vektor(beta, ket1)
    print(f"       = [{part2[0]:.3f}, {part2[1]:.3f}]")
    
    print_step(4, "Addiere beide Vektoren")
    print(f"\n  In Python:")
    print(f"  result = [{part1[0]:.3f} + {part2[0]:.3f}, {part1[1]:.3f} + {part2[1]:.3f}]")
    
    result = vektor_addieren(part1, part2)
    
    print(f"\n  Schritt für Schritt:")
    print(f"  Erste Komponente:  {part1[0]:.3f} + {part2[0]:.3f} = {result[0]:.3f}")
    print(f"  Zweite Komponente: {part1[1]:.3f} + {part2[1]:.3f} = {result[1]:.3f}")
    
    # Normierung prüfen
    print_step(5, "Länge berechnen (Normierung prüfen)")
    print(f"\n  |v| = √(v₀² + v₁²)")
    print(f"      = √({result[0]:.3f}² + {result[1]:.3f}²)")
    
    v0_quadrat = result[0]**2
    v1_quadrat = result[1]**2
    summe = v0_quadrat + v1_quadrat
    
    print(f"      = √({v0_quadrat:.3f} + {v1_quadrat:.3f})")
    print(f"      = √{summe:.3f}")
    
    norm = vektor_norm(result)
    print(f"      = {norm:.3f}")
    
    print(f"\n✓ Ergebnis: |ψ⟩ = [{result[0]:.3f}, {result[1]:.3f}]")
    print(f"✓ Länge: {norm:.3f}")
    
    if abs(norm - 1.0) < 0.001:
        print("✓✓ NORMIERT! (Länge = 1)")
    
    return result

def zeige_ket_zu_bra():
    """Zeigt die Umwandlung von Ket zu Bra"""
    print_header("Von Ket zu Bra: Konjugiert Transponierte")
    
    # Beispiel mit komplexen Zahlen
    ket = [3 + 2j, 1 - 1j]  # Python komplexe Zahlen: j statt i
    
    print_step(1, "Gegeben: Ein Ket mit komplexen Zahlen")
    print(f"\n  |ψ⟩ = [{ket[0]}]")
    print(f"        [{ket[1]}]")
    print(f"\n  In Python: ket = [{ket[0]}, {ket[1]}]")
    
    print_step(2, "Transponieren (Spalte → Zeile)")
    print(f"\n  Das ist in Python nur konzeptuell - wir haben schon eine Liste.")
    print(f"  |ψ⟩ᵀ = [{ket[0]}, {ket[1]}]")
    
    print_step(3, "Konjugieren (Vorzeichen vor j umkehren)")
    print(f"\n  In Python:")
    print(f"  bra = [ket[0].conjugate(), ket[1].conjugate()]")
    
    bra = [komplex_konjugieren(ket[0]), komplex_konjugieren(ket[1])]
    
    print(f"\n  Schritt für Schritt:")
    print(f"  ({ket[0]}).conjugate() = {bra[0]}")
    print(f"  ({ket[1]}).conjugate() = {bra[1]}")
    
    print_step(4, "Ergebnis: Das Bra")
    print(f"\n  ⟨ψ| = [{bra[0]}, {bra[1]}]")
    
    print("\n✓ Fertig! Aus dem Ket wurde ein Bra.")
    
    return bra

def zeige_skalarprodukt():
    """Zeigt Skalarprodukt-Berechnung"""
    print_header("Skalarprodukt (Bracket): ⟨0|1⟩")
    
    ket0 = [1, 0]
    ket1 = [0, 1]
    
    print_step(1, "Gegeben")
    print(f"\n  |0⟩ = {ket0}")
    print(f"  |1⟩ = {ket1}")
    
    print_step(2, "Mache aus |0⟩ das Bra ⟨0|")
    bra0 = [komplex_konjugieren(ket0[0]), komplex_konjugieren(ket0[1])]
    print(f"\n  ⟨0| = {bra0}  (transponiert + konjugiert)")
    print(f"  Bei reellen Zahlen ändert sich nichts.")
    
    print_step(3, "Berechne das Skalarprodukt")
    print(f"\n  ⟨0|1⟩ = ⟨0|[0] · ⟨0|[1] + ⟨0|[1] · |1⟩[1]")
    print(f"              ↓              ↓")
    print(f"  In Python:")
    print(f"  result = bra0[0] * ket1[0] + bra0[1] * ket1[1]")
    print(f"         = {bra0[0]} * {ket1[0]} + {bra0[1]} * {ket1[1]}")
    
    term1 = bra0[0] * ket1[0]
    term2 = bra0[1] * ket1[1]
    
    print(f"\n  Schritt für Schritt:")
    print(f"  Erster Term:  {bra0[0]} × {ket1[0]} = {term1}")
    print(f"  Zweiter Term: {bra0[1]} × {ket1[1]} = {term2}")
    print(f"  Summe: {term1} + {term2} = {term1 + term2}")
    
    result = skalarprodukt(ket0, ket1)
    
    print(f"\n  = {result}")
    
    print("\n" + "="*70)
    if abs(result) < 0.0001:
        print("✓✓ SKALARPRODUKT = 0  →  ORTHOGONAL!")
        print("   Die Vektoren stehen senkrecht (90°) zueinander!")
    else:
        print(f"   Skalarprodukt = {result}  →  NICHT orthogonal")
    print("="*70)
    
    return result

def zeige_alle_kombinationen():
    """Zeigt alle vier möglichen Skalarprodukte"""
    print_header("Alle Basis-Skalarprodukte")
    
    ket0 = [1, 0]
    ket1 = [0, 1]
    
    kombinationen = [
        ("⟨0|0⟩", ket0, ket0, "Vektor mit sich selbst → immer 1"),
        ("⟨0|1⟩", ket0, ket1, "Orthogonale Vektoren → immer 0"),
        ("⟨1|0⟩", ket1, ket0, "Orthogonale Vektoren → immer 0"),
        ("⟨1|1⟩", ket1, ket1, "Vektor mit sich selbst → immer 1"),
    ]
    
    for name, bra, ket, beschreibung in kombinationen:
        result = skalarprodukt(bra, ket)
        print(f"\n  {name} = bra[0]*ket[0] + bra[1]*ket[1]")
        print(f"        = {bra[0]}*{ket[0]} + {bra[1]}*{ket[1]}")
        print(f"        = {result}")
        print(f"        → {beschreibung}")
    
    print("\n" + "="*70)
    print("REGEL: ⟨i|j⟩ = 1 wenn i=j, sonst 0")
    print("       (Das nennt man 'Orthonormalität')")
    print("="*70)

def zeige_betrag_komplex():
    """Zeigt wie man den Betrag komplexer Zahlen berechnet"""
    print_header("BONUS: Betrag komplexer Zahlen")
    
    z = 3 + 4j
    
    print(f"\nGegeben: z = {z}")
    
    print(f"\nBetrag |z| berechnen:")
    print(f"  |z| = √(Realteil² + Imaginärteil²)")
    print(f"      = √({z.real}² + {z.imag}²)")
    
    real_quadrat = z.real**2
    imag_quadrat = z.imag**2
    
    print(f"      = √({real_quadrat} + {imag_quadrat})")
    print(f"      = √{real_quadrat + imag_quadrat}")
    
    betrag = abs(z)  # Python's eingebaute abs() Funktion
    
    print(f"      = {betrag}")
    
    print(f"\n  In Python: abs({z}) = {betrag}")
    
    print("\n" + "-"*70)
    print("Oder mit z·z*:")
    z_konj = z.conjugate()
    print(f"  z* = {z_konj}")
    print(f"  z·z* = {z} × {z_konj} = {z * z_konj}")
    print(f"  √(z·z*) = √{z * z_konj} = {math.sqrt((z * z_konj).real)}")

def tensorprodukt(v1, v2):
    """
    Berechnet das Tensorprodukt zweier 2D-Vektoren.
    Ergebnis ist ein 4D-Vektor.
    
    [a] ⊗ [c] = [a·c]
    [b]   [d]   [a·d]
                [b·c]
                [b·d]
    """
    return [
        v1[0] * v2[0],  # a·c
        v1[0] * v2[1],  # a·d
        v1[1] * v2[0],  # b·c
        v1[1] * v2[1]   # b·d
    ]

def zeige_tensorprodukt():
    """Zeigt Tensorprodukt-Berechnung für 2-Qubit-Zustände"""
    print_header("TENSORPRODUKT: Zwei Qubits kombinieren")
    
    ket0 = [1, 0]
    ket1 = [0, 1]
    
    print("\nDas Tensorprodukt ⊗ kombiniert zwei Vektoren zu einem größeren.")
    print("Aus zwei 2D-Vektoren wird ein 4D-Vektor!")
    
    print_step(1, "Die Regel verstehen")
    print("\n  [a] ⊗ [c] = [a·c]")
    print("  [b]   [d]   [a·d]")
    print("              [b·c]")
    print("              [b·d]")
    print("\n  → Jedes Element des ersten Vektors mal den ganzen zweiten Vektor")
    
    print_step(2, "Beispiel: |0⟩ ⊗ |0⟩ = |00⟩")
    print(f"\n  |0⟩ = {ket0}")
    print(f"  |0⟩ = {ket0}")
    
    print(f"\n  In Python:")
    print(f"  result = [")
    print(f"      {ket0[0]} * {ket0[0]},  # erste Komponente von |0⟩ mal ganzer |0⟩")
    print(f"      {ket0[0]} * {ket0[1]},")
    print(f"      {ket0[1]} * {ket0[0]},  # zweite Komponente von |0⟩ mal ganzer |0⟩")
    print(f"      {ket0[1]} * {ket0[1]}")
    print(f"  ]")
    
    ket00 = tensorprodukt(ket0, ket0)
    
    print(f"\n  Schritt für Schritt:")
    print(f"  Position 0: {ket0[0]} × {ket0[0]} = {ket00[0]}")
    print(f"  Position 1: {ket0[0]} × {ket0[1]} = {ket00[1]}")
    print(f"  Position 2: {ket0[1]} × {ket0[0]} = {ket00[2]}")
    print(f"  Position 3: {ket0[1]} × {ket0[1]} = {ket00[3]}")
    
    print(f"\n✓ Ergebnis: |00⟩ = {ket00}")
    print(f"            Das ist ein 4-dimensionaler Vektor!")
    
    print_step(3, "Alle vier 2-Qubit-Basiszustände")
    
    basis_2qubit = [
        ("|00⟩", ket0, ket0, "Binär 00 = Position 0"),
        ("|01⟩", ket0, ket1, "Binär 01 = Position 1"),
        ("|10⟩", ket1, ket0, "Binär 10 = Position 2"),
        ("|11⟩", ket1, ket1, "Binär 11 = Position 3"),
    ]
    
    for name, v1, v2, beschreibung in basis_2qubit:
        result = tensorprodukt(v1, v2)
        print(f"\n  {name} = |{v1[0]},{v1[1]}⟩ ⊗ |{v2[0]},{v2[1]}⟩ = {result}")
        print(f"        → {beschreibung}")
    
    print_step(4, "Allgemeiner 2-Qubit-Zustand")
    
    print("\n  Ein beliebiger 2-Qubit-Zustand:")
    print("  |ψ⟩ = α|00⟩ + β|01⟩ + γ|10⟩ + δ|11⟩")
    print("\n  Als 4D-Vektor:")
    print("  |ψ⟩ = [α, β, γ, δ]")
    print("\n  Mit Normierung: |α|² + |β|² + |γ|² + |δ|² = 1")
    
    print_step(5, "Beispiel: Bell-Zustand (verschränkt!)")
    
    alpha = 1/math.sqrt(2)
    beta = 0
    gamma = 0
    delta = 1/math.sqrt(2)
    
    print(f"\n  |Φ⁺⟩ = 1/√2 (|00⟩ + |11⟩)")
    print(f"       = {alpha:.3f}|00⟩ + {beta}|01⟩ + {gamma}|10⟩ + {delta:.3f}|11⟩")
    print(f"       = [{alpha:.3f}, {beta}, {gamma}, {delta:.3f}]")
    
    print("\n  Das ist ein verschränkter Zustand!")
    print("  Man kann ihn NICHT als |ψ₁⟩ ⊗ |ψ₂⟩ schreiben.")
    
    norm_squared = alpha**2 + beta**2 + gamma**2 + delta**2
    print(f"\n  Normierung: {alpha:.3f}² + {beta}² + {gamma}² + {delta:.3f}²")
    print(f"            = {norm_squared:.3f} ✓")

# ========== HAUPTPROGRAMM ==========

if __name__ == "__main__":
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  DIRAC-NOTATION - PURE PYTHON".center(68) + "█")
    print("█" + "  Ohne NumPy - Jede Operation explizit".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    # 1. Basis-Vektoren
    zeige_basis_vektoren()
    
    # 2. Skalar-Multiplikation
    zeige_skalar_multiplikation()
    
    # 3. Linearkombination
    zeige_linearkombination()
    
    # 4. Ket zu Bra
    zeige_ket_zu_bra()
    
    # 5. Skalarprodukt
    zeige_skalarprodukt()
    
    # 6. Alle Kombinationen
    zeige_alle_kombinationen()
    
    # 7. Tensorprodukt (2-Qubit-Zustände)
    zeige_tensorprodukt()
    
    # 8. Bonus: Betrag komplexer Zahlen
    zeige_betrag_komplex()
    
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  FERTIG!".center(68) + "█")
    print("█" + "  Jede Rechnung wurde explizit mit Python gemacht!".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70 + "\n")
