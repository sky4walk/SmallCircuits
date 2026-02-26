"""
Quanten-Simulator - Pure Python
================================

Simuliert Quantenoperationen ohne NumPy:
- Tensorprodukte von Vektoren und Matrizen
- Quantengatter (H, X, Y, Z, CNOT)
- Verschränkung mit CNOT
- Matrix-Vektor-Multiplikation

Alle Operationen sind explizit und Schritt für Schritt sichtbar.
"""

import math

def print_header(title):
    """Schöner Header für Abschnitte"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_step(step_num, description):
    """Nummerierte Schritte"""
    print(f"\n[Schritt {step_num}] {description}")
    print("-" * 70)

def vektor_als_string(v, name="v"):
    """Formatiert einen Vektor schön zur Anzeige"""
    def format_wert(val):
        if isinstance(val, complex):
            if val.imag == 0:
                return f"{val.real:.3f}"
            elif val.real == 0:
                return f"{val.imag:.3f}j"
            else:
                return f"({val.real:.3f}+{val.imag:.3f}j)" if val.imag >= 0 else f"({val.real:.3f}{val.imag:.3f}j)"
        else:
            return f"{val:.3f}" if isinstance(val, float) else str(val)
    
    lines = [f"{name} = ["]
    for val in v:
        lines.append(f"      {format_wert(val)}")
    lines.append("     ]ᵀ")
    return "\n".join(lines)

def matrix_als_string(m, name="M"):
    """Formatiert eine Matrix schön zur Anzeige"""
    if not m or not m[0]:
        return f"{name} = []"
    
    def format_wert(val):
        if isinstance(val, complex):
            if val.imag == 0:
                return f"{val.real:.3f}"
            elif val.real == 0:
                return f"{val.imag:.3f}j"
            else:
                return f"{val.real:.2f}+{val.imag:.2f}j" if val.imag >= 0 else f"{val.real:.2f}{val.imag:.2f}j"
        else:
            return f"{val:.3f}" if isinstance(val, float) else str(val)
    
    # Finde maximale Breite
    max_breite = max(len(format_wert(val)) for zeile in m for val in zeile)
    
    lines = [f"{name} = ["]
    for zeile in m:
        zeile_str = "      [ "
        zeile_str += "  ".join(format_wert(val).rjust(max_breite) for val in zeile)
        zeile_str += " ]"
        lines.append(zeile_str)
    lines.append("     ]")
    return "\n".join(lines)

# ============================================================================
# TENSORPRODUKT VON VEKTOREN
# ============================================================================

def tensor_vektor_vektor(v1, v2, verbose=True):
    """
    Berechnet das Tensorprodukt zweier Vektoren.
    
    Für v1 = [a, b] und v2 = [c, d]:
    v1 ⊗ v2 = [a·c, a·d, b·c, b·d]
    """
    if verbose:
        print_header("Tensorprodukt: Vektor ⊗ Vektor")
        print(f"\nGegeben:")
        print(vektor_als_string(v1, "v₁"))
        print(vektor_als_string(v2, "v₂"))
        print(f"\nBerechnung:")
    
    ergebnis = []
    
    for i, elem1 in enumerate(v1):
        if verbose:
            print(f"\n  Element {i} von v₁: {elem1}")
        
        for j, elem2 in enumerate(v2):
            produkt = elem1 * elem2
            ergebnis.append(produkt)
            
            if verbose:
                print(f"    {elem1} × {elem2} = {produkt} → Position {len(ergebnis)-1}")
    
    if verbose:
        print(f"\n✓ Ergebnis:")
        print(vektor_als_string(ergebnis, "v₁ ⊗ v₂"))
    
    return ergebnis

# ============================================================================
# TENSORPRODUKT VON MATRIZEN
# ============================================================================

def tensor_matrix_matrix(m1, m2, verbose=True):
    """
    Berechnet das Tensorprodukt zweier Matrizen.
    
    Für 2×2-Matrizen:
    A ⊗ B = [ a₁₁·B  a₁₂·B ]
            [ a₂₁·B  a₂₂·B ]
    """
    if verbose:
        print_header("Tensorprodukt: Matrix ⊗ Matrix")
        print(f"\nGegeben:")
        print(matrix_als_string(m1, "M₁"))
        print(matrix_als_string(m2, "M₂"))
    
    zeilen1 = len(m1)
    spalten1 = len(m1[0])
    zeilen2 = len(m2)
    spalten2 = len(m2[0])
    
    # Ergebnismatrix: (zeilen1 * zeilen2) × (spalten1 * spalten2)
    ergebnis_zeilen = zeilen1 * zeilen2
    ergebnis_spalten = spalten1 * spalten2
    ergebnis = [[0 for _ in range(ergebnis_spalten)] for _ in range(ergebnis_zeilen)]
    
    if verbose:
        print(f"\nBerechnung:")
        print(f"Jedes Element von M₁ wird mit der GANZEN Matrix M₂ multipliziert:\n")
    
    # Für jedes Element in m1
    for i1 in range(zeilen1):
        for j1 in range(spalten1):
            elem1 = m1[i1][j1]
            
            if verbose:
                print(f"  M₁[{i1}][{j1}] = {elem1}")
                print(f"  {elem1} × M₂:")
            
            # Multipliziere elem1 mit jeder Position in m2
            for i2 in range(zeilen2):
                for j2 in range(spalten2):
                    elem2 = m2[i2][j2]
                    produkt = elem1 * elem2
                    
                    # Position im Ergebnis
                    ziel_zeile = i1 * zeilen2 + i2
                    ziel_spalte = j1 * spalten2 + j2
                    
                    ergebnis[ziel_zeile][ziel_spalte] = produkt
                    
                    if verbose:
                        print(f"    {elem1} × {elem2} = {produkt} → Position [{ziel_zeile}][{ziel_spalte}]")
            
            if verbose:
                print()
    
    if verbose:
        print(f"✓ Ergebnis:")
        print(matrix_als_string(ergebnis, "M₁ ⊗ M₂"))
    
    return ergebnis

# ============================================================================
# MATRIX-VEKTOR-MULTIPLIKATION
# ============================================================================

def matrix_mal_vektor(matrix, vektor, verbose=True):
    """
    Multipliziert eine Matrix mit einem Vektor.
    
    Ergebnis[i] = Zeile[i] · Vektor
    """
    if verbose:
        print_header("Matrix-Vektor-Multiplikation")
        print(f"\nGegeben:")
        print(matrix_als_string(matrix, "M"))
        print(vektor_als_string(vektor, "v"))
        print(f"\nBerechnung:")
    
    zeilen = len(matrix)
    spalten = len(matrix[0])
    
    if len(vektor) != spalten:
        raise ValueError(f"Dimensionen passen nicht: Matrix hat {spalten} Spalten, Vektor hat {len(vektor)} Elemente")
    
    ergebnis = []
    
    for i, zeile in enumerate(matrix):
        if verbose:
            print(f"\n  Zeile {i}: {zeile}")
        
        summe = 0
        terme = []
        
        for j, matrix_elem in enumerate(zeile):
            vektor_elem = vektor[j]
            produkt = matrix_elem * vektor_elem
            summe += produkt
            terme.append(f"{matrix_elem}×{vektor_elem}")
            
            if verbose:
                print(f"    {matrix_elem} × {vektor_elem} = {produkt}")
        
        ergebnis.append(summe)
        
        if verbose:
            print(f"  Summe: {' + '.join(terme)} = {summe}")
    
    if verbose:
        print(f"\n✓ Ergebnis:")
        print(vektor_als_string(ergebnis, "M·v"))
    
    return ergebnis

# ============================================================================
# QUANTENGATTER DEFINITIONEN
# ============================================================================

class QuantenGatter:
    """Sammlung von Standard-Quantengattern"""
    
    @staticmethod
    def I():
        """Identität (tut nichts)"""
        return [[1, 0],
                [0, 1]]
    
    @staticmethod
    def X():
        """Pauli-X (NOT-Gatter)"""
        return [[0, 1],
                [1, 0]]
    
    @staticmethod
    def Y():
        """Pauli-Y (mit komplexem i)"""
        return [[0, -1j],
                [1j, 0]]
    
    @staticmethod
    def Z():
        """Pauli-Z (Phase-Flip)"""
        return [[1, 0],
                [0, -1]]
    
    @staticmethod
    def H():
        """Hadamard-Gatter"""
        s = 1 / math.sqrt(2)
        return [[s, s],
                [s, -s]]
    
    @staticmethod
    def S():
        """S-Gatter (Phase π/2)"""
        return [[1, 0],
                [0, 1j]]
    
    @staticmethod
    def T():
        """T-Gatter (Phase π/4)"""
        phase = cmath.exp(1j * math.pi / 4)
        return [[1, 0],
                [0, phase]]
    
    @staticmethod
    def CNOT():
        """CNOT-Gatter (2-Qubit)"""
        return [[1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0]]

# ============================================================================
# BASIS-ZUSTÄNDE
# ============================================================================

class BasisZustand:
    """Standard Qubit-Zustände"""
    
    @staticmethod
    def ket0():
        """|0⟩"""
        return [1, 0]
    
    @staticmethod
    def ket1():
        """|1⟩"""
        return [0, 1]
    
    @staticmethod
    def ket00():
        """|00⟩"""
        return [1, 0, 0, 0]
    
    @staticmethod
    def ket01():
        """|01⟩"""
        return [0, 1, 0, 0]
    
    @staticmethod
    def ket10():
        """|10⟩"""
        return [0, 0, 1, 0]
    
    @staticmethod
    def ket11():
        """|11⟩"""
        return [0, 0, 0, 1]

# ============================================================================
# QUANTENOPERATIONEN
# ============================================================================

def gatter_anwenden(gatter, zustand, gatter_name="Gatter", zustand_name="|ψ⟩"):
    """Wendet ein Quantengatter auf einen Zustand an"""
    print_header(f"{gatter_name} auf {zustand_name} anwenden")
    print(f"\n{gatter_name}:")
    print(matrix_als_string(gatter, gatter_name))
    print(f"\n{zustand_name}:")
    print(vektor_als_string(zustand, zustand_name))
    
    ergebnis = matrix_mal_vektor(gatter, zustand, verbose=True)
    return ergebnis

def bell_zustand_erstellen():
    """Erstellt den Bell-Zustand |Φ⁺⟩ = 1/√2(|00⟩ + |11⟩)"""
    print_header("Bell-Zustand |Φ⁺⟩ erstellen")
    
    print("\nSchritt-für-Schritt Verschränkung:")
    print("\nStart: |00⟩")
    zustand = BasisZustand.ket00()
    print(vektor_als_string(zustand, "|ψ⟩"))
    
    # Schritt 1: H ⊗ I auf |00⟩
    print_step(1, "Hadamard auf Qubit 1 (H ⊗ I)")
    H = QuantenGatter.H()
    I = QuantenGatter.I()
    H_tensor_I = tensor_matrix_matrix(H, I, verbose=True)
    
    zustand = matrix_mal_vektor(H_tensor_I, zustand, verbose=True)
    print(f"\n→ Zustand nach H⊗I: 1/√2(|00⟩ + |10⟩)")
    print("   (Noch NICHT verschränkt - ist Produktzustand!)")
    
    # Schritt 2: CNOT
    print_step(2, "CNOT-Gatter anwenden")
    CNOT = QuantenGatter.CNOT()
    print(matrix_als_string(CNOT, "CNOT"))
    
    zustand = matrix_mal_vektor(CNOT, zustand, verbose=True)
    print(f"\n→ Zustand nach CNOT: 1/√2(|00⟩ + |11⟩) = |Φ⁺⟩")
    print("   ✓✓ JETZT VERSCHRÄNKT!")
    
    return zustand

def verschiedene_gatter_testen():
    """Testet verschiedene Quantengatter"""
    print_header("Verschiedene Quantengatter testen")
    
    # X-Gatter (NOT)
    print("\n" + "─"*70)
    print("X-Gatter (NOT): |0⟩ → |1⟩")
    print("─"*70)
    ket0 = BasisZustand.ket0()
    X = QuantenGatter.X()
    ergebnis = gatter_anwenden(X, ket0, "X", "|0⟩")
    print("\n✓ |0⟩ wurde zu |1⟩ geflippt!")
    
    # Hadamard
    print("\n" + "─"*70)
    print("Hadamard: |0⟩ → 1/√2(|0⟩ + |1⟩)")
    print("─"*70)
    H = QuantenGatter.H()
    ergebnis = gatter_anwenden(H, ket0, "H", "|0⟩")
    print("\n✓ Superposition erstellt!")
    
    # S-Gatter (mit komplexer Phase)
    print("\n" + "─"*70)
    print("S-Gatter: |1⟩ → i|1⟩")
    print("─"*70)
    ket1 = BasisZustand.ket1()
    S = QuantenGatter.S()
    ergebnis = gatter_anwenden(S, ket1, "S", "|1⟩")
    print("\n✓ Phase hinzugefügt!")

def zwei_qubits_operationen():
    """Demonstriert 2-Qubit-Operationen"""
    print_header("2-Qubit-Operationen")
    
    # Tensorprodukt von Zuständen
    print("\n" + "─"*70)
    print("Tensorprodukt: |0⟩ ⊗ |1⟩ = |01⟩")
    print("─"*70)
    ket0 = BasisZustand.ket0()
    ket1 = BasisZustand.ket1()
    ket01 = tensor_vektor_vektor(ket0, ket1, verbose=True)
    
    # H auf erstes Qubit
    print("\n" + "─"*70)
    print("H ⊗ I auf |01⟩")
    print("─"*70)
    H = QuantenGatter.H()
    I = QuantenGatter.I()
    H_I = tensor_matrix_matrix(H, I, verbose=True)
    ergebnis = matrix_mal_vektor(H_I, ket01, verbose=True)
    print("\n✓ Erstes Qubit in Superposition!")
    
    # CNOT auf |10⟩
    print("\n" + "─"*70)
    print("CNOT auf |10⟩ (Control=1, Target=0)")
    print("─"*70)
    ket10 = BasisZustand.ket10()
    CNOT = QuantenGatter.CNOT()
    ergebnis = gatter_anwenden(CNOT, ket10, "CNOT", "|10⟩")
    print("\n✓ Target wurde geflippt: |10⟩ → |11⟩")

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

if __name__ == "__main__":
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  QUANTEN-SIMULATOR - PURE PYTHON".center(68) + "█")
    print("█" + "  Tensorprodukte · Gatter · Verschränkung".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    while True:
        print("\n" + "="*70)
        print("MENÜ")
        print("="*70)
        print("\n1. Tensorprodukt: Vektor ⊗ Vektor")
        print("2. Tensorprodukt: Matrix ⊗ Matrix")
        print("3. Matrix-Vektor-Multiplikation")
        print("4. Verschiedene Quantengatter testen")
        print("5. 2-Qubit-Operationen")
        print("6. Bell-Zustand erstellen (Verschränkung!)")
        print("0. Beenden")
        
        wahl = input("\nWähle eine Option (0-6): ").strip()
        
        if wahl == "1":
            print_header("Beispiel: |0⟩ ⊗ |1⟩")
            ket0 = BasisZustand.ket0()
            ket1 = BasisZustand.ket1()
            tensor_vektor_vektor(ket0, ket1, verbose=True)
        
        elif wahl == "2":
            print_header("Beispiel: H ⊗ I")
            H = QuantenGatter.H()
            I = QuantenGatter.I()
            tensor_matrix_matrix(H, I, verbose=True)
        
        elif wahl == "3":
            print_header("Beispiel: H · |0⟩")
            H = QuantenGatter.H()
            ket0 = BasisZustand.ket0()
            matrix_mal_vektor(H, ket0, verbose=True)
        
        elif wahl == "4":
            verschiedene_gatter_testen()
        
        elif wahl == "5":
            zwei_qubits_operationen()
        
        elif wahl == "6":
            bell_zustand_erstellen()
        
        elif wahl == "0":
            print("\n" + "█"*70)
            print("█" + " "*68 + "█")
            print("█" + "  Auf Wiedersehen!".center(68) + "█")
            print("█" + " "*68 + "█")
            print("█"*70 + "\n")
            break
        
        else:
            print("\n❌ Ungültige Eingabe. Bitte wähle 0-6.")
        
        input("\n[Drücke Enter für das Menü...]")
