"""
Simplex-Algorithmus Tutorial
=============================
Dieses Skript erklärt den Simplex-Algorithmus Schritt für Schritt
und löst ein Beispiel-Optimierungsproblem.
"""

import numpy as np
from typing import Tuple, Optional
import sys


class SimplexSolver:
    """
    Eine Klasse, die den Simplex-Algorithmus implementiert und jeden Schritt erklärt.
    """
    
    def __init__(self, c, A, b, verbose=True):
        """
        Initialisiert das lineare Optimierungsproblem in Standardform:
        
        Maximiere: c^T * x
        Unter den Nebenbedingungen: A * x <= b
                                     x >= 0
        
        Parameter:
        - c: Koeffizientenvektor der Zielfunktion (zu maximieren)
        - A: Koeffizientenmatrix der Nebenbedingungen
        - b: Rechte Seite der Nebenbedingungen
        - verbose: Wenn True, werden alle Schritte detailliert ausgegeben
        """
        self.verbose = verbose
        self.iteration = 0
        
        # Konvertiere in Standardform mit Schlupfvariablen
        self.m, self.n = A.shape  # m = Anzahl Nebenbedingungen, n = Anzahl Variablen
        
        # Erstelle das Simplex-Tableau
        # [A | I | b]
        # [c | 0 | 0]
        self.tableau = np.zeros((self.m + 1, self.n + self.m + 1))
        
        # Fülle die Nebenbedingungen ein
        self.tableau[:self.m, :self.n] = A
        self.tableau[:self.m, self.n:self.n+self.m] = np.eye(self.m)  # Schlupfvariablen
        self.tableau[:self.m, -1] = b
        
        # Fülle die Zielfunktion ein (negative Koeffizienten für Maximierung)
        self.tableau[-1, :self.n] = -c
        
        # Basis-Variablen (anfangs sind das die Schlupfvariablen)
        self.basis = list(range(self.n, self.n + self.m))
        
        if self.verbose:
            self._print_header()
            self._print_tableau("Initialisierung")
    
    def _print_header(self):
        """Druckt eine informative Überschrift"""
        print("\n" + "="*80)
        print("SIMPLEX-ALGORITHMUS TUTORIAL")
        print("="*80)
        print("\nDer Simplex-Algorithmus löst lineare Optimierungsprobleme:")
        print("  Maximiere: c₁x₁ + c₂x₂ + ... + cₙxₙ")
        print("  Unter: a₁₁x₁ + a₁₂x₂ + ... + a₁ₙxₙ ≤ b₁")
        print("         a₂₁x₁ + a₂₂x₂ + ... + a₂ₙxₙ ≤ b₂")
        print("         ...")
        print("         x₁, x₂, ..., xₙ ≥ 0")
        print("\n" + "="*80 + "\n")
    
    def _print_tableau(self, title):
        """Druckt das aktuelle Simplex-Tableau"""
        print(f"\n{'─'*80}")
        print(f"📊 {title}")
        print(f"{'─'*80}")
        
        # Variable Namen
        var_names = [f"x{i+1}" for i in range(self.n)] + \
                   [f"s{i+1}" for i in range(self.m)] + ["RHS"]
        
        # Drucke Tableau
        print("\nBasis  |", "  ".join(f"{v:>6}" for v in var_names))
        print("─" * (9 + 8 * len(var_names)))
        
        for i in range(self.m):
            basis_var = f"s{self.basis[i]-self.n+1}" if self.basis[i] >= self.n else f"x{self.basis[i]+1}"
            row_str = f"{basis_var:>6} |"
            for j in range(len(var_names)):
                row_str += f"{self.tableau[i, j]:>7.2f} "
            print(row_str)
        
        print("─" * (9 + 8 * len(var_names)))
        z_row = "   Z   |"
        for j in range(len(var_names)):
            z_row += f"{self.tableau[-1, j]:>7.2f} "
        print(z_row)
        print()
    
    def _find_pivot_column(self) -> Optional[int]:
        """
        Findet die Pivot-Spalte (Eingangsvariable)
        Das ist die Spalte mit dem negativsten Wert in der Z-Zeile
        """
        z_row = self.tableau[-1, :-1]  # Letzte Zeile ohne RHS
        min_val = np.min(z_row)
        
        if min_val >= 0:
            return None  # Optimal gefunden
        
        pivot_col = np.argmin(z_row)
        
        if self.verbose:
            print(f"🎯 Schritt 1: Pivot-Spalte finden")
            print(f"   Suche negativsten Wert in Z-Zeile: {min_val:.2f}")
            var_name = f"x{pivot_col+1}" if pivot_col < self.n else f"s{pivot_col-self.n+1}"
            print(f"   ➜ Pivot-Spalte: {var_name} (Spalte {pivot_col})")
        
        return pivot_col
    
    def _find_pivot_row(self, pivot_col) -> Optional[int]:
        """
        Findet die Pivot-Zeile (Ausgangsvariable)
        Verwendet die Minimum-Ratio-Test
        """
        ratios = []
        valid_rows = []
        
        print(f"\n🎯 Schritt 2: Pivot-Zeile finden (Minimum-Ratio-Test)")
        print(f"   Berechne: RHS / Pivot-Spalten-Koeffizient")
        
        for i in range(self.m):
            if self.tableau[i, pivot_col] > 0:
                ratio = self.tableau[i, -1] / self.tableau[i, pivot_col]
                ratios.append(ratio)
                valid_rows.append(i)
                basis_var = f"s{self.basis[i]-self.n+1}" if self.basis[i] >= self.n else f"x{self.basis[i]+1}"
                print(f"   Zeile {i} ({basis_var}): {self.tableau[i, -1]:.2f} / {self.tableau[i, pivot_col]:.2f} = {ratio:.2f}")
            else:
                print(f"   Zeile {i}: Übersprungen (Koeffizient ≤ 0)")
        
        if not valid_rows:
            return None  # Unbeschränkt
        
        min_ratio_idx = np.argmin(ratios)
        pivot_row = valid_rows[min_ratio_idx]
        
        basis_var = f"s{self.basis[pivot_row]-self.n+1}" if self.basis[pivot_row] >= self.n else f"x{self.basis[pivot_row]+1}"
        print(f"   ➜ Kleinste Ratio: {ratios[min_ratio_idx]:.2f} in Zeile {pivot_row} ({basis_var})")
        
        return pivot_row
    
    def _pivot(self, pivot_row, pivot_col):
        """
        Führt die Pivot-Operation durch
        """
        pivot_element = self.tableau[pivot_row, pivot_col]
        
        old_basis = self.basis[pivot_row]
        new_basis = pivot_col
        
        old_var = f"s{old_basis-self.n+1}" if old_basis >= self.n else f"x{old_basis+1}"
        new_var = f"s{new_basis-self.n+1}" if new_basis >= self.n else f"x{new_basis+1}"
        
        print(f"\n🎯 Schritt 3: Pivot-Operation")
        print(f"   Pivot-Element: Zeile {pivot_row}, Spalte {pivot_col}")
        print(f"   Wert: {pivot_element:.2f}")
        print(f"   Basis-Tausch: {old_var} verlässt, {new_var} tritt ein")
        
        # Normalisiere die Pivot-Zeile
        self.tableau[pivot_row, :] /= pivot_element
        
        # Eliminiere alle anderen Einträge in der Pivot-Spalte
        for i in range(self.m + 1):
            if i != pivot_row:
                factor = self.tableau[i, pivot_col]
                self.tableau[i, :] -= factor * self.tableau[pivot_row, :]
        
        # Aktualisiere die Basis
        self.basis[pivot_row] = pivot_col
    
    def solve(self) -> Tuple[Optional[np.ndarray], Optional[float]]:
        """
        Löst das Optimierungsproblem mit dem Simplex-Algorithmus
        
        Rückgabe:
        - Optimale Lösung (x-Werte)
        - Optimaler Zielfunktionswert
        """
        max_iterations = 100
        
        while self.iteration < max_iterations:
            self.iteration += 1
            
            if self.verbose:
                print(f"\n{'═'*80}")
                print(f"ITERATION {self.iteration}")
                print(f"{'═'*80}")
            
            # Schritt 1: Finde Pivot-Spalte
            pivot_col = self._find_pivot_column()
            
            if pivot_col is None:
                if self.verbose:
                    print("\n✅ OPTIMALE LÖSUNG GEFUNDEN!")
                    print("   Alle Koeffizienten in der Z-Zeile sind ≥ 0")
                break
            
            # Schritt 2: Finde Pivot-Zeile
            pivot_row = self._find_pivot_row(pivot_col)
            
            if pivot_row is None:
                if self.verbose:
                    print("\n⚠️  Problem ist unbeschränkt!")
                return None, None
            
            # Schritt 3: Pivot-Operation
            self._pivot(pivot_row, pivot_col)
            
            if self.verbose:
                self._print_tableau(f"Nach Iteration {self.iteration}")
        
        # Extrahiere die Lösung
        solution = np.zeros(self.n)
        for i, basis_var in enumerate(self.basis):
            if basis_var < self.n:
                solution[basis_var] = self.tableau[i, -1]
        
        optimal_value = self.tableau[-1, -1]
        
        if self.verbose:
            self._print_solution(solution, optimal_value)
        
        return solution, optimal_value
    
    def _print_solution(self, solution, optimal_value):
        """Druckt die finale Lösung"""
        print(f"\n{'═'*80}")
        print("🎉 FINALE LÖSUNG")
        print(f"{'═'*80}")
        print("\nOptimale Werte der Variablen:")
        for i in range(len(solution)):
            print(f"   x{i+1} = {solution[i]:.4f}")
        print(f"\nMaximaler Zielfunktionswert:")
        print(f"   Z = {optimal_value:.4f}")
        print(f"{'═'*80}\n")


