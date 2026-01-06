"""
Turing Machine zu Clockwise Turing Machine Konverter
Basierend auf Neary & Woods (2005)
"""

class TuringMachine:
    """Klassische Turing-Maschine"""
    def __init__(self, states, symbols, blank, transitions, start_state, halt_states):
        self.states = states
        self.symbols = symbols
        self.blank = blank
        self.transitions = transitions  # Dict: (state, symbol) -> (new_symbol, direction, new_state)
        self.start_state = start_state
        self.halt_states = halt_states

    def __repr__(self):
        return f"TM(states={len(self.states)}, symbols={len(self.symbols)})"


class ClockwiseTM:
    """Clockwise Turing-Maschine mit zirkulärem Tape"""
    def __init__(self, states, symbols, transitions, start_state, halt_state):
        self.states = states
        self.symbols = symbols
        self.transitions = transitions  # Dict: (state, symbol) -> (write_value, next_state)
        self.start_state = start_state
        self.halt_state = halt_state

    def __repr__(self):
        return f"CTM(states={len(self.states)}, symbols={len(self.symbols)})"


def convert_tm_to_ctm(tm):
    """
    Konvertiert eine Turing-Maschine in eine Clockwise TM.
    Implementiert Lemma 1 aus dem Paper.
    """

    # Erstelle neue Zustände für CTM
    ctm_states = set()

    # Hauptzustände (entsprechen den TM-Zuständen)
    for q in tm.states:
        ctm_states.add(q)

    # Hilfszustände für Links-Bewegungen
    for q in tm.states:
        if q not in tm.halt_states:
            for s in tm.symbols:
                if s != tm.blank:
                    ctm_states.add(f"{q},{s}")
            ctm_states.add(f"{q},r")
            ctm_states.add(f"{q},r'")
            ctm_states.add(f"{q},l")

    # Neue Symbole für CTM
    ctm_symbols = set()
    # Kodiere Nicht-Blank-Symbole
    for i, s in enumerate(tm.symbols):
        if s != tm.blank:
            ctm_symbols.add(f"σ_{i+2}")
    ctm_symbols.add('r')  # Rechte Blanks
    ctm_symbols.add('l')  # Linke Blanks
    ctm_symbols.add('γ')  # Marker-Symbol

    # Erstelle Übergänge
    ctm_transitions = {}

    # Symbol-Mapping: TM-Symbol -> CTM-Symbol
    symbol_map = {tm.blank: None}
    idx = 2
    for s in tm.symbols:
        if s != tm.blank:
            symbol_map[s] = f"σ_{idx}"
            idx += 1

    # Konvertiere jede TM-Transition
    for (state, read_sym), (write_sym, direction, next_state) in tm.transitions.items():
        if state in tm.halt_states:
            continue

        if direction == 'R':  # Rechts-Bewegung -> Uhrzeigersinn
            if read_sym != tm.blank:
                # Normale Rechts-Bewegung: (q_x, σ_k, σ_j, R, q_y) -> (q_x, σ_k, σ_j, q_y)
                ctm_read = symbol_map[read_sym]
                ctm_write = symbol_map[write_sym] if write_sym != tm.blank else 'l'
                ctm_transitions[(state, ctm_read)] = (ctm_write, next_state)

            elif read_sym == tm.blank:
                if write_sym != tm.blank:
                    # Blank links: (q_x, blank, σ_j, R, q_y) -> (q_x, l, lσ_j, q_y)
                    ctm_transitions[(state, 'l')] = (f"l{symbol_map[write_sym]}", next_state)

                    # Blank rechts: mehrere Transitionen nötig
                    ctm_transitions[(state, 'r')] = (f"{symbol_map[write_sym]}r", f"{next_state},r'")
                    # Bewege zum r zurück
                    for sym in ctm_symbols:
                        if sym not in ['γ', 'r']:
                            ctm_transitions[(f"{next_state},r'", sym)] = (sym, f"{next_state},r'")
                    ctm_transitions[(f"{next_state},r'", 'r')] = ('r', next_state)

        elif direction == 'L':  # Links-Bewegung -> gegen Uhrzeigersinn
            # Markiere Position mit γ
            if read_sym == tm.blank:
                # Blank links oder rechts
                ctm_transitions[(state, 'l')] = (f"lγ", f"{next_state},{symbol_map.get(write_sym, 'l')}")
                ctm_transitions[(state, 'r')] = (f"γ{symbol_map.get(write_sym, 'r')}", f"{next_state},r")
            else:
                ctm_read = symbol_map[read_sym]
                ctm_transitions[(state, ctm_read)] = ('γ', f"{next_state},{symbol_map.get(write_sym, ctm_read)}")

            # Verschiebe Symbole im Uhrzeigersinn (simuliert Links-Bewegung)
            for sym1 in ctm_symbols:
                if sym1 != 'γ':
                    for sym2 in ctm_symbols:
                        if sym2 != 'γ':
                            state_name = f"{next_state},{symbol_map.get(write_sym, 'r')}"
                            if state_name in ctm_states:
                                ctm_transitions[(state_name, sym2)] = (sym1, f"{next_state},{sym2}")

            # Beende wenn γ erreicht wird
            # (Vereinfachte Darstellung)

    # Halt-Zustand
    halt_state = list(tm.halt_states)[0] if tm.halt_states else f"{tm.start_state}_halt"

    return ClockwiseTM(
        states=ctm_states,
        symbols=ctm_symbols,
        transitions=ctm_transitions,
        start_state=tm.start_state,
        halt_state=halt_state
    )


