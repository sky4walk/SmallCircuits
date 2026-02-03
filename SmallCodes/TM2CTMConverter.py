"""
Turing Machine to Clockwise Turing Machine Converter mit Simulator

Basierend auf Lemma 2.1 aus:
"Four Small Universal Turing Machines" von Neary & Woods (2009)

Version OHNE dataclass - alles manuell ausprogrammiert
"""

import time


# ═══════════════════════════════════════════════════════════════════════════
# DIRECTION - Enum-Ersatz als einfache Klasse
# ═══════════════════════════════════════════════════════════════════════════

class Direction:
    """
    Ersetzt enum.Enum für Bewegungsrichtungen.
    Statt Enum verwenden wir Klassenattribute.
    """
    LEFT = 'L'
    RIGHT = 'R'


# ═══════════════════════════════════════════════════════════════════════════
# TMTRANSITION - Übergang einer Standard-Turing-Maschine
# ═══════════════════════════════════════════════════════════════════════════

class TMTransition:
    """
    Übergang einer Standard-Turing-Maschine.

    Ersetzt: @dataclass(frozen=True)

    Ein Übergang hat die Form: (aktueller_zustand, gelesenes_symbol) ->
                               (geschriebenes_symbol, richtung, neuer_zustand)

    Attribute:
        current_state: Der aktuelle Zustand der TM
        read_symbol: Das Symbol, das gelesen wird
        write_symbol: Das Symbol, das geschrieben wird
        direction: Die Bewegungsrichtung (LEFT oder RIGHT)
        next_state: Der Folgezustand
    """

    def __init__(self, current_state, read_symbol, write_symbol, direction, next_state):
        """
        Konstruktor - initialisiert alle Attribute.

        Bei @dataclass würde dies automatisch generiert werden.
        frozen=True bedeutet, dass die Attribute nach der Erstellung
        nicht mehr geändert werden können (immutable).
        """
        # Wir speichern die Werte in "privaten" Variablen
        self._current_state = current_state
        self._read_symbol = read_symbol
        self._write_symbol = write_symbol
        self._direction = direction
        self._next_state = next_state

    # ─────────────────────────────────────────────────────────────────────
    # Properties - Getter für die Attribute (simuliert frozen=True)
    # ─────────────────────────────────────────────────────────────────────

    @property
    def current_state(self):
        """Getter für current_state"""
        return self._current_state

    @property
    def read_symbol(self):
        """Getter für read_symbol"""
        return self._read_symbol

    @property
    def write_symbol(self):
        """Getter für write_symbol"""
        return self._write_symbol

    @property
    def direction(self):
        """Getter für direction"""
        return self._direction

    @property
    def next_state(self):
        """Getter für next_state"""
        return self._next_state

    # ─────────────────────────────────────────────────────────────────────
    # Spezielle Methoden (würden von @dataclass generiert)
    # ─────────────────────────────────────────────────────────────────────

    def __str__(self):
        """
        String-Darstellung für print().
        Zeigt den Übergang in mathematischer Notation.
        """
        return f"δ({self._current_state}, {self._read_symbol}) = ({self._write_symbol}, {self._direction}, {self._next_state})"

    def __repr__(self):
        """
        Technische String-Darstellung für Debugging.
        Bei @dataclass automatisch generiert.
        """
        return f"TMTransition(current_state={self._current_state!r}, read_symbol={self._read_symbol!r}, write_symbol={self._write_symbol!r}, direction={self._direction!r}, next_state={self._next_state!r})"

    def __eq__(self, other):
        """
        Gleichheitsvergleich (==).
        Bei @dataclass automatisch generiert.
        Zwei Transitionen sind gleich, wenn alle Attribute gleich sind.
        """
        if not isinstance(other, TMTransition):
            return False
        return (self._current_state == other._current_state and
                self._read_symbol == other._read_symbol and
                self._write_symbol == other._write_symbol and
                self._direction == other._direction and
                self._next_state == other._next_state)

    def __hash__(self):
        """
        Hash-Wert für Verwendung in Sets und als Dict-Keys.
        Bei @dataclass(frozen=True) automatisch generiert.
        Nur immutable Objekte können gehasht werden.
        """
        return hash((self._current_state, self._read_symbol,
                     self._write_symbol, self._direction, self._next_state))


# ═══════════════════════════════════════════════════════════════════════════
# CTMTRANSITION - Übergang einer Clockwise Turing Machine
# ═══════════════════════════════════════════════════════════════════════════