def beispiel_1():
    """
    Beispiel 1: Klassisches Produktionsplanungsproblem
    
    Ein Unternehmen stellt zwei Produkte A und B her.
    - Produkt A bringt 3€ Gewinn, Produkt B bringt 5€ Gewinn
    - Für A werden 1h Arbeit benötigt, für B 2h
    - Verfügbare Arbeitszeit: 4h
    - Für A werden 2 Einheiten Material benötigt, für B 1 Einheit
    - Verfügbares Material: 4 Einheiten
    
    Maximiere: 3x₁ + 5x₂
    Unter: x₁ + 2x₂ ≤ 4  (Arbeitszeit)
           2x₁ + x₂ ≤ 4  (Material)
           x₁, x₂ ≥ 0
    """
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*25 + "BEISPIEL 1: PRODUKTIONSPLANUNG" + " "*23 + "║")
    print("╚" + "═"*78 + "╝")
    
    print("\n📝 Problembeschreibung:")
    print("   Maximiere: 3x₁ + 5x₂ (Gewinn)")
    print("   Unter den Nebenbedingungen:")
    print("      x₁ + 2x₂ ≤ 4  (Arbeitszeit)")
    print("      2x₁ + x₂ ≤ 4  (Material)")
    print("      x₁, x₂ ≥ 0")
    
    c = np.array([3, 5])  # Zielfunktion
    A = np.array([
        [1, 2],  # Arbeitszeit
        [2, 1]   # Material
    ])
    b = np.array([4, 4])
    
    solver = SimplexSolver(c, A, b, verbose=True)
    solution, value = solver.solve()
    
    return solution, value