class CTMSimulator:
    """Simulator für Clockwise Turing Machines"""
    def __init__(self, ctm):
        self.ctm = ctm
        self.tape = []
        self.head_pos = 0
        self.current_state = ctm.start_state
        self.steps = 0
        self.max_steps = 1000

    def initialize_tape(self, input_symbols):
        """Initialisiert das zirkuläre Tape mit Input"""
        self.tape = list(input_symbols)
        self.head_pos = 0
        self.current_state = self.ctm.start_state
        self.steps = 0

    def step(self):
        """Führt einen Simulationsschritt aus"""
        if self.current_state == self.ctm.halt_state:
            return False  # Bereits gestoppt

        if self.steps >= self.max_steps:
            return False  # Maximale Schritte erreicht

        # Lese aktuelles Symbol
        current_symbol = self.tape[self.head_pos] if self.tape else None

        # Suche Übergang
        if (self.current_state, current_symbol) not in self.ctm.transitions:
            return False  # Keine Transition, Halt

        write_value, next_state = self.ctm.transitions[(self.current_state, current_symbol)]

        # Schreibe Wert
        if isinstance(write_value, str) and len(write_value) == 2:
            # Schreibe 2 Symbole (Zelle wird zu 2 Zellen)
            self.tape[self.head_pos] = write_value[0]
            self.tape.insert(self.head_pos + 1, write_value[1])
        else:
            # Schreibe 1 Symbol
            self.tape[self.head_pos] = write_value

        # Bewege Kopf im Uhrzeigersinn
        self.head_pos = (self.head_pos + 1) % len(self.tape)

        # Wechsle Zustand
        self.current_state = next_state
        self.steps += 1

        return True  # Weitermachen

    def run(self, input_symbols, verbose=False, step_limit=None):
        """Führt die CTM aus bis zum Halt"""
        if step_limit:
            self.max_steps = step_limit

        self.initialize_tape(input_symbols)

        if verbose:
            print(f"\n{'='*70}")
            print(f"CTM SIMULATION START")
            print(f"{'='*70}")
            self.print_state()

        while self.step():
            if verbose and self.steps <= 20:
                self.print_state()
            elif verbose and self.steps == 21:
                print("\n... (weitere Schritte werden nicht angezeigt) ...")

        if verbose:
            print(f"\n{'='*70}")
            print(f"CTM SIMULATION ENDE nach {self.steps} Schritten")
            print(f"{'='*70}")
            self.print_state()

        return self.tape, self.current_state, self.steps

    def print_state(self):
        """Zeigt den aktuellen Zustand der CTM"""
        tape_str = ''.join([str(s) if len(str(s)) <= 3 else str(s)[:3] for s in self.tape])

        # Markiere Kopfposition
        pointer = ' ' * (self.head_pos * 3) + '↓'

        print(f"\nSchritt {self.steps:3d}  |  Zustand: {self.current_state}")
        print(f"Tape:      {tape_str}")
        print(f"           {pointer}")


def print_ctm_details(ctm):
    """Gibt Details der CTM aus"""
    print(f"\n{'='*60}")
    print(f"CLOCKWISE TURING MACHINE")
    print(f"{'='*60}")
    print(f"Anzahl Zustände: {len(ctm.states)}")
    print(f"Anzahl Symbole: {len(ctm.symbols)}")
    print(f"Start-Zustand: {ctm.start_state}")
    print(f"Halt-Zustand: {ctm.halt_state}")

    print(f"\nZustände: {sorted(list(ctm.states)[:10])}{'...' if len(ctm.states) > 10 else ''}")
    print(f"Symbole: {sorted(ctm.symbols)}")

    print(f"\nÜbergänge ({len(ctm.transitions)} gesamt):")
    for i, ((state, symbol), (write, next_state)) in enumerate(ctm.transitions.items()):
        if i < 15:  # Zeige erste 15 Übergänge
            print(f"  ({state}, {symbol}) -> ({write}, {next_state})")
        elif i == 15:
            print(f"  ... und {len(ctm.transitions) - 15} weitere")
            break


