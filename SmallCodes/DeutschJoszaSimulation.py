"""
Deutsch-Jozsa-Algorithmus Simulation
=====================================

Simuliert den Deutsch-Jozsa-Algorithmus klassisch und quantenmechanisch.
Zeigt den Quantenvorteil: 1 Abfrage statt exponentiell vieler!

Pure Python - keine Quantencomputer-Bibliotheken nötig.
"""

import math
import random

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
    """Formatiert einen Vektor schön"""
    def format_wert(val):
        if isinstance(val, complex):
            if abs(val.imag) < 1e-10:
                return f"{val.real:.3f}"
            elif abs(val.real) < 1e-10:
                return f"{val.imag:.3f}j"
            else:
                sign = "+" if val.imag >= 0 else ""
                return f"({val.real:.3f}{sign}{val.imag:.3f}j)"
        else:
            return f"{val:.3f}"
    
    lines = [f"{name} = ["]
    for val in v:
        lines.append(f"      {format_wert(val)}")
    lines.append("     ]ᵀ")
    return "\n".join(lines)

# ============================================================================
# FUNKTIONEN DEFINIEREN
# ============================================================================

def erstelle_konstante_funktion(n_bits, wert):
    """
    Erstellt eine konstante Funktion.
    
    Args:
        n_bits: Anzahl der Input-Bits
        wert: Ausgabewert (0 oder 1)
    
    Returns:
        Funktion, die immer wert zurückgibt
    """
    def f(x):
        return wert
    
    f.typ = "konstant"
    f.beschreibung = f"f(x) = {wert} für alle x"
    return f