def beispiel_2():
    """
    Beispiel 2: Größeres Problem mit 3 Variablen
    
    Maximiere: 2x₁ + 3x₂ + 4x₃
    Unter: x₁ + x₂ + 2x₃ ≤ 5
           2x₁ + x₂ + x₃ ≤ 4
           x₁, x₂, x₃ ≥ 0
    """
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*22 + "BEISPIEL 2: ERWEITERTE OPTIMIERUNG" + " "*22 + "║")
    print("╚" + "═"*78 + "╝")
    
    print("\n📝 Problembeschreibung:")
    print("   Maximiere: 2x₁ + 3x₂ + 4x₃")
    print("   Unter den Nebenbedingungen:")
    print("      x₁ + x₂ + 2x₃ ≤ 5")
    print("      2x₁ + x₂ + x₃ ≤ 4")
    print("      x₁, x₂, x₃ ≥ 0")
    
    c = np.array([2, 3, 4])
    A = np.array([
        [1, 1, 2],
        [2, 1, 1]
    ])
    b = np.array([5, 4])
    
    solver = SimplexSolver(c, A, b, verbose=True)
    solution, value = solver.solve()
    
    return solution, value


def hauptmenu():
    """Zeigt das Hauptmenü und lässt den Benutzer ein Beispiel wählen"""
    while True:
        print("\n" + "╔" + "═"*78 + "╗")
        print("║" + " "*20 + "SIMPLEX-ALGORITHMUS LERNPROGRAMM" + " "*26 + "║")
        print("╚" + "═"*78 + "╝")
        print("\n📚 Wähle ein Beispiel:")
        print("   [1] Beispiel 1: Produktionsplanung (2 Variablen)")
        print("   [2] Beispiel 2: Erweiterte Optimierung (3 Variablen)")
        print("   [3] Eigenes Problem eingeben")
        print("   [0] Beenden")
        
        wahl = input("\nDeine Wahl: ").strip()
        
        if wahl == "1":
            beispiel_1()
        elif wahl == "2":
            beispiel_2()
        elif wahl == "3":
            eigenes_problem()
        elif wahl == "0":
            print("\n👋 Auf Wiedersehen!")
            break
        else:
            print("\n❌ Ungültige Eingabe. Bitte wähle 0, 1, 2 oder 3.")
        
        input("\n⏸️  Drücke Enter, um fortzufahren...")


