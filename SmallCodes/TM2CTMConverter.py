
"""
Turing Machine to Clockwise Turing Machine Converter mit Simulator

Basierend auf Lemma 2.1 aus:
"Four Small Universal Turing Machines" von Neary & Woods (2009)
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Set, Optional
from enum import Enum
import time


class Direction(Enum):
    LEFT = 'L'
    RIGHT = 'R'


@dataclass(frozen=True)
class TMTransition:
    """Übergang einer Standard-Turing-Maschine"""
    current_state: str
    read_symbol: str
    write_symbol: str
    direction: Direction
    next_state: str

    def __str__(self):
        return f"δ({self.current_state}, {self.read_symbol}) = ({self.write_symbol}, {self.direction.value}, {self.next_state})"


@dataclass(frozen=True)
class CTMTransition:
    """Übergang einer Clockwise Turing Machine"""
    current_state: str
    read_symbol: str
    write_value: str  # Ein Symbol oder zwei Symbole (für Zellteilung)
    next_state: str

    def __str__(self):
        if len(self.write_value) == 1:
            return f"δ({self.current_state}, {self.read_symbol}) = ({self.write_value}, {self.next_state})"
        else:
            return f"δ({self.current_state}, {self.read_symbol}) = ({self.write_value[0]}·{self.write_value[1]}, {self.next_state})"


class TuringMachine:
    """Standard-Turing-Maschine"""

    def __init__(self,
                 states: Set[str],
                 alphabet: Set[str],
                 blank: str,
                 initial_state: str,
                 final_states: Set[str],
                 transitions: List[TMTransition]):
        self.states = states
        self.alphabet = alphabet
        self.blank = blank
        self.initial_state = initial_state
        self.final_states = final_states
        self.transitions = transitions

        # Transition-Lookup erstellen
        self.transition_map: Dict[Tuple[str, str], TMTransition] = {}
        for t in transitions:
            self.transition_map[(t.current_state, t.read_symbol)] = t

    def __str__(self):
        lines = [
            "╔══════════════════════════════════════╗",
            "║       STANDARD TURING MACHINE        ║",
            "╚══════════════════════════════════════╝",
            f"  Zustände Q:    {sorted(self.states)}",
            f"  Alphabet Σ:    {sorted(self.alphabet)}",
            f"  Blank:         {self.blank}",
            f"  Startzustand:  {self.initial_state}",
            f"  Endzustände:   {sorted(self.final_states)}",
            "  Übergänge δ:"
        ]
        for t in self.transitions:
            lines.append(f"    {t}")
        return "\n".join(lines)


class TMSimulator:
    """Simulator für Standard-Turing-Maschinen"""

    def __init__(self, tm: TuringMachine):
        self.tm = tm
        self.tape: List[str] = []
        self.head_position: int = 0
        self.current_state: str = ""
        self.step_count: int = 0
        self.history: List[Tuple[str, List[str], int]] = []

    def initialize(self, input_string: str):
        """Initialisiert den Simulator mit einer Eingabe"""
        self.tape = list(input_string) if input_string else [self.tm.blank]
        self.head_position = 0
        self.current_state = self.tm.initial_state
        self.step_count = 0
        self.history = []
        self._save_state()

    def _save_state(self):
        """Speichert den aktuellen Zustand in der Historie"""
        self.history.append((
            self.current_state,
            self.tape.copy(),
            self.head_position
        ))

    def _ensure_tape_bounds(self):
        """Erweitert das Band falls nötig"""
        while self.head_position < 0:
            self.tape.insert(0, self.tm.blank)
            self.head_position += 1
        while self.head_position >= len(self.tape):
            self.tape.append(self.tm.blank)

    def step(self) -> bool:
        """
        Führt einen einzelnen Schritt aus.
        Gibt True zurück wenn die Maschine weiterlaufen kann.
        """
        if self.current_state in self.tm.final_states:
            return False

        self._ensure_tape_bounds()
        read_symbol = self.tape[self.head_position]

        # Transition suchen
        key = (self.current_state, read_symbol)
        if key not in self.tm.transition_map:
            return False

        transition = self.tm.transition_map[key]

        # Transition ausführen
        self.tape[self.head_position] = transition.write_symbol

        if transition.direction == Direction.RIGHT:
            self.head_position += 1
        else:
            self.head_position -= 1

        self.current_state = transition.next_state
        self.step_count += 1

        self._ensure_tape_bounds()
        self._save_state()

        return self.current_state not in self.tm.final_states

    def run(self, max_steps: int = 1000) -> bool:
        """
        Führt die Maschine aus bis sie hält oder max_steps erreicht.
        Gibt True zurück wenn die Maschine normal gehalten hat.
        """
        while self.step_count < max_steps:
            if not self.step():
                return True
        return False

    def get_tape_string(self) -> str:
        """Gibt den Bandinhalt als String zurück (ohne führende/trailing Blanks)"""
        result = ''.join(self.tape)
        # Blanks am Anfang und Ende entfernen
        result = result.strip(self.tm.blank)
        return result if result else self.tm.blank

    def format_configuration(self, state: str = None, tape: List[str] = None,
                            head_pos: int = None, step: int = None) -> str:
        """Formatiert eine Konfiguration für die Anzeige"""
        if state is None:
            state = self.current_state
        if tape is None:
            tape = self.tape
        if head_pos is None:
            head_pos = self.head_position
        if step is None:
            step = self.step_count

        # Band mit Kopfmarkierung erstellen
        tape_str = ""
        for i, symbol in enumerate(tape):
            if i == head_pos:
                tape_str += f"[{symbol}]"
            else:
                tape_str += f" {symbol} "

        return f"Schritt {step:3d}: {state:10s} |{tape_str}|"

    def print_execution(self, delay: float = 0.0):
        """Gibt die gesamte Ausführungshistorie aus"""
        print("\n┌" + "─" * 58 + "┐")
        print("│" + " AUSFÜHRUNG DER STANDARD-TM ".center(58) + "│")
        print("└" + "─" * 58 + "┘\n")

        for i, (state, tape, head_pos) in enumerate(self.history):
            print(self.format_configuration(state, tape, head_pos, i))
            if delay > 0:
                time.sleep(delay)

        status = "AKZEPTIERT" if self.current_state in self.tm.final_states else "GESTOPPT"
        print(f"\n  === {status} nach {self.step_count} Schritten ===")
        print(f"  Endzustand: {self.current_state}")
        print(f"  Bandinhalt: {self.get_tape_string()}")


class ClockwiseTuringMachine:
    """Clockwise Turing Machine (zirkuläres Band, nur Uhrzeigersinn)"""

    def __init__(self,
                 states: Set[str],
                 alphabet: Set[str],
                 initial_state: str,
                 final_state: str,
                 transitions: List[CTMTransition]):
        self.states = states
        self.alphabet = alphabet
        self.initial_state = initial_state
        self.final_state = final_state
        self.transitions = transitions

        # Transition-Lookup erstellen
        self.transition_map: Dict[Tuple[str, str], CTMTransition] = {}
        for t in transitions:
            self.transition_map[(t.current_state, t.read_symbol)] = t

    def __str__(self):
        lines = [
            "╔══════════════════════════════════════╗",
            "║      CLOCKWISE TURING MACHINE        ║",
            "╚══════════════════════════════════════╝",
            f"  Zustände ({len(self.states):2d}): {sorted(self.states)[:5]}{'...' if len(self.states) > 5 else ''}",
            f"  Alphabet ({len(self.alphabet):2d}): {sorted(self.alphabet)}",
            f"  Startzustand:  {self.initial_state}",
            f"  Endzustand:    {self.final_state}",
            f"  Übergänge ({len(self.transitions):2d}):"
        ]
        for t in self.transitions[:15]:
            lines.append(f"    {t}")
        if len(self.transitions) > 15:
            lines.append(f"    ... und {len(self.transitions) - 15} weitere")
        return "\n".join(lines)


class CTMSimulator:
    """Simulator für Clockwise Turing Machines"""

    # Spezielle Symbole
    MARKER = "M"      # σₘ
    RIGHT_END = "R"   # σᵣ
    LEFT_END = "L"    # σₗ

    def __init__(self, ctm: ClockwiseTuringMachine):
        self.ctm = ctm
        self.tape: List[str] = []  # Zirkuläres Band als Liste
        self.head_position: int = 0
        self.current_state: str = ""
        self.step_count: int = 0
        self.history: List[Tuple[str, List[str], int, Optional[CTMTransition]]] = []

    def initialize(self, input_string: str):
        """
        Initialisiert den Simulator mit einer Eingabe.
        Das Band wird zirkulär mit L und R Markern versehen.
        """
        # Band aufbauen: L [Eingabe] R
        self.tape = [self.LEFT_END]
        if input_string:
            self.tape.extend(list(input_string))
        self.tape.append(self.RIGHT_END)

        self.head_position = 1  # Erste Position nach L
        self.current_state = self.ctm.initial_state
        self.step_count = 0
        self.history = []
        self._save_state(None)

    def _save_state(self, transition: Optional[CTMTransition]):
        """Speichert den aktuellen Zustand in der Historie"""
        self.history.append((
            self.current_state,
            self.tape.copy(),
            self.head_position,
            transition
        ))

    def _move_clockwise(self):
        """Bewegt den Kopf im Uhrzeigersinn (zirkulär)"""
        self.head_position = (self.head_position + 1) % len(self.tape)

    def step(self) -> bool:
        """
        Führt einen einzelnen Schritt aus.
        Gibt True zurück wenn die Maschine weiterlaufen kann.
        """
        if self.current_state == self.ctm.final_state:
            return False

        read_symbol = self.tape[self.head_position]

        # Transition suchen
        key = (self.current_state, read_symbol)
        if key not in self.ctm.transition_map:
            return False

        transition = self.ctm.transition_map[key]

        # Transition ausführen
        if len(transition.write_value) == 1:
            # Einfaches Überschreiben
            self.tape[self.head_position] = transition.write_value
        else:
            # Zellteilung: Eine Zelle wird zu zwei Zellen
            self.tape[self.head_position] = transition.write_value[0]
            self.tape.insert(self.head_position + 1, transition.write_value[1])

        self.current_state = transition.next_state
        self._move_clockwise()
        self.step_count += 1

        self._save_state(transition)

        return self.current_state != self.ctm.final_state

    def run(self, max_steps: int = 1000) -> bool:
        """
        Führt die Maschine aus bis sie hält oder max_steps erreicht.
        Gibt True zurück wenn die Maschine normal gehalten hat.
        """
        while self.step_count < max_steps:
            if not self.step():
                return True
        return False

    def get_tape_string(self) -> str:
        """Gibt den Bandinhalt als String zurück (ohne spezielle Marker)"""
        result = ''.join(s for s in self.tape
                        if s not in {self.LEFT_END, self.RIGHT_END, self.MARKER})
        return result if result else "ε"

    def format_configuration(self, state: str, tape: List[str],
                            head_pos: int, step: int,
                            transition: Optional[CTMTransition] = None) -> str:
        """Formatiert eine Konfiguration für die Anzeige (zirkulär)"""

        # Zirkuläres Band darstellen
        n = len(tape)

        # Band-String erstellen
        tape_str = ""
        for i in range(n):
            symbol = tape[i]
            # Symbol kürzen wenn nötig
            display = symbol if len(symbol) <= 2 else symbol[:2]

            if i == head_pos:
                tape_str += f"[{display}]"
            else:
                tape_str += f" {display} "

        # Zustand kürzen für bessere Darstellung
        state_display = state if len(state) <= 12 else state[:10] + ".."

        result = f"Schritt {step:3d}: {state_display:12s} |{tape_str}|"

        # Transition anzeigen falls vorhanden
        if transition:
            result += f"  <- {transition}"

        return result

    def format_circular_tape(self, tape: List[str], head_pos: int) -> str:
        """Formatiert das Band als Kreis (für detaillierte Ansicht)"""
        n = len(tape)
        lines = []

        # Obere Linie
        lines.append("    ┌" + "───┬" * (n-1) + "───┐")

        # Symbole
        symbol_line = "    │"
        for i, symbol in enumerate(tape):
            display = symbol if len(symbol) <= 2 else symbol[:2]
            if i == head_pos:
                symbol_line += f">{display}<│"
            else:
                symbol_line += f" {display} │"
        lines.append(symbol_line)

        # Untere Linie mit Verbindung (zirkulär)
        lines.append("    └" + "───┴" * (n-1) + "───┘")
        lines.append("     ↑" + " " * (n * 4 - 2) + "↑")
        lines.append("     └" + "─" * (n * 4 - 2) + "┘ (zirkulär)")

        return "\n".join(lines)

    def print_execution(self, delay: float = 0.0, detailed: bool = False):
        """Gibt die gesamte Ausführungshistorie aus"""
        print("\n┌" + "─" * 70 + "┐")
        print("│" + " AUSFÜHRUNG DER CLOCKWISE TM ".center(70) + "│")
        print("└" + "─" * 70 + "┘\n")

        for i, (state, tape, head_pos, transition) in enumerate(self.history):
            print(self.format_configuration(state, tape, head_pos, i,
                                           transition if i > 0 else None))

            if detailed and i < len(self.history) - 1:
                print(self.format_circular_tape(tape, head_pos))
                print()

            if delay > 0:
                time.sleep(delay)

        status = "AKZEPTIERT" if self.current_state == self.ctm.final_state else "GESTOPPT"
        print(f"\n  === {status} nach {self.step_count} Schritten ===")
        print(f"  Endzustand: {self.current_state}")
        print(f"  Bandinhalt: {self.get_tape_string()}")


class TMtoClockwiseConverter:
    """Konvertiert eine Standard-TM in eine Clockwise TM"""

    MARKER = "M"      # σₘ
    RIGHT_END = "R"   # σᵣ
    LEFT_END = "L"    # σₗ

    def __init__(self, tm: TuringMachine):
        self.tm = tm
        self.ctm_states: Set[str] = set()
        self.ctm_alphabet: Set[str] = set()
        self.ctm_transitions: List[CTMTransition] = []

    def convert(self) -> ClockwiseTuringMachine:
        """Führt die Konvertierung durch"""

        # Alphabet aufbauen (ohne Blank, plus spezielle Symbole)
        self.ctm_alphabet = {s for s in self.tm.alphabet if s != self.tm.blank}
        self.ctm_alphabet.add(self.MARKER)
        self.ctm_alphabet.add(self.RIGHT_END)
        self.ctm_alphabet.add(self.LEFT_END)

        # Basiszustände übernehmen
        self.ctm_states = set(self.tm.states)

        # Jeden Übergang konvertieren
        for transition in self.tm.transitions:
            if transition.direction == Direction.RIGHT:
                self._convert_right_move(transition)
            else:
                self._convert_left_move(transition)

        # Endzustand bestimmen
        final_state = next(iter(self.tm.final_states))

        return ClockwiseTuringMachine(
            states=self.ctm_states,
            alphabet=self.ctm_alphabet,
            initial_state=self.tm.initial_state,
            final_state=final_state,
            transitions=self.ctm_transitions
        )

    def _convert_right_move(self, t: TMTransition):
        """Konvertiert eine Rechtsbewegung"""

        if t.read_symbol == self.tm.blank:
            # Am rechten Rand: Zellteilung (neues Symbol + R-Marker)
            if t.write_symbol == self.tm.blank:
                # Blank bleibt Blank - einfach weitergehen
                self.ctm_transitions.append(CTMTransition(
                    current_state=t.current_state,
                    read_symbol=self.RIGHT_END,
                    write_value=self.RIGHT_END,
                    next_state=t.next_state
                ))
            else:
                # Neues Symbol einfügen
                self.ctm_transitions.append(CTMTransition(
                    current_state=t.current_state,
                    read_symbol=self.RIGHT_END,
                    write_value=t.write_symbol + self.RIGHT_END,
                    next_state=t.next_state
                ))
        else:
            # Normaler Fall
            self.ctm_transitions.append(CTMTransition(
                current_state=t.current_state,
                read_symbol=t.read_symbol,
                write_value=t.write_symbol,
                next_state=t.next_state
            ))

    def _convert_left_move(self, t: TMTransition):
        """Konvertiert eine Linksbewegung durch Band-Rotation"""

        qx = t.current_state
        qy = t.next_state
        write_sym = t.write_symbol if t.write_symbol != self.tm.blank else self.RIGHT_END

        # Initialer Carry-Zustand
        carry_state_initial = f"{qy}_{write_sym}"
        self.ctm_states.add(carry_state_initial)

        # Schritt 1: Markieren
        if t.read_symbol == self.tm.blank:
            # Am rechten Rand: R-Marker wird zu M + write_sym
            self.ctm_transitions.append(CTMTransition(
                current_state=qx,
                read_symbol=self.RIGHT_END,
                write_value=self.MARKER + write_sym,
                next_state=f"{qy}_{self.RIGHT_END}"
            ))
            self.ctm_states.add(f"{qy}_{self.RIGHT_END}")
        else:
            self.ctm_transitions.append(CTMTransition(
                current_state=qx,
                read_symbol=t.read_symbol,
                write_value=self.MARKER,
                next_state=carry_state_initial
            ))

        # Schritt 2: Rotations-Regeln
        all_symbols = self.ctm_alphabet - {self.MARKER}

        for sigma in all_symbols:
            carry_state = f"{qy}_{sigma}"
            self.ctm_states.add(carry_state)

            for sigma_read in self.ctm_alphabet:
                if sigma_read == self.MARKER:
                    # Marker gefunden → Rotation fertig
                    self.ctm_transitions.append(CTMTransition(
                        current_state=carry_state,
                        read_symbol=self.MARKER,
                        write_value=sigma,
                        next_state=qy
                    ))
                else:
                    # Weiter rotieren
                    next_carry = f"{qy}_{sigma_read}"
                    self.ctm_states.add(next_carry)
                    self.ctm_transitions.append(CTMTransition(
                        current_state=carry_state,
                        read_symbol=sigma_read,
                        write_value=sigma,
                        next_state=next_carry
                    ))


# ═══════════════════════════════════════════════════════════════════════════
# BEISPIEL-TURING-MASCHINEN
# ═══════════════════════════════════════════════════════════════════════════

def create_simple_example_tm() -> TuringMachine:
    """
    Einfache TM für Demonstrationszwecke.
    Regel 1: (q1, 0, 1, R, q2)
    Regel 2: (q2, 1, 0, L, q3)
    """
    return TuringMachine(
        states={'q1', 'q2', 'q3'},
        alphabet={'0', '1', '□'},
        blank='□',
        initial_state='q1',
        final_states={'q3'},
        transitions=[
            TMTransition('q1', '0', '1', Direction.RIGHT, 'q2'),
            TMTransition('q2', '1', '0', Direction.LEFT, 'q3'),
        ]
    )


def create_increment_tm() -> TuringMachine:
    """
    TM die eine Binärzahl um 1 inkrementiert.
    Beispiel: 1011 → 1100
    """
    return TuringMachine(
        states={'qR', 'qI', 'qH'},
        alphabet={'0', '1', '□'},
        blank='□',
        initial_state='qR',
        final_states={'qH'},
        transitions=[
            # qR: Nach rechts zum Ende
            TMTransition('qR', '0', '0', Direction.RIGHT, 'qR'),
            TMTransition('qR', '1', '1', Direction.RIGHT, 'qR'),
            TMTransition('qR', '□', '□', Direction.LEFT, 'qI'),
            # qI: Inkrementieren
            TMTransition('qI', '0', '1', Direction.LEFT, 'qH'),
            TMTransition('qI', '1', '0', Direction.LEFT, 'qI'),
            TMTransition('qI', '□', '1', Direction.RIGHT, 'qH'),
        ]
    )


# ═══════════════════════════════════════════════════════════════════════════
# HAUPT-DEMO-FUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════

def demo_simple():
    """Demonstriert die einfache TM und ihre Clockwise-Version"""

    print("\n" + "=" * 72)
    print(" DEMO 1: Einfache TM mit Rechts- und Linksbewegung ".center(72, "="))
    print("=" * 72)

    # TM erstellen
    tm = create_simple_example_tm()
    print(f"\n{tm}")

    # TM simulieren
    print("\n" + "-" * 72)
    print(" Simulation der Standard-TM ".center(72))
    print("-" * 72)

    sim_tm = TMSimulator(tm)
    sim_tm.initialize("01")
    sim_tm.run()
    sim_tm.print_execution()

    # Zu Clockwise konvertieren
    print("\n" + "-" * 72)
    print(" Konvertierung zu Clockwise TM ".center(72))
    print("-" * 72)

    converter = TMtoClockwiseConverter(tm)
    ctm = converter.convert()
    print(f"\n{ctm}")

    # Clockwise TM simulieren
    print("\n" + "-" * 72)
    print(" Simulation der Clockwise TM ".center(72))
    print("-" * 72)

    sim_ctm = CTMSimulator(ctm)
    sim_ctm.initialize("01")
    sim_ctm.run()
    sim_ctm.print_execution()

    # Vergleich
    print("\n" + "-" * 72)
    print(" VERGLEICH ".center(72))
    print("-" * 72)
    print(f"  Standard-TM:  {len(tm.states)} Zustände, {len(tm.transitions)} Übergänge, {sim_tm.step_count} Schritte")
    print(f"  Clockwise-TM: {len(ctm.states)} Zustände, {len(ctm.transitions)} Übergänge, {sim_ctm.step_count} Schritte")


def demo_increment():
    """Demonstriert die Inkrement-TM"""

    print("\n" + "=" * 72)
    print(" DEMO 2: Binär-Inkrement TM ".center(72, "="))
    print("=" * 72)

    tm = create_increment_tm()
    print(f"\n{tm}")

    test_inputs = ["1011", "111", "1000"]

    for input_str in test_inputs:
        print("\n" + "-" * 72)
        print(f" Eingabe: {input_str} ".center(72))
        print("-" * 72)

        # Standard-TM
        sim_tm = TMSimulator(tm)
        sim_tm.initialize(input_str)
        sim_tm.run()
        sim_tm.print_execution()

        # Clockwise-TM
        converter = TMtoClockwiseConverter(tm)
        ctm = converter.convert()

        sim_ctm = CTMSimulator(ctm)
        sim_ctm.initialize(input_str)
        sim_ctm.run()
        sim_ctm.print_execution()

        print(f"\n  Ergebnis Standard-TM:  {input_str} -> {sim_tm.get_tape_string()}")
        print(f"  Ergebnis Clockwise-TM: {input_str} -> {sim_ctm.get_tape_string()}")


def demo_detailed_clockwise():
    """Zeigt detaillierte Ansicht der Clockwise-TM Ausführung"""

    print("\n" + "=" * 72)
    print(" DEMO 3: Detaillierte Clockwise-TM Ansicht ".center(72, "="))
    print("=" * 72)

    tm = create_simple_example_tm()
    converter = TMtoClockwiseConverter(tm)
    ctm = converter.convert()

    print(f"\n{ctm}")

    sim = CTMSimulator(ctm)
    sim.initialize("01")
    sim.run()
    sim.print_execution(detailed=True)


# ═══════════════════════════════════════════════════════════════════════════
# HAUPTPROGRAMM
# ═══════════════════════════════════════════════════════════════════════════

def demo_multi_left():
    """Demonstriert eine TM mit mehreren Linksbewegungen"""

    print("\n" + "=" * 72)
    print(" DEMO: TM mit mehreren Rechts- und Linksbewegungen ".center(72, "="))
    print("=" * 72)

    # TM: Liest "ab", schreibt "BA" (spiegelt und kapitalisiert)
    # q0,a -> A,R,q1
    # q1,b -> B,L,q2
    # q2,A -> A,L,qH (nochmal links)
    tm = TuringMachine(
        states={'q0', 'q1', 'q2', 'qH'},
        alphabet={'a', 'b', 'A', 'B', '□'},
        blank='□',
        initial_state='q0',
        final_states={'qH'},
        transitions=[
            TMTransition('q0', 'a', 'A', Direction.RIGHT, 'q1'),
            TMTransition('q1', 'b', 'B', Direction.LEFT, 'q2'),
            TMTransition('q2', 'A', 'X', Direction.LEFT, 'qH'),  # Nochmal links
        ]
    )

    print(f"\n{tm}")

    # Standard-TM
    print("\n" + "-" * 72)
    print(" Simulation der Standard-TM ".center(72))
    print("-" * 72)

    sim_tm = TMSimulator(tm)
    sim_tm.initialize("ab")
    sim_tm.run()
    sim_tm.print_execution()

    # Clockwise-TM
    print("\n" + "-" * 72)
    print(" Simulation der Clockwise TM ".center(72))
    print("-" * 72)

    converter = TMtoClockwiseConverter(tm)
    ctm = converter.convert()
    print(f"\n{ctm}")

    sim_ctm = CTMSimulator(ctm)
    sim_ctm.initialize("ab")
    sim_ctm.run()
    sim_ctm.print_execution()

    # Vergleich
    print("\n" + "-" * 72)
    print(" VERGLEICH ".center(72))
    print("-" * 72)
    print(f"  Standard-TM:  {sim_tm.step_count} Schritte, Ergebnis: {sim_tm.get_tape_string()}")
    print(f"  Clockwise-TM: {sim_ctm.step_count} Schritte, Ergebnis: {sim_ctm.get_tape_string()}")


if __name__ == "__main__":
    print("\n" + "#" * 72)
    print("#" + " TM -> CLOCKWISE TM KONVERTER MIT SIMULATOR ".center(70) + "#")
    print("#" * 72)

    # Demo 1: Einfache TM (funktioniert korrekt)
    demo_simple()

    # Demo 2: Mehrere Links-Bewegungen
    print("\n\n")
    demo_multi_left()

    # Demo 3: Detaillierte Ansicht
    print("\n\n")
    demo_detailed_clockwise()