class CTMTransition:
    """
    Übergang einer Clockwise Turing Machine.

    Unterschied zur TMTransition:
    - Keine Richtung (immer Uhrzeigersinn)
    - write_value kann 1 oder 2 Symbole sein (für Zellteilung)

    Attribute:
        current_state: Der aktuelle Zustand
        read_symbol: Das gelesene Symbol
        write_value: Das geschriebene Symbol (oder zwei Symbole bei Zellteilung)
        next_state: Der Folgezustand
    """

    def __init__(self, current_state, read_symbol, write_value, next_state):
        """Konstruktor"""
        self._current_state = current_state
        self._read_symbol = read_symbol
        self._write_value = write_value  # Kann "a" oder "ab" sein
        self._next_state = next_state

    # Properties (Getter)
    @property
    def current_state(self):
        return self._current_state

    @property
    def read_symbol(self):
        return self._read_symbol

    @property
    def write_value(self):
        return self._write_value

    @property
    def next_state(self):
        return self._next_state

    def __str__(self):
        """String-Darstellung"""
        if len(self._write_value) == 1:
            # Normales Überschreiben
            return f"δ({self._current_state}, {self._read_symbol}) = ({self._write_value}, {self._next_state})"
        else:
            # Zellteilung: Eine Zelle wird zu zwei
            return f"δ({self._current_state}, {self._read_symbol}) = ({self._write_value[0]}·{self._write_value[1]}, {self._next_state})"

    def __repr__(self):
        return f"CTMTransition(current_state={self._current_state!r}, read_symbol={self._read_symbol!r}, write_value={self._write_value!r}, next_state={self._next_state!r})"

    def __eq__(self, other):
        if not isinstance(other, CTMTransition):
            return False
        return (self._current_state == other._current_state and
                self._read_symbol == other._read_symbol and
                self._write_value == other._write_value and
                self._next_state == other._next_state)

    def __hash__(self):
        return hash((self._current_state, self._read_symbol,
                     self._write_value, self._next_state))


# ═══════════════════════════════════════════════════════════════════════════
# TURINGMACHINE - Standard-Turing-Maschine
# ═══════════════════════════════════════════════════════════════════════════

class TuringMachine:
    """
    Standard-Turing-Maschine mit einem Band.

    Eine TM ist ein 6-Tupel: M = (Q, Σ, blank, δ, q0, F)
    - Q: Endliche Menge von Zuständen
    - Σ: Bandalphabet
    - blank: Leerzeichen-Symbol
    - δ: Übergangsfunktion
    - q0: Startzustand
    - F: Menge der Endzustände
    """

    def __init__(self, states, alphabet, blank, initial_state, final_states, transitions):
        """
        Konstruktor für die Turing-Maschine.

        Args:
            states: Set von Zuständen (z.B. {'q0', 'q1', 'q2'})
            alphabet: Set von Bandsymbolen (z.B. {'0', '1', '□'})
            blank: Das Leerzeichen-Symbol (z.B. '□')
            initial_state: Startzustand (z.B. 'q0')
            final_states: Set von Endzuständen (z.B. {'q2'})
            transitions: Liste von TMTransition-Objekten
        """
        self.states = states
        self.alphabet = alphabet
        self.blank = blank
        self.initial_state = initial_state
        self.final_states = final_states
        self.transitions = transitions

        # ─────────────────────────────────────────────────────────────────
        # Transition-Lookup-Tabelle erstellen
        # ─────────────────────────────────────────────────────────────────
        # Dict[Tuple[str, str], TMTransition]
        # Schlüssel: (aktueller_zustand, gelesenes_symbol)
        # Wert: Die entsprechende Transition
        #
        # Dies ermöglicht O(1) Zugriff statt O(n) Suche
        # ─────────────────────────────────────────────────────────────────
        self.transition_map = {}
        for t in transitions:
            key = (t.current_state, t.read_symbol)
            self.transition_map[key] = t

    def __str__(self):
        """Formatierte Ausgabe der TM-Definition"""
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


# ═══════════════════════════════════════════════════════════════════════════
# TMSIMULATOR - Simulator für Standard-Turing-Maschinen
# ═══════════════════════════════════════════════════════════════════════════

