"""
Enigma Machine Simulator
Simuliert die Enigma M3 Verschlüsselungsmaschine
"""

class Rotor:
    """Repräsentiert einen Enigma-Rotor mit Verdrahtung und Rotation"""

    # Historische Rotor-Verdrahtungen (Enigma I)
    ROTORS = {
        'I':   'EKMFLGDQVZNTOWYHXUSPAIBRCJ',
        'II':  'AJDKSIRUXBLHWTMCQGZNPYFVOE',
        'III': 'BDFHJLCPRTXVZNYEIWGAKMUSQO',
        'IV':  'ESOVPZJAYQUIRHXLNFTGKDCMWB',
        'V':   'VZBRGITYUPSDNHLXAWMJQOFECK'
    }

    # Positionen, an denen der nächste Rotor weiterdreht
    NOTCHES = {
        'I': 'Q',
        'II': 'E',
        'III': 'V',
        'IV': 'J',
        'V': 'Z'
    }

    def __init__(self, wiring_name, ring_setting=0, initial_position=0):
        self.wiring = self.ROTORS[wiring_name]
        self.notch = self.NOTCHES[wiring_name]
        self.ring_setting = ring_setting
        self.position = initial_position

    def encode_forward(self, char):
        """Kodiert einen Buchstaben vorwärts durch den Rotor"""
        shift = self.position - self.ring_setting
        # Eingangsposition berechnen
        char_pos = (ord(char) - ord('A') + shift) % 26
        # Durch Verdrahtung
        encoded_char = self.wiring[char_pos]
        # Ausgangsposition berechnen
        output_pos = (ord(encoded_char) - ord('A') - shift) % 26
        return chr(output_pos + ord('A'))

    def encode_backward(self, char):
        """Kodiert einen Buchstaben rückwärts durch den Rotor"""
        shift = self.position - self.ring_setting
        # Eingangsposition berechnen
        char_pos = (ord(char) - ord('A') + shift) % 26
        input_char = chr(char_pos + ord('A'))
        # Rückwärts durch Verdrahtung
        encoded_pos = self.wiring.index(input_char)
        # Ausgangsposition berechnen
        output_pos = (encoded_pos - shift) % 26
        return chr(output_pos + ord('A'))

    def rotate(self):
        """Dreht den Rotor um eine Position weiter"""
        self.position = (self.position + 1) % 26
        return self.at_notch()

    def at_notch(self):
        """Prüft, ob der Rotor an der Übertragsposition ist"""
        return chr(self.position + ord('A')) == self.notch


class Reflector:
    """Repräsentiert den Enigma-Reflektor"""

    REFLECTORS = {
        'B': 'YRUHQSLDPXNGOKMIEBFZCWVJAT',
        'C': 'FVPJIAOYEDRZXWGCTKUQSBNMHL'
    }

    def __init__(self, reflector_type='B'):
        self.wiring = self.REFLECTORS[reflector_type]

    def reflect(self, char):
        """Reflektiert einen Buchstaben"""
        pos = ord(char) - ord('A')
        return self.wiring[pos]


class Plugboard:
    """Repräsentiert das Steckerbrett"""

    def __init__(self, pairs=''):
        """
        pairs: String mit Buchstabenpaaren, z.B. 'AB CD EF'
        """
        self.mapping = {}
        if pairs:
            for pair in pairs.split():
                if len(pair) == 2:
                    a, b = pair.upper()
                    self.mapping[a] = b
                    self.mapping[b] = a

    def swap(self, char):
        """Tauscht einen Buchstaben durch das Steckerbrett"""
        return self.mapping.get(char, char)


