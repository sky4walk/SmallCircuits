#!/usr/bin/env python3
"""
FlipJump-Interpreter nach der Spezifikation von Tom Herman (github.com/tomhea/flipjump).

Ein Befehl "F;J" belegt 2*w Bit: erst das Wort F, dann das Wort J (je w Bit,
niedrigstes Bit zuerst). Die CPU startet bei Adresse 0, flippt Bit F und springt
nach J. Gleiche Semantik wie der FlipJump-Simulator auf
https://sky4walk.github.io/SmallCircuits/SmallHtml/flipjump_simulator.html

Aufruf:
    python3 flipjump.py                         # eingebaute Beispiele
    python3 flipjump.py programm.bits -w 16     # Bitstring aus dem Simulator
    python3 flipjump.py programm.bits -w 16 -i "Hallo" --trace
"""

import argparse
import sys


class FlipJump:
    def __init__(self, w=16, size_bits=None):
        if w not in (8, 16, 32, 64):
            raise ValueError("w muss 8, 16, 32 oder 64 sein")
        self.w = w
        self.dw = 2 * w
        self.size = size_bits if size_bits is not None else 256 * self.dw
        self.mem = bytearray((self.size + 7) // 8)
        self.in_addr = 3 * w + w.bit_length()   # Eingabebit: 3w + #w

    # ---------- Bits und Wörter ----------
    def get_bit(self, a):
        return (self.mem[a // 8] >> (a % 8)) & 1

    def set_bit(self, a, v):
        if v:
            self.mem[a // 8] |= 1 << (a % 8)
        else:
            self.mem[a // 8] &= ~(1 << (a % 8)) & 0xFF

    def flip_bit(self, a):
        self.mem[a // 8] ^= 1 << (a % 8)

    def read_word(self, a):
        """w Bit ab Adresse a, niedrigstes Bit zuerst"""
        v = 0
        for i in range(self.w):
            v |= self.get_bit(a + i) << i
        return v

    def write_word(self, a, value):
        for i in range(self.w):
            self.set_bit(a + i, (value >> i) & 1)

    def op(self, addr, f, j):
        """Befehl F;J an Adresse addr schreiben"""
        self.write_word(addr, f)
        self.write_word(addr + self.w, j)

    # ---------- Laden / Speichern ----------
    @classmethod
    def from_bitstring(cls, bits, w):
        bits = "".join(bits.split())
        if set(bits) - {"0", "1"}:
            raise ValueError("Bitstring darf nur 0 und 1 enthalten")
        m = cls(w, len(bits))
        for a, c in enumerate(bits):
            if c == "1":
                m.set_bit(a, 1)
        return m

    def to_bitstring(self):
        return "".join(str(self.get_bit(a)) for a in range(self.size))

    # ---------- Ausführung ----------
    def run(self, input_bytes=b"", max_ops=10_000_000, trace=False):
        """
        Führt das Programm ab Adresse 0 aus.
        Rückgabe: (Grund, Ausgabe als bytes, Anzahl Befehle)
        Grund ist 'Ende' (Selbstschleife), 'EOF', 'Sprungfehler',
        'Speicherfehler' oder 'Limit'.
        """
        w, dw = self.w, self.dw
        in_bits = [(b >> i) & 1 for b in input_bytes for i in range(8)]
        in_pos = 0
        out_bits = []
        ip = 0
        ops = 0
        cause = "Limit"

        while ops < max_ops:
            if ip + dw > self.size:
                cause = "Speicherfehler"
                break
            f = self.read_word(ip)                 # 1. Flip-Wort lesen
            if f == dw or f == dw + 1:             # 2. Ausgabe: Flip auf 2w / 2w+1
                out_bits.append(f - dw)
            if ip <= self.in_addr < ip + dw:       # 3. Eingabebit nachladen
                if in_pos >= len(in_bits):
                    cause = "EOF"
                    break
                self.set_bit(self.in_addr, in_bits[in_pos])
                in_pos += 1
            if f >= self.size:
                cause = "Speicherfehler"
                break
            self.flip_bit(f)                       # 4. FLIP
            j = self.read_word(ip + w)             # 5. Sprungwort erst NACH dem Flip lesen
            ops += 1
            if trace:
                print(f"{ip:7}:  flip {f:<7} -> {j}")
            if j == ip and not (ip <= f < ip + dw):
                cause = "Ende"                     # Selbstschleife = reguläres Ende
                break
            if j < dw:
                cause = "Sprungfehler"
                break
            ip = j                                 # 6. JUMP

        out = bytearray()
        for k in range(0, len(out_bits) - 7, 8):
            out.append(sum(out_bits[k + i] << i for i in range(8)))
        return cause, bytes(out), ops


# ---------- Beispiele ----------
def beispiel_grundprinzip():
    """Esolang-Wiki-Beispiel, umgerechnet auf w = 16"""
    m = FlipJump(w=16, size_bits=224)
    dw = m.dw
    m.op(0 * dw, 200, 64)   # flippe Bit 200, springe nach 64
    m.op(1 * dw, 8, 111)    # wird nie ausgeführt
    m.op(2 * dw, 32, 64)    # flippe Bit 32 (aus 8;111 wird 9;111), Selbstschleife
    return m


def beispiel_hello(text="Hello, World!", w=16):
    """Hello World ohne Bibliothek: jedes Ausgabebit ist ein Flip auf 2w oder 2w+1"""
    dw = 2 * w
    bits = [(ord(c) >> i) & 1 for c in text for i in range(8)]
    n_ops = 2 + len(bits) + 1
    m = FlipJump(w, n_ops * dw)
    m.op(0, 0, 2 * dw)          # startup: über den IO-Befehl springen
    m.op(dw, 0, 0)              # IO-Befehl bei Adresse 2w (wird nie ausgeführt)
    addr = 2 * dw
    for b in bits:
        m.op(addr, dw + b, addr + dw)   # IO+0 bzw. IO+1 flippen, weiter
        addr += dw
    m.op(addr, 0, addr)         # Selbstschleife = Ende
    return m


def main():
    ap = argparse.ArgumentParser(description="FlipJump-Interpreter (Tom Herman)")
    ap.add_argument("datei", nargs="?", help="Bitstring-Datei (Export aus dem Simulator)")
    ap.add_argument("-w", type=int, default=16, help="Wortbreite (Standard 16)")
    ap.add_argument("-i", "--input", default="", help="Eingabetext")
    ap.add_argument("--max", type=int, default=10_000_000, help="max. Befehle")
    ap.add_argument("--trace", action="store_true", help="jeden Befehl ausgeben")
    args = ap.parse_args()

    if args.datei:
        with open(args.datei, encoding="ascii") as fh:
            m = FlipJump.from_bitstring(fh.read(), args.w)
        cause, out, ops = m.run(args.input.encode("utf-8"), args.max, args.trace)
        sys.stdout.write(out.decode("utf-8", errors="replace"))
        print(f"\n[{cause} nach {ops} Befehlen]")
        return

    m = beispiel_grundprinzip()
    cause, out, ops = m.run(trace=True)
    print(f"Grundprinzip: {cause} nach {ops} Befehlen, "
          f"Befehl bei 32 ist jetzt {m.read_word(32)};{m.read_word(48)}")

    m = beispiel_hello()
    cause, out, ops = m.run()
    print(f"Hello World:  {out.decode()!r}  ({cause} nach {ops} Befehlen)")


if __name__ == "__main__":
    main()