class TMSimulator:
    """
    Simulator für Standard-Turing-Maschinen.

    Führt eine TM Schritt für Schritt aus und speichert
    die Historie für spätere Anzeige.
    """

    def __init__(self, tm):
        """
        Konstruktor.

        Args:
            tm: Die zu simulierende TuringMachine
        """
        self.tm = tm

        # Simulationszustand
        self.tape = []           # Das Band als Liste von Symbolen
        self.head_position = 0   # Position des Lese-/Schreibkopfs
        self.current_state = ""  # Aktueller Zustand
        self.step_count = 0      # Anzahl der ausgeführten Schritte

        # Historie: Liste von (zustand, band, kopfposition)
        self.history = []

    def initialize(self, input_string):
        """
        Initialisiert den Simulator mit einer Eingabe.

        Args:
            input_string: Die Eingabe auf dem Band (z.B. "01")
        """
        # Band mit Eingabe füllen
        if input_string:
            self.tape = list(input_string)  # "01" -> ['0', '1']
        else:
            self.tape = [self.tm.blank]     # Leeres Band

        self.head_position = 0
        self.current_state = self.tm.initial_state
        self.step_count = 0
        self.history = []

        # Anfangszustand speichern
        self._save_state()

    def _save_state(self):
        """Speichert den aktuellen Zustand in der Historie."""
        # Wichtig: tape.copy() erstellt eine Kopie der Liste!
        # Ohne copy() würden alle Historie-Einträge auf dieselbe Liste zeigen
        self.history.append((
            self.current_state,
            self.tape.copy(),
            self.head_position
        ))

    def _ensure_tape_bounds(self):
        """
        Erweitert das Band falls der Kopf außerhalb ist.

        Das Band einer TM ist konzeptionell unendlich.
        Wir erweitern es bei Bedarf mit Blank-Symbolen.
        """
        # Kopf ist links vom Band
        while self.head_position < 0:
            self.tape.insert(0, self.tm.blank)  # Blank am Anfang einfügen
            self.head_position += 1              # Kopfposition anpassen

        # Kopf ist rechts vom Band
        while self.head_position >= len(self.tape):
            self.tape.append(self.tm.blank)      # Blank am Ende anfügen

    def step(self):
        """
        Führt einen einzelnen Schritt der TM aus.

        Returns:
            True wenn die Maschine weiterlaufen kann,
            False wenn sie angehalten hat.
        """
        # ─────────────────────────────────────────────────────────────────
        # Prüfen ob wir in einem Endzustand sind
        # ─────────────────────────────────────────────────────────────────
        if self.current_state in self.tm.final_states:
            return False

        # ─────────────────────────────────────────────────────────────────
        # Band erweitern falls nötig und Symbol lesen
        # ─────────────────────────────────────────────────────────────────
        self._ensure_tape_bounds()
        read_symbol = self.tape[self.head_position]

        # ─────────────────────────────────────────────────────────────────
        # Transition suchen
        # ─────────────────────────────────────────────────────────────────
        key = (self.current_state, read_symbol)
        if key not in self.tm.transition_map:
            # Keine Transition definiert -> Maschine hält an
            return False

        transition = self.tm.transition_map[key]

        # ─────────────────────────────────────────────────────────────────
        # Transition ausführen
        # ─────────────────────────────────────────────────────────────────

        # 1. Symbol schreiben
        self.tape[self.head_position] = transition.write_symbol

        # 2. Kopf bewegen
        if transition.direction == Direction.RIGHT:
            self.head_position += 1
        else:  # LEFT
            self.head_position -= 1

        # 3. Zustand wechseln
        self.current_state = transition.next_state

        # 4. Schrittzähler erhöhen
        self.step_count += 1

        # ─────────────────────────────────────────────────────────────────
        # Band erweitern und Zustand speichern
        # ─────────────────────────────────────────────────────────────────
        self._ensure_tape_bounds()
        self._save_state()

        # Maschine läuft weiter, wenn wir nicht in einem Endzustand sind
        return self.current_state not in self.tm.final_states

    def run(self, max_steps=1000):
        """
        Führt die Maschine aus bis sie hält oder max_steps erreicht.

        Args:
            max_steps: Maximale Anzahl Schritte (Schutz vor Endlosschleifen)

        Returns:
            True wenn die Maschine normal gehalten hat,
            False wenn max_steps erreicht wurde.
        """
        while self.step_count < max_steps:
            if not self.step():
                return True  # Normal gehalten
        return False  # max_steps erreicht

    def get_tape_string(self):
        """
        Gibt den Bandinhalt als String zurück.
        Entfernt führende und abschließende Blanks.
        """
        result = ''.join(self.tape)
        result = result.strip(self.tm.blank)
        return result if result else self.tm.blank

    def format_configuration(self, state=None, tape=None, head_pos=None, step=None):
        """
        Formatiert eine Konfiguration für die Anzeige.

        Eine Konfiguration zeigt: Schritt, Zustand, Band mit Kopfposition
        """
        # Standardwerte verwenden falls nicht angegeben
        if state is None:
            state = self.current_state
        if tape is None:
            tape = self.tape
        if head_pos is None:
            head_pos = self.head_position
        if step is None:
            step = self.step_count

        # Band mit Kopfmarkierung erstellen
        # [x] markiert die Position des Kopfes
        tape_str = ""
        for i, symbol in enumerate(tape):
            if i == head_pos:
                tape_str += f"[{symbol}]"
            else:
                tape_str += f" {symbol} "

        return f"Schritt {step:3d}: {state:10s} |{tape_str}|"

    def print_execution(self, delay=0.0):
        """
        Gibt die gesamte Ausführungshistorie aus.

        Args:
            delay: Verzögerung zwischen den Schritten (für Animation)
        """
        print("\n┌" + "─" * 58 + "┐")
        print("│" + " AUSFÜHRUNG DER STANDARD-TM ".center(58) + "│")
        print("└" + "─" * 58 + "┘\n")

        # Jeden gespeicherten Zustand ausgeben
        for i, (state, tape, head_pos) in enumerate(self.history):
            print(self.format_configuration(state, tape, head_pos, i))
            if delay > 0:
                time.sleep(delay)

        # Endergebnis
        if self.current_state in self.tm.final_states:
            status = "AKZEPTIERT"
        else:
            status = "GESTOPPT"

        print(f"\n  === {status} nach {self.step_count} Schritten ===")
        print(f"  Endzustand: {self.current_state}")
        print(f"  Bandinhalt: {self.get_tape_string()}")