def erstelle_balancierte_funktion(n_bits):
    """
    Erstellt eine zufällige balancierte Funktion.
    
    Args:
        n_bits: Anzahl der Input-Bits
    
    Returns:
        Funktion, die für genau die Hälfte der Inputs 1 zurückgibt
    """
    # Erstelle alle möglichen Inputs
    anzahl = 2**n_bits
    alle_inputs = list(range(anzahl))
    
    # Wähle zufällig die Hälfte für Ausgabe 1
    random.shuffle(alle_inputs)
    ones_set = set(alle_inputs[:anzahl//2])
    
    def f(x):
        return 1 if x in ones_set else 0
    
    f.typ = "balanciert"
    f.beschreibung = f"f(x) = 1 für {len(ones_set)} von {anzahl} Inputs"
    return f

def zeige_funktionstabelle(f, n_bits):
    """Zeigt die komplette Wahrheitstabelle einer Funktion"""
    print(f"\nFunktionstabelle ({f.beschreibung}):")
    print("-" * 40)
    print("Input (binär)  | Input (dez) | Output")
    print("-" * 40)
    
    outputs = []
    for x in range(2**n_bits):
        binary = format(x, f'0{n_bits}b')
        output = f(x)
        outputs.append(output)
        print(f"     {binary}      |     {x:2d}      |   {output}")
    
    print("-" * 40)
    anzahl_ones = sum(outputs)
    anzahl_zeros = len(outputs) - anzahl_ones
    print(f"Statistik: {anzahl_zeros} Nullen, {anzahl_ones} Einsen")
    
    if anzahl_ones == 0 or anzahl_ones == len(outputs):
        print("→ KONSTANT")
    elif anzahl_ones == len(outputs) // 2:
        print("→ BALANCIERT")
    else:
        print("→ WEDER KONSTANT NOCH BALANCIERT (sollte nicht vorkommen!)")

# ============================================================================
# KLASSISCHER ALGORITHMUS
# ============================================================================

def deutsch_jozsa_klassisch(f, n_bits, verbose=True):
    """
    Klassischer Deutsch-Jozsa-Algorithmus.
    
    Testet die Funktion, bis sicher ist, ob konstant oder balanciert.
    
    Args:
        f: Die zu testende Funktion
        n_bits: Anzahl der Input-Bits
        verbose: Ob Details ausgegeben werden sollen
    
    Returns:
        ("konstant" oder "balanciert", anzahl_abfragen)
    """
    if verbose:
        print_header("KLASSISCHER ALGORITHMUS")
        print(f"\nTeste Funktion mit {n_bits} Bits ({2**n_bits} mögliche Inputs)")
    
    max_tests = 2**(n_bits-1) + 1
    if verbose:
        print(f"Worst-Case: Bis zu {max_tests} Tests nötig")
    
    # Teste die Funktion
    erster_wert = f(0)
    abfragen = 1
    
    if verbose:
        print(f"\nTest 1: f(0) = {erster_wert}")
    
    # Teste weitere Werte
    for x in range(1, max_tests):
        aktueller_wert = f(x)
        abfragen += 1
        
        if verbose:
            binary = format(x, f'0{n_bits}b')
            print(f"Test {abfragen}: f({binary}) = f({x}) = {aktueller_wert}")
        
        # Wenn unterschiedlich → balanciert!
        if aktueller_wert != erster_wert:
            if verbose:
                print(f"\n✓ Unterschiedliche Werte gefunden!")
                print(f"  f(0) = {erster_wert} ≠ f({x}) = {aktueller_wert}")
                print(f"  → Funktion ist BALANCIERT")
                print(f"\nAnzahl Abfragen: {abfragen}")
            return "balanciert", abfragen
    
    # Alle getesteten Werte gleich → konstant
    if verbose:
        print(f"\n✓ Alle {abfragen} Tests ergaben {erster_wert}")
        print(f"  → Funktion ist KONSTANT")
        print(f"\nAnzahl Abfragen: {abfragen}")
    
    return "konstant", abfragen

# ============================================================================
# QUANTENMECHANISCHE HILFSFUNKTIONEN
# ============================================================================

def hadamard_matrix(n):
    """
    Erstellt die n-Qubit Hadamard-Matrix.
    
    H⊗ⁿ = H ⊗ H ⊗ ... ⊗ H (n mal)
    """
    # Basis: 1-Qubit Hadamard
    H1 = [[1/math.sqrt(2), 1/math.sqrt(2)],
          [1/math.sqrt(2), -1/math.sqrt(2)]]
    
    if n == 1:
        return H1
    
    # Tensorprodukt für mehrere Qubits
    result = H1
    for _ in range(n - 1):
        result = tensor_produkt_matrix(result, H1)
    
    return result

def tensor_produkt_matrix(A, B):
    """Berechnet das Tensorprodukt zweier Matrizen"""
    rows_A, cols_A = len(A), len(A[0])
    rows_B, cols_B = len(B), len(B[0])
    
    result = [[0 for _ in range(cols_A * cols_B)] 
              for _ in range(rows_A * rows_B)]
    
    for i in range(rows_A):
        for j in range(cols_A):
            for k in range(rows_B):
                for l in range(cols_B):
                    result[i * rows_B + k][j * cols_B + l] = A[i][j] * B[k][l]
    
    return result

def matrix_mal_vektor(matrix, vektor):
    """Multipliziert eine Matrix mit einem Vektor"""
    result = [0] * len(matrix)
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            result[i] += matrix[i][j] * vektor[j]
    return result

def oracle_matrix(f, n):
    """
    Erstellt die Oracle-Matrix für die Funktion f.
    
    Das Oracle implementiert: |x⟩|y⟩ → |x⟩|y ⊕ f(x)⟩
    wobei ⊕ XOR ist.
    """
    size = 2**(n + 1)  # n Qubits + 1 Hilfsqubit
    matrix = [[0 for _ in range(size)] for _ in range(size)]
    
    for i in range(size):
        # i repräsentiert |x⟩|y⟩
        # Obere n Bits = x, unterste Bit = y
        x = i >> 1  # Obere n Bits
        y = i & 1   # Unterste Bit
        
        # Berechne neuen Zustand
        new_y = y ^ f(x)  # XOR
        new_i = (x << 1) | new_y
        
        matrix[new_i][i] = 1
    
    return matrix

# ============================================================================
# QUANTENALGORITHMUS
# ============================================================================

def deutsch_jozsa_quantum(f, n_bits, verbose=True):
    """
    Quanten-Deutsch-Jozsa-Algorithmus.
    
    Bestimmt mit EINER Abfrage ob konstant oder balanciert.
    
    Args:
        f: Die zu testende Funktion
        n_bits: Anzahl der Input-Bits
        verbose: Ob Details ausgegeben werden sollen
    
    Returns:
        ("konstant" oder "balanciert", anzahl_abfragen)
    """
    if verbose:
        print_header("QUANTEN-ALGORITHMUS")
        print(f"\nSimuliere {n_bits}-Qubit Deutsch-Jozsa")
    
    # Initialisierung
    if verbose:
        print_step(1, "Initialisierung")
        print(f"Starte mit |0...0⟩|1⟩ ({n_bits} Qubits + 1 Hilfsqubit)")
    
    # Zustandsvektor: n Qubits in |0⟩, 1 Qubit in |1⟩
    # |00...01⟩ (letztes Bit ist 1)
    dim = 2**(n_bits + 1)
    zustand = [0] * dim
    zustand[1] = 1  # |00...01⟩
    
    if verbose and n_bits <= 2:
        print(vektor_als_string(zustand, "Zustand"))
    
    # Schritt 2: Hadamard auf alle Qubits
    if verbose:
        print_step(2, "Hadamard auf alle Qubits")
        print(f"Bringe alle {n_bits + 1} Qubits in Superposition")
    
    H = hadamard_matrix(n_bits + 1)
    zustand = matrix_mal_vektor(H, zustand)
    
    if verbose:
        print(f"✓ Zustand ist jetzt in Superposition über alle {2**n_bits} Inputs!")
        if n_bits <= 2:
            print(vektor_als_string(zustand, "Zustand nach H"))
    
    # Schritt 3: Oracle (Funktionsauswertung)
    if verbose:
        print_step(3, "Oracle anwenden (Funktion auswerten)")
        print(f"Wende f auf ALLE {2**n_bits} Werte GLEICHZEITIG an!")
        print("Dies ist die einzige Funktionsabfrage!")
    
    oracle = oracle_matrix(f, n_bits)
    zustand = matrix_mal_vektor(oracle, zustand)
    
    if verbose:
        print("✓ Funktion wurde auf alle Inputs in Superposition ausgewertet")
        if n_bits <= 2:
            print(vektor_als_string(zustand, "Zustand nach Oracle"))
    
    # Schritt 4: Hadamard auf die ersten n Qubits
    if verbose:
        print_step(4, "Hadamard auf Arbeitsqubits")
        print("Bringe Interferenz-Information zusammen")
    
    # Hadamard nur auf ersten n Qubits
    H_work = hadamard_matrix(n_bits)
    I = [[1, 0], [0, 1]]  # Identität auf Hilfsqubit
    H_gesamt = tensor_produkt_matrix(H_work, I)
    zustand = matrix_mal_vektor(H_gesamt, zustand)
    
    if verbose:
        print("✓ Interferenz ausgewertet")
        if n_bits <= 2:
            print(vektor_als_string(zustand, "Zustand nach 2. Hadamard"))
    
    # Schritt 5: Messung
    if verbose:
        print_step(5, "Messung der ersten n Qubits")
    
    # Berechne Wahrscheinlichkeit für |00...0⟩ in ersten n Qubits
    # Das sind die Zustände 0 und 1 (Hilfsqubit kann 0 oder 1 sein)
    prob_all_zero = abs(zustand[0])**2 + abs(zustand[1])**2
    
    if verbose:
        print(f"\nWahrscheinlichkeit für |0...0⟩: {prob_all_zero:.4f}")
        print(f"Wahrscheinlichkeit für andere: {1-prob_all_zero:.4f}")
    
    # Entscheidung
    if prob_all_zero > 0.99:  # Fast 1
        ergebnis = "konstant"
        if verbose:
            print(f"\n✓ Messung ergibt |0...0⟩")
            print(f"  → Konstruktive Interferenz bei |0⟩")
            print(f"  → Funktion ist KONSTANT")
    else:  # Fast 0
        ergebnis = "balanciert"
        if verbose:
            print(f"\n✓ Messung ergibt NICHT |0...0⟩")
            print(f"  → Destruktive Interferenz bei |0⟩")
            print(f"  → Funktion ist BALANCIERT")
    
    if verbose:
        print(f"\nAnzahl Funktionsabfragen: 1")
    
    return ergebnis, 1

# ============================================================================
# VERGLEICH
# ============================================================================

def vergleiche_algorithmen(n_bits=3):
    """Vergleicht klassischen und Quantenalgorithmus"""
    
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  DEUTSCH-JOZSA ALGORITHMUS VERGLEICH".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    # Test 1: Konstante Funktion (f(x) = 0)
    print_header(f"TEST 1: KONSTANTE FUNKTION (n={n_bits})")
    print("\nFunktion: f(x) = 0 für alle x")
    
    f = erstelle_konstante_funktion(n_bits, 0)
    zeige_funktionstabelle(f, n_bits)
    
    # Klassisch
    klassisch_ergebnis, klassisch_abfragen = deutsch_jozsa_klassisch(f, n_bits)
    
    # Quantum
    quantum_ergebnis, quantum_abfragen = deutsch_jozsa_quantum(f, n_bits)
    
    # Vergleich
    print("\n" + "="*70)
    print("VERGLEICH:")
    print("="*70)
    print(f"Klassisch:  {klassisch_ergebnis:12s}  ({klassisch_abfragen} Abfragen)")
    print(f"Quantum:    {quantum_ergebnis:12s}  ({quantum_abfragen} Abfrage)")
    print(f"Speedup:    {klassisch_abfragen}× schneller!")
    
    # Test 2: Balancierte Funktion
    print_header(f"TEST 2: BALANCIERTE FUNKTION (n={n_bits})")
    print(f"\nFunktion: f(x) = 1 für genau {2**(n_bits-1)} von {2**n_bits} Inputs")
    
    f = erstelle_balancierte_funktion(n_bits)
    zeige_funktionstabelle(f, n_bits)
    
    # Klassisch
    klassisch_ergebnis, klassisch_abfragen = deutsch_jozsa_klassisch(f, n_bits)
    
    # Quantum
    quantum_ergebnis, quantum_abfragen = deutsch_jozsa_quantum(f, n_bits)
    
    # Vergleich
    print("\n" + "="*70)
    print("VERGLEICH:")
    print("="*70)
    print(f"Klassisch:  {klassisch_ergebnis:12s}  ({klassisch_abfragen} Abfragen)")
    print(f"Quantum:    {quantum_ergebnis:12s}  ({quantum_abfragen} Abfrage)")
    print(f"Speedup:    {klassisch_abfragen}× schneller!")
    
    # Gesamtvergleich
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  FAZIT".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    print(f"""
Der Quantenalgorithmus braucht IMMER nur 1 Abfrage!
Der klassische Algorithmus braucht bis zu {2**(n_bits-1) + 1} Abfragen.

Das ist ein exponentieller Vorteil: O(1) vs. O(2ⁿ)

Je mehr Qubits, desto größer der Unterschied:
  n=1:  Quantum: 1,  Klassisch: 2      (2× schneller)
  n=3:  Quantum: 1,  Klassisch: 5      (5× schneller)
  n=5:  Quantum: 1,  Klassisch: 17     (17× schneller)
  n=10: Quantum: 1,  Klassisch: 513    (513× schneller!)
  n=20: Quantum: 1,  Klassisch: 524289 (>500000× schneller!!)
""")

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

if __name__ == "__main__":
    # Einfacher Test mit 2 Bits
    print("\n" + "="*70)
    print("  Möchtest du einen schnellen Demo (n=2) oder")
    print("  einen ausführlichen Vergleich (n=3)?")
    print("="*70)
    print("\n1 - Schneller Demo (n=2, einfach zu folgen)")
    print("2 - Ausführlicher Vergleich (n=3)")
    print("3 - Großer Vergleich (n=4, viele Zustände)")
    
    wahl = input("\nWähle (1-3, oder Enter für Demo): ").strip()
    
    if wahl == "2":
        vergleiche_algorithmen(n_bits=3)
    elif wahl == "3":
        vergleiche_algorithmen(n_bits=4)
    else:
        vergleiche_algorithmen(n_bits=2)
    
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Simulation abgeschlossen!".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70 + "\n")
