"""
Grover-Algorithmus - Geheimzahl finden
=======================================

Zeigt ALLE Matrizen und Rechnungen im Detail!
Nur das Geheimzahl-Beispiel, dafür sehr ausführlich.
"""

import math

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_step(step, title):
    print("\n" + "-"*70)
    print(f"SCHRITT {step}: {title}")
    print("-"*70)

def zeige_matrix(matrix, name="Matrix", max_size=8):
    """Zeigt eine Matrix schön formatiert"""
    size = len(matrix)
    
    if size > max_size:
        print(f"\n{name} ({size}×{size}) - zu groß zum Anzeigen")
        return
    
    print(f"\n{name} ({size}×{size}):")
    
    # Kopfzeile
    print("      ", end="")
    for j in range(size):
        print(f"|{j}⟩    ", end="")
    print()
    print("    " + "-" * (size * 7 + 2))
    
    # Zeilen
    for i in range(size):
        print(f"|{i}⟩ | ", end="")
        for j in range(size):
            val = matrix[i][j]
            if isinstance(val, complex):
                if abs(val.imag) < 1e-10:
                    print(f"{val.real:5.2f} ", end="")
                else:
                    print(f"{val.real:.1f}{val.imag:+.1f}j ", end="")
            else:
                print(f"{val:5.2f} ", end="")
        print()

def zeige_vektor(vektor, name="Vektor"):
    """Zeigt einen Vektor mit Wahrscheinlichkeiten"""
    n_qubits = int(math.log2(len(vektor)))
    
    print(f"\n{name}:")
    print("  Index | Binär | Amplitude      | Wahrscheinlichkeit")
    print("  " + "-" * 55)
    
    for i, amp in enumerate(vektor):
        binary = format(i, f'0{n_qubits}b')
        prob = abs(amp)**2
        
        if isinstance(amp, complex):
            if abs(amp.imag) < 1e-10:
                amp_str = f"{amp.real:6.3f}      "
            else:
                sign = "+" if amp.imag >= 0 else ""
                amp_str = f"{amp.real:.3f}{sign}{amp.imag:.3f}j"
        else:
            amp_str = f"{amp:6.3f}      "
        
        print(f"    {i}   | {binary}  | {amp_str} | {prob:6.2%}")

# ============================================================================
# MATRIX-OPERATIONEN
# ============================================================================

def hadamard_1qubit():
    """Hadamard für 1 Qubit"""
    s = 1 / math.sqrt(2)
    return [[s, s], [s, -s]]

def tensor_produkt_matrix(A, B):
    """A ⊗ B"""
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

def hadamard_n_qubits(n):
    """Hadamard auf n Qubits"""
    H = hadamard_1qubit()
    result = H
    
    for i in range(n - 1):
        result = tensor_produkt_matrix(result, H)
    
    return result

def matrix_mal_vektor(matrix, vektor):
    """Matrix × Vektor"""
    result = []
    for i in range(len(matrix)):
        summe = 0
        for j in range(len(matrix[0])):
            summe += matrix[i][j] * vektor[j]
        result.append(summe)
    return result

# ============================================================================
# GROVER-KOMPONENTEN
# ============================================================================

def funktion_geheimzahl(geheimzahl):
    """Funktion die Geheimzahl prüft"""
    def f(x):
        return 1 if x == geheimzahl else 0
    f.geheimzahl = geheimzahl
    f.beschreibung = "Prüft ob x == Geheimzahl"
    return f

def oracle_aus_funktion(n, f):
    """Baut Oracle aus Funktion"""
    size = 2**n
    
    # Identitätsmatrix
    matrix = [[1 if i == j else 0 for j in range(size)] for i in range(size)]
    
    # Teste alle Werte
    loesungen = []
    for x in range(size):
        if f(x) == 1:
            matrix[x][x] = -1
            loesungen.append(x)
    
    return matrix, loesungen

def diffusion_operator(n):
    """D = 2|s⟩⟨s| - I"""
    size = 2**n
    
    # 2|s⟩⟨s| - I
    matrix = [[-2/size for _ in range(size)] for _ in range(size)]
    
    for i in range(size):
        matrix[i][i] += 2/size + 1
    
    return matrix