# ═══════════════════════════════════════════════════════════════════════════
# CLOCKWISETURINGMACHINE - Clockwise Turing Machine
# ═══════════════════════════════════════════════════════════════════════════

class ClockwiseTuringMachine:
    """
    Clockwise Turing Machine (zirkuläres Band, nur Uhrzeigersinn).

    Unterschiede zur Standard-TM:
    1. Das Band ist zirkulär (ein Ring)
    2. Der Kopf bewegt sich NUR im Uhrzeigersinn
    3. Transitionen können eine Zelle in zwei teilen
    """

    def __init__(self, states, alphabet, initial_state, final_state, transitions):
        """
        Konstruktor.

        Args:
            states: Set von Zuständen
            alphabet: Set von Bandsymbolen
            initial_state: Startzustand
            final_state: Der EINE Endzustand (CTM hat nur einen)
            transitions: Liste von CTMTransition-Objekten
        """
        self.states = states
        self.alphabet = alphabet
        self.initial_state = initial_state
        self.final_state = final_state  # Nur EIN Endzustand
        self.transitions = transitions

        # Transition-Lookup erstellen
        self.transition_map = {}
        for t in transitions:
            key = (t.current_state, t.read_symbol)
            self.transition_map[key] = t

    def __str__(self):
        """Formatierte Ausgabe der CTM-Definition"""
        lines = [
            "╔══════════════════════════════════════╗",
            "║      CLOCKWISE TURING MACHINE        ║",
            "╚══════════════════════════════════════╝",
        ]

        # Zustände (nur erste 5 anzeigen wenn zu viele)
        sorted_states = sorted(self.states)
        if len(sorted_states) > 5:
            states_str = f"{sorted_states[:5]}..."
        else:
            states_str = str(sorted_states)
        lines.append(f"  Zustände ({len(self.states):2d}): {states_str}")

        lines.append(f"  Alphabet ({len(self.alphabet):2d}): {sorted(self.alphabet)}")
        lines.append(f"  Startzustand:  {self.initial_state}")
        lines.append(f"  Endzustand:    {self.final_state}")
        lines.append(f"  Übergänge ({len(self.transitions):2d}):")

        # Nur erste 15 Transitionen anzeigen
        for t in self.transitions[:15]:
            lines.append(f"    {t}")
        if len(self.transitions) > 15:
            lines.append(f"    ... und {len(self.transitions) - 15} weitere")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# CTMSIMULATOR - Simulator für Clockwise Turing Machines
# ═══════════════════════════════════════════════════════════════════════════

