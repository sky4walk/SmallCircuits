#!/usr/bin/env python3
"""
SHA-256 Hash Berechnung (Pure Python Implementation)
Zeigt die komplette Funktionsweise des SHA-256 Algorithmus
"""

import sys
import os

# SHA-256 Konstanten: Erste 32 Bits der Kubikwurzeln der ersten 64 Primzahlen
K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]

# Anfangswerte: Erste 32 Bits der Quadratwurzeln der ersten 8 Primzahlen
H_INIT = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
]

def right_rotate(value, shift):
    """Rotiert eine 32-Bit Zahl nach rechts"""
    return ((value >> shift) | (value << (32 - shift))) & 0xffffffff

def sha256_transform(chunk, h):
    """Verarbeitet einen 512-Bit Block"""
    # Nachricht in 16 32-Bit Wörter aufteilen
    w = []
    for i in range(16):
        w.append(int.from_bytes(chunk[i*4:(i+1)*4], byteorder='big'))

    # Erweitere auf 64 Wörter
    for i in range(16, 64):
        s0 = right_rotate(w[i-15], 7) ^ right_rotate(w[i-15], 18) ^ (w[i-15] >> 3)
        s1 = right_rotate(w[i-2], 17) ^ right_rotate(w[i-2], 19) ^ (w[i-2] >> 10)
        w.append((w[i-16] + s0 + w[i-7] + s1) & 0xffffffff)

    # Initialisiere Arbeitsvariablen
    a, b, c, d, e, f, g, h_val = h

    # Hauptschleife (64 Runden)
    for i in range(64):
        S1 = right_rotate(e, 6) ^ right_rotate(e, 11) ^ right_rotate(e, 25)
        ch = (e & f) ^ ((~e) & g)
        temp1 = (h_val + S1 + ch + K[i] + w[i]) & 0xffffffff
        S0 = right_rotate(a, 2) ^ right_rotate(a, 13) ^ right_rotate(a, 22)
        maj = (a & b) ^ (a & c) ^ (b & c)
        temp2 = (S0 + maj) & 0xffffffff

        h_val = g
        g = f
        f = e
        e = (d + temp1) & 0xffffffff
        d = c
        c = b
        b = a
        a = (temp1 + temp2) & 0xffffffff

    # Addiere zum Hash-Wert
    return [
        (h[0] + a) & 0xffffffff,
        (h[1] + b) & 0xffffffff,
        (h[2] + c) & 0xffffffff,
        (h[3] + d) & 0xffffffff,
        (h[4] + e) & 0xffffffff,
        (h[5] + f) & 0xffffffff,
        (h[6] + g) & 0xffffffff,
        (h[7] + h_val) & 0xffffffff
    ]

def sha256(data):
    """Berechnet SHA-256 Hash von Bytes"""
    # Kopiere die initialen Hash-Werte
    h = H_INIT.copy()

    # Preprocessing: Länge der Nachricht in Bits
    ml = len(data) * 8

    # Padding: Füge '1' Bit hinzu (als 0x80 Byte)
    data += b'\x80'

    # Füge '0' Bits hinzu bis Länge ≡ 448 (mod 512)
    while len(data) % 64 != 56:
        data += b'\x00'

    # Füge die ursprüngliche Länge als 64-Bit Big-Endian Zahl hinzu
    data += ml.to_bytes(8, byteorder='big')

    # Verarbeite die Nachricht in 512-Bit Blöcken
    for i in range(0, len(data), 64):
        chunk = data[i:i+64]
        h = sha256_transform(chunk, h)

    # Erzeuge finalen Hash als Hex-String
    return ''.join(f'{value:08x}' for value in h)

def calculate_sha256_file(filepath):
    """Berechnet SHA-256 Hash einer Datei"""
    try:
        with open(filepath, "rb") as f:
            # Lese die gesamte Datei (für sehr große Dateien könnte man das optimieren)
            data = f.read()
        return sha256(data)
    except FileNotFoundError:
        return None
    except PermissionError:
        return None

def calculate_sha256_string(text):
    """Berechnet SHA-256 Hash eines Strings"""
    return sha256(text.encode('utf-8'))