def eigenes_problem():
    """Erlaubt dem Benutzer, ein eigenes Problem einzugeben"""
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*26 + "EIGENES PROBLEM EINGEBEN" + " "*28 + "║")
    print("╚" + "═"*78 + "╝")
    
    try:
        n = int(input("\nAnzahl der Variablen: "))
        m = int(input("Anzahl der Nebenbedingungen: "))
        
        print(f"\nZielfunktion (zu maximieren): c₁x₁ + c₂x₂ + ... + c{n}x{n}")
        c = np.zeros(n)
        for i in range(n):
            c[i] = float(input(f"  c{i+1} = "))
        
        print(f"\nNebenbedingungen (Form: a₁x₁ + a₂x₂ + ... + a{n}x{n} ≤ b)")
        A = np.zeros((m, n))
        b = np.zeros(m)
        
        for i in range(m):
            print(f"\nNebenbedingung {i+1}:")
            for j in range(n):
                A[i, j] = float(input(f"  a{i+1},{j+1} = "))
            b[i] = float(input(f"  b{i+1} = "))
        
        print("\n" + "─"*80)
        solver = SimplexSolver(c, A, b, verbose=True)
        solver.solve()
        
    except ValueError:
        print("\n❌ Fehler: Bitte gib nur Zahlen ein.")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                               ║
    ║                     WILLKOMMEN ZUM SIMPLEX-ALGORITHMUS                        ║
    ║                              LERNPROGRAMM                                     ║
    ║                                                                               ║
    ║  Dieses Programm zeigt dir Schritt für Schritt, wie der Simplex-Algorithmus  ║
    ║  funktioniert und löst lineare Optimierungsprobleme interaktiv.              ║
    ║                                                                               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    hauptmenu()