class CTMSimulator:
    """
    Simulator für Clockwise Turing Machines.

    Besonderheiten:
    - Das Band ist zirkulär (Modulo-Arithmetik für Kopfbewegung)
    - Es gibt spezielle Marker-Symbole (L, R, M)
    """

    # Spezielle Symbole
    MARKER = "M"      # σₘ - Marker für Linksbewegung
    RIGHT_END = "R"   # σᵣ - Markiert rechtes Ende
    LEFT_END = "L"    # σₗ - Markiert linkes Ende

    def __init__(self, ctm):
        """
        Konstruktor.

        Args:
            ctm: Die zu simulierende ClockwiseTuringMachine
        """
        self.ctm = ctm

        # Simulationszustand
        self.tape = []           # Zirkuläres Band als Liste
        self.head_position = 0   # Position des Kopfes
        self.current_state = ""  # Aktueller Zustand
        self.step_count = 0      # Schrittzähler

        # Historie: (zustand, band, kopfposition, transition)
        self.history = []

    def initialize(self, input_string):
        """
        Initialisiert den Simulator mit einer Eingabe.

        Das Band wird so aufgebaut:
        [L] [Eingabe...] [R]

        L und R markieren die ursprünglichen Enden.
        """
        # Band aufbauen
        self.tape = [self.LEFT_END]      # Linker Marker
        if input_string:
            self.tape.extend(list(input_string))  # Eingabe
        self.tape.append(self.RIGHT_END)  # Rechter Marker

        self.head_position = 1  # Startet auf erstem Eingabesymbol
        self.current_state = self.ctm.initial_state
        self.step_count = 0
        self.history = []

        self._save_state(None)  # Anfangszustand (keine Transition)

    def _save_state(self, transition):
        """Speichert den aktuellen Zustand in der Historie."""
        self.history.append((
            self.current_state,
            self.tape.copy(),
            self.head_position,
            transition
        ))

    def _move_clockwise(self):
        """
        Bewegt den Kopf im Uhrzeigersinn.

        Bei einem zirkulären Band mit n Zellen:
        Position (i + 1) mod n

        Wenn wir am Ende sind (Position n-1), gehen wir zu Position 0.
        """
        self.head_position = (self.head_position + 1) % len(self.tape)

    def step(self):
        """
        Führt einen einzelnen Schritt der CTM aus.

        Returns:
            True wenn die Maschine weiterlaufen kann,
            False wenn sie angehalten hat.
        """
        # ─────────────────────────────────────────────────────────────────
        # Prüfen ob wir im Endzustand sind
        # ─────────────────────────────────────────────────────────────────
        if self.current_state == self.ctm.final_state:
            return False

        # ─────────────────────────────────────────────────────────────────
        # Symbol lesen und Transition suchen
        # ─────────────────────────────────────────────────────────────────
        read_symbol = self.tape[self.head_position]

        key = (self.current_state, read_symbol)
        if key not in self.ctm.transition_map:
            return False  # Keine Transition -> halt

        transition = self.ctm.transition_map[key]

        # ─────────────────────────────────────────────────────────────────
        # Transition ausführen
        # ─────────────────────────────────────────────────────────────────

        if len(transition.write_value) == 1:
            # ─────────────────────────────────────────────────────────────
            # Normales Überschreiben: Eine Zelle bleibt eine Zelle
            # ─────────────────────────────────────────────────────────────
            self.tape[self.head_position] = transition.write_value
        else:
            # ─────────────────────────────────────────────────────────────
            # Zellteilung: Eine Zelle wird zu ZWEI Zellen
            #
            # Beispiel: write_value = "MR"
            # Vorher:  [..., X, ...]
            #               ^
            # Nachher: [..., M, R, ...]
            #               ^
            # ─────────────────────────────────────────────────────────────
            self.tape[self.head_position] = transition.write_value[0]
            self.tape.insert(self.head_position + 1, transition.write_value[1])

        # Zustand wechseln
        self.current_state = transition.next_state

        # Kopf im Uhrzeigersinn bewegen
        self._move_clockwise()

        self.step_count += 1
        self._save_state(transition)

        return self.current_state != self.ctm.final_state

    def run(self, max_steps=1000):
        """Führt die Maschine aus bis sie hält."""
        while self.step_count < max_steps:
            if not self.step():
                return True
        return False

    def get_tape_string(self):
        """Gibt den Bandinhalt ohne spezielle Marker zurück."""
        result = ''.join(s for s in self.tape
                        if s not in {self.LEFT_END, self.RIGHT_END, self.MARKER})
        return result if result else "ε"

    def format_configuration(self, state, tape, head_pos, step, transition=None):
        """Formatiert eine Konfiguration für die Anzeige."""
        # Band-String erstellen
        tape_str = ""
        for i in range(len(tape)):
            symbol = tape[i]
            # Symbol kürzen wenn nötig
            display = symbol if len(symbol) <= 2 else symbol[:2]

            if i == head_pos:
                tape_str += f"[{display}]"
            else:
                tape_str += f" {display} "

        # Zustand kürzen
        state_display = state if len(state) <= 12 else state[:10] + ".."

        result = f"Schritt {step:3d}: {state_display:12s} |{tape_str}|"

        # Transition anzeigen
        if transition:
            result += f"  <- {transition}"

        return result

    def format_circular_tape(self, tape, head_pos):
        """
        Formatiert das Band als Kreis (ASCII-Art).

        Zeigt die zirkuläre Natur des Bandes.
        """
        n = len(tape)
        lines = []

        # Obere Linie
        lines.append("    ┌" + "───┬" * (n-1) + "───┐")

        # Symbole
        symbol_line = "    │"
        for i, symbol in enumerate(tape):
            display = symbol if len(symbol) <= 2 else symbol[:2]
            if i == head_pos:
                symbol_line += f">{display}<│"  # Kopfposition markiert
            else:
                symbol_line += f" {display} │"
        lines.append(symbol_line)

        # Untere Linie
        lines.append("    └" + "───┴" * (n-1) + "───┘")

        # Zirkuläre Verbindung anzeigen
        lines.append("     ↑" + " " * (n * 4 - 2) + "↑")
        lines.append("     └" + "─" * (n * 4 - 2) + "┘ (zirkulär)")

        return "\n".join(lines)

    def print_execution(self, delay=0.0, detailed=False):
        """Gibt die gesamte Ausführungshistorie aus."""
        print("\n┌" + "─" * 70 + "┐")
        print("│" + " AUSFÜHRUNG DER CLOCKWISE TM ".center(70) + "│")
        print("└" + "─" * 70 + "┘\n")

        for i, (state, tape, head_pos, transition) in enumerate(self.history):
            # Transition nur ab Schritt 1 anzeigen
            trans_to_show = transition if i > 0 else None
            print(self.format_configuration(state, tape, head_pos, i, trans_to_show))

            # Detaillierte Ansicht: Zirkuläres Band zeigen
            if detailed and i < len(self.history) - 1:
                print(self.format_circular_tape(tape, head_pos))
                print()

            if delay > 0:
                time.sleep(delay)

        # Endergebnis
        if self.current_state == self.ctm.final_state:
            status = "AKZEPTIERT"
        else:
            status = "GESTOPPT"

        print(f"\n  === {status} nach {self.step_count} Schritten ===")
        print(f"  Endzustand: {self.current_state}")
        print(f"  Bandinhalt: {self.get_tape_string()}")