def main():
    # Prüfe zuerst ob stdin verfügbar ist (Pipe oder Redirect)
    stdin_is_pipe = False
    try:
        stdin_is_pipe = not sys.stdin.isatty()
    except:
        pass

    if len(sys.argv) == 1 and stdin_is_pipe:
        # Stdin-Modus ohne Argumente
        data = sys.stdin.buffer.read()
        hash_value = sha256(data)
        print(f"{hash_value}  -")
        return

    if len(sys.argv) < 2:
        print("SHA-256 Hash Tool (Pure Python Implementation)")
        print("=" * 50)
        print("\nVerwendung:")
        print("  Dateien:  python sha256sum.py datei1.txt datei2.txt")
        print("  Text:     python sha256sum.py -s 'Dein Text hier'")
        print("  Stdin:    echo 'Text' | python sha256sum.py")
        print("           oder: python sha256sum.py -")
        print("\nOptionen:")
        print("  -s, --string   Hash von Text berechnen")
        print("  -c, --check    Hash-Datei überprüfen")
        print("  -d, --demo     Zeige Demo mit Erklärungen")
        print("  -            Lese von stdin")
        sys.exit(1)

    # Demo-Modus
    if sys.argv[1] in ['-d', '--demo']:
        print("=== SHA-256 Demo ===\n")
        test_text = "Hallo Welt"
        print(f"Text: '{test_text}'")
        print(f"Bytes: {test_text.encode('utf-8')}")
        hash_result = calculate_sha256_string(test_text)
        print(f"SHA-256: {hash_result}\n")

        print("Der Algorithmus:")
        print("1. Teilt die Nachricht in 512-Bit Blöcke")
        print("2. Fügt Padding hinzu (0x80 + Nullen + Länge)")
        print("3. Verarbeitet jeden Block mit 64 Runden")
        print("4. Verwendet bitweise Operationen (XOR, AND, Rotation)")
        print("5. Kombiniert das Ergebnis zum finalen Hash")
        return

    # Expliziter Stdin-Modus mit "-"
    if sys.argv[1] == '-':
        data = sys.stdin.buffer.read()
        hash_value = sha256(data)
        print(f"{hash_value}  -")
        return

    # String-Modus
    if sys.argv[1] in ['-s', '--string']:
        if len(sys.argv) < 3:
            print("Fehler: Kein Text angegeben")
            sys.exit(1)
        text = ' '.join(sys.argv[2:])
        hash_value = calculate_sha256_string(text)
        print(f"{hash_value}  '{text}'")
        return

    # Check-Modus
    if sys.argv[1] in ['-c', '--check']:
        if len(sys.argv) < 3:
            print("Fehler: Keine Hash-Datei angegeben")
            sys.exit(1)

        check_file = sys.argv[2]
        if not os.path.exists(check_file):
            print(f"Fehler: Datei '{check_file}' nicht gefunden")
            sys.exit(1)

        with open(check_file, 'r') as f:
            all_ok = True
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue

                expected_hash, filepath = parts
                actual_hash = calculate_sha256_file(filepath)

                if actual_hash is None:
                    print(f"{filepath}: FEHLER (Datei nicht lesbar)")
                    all_ok = False
                elif actual_hash == expected_hash:
                    print(f"{filepath}: OK")
                else:
                    print(f"{filepath}: FEHLGESCHLAGEN")
                    all_ok = False

        sys.exit(0 if all_ok else 1)

    # Datei-Modus (Standard)
    for filepath in sys.argv[1:]:
        if not os.path.exists(filepath):
            print(f"Fehler: Datei '{filepath}' nicht gefunden", file=sys.stderr)
            continue

        if os.path.isdir(filepath):
            print(f"Fehler: '{filepath}' ist ein Verzeichnis", file=sys.stderr)
            continue

        hash_value = calculate_sha256_file(filepath)
        if hash_value:
            print(f"{hash_value}  {filepath}")
        else:
            print(f"Fehler: Konnte '{filepath}' nicht lesen", file=sys.stderr)

if __name__ == "__main__":
    main()