class Enigma:
    """Die Enigma-Maschine"""

    def __init__(self, rotors, reflector='B', ring_settings=(0,0,0),
                 initial_positions=(0,0,0), plugboard=''):
        """
        rotors: Tuple mit 3 Rotor-Namen, z.B. ('I', 'II', 'III')
        reflector: Reflektor-Typ ('B' oder 'C')
        ring_settings: Ringstellung für jeden Rotor (0-25)
        initial_positions: Startposition für jeden Rotor (0-25)
        plugboard: Steckerbrett-Verbindungen, z.B. 'AB CD EF'
        """
        self.left = Rotor(rotors[0], ring_settings[0], initial_positions[0])
        self.middle = Rotor(rotors[1], ring_settings[1], initial_positions[1])
        self.right = Rotor(rotors[2], ring_settings[2], initial_positions[2])
        self.reflector = Reflector(reflector)
        self.plugboard = Plugboard(plugboard)

    def _rotate_rotors(self):
        """Rotiert die Rotoren (Double-Stepping Mechanismus)"""
        # Double-stepping: Wenn mittlerer Rotor am Notch ist
        if self.middle.at_notch():
            self.middle.rotate()
            self.left.rotate()
        # Rechter Rotor dreht immer
        if self.right.rotate():
            # Wenn rechter Rotor am Notch ist, dreht mittlerer
            if not self.middle.at_notch():
                self.middle.rotate()

    def encode_char(self, char):
        """Kodiert einen einzelnen Buchstaben"""
        if not char.isalpha():
            return char

        char = char.upper()

        # Rotoren drehen VOR der Verschlüsselung
        self._rotate_rotors()

        # Durch Steckerbrett
        char = self.plugboard.swap(char)

        # Vorwärts durch die Rotoren
        char = self.right.encode_forward(char)
        char = self.middle.encode_forward(char)
        char = self.left.encode_forward(char)

        # Durch Reflektor
        char = self.reflector.reflect(char)

        # Rückwärts durch die Rotoren
        char = self.left.encode_backward(char)
        char = self.middle.encode_backward(char)
        char = self.right.encode_backward(char)

        # Durch Steckerbrett zurück
        char = self.plugboard.swap(char)

        return char

    def encode(self, text):
        """Kodiert einen ganzen Text"""
        result = []
        for char in text:
            result.append(self.encode_char(char))
        return ''.join(result)

    def reset(self, initial_positions=(0,0,0)):
        """Setzt die Rotoren auf neue Startpositionen"""
        self.left.position = initial_positions[0]
        self.middle.position = initial_positions[1]
        self.right.position = initial_positions[2]


# Beispiel-Verwendung
if __name__ == "__main__":
    print("=== ENIGMA MASCHINE SIMULATOR ===\n")

    # Enigma-Maschine konfigurieren
    enigma = Enigma(
        rotors=('I', 'II', 'III'),
        reflector='B',
        ring_settings=(0, 0, 0),
        initial_positions=(0, 0, 0),  # A, A, A
        plugboard='AB CD EF GH IJ'
    )

    # Text verschlüsseln
    plaintext = "HELLO WORLD"
    print(f"Klartext:        {plaintext}")

    ciphertext = enigma.encode(plaintext)
    print(f"Verschlüsselt:   {ciphertext}")

    # Für Entschlüsselung: Maschine zurücksetzen und nochmal durchlaufen
    enigma.reset(initial_positions=(0, 0, 0))
    decrypted = enigma.encode(ciphertext)
    print(f"Entschlüsselt:   {decrypted}")

    print("\n" + "="*40)
    print("\n=== ZWEITES BEISPIEL ===\n")

    # Längerer Text
    enigma2 = Enigma(
        rotors=('III', 'II', 'I'),
        reflector='B',
        ring_settings=(1, 1, 1),
        initial_positions=(5, 12, 20),  # F, M, U
        plugboard='AR GK OX'
    )

    message = "ATTACKATDAWN"
    print(f"Nachricht:       {message}")

    encrypted = enigma2.encode(message)
    print(f"Verschlüsselt:   {encrypted}")

    # Entschlüsseln
    enigma2.reset(initial_positions=(5, 12, 20))
    decrypted2 = enigma2.encode(encrypted)
    print(f"Entschlüsselt:   {decrypted2}")

    print("\n" + "="*40)
    print("\nHinweis: Die Enigma ist symmetrisch - dieselbe")
    print("Konfiguration ver- und entschlüsselt!")