# ═══════════════════════════════════════════════════════════════════════════
# TMTOCLOCKWISECONVERTER - Der Kern-Algorithmus!
# ═══════════════════════════════════════════════════════════════════════════

class TMtoClockwiseConverter:
    """
    Konvertiert eine Standard-TM in eine Clockwise TM.

    Dies ist der Kern-Algorithmus basierend auf Lemma 2.1 aus dem Paper.

    Grundidee:
    - Rechtsbewegungen sind trivial (Uhrzeigersinn = Rechts)
    - Linksbewegungen erfordern Band-Rotation:
      1. Aktuelle Position markieren
      2. Alle Symbole im Uhrzeigersinn rotieren
      3. Wenn Marker wieder erreicht, ist Rotation fertig
    """

    # Spezielle Symbole
    MARKER = "M"      # σₘ - Marker für Linksbewegung
    RIGHT_END = "R"   # σᵣ - Rechtes Ende
    LEFT_END = "L"    # σₗ - Linkes Ende

    def __init__(self, tm):
        """
        Konstruktor.

        Args:
            tm: Die zu konvertierende TuringMachine
        """
        self.tm = tm

        # Diese werden während der Konvertierung aufgebaut
        self.ctm_states = set()           # Zustände der CTM
        self.ctm_alphabet = set()         # Alphabet der CTM
        self.ctm_transitions = []         # Transitionen der CTM

    def convert(self):
        """
        Führt die Konvertierung durch.

        Returns:
            ClockwiseTuringMachine
        """
        # ─────────────────────────────────────────────────────────────────
        # 1. Alphabet aufbauen
        # ─────────────────────────────────────────────────────────────────
        # Alle Symbole außer Blank übernehmen
        self.ctm_alphabet = set()
        for s in self.tm.alphabet:
            if s != self.tm.blank:
                self.ctm_alphabet.add(s)

        # Spezielle Symbole hinzufügen
        self.ctm_alphabet.add(self.MARKER)
        self.ctm_alphabet.add(self.RIGHT_END)
        self.ctm_alphabet.add(self.LEFT_END)

        # ─────────────────────────────────────────────────────────────────
        # 2. Basiszustände übernehmen
        # ─────────────────────────────────────────────────────────────────
        self.ctm_states = set(self.tm.states)

        # ─────────────────────────────────────────────────────────────────
        # 3. Jeden Übergang konvertieren
        # ─────────────────────────────────────────────────────────────────
        for transition in self.tm.transitions:
            if transition.direction == Direction.RIGHT:
                self._convert_right_move(transition)
            else:
                self._convert_left_move(transition)

        # ─────────────────────────────────────────────────────────────────
        # 4. CTM erstellen und zurückgeben
        # ─────────────────────────────────────────────────────────────────
        # Wir nehmen den ersten Endzustand der Original-TM
        final_state = None
        for state in self.tm.final_states:
            final_state = state
            break

        return ClockwiseTuringMachine(
            states=self.ctm_states,
            alphabet=self.ctm_alphabet,
            initial_state=self.tm.initial_state,
            final_state=final_state,
            transitions=self.ctm_transitions
        )

    def _convert_right_move(self, t):
        """
        Konvertiert eine Rechtsbewegung.

        Rechtsbewegung ist einfach, da Uhrzeigersinn = Rechts.

        Standard:  δ(qx, σ) = (σ', R, qy)
        Clockwise: δ(qx, σ) = (σ', qy)

        Spezialfall: Blank lesen (am rechten Rand)
        """
        if t.read_symbol == self.tm.blank:
            # ─────────────────────────────────────────────────────────────
            # Spezialfall: Blank lesen bedeutet wir sind am rechten Rand
            # ─────────────────────────────────────────────────────────────
            if t.write_symbol == self.tm.blank:
                # Blank bleibt Blank - R-Marker bleibt
                self.ctm_transitions.append(CTMTransition(
                    current_state=t.current_state,
                    read_symbol=self.RIGHT_END,
                    write_value=self.RIGHT_END,
                    next_state=t.next_state
                ))
            else:
                # Neues Symbol einfügen durch Zellteilung
                # R wird zu: [neues_symbol][R]
                self.ctm_transitions.append(CTMTransition(
                    current_state=t.current_state,
                    read_symbol=self.RIGHT_END,
                    write_value=t.write_symbol + self.RIGHT_END,
                    next_state=t.next_state
                ))
        else:
            # ─────────────────────────────────────────────────────────────
            # Normalfall: Einfach Symbol ersetzen
            # ─────────────────────────────────────────────────────────────
            self.ctm_transitions.append(CTMTransition(
                current_state=t.current_state,
                read_symbol=t.read_symbol,
                write_value=t.write_symbol,
                next_state=t.next_state
            ))

    def _convert_left_move(self, t):
        """
        Konvertiert eine Linksbewegung durch Band-Rotation.

        Dies ist der komplexe Teil!

        Standard:  δ(qx, σ) = (σ', L, qy)

        Clockwise (mehrere Schritte):
        1. Markiere aktuelle Position mit M
        2. Merke das zu schreibende Symbol im Zustand
        3. Rotiere alle Symbole im Uhrzeigersinn
        4. Wenn M wieder erreicht, schreibe letztes gemerktes Symbol

        Beispiel: Band [a, b, c], Kopf auf b, schreibe X, gehe links

        Schritt 1: [a, M, c]     Kopf auf c, Zustand trägt "X"
        Schritt 2: [a, M, X]     Kopf auf a, Zustand trägt "c"
        Schritt 3: [c, M, X]     Kopf auf M, Zustand trägt "a"
        Schritt 4: [c, a, X]     Kopf auf X, fertig!

        Der Kopf ist jetzt relativ zum Bandinhalt LINKS!
        """
        qx = t.current_state
        qy = t.next_state

        # Das zu schreibende Symbol (Blank wird zu R-Marker)
        if t.write_symbol == self.tm.blank:
            write_sym = self.RIGHT_END
        else:
            write_sym = t.write_symbol

        # ─────────────────────────────────────────────────────────────────
        # Schritt 1: Markiere aktuelle Position
        # ─────────────────────────────────────────────────────────────────
        # Der erste Carry-Zustand trägt das zu schreibende Symbol
        carry_state_initial = f"{qy}_{write_sym}"
        self.ctm_states.add(carry_state_initial)

        if t.read_symbol == self.tm.blank:
            # Am rechten Rand: R-Marker wird zu [M][write_sym]
            self.ctm_transitions.append(CTMTransition(
                current_state=qx,
                read_symbol=self.RIGHT_END,
                write_value=self.MARKER + write_sym,
                next_state=f"{qy}_{self.RIGHT_END}"
            ))
            self.ctm_states.add(f"{qy}_{self.RIGHT_END}")
        else:
            # Normalfall: Symbol wird zu M
            self.ctm_transitions.append(CTMTransition(
                current_state=qx,
                read_symbol=t.read_symbol,
                write_value=self.MARKER,
                next_state=carry_state_initial
            ))

        # ─────────────────────────────────────────────────────────────────
        # Schritt 2: Rotations-Regeln generieren
        # ─────────────────────────────────────────────────────────────────
        # Für jedes Symbol σ brauchen wir einen Carry-Zustand qy_σ
        # Dieser Zustand "trägt" das Symbol σ, das als nächstes
        # geschrieben werden soll.

        all_symbols = self.ctm_alphabet - {self.MARKER}

        for sigma in all_symbols:
            carry_state = f"{qy}_{sigma}"
            self.ctm_states.add(carry_state)

            for sigma_read in self.ctm_alphabet:
                if sigma_read == self.MARKER:
                    # ─────────────────────────────────────────────────────
                    # Marker gefunden → Rotation abgeschlossen!
                    # Schreibe das getragene Symbol und gehe zu qy
                    # ─────────────────────────────────────────────────────
                    self.ctm_transitions.append(CTMTransition(
                        current_state=carry_state,
                        read_symbol=self.MARKER,
                        write_value=sigma,
                        next_state=qy
                    ))
                else:
                    # ─────────────────────────────────────────────────────
                    # Weiter rotieren:
                    # - Schreibe das getragene Symbol (sigma)
                    # - Merke das gelesene Symbol (sigma_read)
                    # - Gehe zu Carry-Zustand für sigma_read
                    # ─────────────────────────────────────────────────────
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