# Beispiel: Einfache Turing-Maschine
def create_example_tm():
    """Erstellt eine Beispiel-TM die eine binäre Zahl inkrementiert"""
    states = {'q0', 'q1', 'q2', 'qh'}
    symbols = {'0', '1', 'B'}  # B = Blank
    blank = 'B'
    start_state = 'q0'
    halt_states = {'qh'}

    # Transitions: (state, symbol) -> (write_symbol, direction, next_state)
    transitions = {
        ('q0', '0'): ('0', 'R', 'q0'),
        ('q0', '1'): ('1', 'R', 'q0'),
        ('q0', 'B'): ('B', 'L', 'q1'),  # Gehe zum Ende
        ('q1', '0'): ('1', 'L', 'qh'),  # 0->1, fertig
        ('q1', '1'): ('0', 'L', 'q1'),  # 1->0, trage über
        ('q1', 'B'): ('1', 'R', 'qh'),  # Am Anfang: füge 1 hinzu
    }

    return TuringMachine(states, symbols, blank, transitions, start_state, halt_states)


def create_simple_ctm_example():
    """Erstellt eine einfache CTM zum Testen"""
    # CTM die ein Pattern rotiert: ABC -> BCA -> CAB -> ABC
    states = {'q0', 'q1', 'q2', 'qh'}
    symbols = {'A', 'B', 'C'}
    transitions = {
        ('q0', 'A'): ('B', 'q1'),
        ('q1', 'B'): ('C', 'q2'),
        ('q2', 'C'): ('A', 'qh'),
    }

    return ClockwiseTM(
        states=states,
        symbols=symbols,
        transitions=transitions,
        start_state='q0',
        halt_state='qh'
    )


def create_counter_ctm():
    """Erstellt eine CTM die zählt: ersetzt A mit B, dann B mit C"""
    states = {'q0', 'q1', 'qh'}
    symbols = {'A', 'B', 'C', 'X'}

    transitions = {
        # Phase 1: Finde erstes A und ersetze mit B
        ('q0', 'X'): ('X', 'q0'),  # Überspringe Marker
        ('q0', 'B'): ('B', 'q0'),  # Überspringe bereits bearbeitete
        ('q0', 'C'): ('C', 'q0'),  # Überspringe
        ('q0', 'A'): ('B', 'q1'),  # Ersetze A mit B

        # Phase 2: Rotiere zurück zum Start
        ('q1', 'X'): ('X', 'q1'),
        ('q1', 'A'): ('A', 'q1'),
        ('q1', 'B'): ('B', 'q1'),
        ('q1', 'C'): ('C', 'q1'),
    }

    return ClockwiseTM(
        states=states,
        symbols=symbols,
        transitions=transitions,
        start_state='q0',
        halt_state='qh'
    )


# Hauptprogramm
if __name__ == "__main__":
    print("Turing Machine zu Clockwise TM Konverter & Simulator")
    print("="*70)

    # Beispiel 1: Einfache CTM
    print("\n" + "="*70)
    print("BEISPIEL 1: Einfache Pattern-Rotation CTM")
    print("="*70)

    simple_ctm = create_simple_ctm_example()
    print(f"\nCTM: {simple_ctm}")
    print(f"Übergänge: {simple_ctm.transitions}")

    # Simuliere
    sim = CTMSimulator(simple_ctm)
    result, final_state, steps = sim.run(['A', 'B', 'C'], verbose=True)

    print(f"\nErgebnis: {''.join(result)}")
    print(f"Endzustand: {final_state}")
    print(f"Schritte: {steps}")

    # Beispiel 2: Counter CTM
    print("\n" + "="*70)
    print("BEISPIEL 2: Counter CTM (A->B Transformation)")
    print("="*70)

    counter_ctm = create_counter_ctm()
    print(f"\nCTM: {counter_ctm}")

    # Simuliere
    sim2 = CTMSimulator(counter_ctm)
    result2, final_state2, steps2 = sim2.run(['X', 'A', 'A', 'A', 'A'], verbose=True, step_limit=20)

    print(f"\nErgebnis: {''.join(result2)}")
    print(f"Endzustand: {final_state2}")
    print(f"Schritte: {steps2}")

    # Beispiel 3: TM zu CTM Konvertierung
    print("\n" + "="*70)
    print("BEISPIEL 3: TM zu CTM Konvertierung")
    print("="*70)

    # Erstelle Beispiel-TM
    tm = create_example_tm()
    print(f"\nOriginal Turing Machine:")
    print(f"  Zustände: {tm.states}")
    print(f"  Symbole: {tm.symbols}")
    print(f"  Blank: '{tm.blank}'")
    print(f"  Start: {tm.start_state}")
    print(f"  Halt: {tm.halt_states}")
    print(f"  Übergänge: {len(tm.transitions)}")

    # Konvertiere zu CTM
    print("\nKonvertiere TM zu CTM...")
    ctm = convert_tm_to_ctm(tm)

    # Zeige CTM Details
    print_ctm_details(ctm)

    print(f"\n{'='*70}")
    print("Hinweise:")
    print("- Die CTM hat ein zirkuläres Tape")
    print("- Links-Bewegungen werden durch Verschiebung simuliert")
    print("- Symbole 'l' und 'r' kodieren unendliche Blank-Sequenzen")
    print("- Symbol 'γ' wird als Marker für Links-Bewegungen verwendet")
    print(f"{'='*70}\n")