# ============================================================================
# HAUPT-ALGORITHMUS
# ============================================================================

def grover_geheimzahl_detailliert():
    """
    Grover für Geheimzahl mit ALLEN Details
    """
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  GROVER-ALGORITHMUS: GEHEIMZAHL FINDEN".center(68) + "█")
    print("█" + "  Alle Matrizen und Rechnungen im Detail".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    # Setup
    n_qubits = 2
    N = 2**n_qubits
    geheime_zahl = 2  # Die Geheimzahl
    
    print("\n PROBLEM:")
    print(f"  Jemand hat eine Zahl zwischen 0 und {N-1} gewählt.")
    print(f"  Du bekommst eine Funktion f(x), die prüft ob x richtig ist.")
    print(f"  Finde die Geheimzahl!")
    
    print("\n  SETUP:")
    print(f"  Anzahl Qubits: {n_qubits}")
    print(f"  Suchraum: {N} Einträge (0, 1, 2, 3)")
    print(f"  Geheimzahl: ??? (versteckt!)")
    
    # Funktion erstellen
    f = funktion_geheimzahl(geheime_zahl)
    
    # ========================================================================
    print_step(1, "Initialisierung")
    # ========================================================================
    
    print("\nStarte mit |00⟩:")
    zustand = [0] * N
    zustand[0] = 1
    
    zeige_vektor(zustand, "Startzustand")
    
    # ========================================================================
    print_step(2, "Hadamard-Transformation → Superposition")
    # ========================================================================
    
    print("\nWende Hadamard auf beide Qubits an: H ⊗ H")
    
    H = hadamard_n_qubits(n_qubits)
    zeige_matrix(H, "Hadamard-Matrix H⊗H")
    
    print("\n Berechnung: H⊗H × |00⟩")
    zustand = matrix_mal_vektor(H, zustand)
    
    zeige_vektor(zustand, "Zustand nach Hadamard")
    
    print("\n Interpretation:")
    print(f"  Alle {N} Zustände haben gleiche Amplitude 1/√{N} = {1/math.sqrt(N):.3f}")
    print(f"  Jeder Zustand hat Wahrscheinlichkeit 1/{N} = {1/N:.1%}")
    
    # ========================================================================
    print_step(3, "Oracle erstellen")
    # ========================================================================
    
    print("\n Teste die Funktion f(x) für alle Werte:")
    print("\n  x | Binär | f(x) | Bedeutung")
    print("  " + "-" * 40)
    for x in range(N):
        binary = format(x, f'0{n_qubits}b')
        result = f(x)
        bedeutung = "← LÖSUNG!" if result == 1 else ""
        print(f"  {x} | {binary}  |  {result}   | {bedeutung}")
    
    O, loesungen = oracle_aus_funktion(n_qubits, f)
    
    zeige_matrix(O, "Oracle-Matrix O")
    
    print("\n Interpretation:")
    print(f"  Diagonal-Matrix mit -1 an Position {loesungen[0]}")
    print(f"  O|{loesungen[0]}⟩ = -|{loesungen[0]}⟩  (Phase flip!)")
    print(f"  O|i⟩ = +|i⟩  für alle anderen i")
    
    # ========================================================================
    print_step(4, "Diffusion-Operator erstellen")
    # ========================================================================
    
    print("\nDiffusion-Operator: D = 2|s⟩⟨s| - I")
    print(f"wobei |s⟩ = 1/√{N} (|0⟩ + |1⟩ + |2⟩ + |3⟩)")
    
    D = diffusion_operator(n_qubits)
    
    zeige_matrix(D, "Diffusion-Matrix D")
    
    print("\n Interpretation:")
    print(f"  Spiegelt alle Amplituden am Durchschnitt")
    print(f"  Verstärkt überdurchschnittliche, schwächt unterdurchschnittliche")
    
    # ========================================================================
    print_step(5, "Grover-Operator G = D · O")
    # ========================================================================
    
    print("\nBerechne G = D × O (Matrix-Multiplikation):")
    
    # G = D · O
    G = [[0 for _ in range(N)] for _ in range(N)]
    for i in range(N):
        for j in range(N):
            for k in range(N):
                G[i][j] += D[i][k] * O[k][j]
    
    zeige_matrix(G, "Grover-Operator G = D·O")
    
    print("\n Interpretation:")
    print(f"  Eine Anwendung von G = erst Oracle, dann Diffusion")
    
    # ========================================================================
    print_step(6, "Grover-Iterationen")
    # ========================================================================
    
    k_optimal = round((math.pi / 4) * math.sqrt(N))
    
    print(f"\nOptimale Anzahl Iterationen: k = ⌊π/4 · √N⌋")
    print(f"                               = ⌊π/4 · √{N}⌋")
    print(f"                               = {k_optimal}")
    
    for iteration in range(k_optimal):
        print(f"\n{'='*70}")
        print(f"  ITERATION {iteration + 1}/{k_optimal}")
        print(f"{'='*70}")
        
        print("\n Wende G an:")
        zustand_alt = zustand.copy()
        zustand = matrix_mal_vektor(G, zustand)
        
        zeige_vektor(zustand, f"Zustand nach Iteration {iteration + 1}")
        
        # Zeige die Änderung
        print("\n Änderung der Amplituden:")
        for i in range(N):
            alt = abs(zustand_alt[i])**2
            neu = abs(zustand[i])**2
            diff = neu - alt
            symbol = "↑" if diff > 0 else "↓" if diff < 0 else "→"
            marker = " ← Lösung" if i == loesungen[0] else ""
            print(f"  |{i}⟩: {alt:6.1%} → {neu:6.1%}  ({diff:+6.1%}) {symbol}{marker}")
    
    # ========================================================================
    print_step(7, "Messung")
    # ========================================================================
    
    print("\n Messe den Zustand:")
    
    wahrscheinlichkeiten = [abs(amp)**2 for amp in zustand]
    gefunden_index = wahrscheinlichkeiten.index(max(wahrscheinlichkeiten))
    gefunden_prob = wahrscheinlichkeiten[gefunden_index]
    
    print(f"\n  Höchste Wahrscheinlichkeit: Index {gefunden_index}")
    print(f"  Wahrscheinlichkeit: {gefunden_prob:.1%}")
    print(f"  Binär: |{format(gefunden_index, f'0{n_qubits}b')}⟩")
    
    # ========================================================================
    print_step(8, "Verifikation")
    # ========================================================================
    
    print(f"\n Prüfe mit der Funktion f:")
    print(f"  f({gefunden_index}) = {f(gefunden_index)}")
    
    if f(gefunden_index) == 1:
        print(f"\n   ERFOLG!")
        print(f"  Die Geheimzahl war {gefunden_index}!")
    else:
        print(f"\n   FEHLER!")
        print(f"  Das ist nicht die Lösung.")
    
    print(f"\n  (Die echte Geheimzahl war {geheime_zahl})")
    
    # ========================================================================
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  ZUSAMMENFASSUNG".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    # ========================================================================
    
    print(f"""
 STATISTIK:
  Suchraum:           {N} Einträge
  Geheimzahl:         {geheime_zahl}
  Gefunden:           {gefunden_index}
  Erfolg:             {"Ja " if gefunden_index == geheime_zahl else "Nein "}
  
  Grover-Iterationen: {k_optimal}
  Wahrscheinlichkeit: {gefunden_prob:.1%}
  
 VERGLEICH:
  Klassisch:          ~{N/2:.0f} Versuche (Durchschnitt)
  Grover:             ~{k_optimal} Iterationen
  Speedup:            ~{N/(2*k_optimal):.1f}
  
 KERNIDEE:
  1. Superposition:   Alle Werte gleichzeitig
  2. Oracle:          Markiere Lösung (Phase flip)
  3. Diffusion:       Verstärke markierte Amplitude
  4. Wiederhole:      √N mal
  5. Messen:          Finde Lösung mit hoher Wahrscheinlichkeit
""")
    
    print("\n" + "█"*70 + "\n")

# ============================================================================
# START
# ============================================================================

if __name__ == "__main__":
    grover_geheimzahl_detailliert()