def create_simple_example_tm():
    """
    Erstellt eine einfache TM für Demonstrationszwecke.

    Regel 1: δ(q1, 0) = (1, R, q2)  - Lies 0, schreibe 1, gehe rechts
    Regel 2: δ(q2, 1) = (0, L, q3)  - Lies 1, schreibe 0, gehe links

    Eingabe "01" wird zu "10"
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


# ═══════════════════════════════════════════════════════════════════════════
# DEMO-FUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════

def demo_simple():
    """Demonstriert die einfache TM und ihre Clockwise-Version."""

    print("\n" + "=" * 72)
    print(" DEMO: Einfache TM mit Rechts- und Linksbewegung ".center(72, "="))
    print("=" * 72)

    # ─────────────────────────────────────────────────────────────────────
    # 1. TM erstellen und anzeigen
    # ─────────────────────────────────────────────────────────────────────
    tm = create_simple_example_tm()
    print(f"\n{tm}")

    # ─────────────────────────────────────────────────────────────────────
    # 2. Standard-TM simulieren
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "-" * 72)
    print(" Simulation der Standard-TM ".center(72))
    print("-" * 72)

    sim_tm = TMSimulator(tm)
    sim_tm.initialize("01")
    sim_tm.run()
    sim_tm.print_execution()

    # ─────────────────────────────────────────────────────────────────────
    # 3. Zu Clockwise TM konvertieren
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "-" * 72)
    print(" Konvertierung zu Clockwise TM ".center(72))
    print("-" * 72)

    converter = TMtoClockwiseConverter(tm)
    ctm = converter.convert()
    print(f"\n{ctm}")

    # ─────────────────────────────────────────────────────────────────────
    # 4. Clockwise TM simulieren
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "-" * 72)
    print(" Simulation der Clockwise TM ".center(72))
    print("-" * 72)

    sim_ctm = CTMSimulator(ctm)
    sim_ctm.initialize("01")
    sim_ctm.run()
    sim_ctm.print_execution()

    # ─────────────────────────────────────────────────────────────────────
    # 5. Vergleich
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "-" * 72)
    print(" VERGLEICH ".center(72))
    print("-" * 72)
    print(f"  Standard-TM:  {len(tm.states)} Zustände, {len(tm.transitions)} Übergänge, {sim_tm.step_count} Schritte")
    print(f"  Clockwise-TM: {len(ctm.states)} Zustände, {len(ctm.transitions)} Übergänge, {sim_ctm.step_count} Schritte")
    print(f"\n  Ergebnis Standard-TM:  01 -> {sim_tm.get_tape_string()}")
    print(f"  Ergebnis Clockwise-TM: 01 -> {sim_ctm.get_tape_string()}")


def demo_detailed():
    """Zeigt detaillierte Ansicht mit zirkulärem Band."""

    print("\n" + "=" * 72)
    print(" DEMO: Detaillierte Clockwise-TM Ansicht ".center(72, "="))
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

if __name__ == "__main__":
    print("\n" + "#" * 72)
    print("#" + " TM -> CLOCKWISE TM KONVERTER (ohne dataclass) ".center(70) + "#")
    print("#" * 72)

    # Demo ausführen
    demo_simple()

    print("\n\n")
    demo_detailed()
