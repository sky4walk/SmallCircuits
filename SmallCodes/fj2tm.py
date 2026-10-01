#!/usr/bin/env python3
"""
fj2tm.py – erzeugt aus einem FlipJump-Speicherabbild eine Turingmaschine im
.tm-Format des Turing Machine Simulators
(https://sky4walk.github.io/SmallCircuits/SmallHtml/turing_machine_simulator.html).

Die erzeugte Maschine ist ein vollständiger FlipJump-Interpreter nach Tom Herman:
Befehl F;J aus 2w Bit, Bit F flippen, nach J springen, Ausgabe über 2w / 2w+1,
Eingabe über 3w+#w, Ende bei Selbstschleife.

Aufruf:
    python3 fj2tm.py programm.bits -w 16 -o programm.tm
    python3 fj2tm.py programm.bits -w 16 -i "Hallo" -o echo.tm
    python3 fj2tm.py programm.bits -w 16 --run        # gleich hier ausführen

programm.bits ist der Bitstring, den der FlipJump-Simulator exportiert.
"""

import argparse
import sys

# ---------------------------------------------------------------------------
# Alphabet
# ---------------------------------------------------------------------------
BLANK = '_'
LEND = '⊢'
FLAG0, FLAG1 = '☐', '☒'          # Merker: Befehl hat sich selbst geflippt
EMPTY = '·'                      # leere Registerstelle
HEX = [chr(0xFF10 + i) for i in range(10)] + [chr(0xFF41 + i) for i in range(6)]  # ０-９ ａ-ｆ
MSTART, MSTART_H = '[', '⟦'      # Speicheranfang, mit Suchmarke
MEND = ']'
SEP = ['', '.', ':', '|', '¦', '‖', '§', '¶']          # Trenner Stufe 1..7
SEPH = ['', '∙', '⁚', '┃', '╎', '╏', '⸗', '⁋']        # dieselben mit Suchmarke
IN_L, IN_R = '{', '}'
IN0, IN1, INX = '◇', '◆', '◦'    # Eingabebits, verbraucht
OUT_L = '»'
PB0, PB1 = '○', '●'              # Ausgabebits, noch nicht zu Zeichen gepackt

# Speicherzellen: Art x Bit x Markierung
KINDS = ['N', 'L', 'O0', 'O1', 'I']   # normal, unter 2w, Ausgabe 0, Ausgabe 1, Eingabebit
MARKS = ['-', 'o', 'P', 'Po', 'N']    # keine, im Befehl, IP, IP+im Befehl, neue IP


def build_cells():
    cs = {('N', 0, '-'): '0', ('N', 1, '-'): '1'}
    pairs = [('N', 'o', 'o'), ('N', 'P', 'p'), ('N', 'Po', 'q'), ('N', 'N', 'n'),
             ('L', '-', 'l'), ('L', 'o', 'm'), ('L', 'P', 'k'), ('L', 'Po', 'j'), ('L', 'N', 'h'),
             ('O0', '-', 'a'), ('O0', 'o', 'b'), ('O0', 'P', 'c'), ('O0', 'Po', 'd'), ('O0', 'N', 'e'),
             ('O1', '-', 'f'), ('O1', 'o', 'g'), ('O1', 'P', 'r'), ('O1', 'Po', 's'), ('O1', 'N', 't'),
             ('I', '-', 'u'), ('I', 'o', 'v'), ('I', 'P', 'w'), ('I', 'Po', 'x'), ('I', 'N', 'y')]
    for k, m, ch in pairs:
        cs[(k, 0, m)] = ch
        cs[(k, 1, m)] = ch.upper()
    assert len(set(cs.values())) == len(cs) == 50
    return cs


CELL = build_cells()
DECODE = {v: k for k, v in CELL.items()}


def cells(marks, kinds=KINDS):
    return [CELL[(k, b, m)] for k in kinds for b in (0, 1) for m in marks]


def outchar(v):
    special = {32: '␣', 95: '＿', 40: '❨', 41: '❩', 44: '‚', 10: '↵', 91: '⁅', 93: '⁆'}
    if v in special:
        return special[v]
    if 33 <= v <= 126:
        return chr(v)
    return '¤'


OUTCHARS = sorted(set(outchar(v) for v in range(256)))


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------
class Gen:
    def __init__(self, w):
        assert w % 4 == 0 and w >= 8, "w muss ein Vielfaches von 4 und mindestens 8 sein"
        self.w, self.dw, self.C = w, 2 * w, w // 4
        self.L = self.C - 1                     # Trennerstufen 1..L
        assert self.L < len(SEP)
        self.T = {}
        self.SEPS = [SEP[l] for l in range(1, self.L + 1)]
        self.SEPHS = [SEPH[l] for l in range(1, self.L + 1)]
        self.REG = [FLAG0, FLAG1, EMPTY] + HEX
        self.INSYM = [IN_L, IN_R, IN0, IN1, INX]
        self.OUTSYM = [OUT_L, PB0, PB1] + OUTCHARS
        self.build()

    # --- Hilfen ---
    def tr(self, q, s, q2, s2=None, d='N'):
        key = (q, s)
        val = (q2, s if s2 is None else s2, d)
        if key in self.T:
            if self.T[key] == val:
                return
            raise ValueError(f'widersprüchlicher Übergang {key}: {self.T[key]} / {val}')
        self.T[key] = val

    def skip(self, q, syms, d):
        for s in syms:
            self.tr(q, s, q, s, d)

    def build(self):
        w, dw, C, L = self.w, self.dw, self.C, self.L
        OP = ['-', 'o', 'Po']           # Marken zwischen Markieren und Löschen
        PJ = ['-', 'P']                 # Marken außerhalb davon
        SEPS, SEPHS = self.SEPS, self.SEPHS

        # ================= SCAN: Befehlszellen markieren =================
        q = 'scan'
        self.skip(q, [LEND] + self.REG + [MSTART] + SEPS + cells(['-']), 'R')
        for k in KINDS:
            for b in (0, 1):
                self.tr(q, CELL[(k, b, 'P')], f'sc1{"i" if k == "I" else ""}', CELL[(k, b, 'Po')], 'R')
        for c in range(1, dw):
            for ni in (False, True):
                q = f'sc{c}{"i" if ni else ""}'
                self.skip(q, SEPS, 'R')
                self.tr(q, MEND, 'FEHLER_SPEICHER')
                for k in KINDS:
                    for b in (0, 1):
                        ni2 = ni or k == 'I'
                        if c + 1 == dw:
                            nxt, d = ('in_go' if ni2 else 'cpR_F0'), ('R' if ni2 else 'L')
                            if not ni2:
                                nxt = 'toip_F0'
                        else:
                            nxt, d = f'sc{c + 1}{"i" if ni2 else ""}', 'R'
                        self.tr(q, CELL[(k, b, '-')], nxt, CELL[(k, b, 'o')], d)

        # zurück nach links zur IP (Lesen von F beginnt dort)
        q = 'toip_F0'
        self.skip(q, cells(['o']) + SEPS, 'L')
        for k in KINDS:
            for b in (0, 1):
                self.tr(q, CELL[(k, b, 'Po')], 'cpR_F0', None, 'N')

        # ================= EINGABE =================
        q = 'in_go'
        self.skip(q, cells(OP) + SEPS + [MEND], 'R')
        self.tr(q, IN_L, 'in_find', None, 'R')
        q = 'in_find'
        self.skip(q, [INX], 'R')
        self.tr(q, IN_R, 'fin_EOF', None, 'R')
        self.tr(q, IN0, 'in_back0', INX, 'L')
        self.tr(q, IN1, 'in_back1', INX, 'L')
        for bit in (0, 1):
            q = f'in_back{bit}'
            self.skip(q, [INX, IN_L, MEND] + SEPS + cells(['-', 'o']), 'L')
            for k in KINDS:
                for b in (0, 1):
                    if k == 'I':
                        self.tr(q, CELL[(k, b, 'Po')], 'cpR_F0', CELL[(k, bit, 'Po')], 'N')
                    else:
                        self.tr(q, CELL[(k, b, 'Po')], f'in_fwd{bit}', None, 'R')
            q = f'in_fwd{bit}'
            self.skip(q, SEPS + cells(['o'], ['N', 'L', 'O0', 'O1']), 'R')
            for b in (0, 1):
                self.tr(q, CELL[('I', b, 'o')], 'toip_F0', CELL[('I', bit, 'o')], 'L')

        # ================= WORT KOPIEREN (F oder J) =================
        for word, base in (('F', 0), ('J', w)):
            for k in range(C):
                s0 = base + 4 * k
                # nach links bis zum Speicheranfang (nur J0 braucht das, aus Speicher oder Ausgabe)
                if word == 'J' and k == 0:
                    q = 'cpL_J0'
                    self.skip(q, cells(OP) + SEPS + [MEND] + self.INSYM + self.OUTSYM, 'L')
                    self.tr(q, MSTART, 'cpR_J0', None, 'N')
                # nach rechts bis zur IP
                q = f'cpR_{word}{k}'
                self.skip(q, self.REG + [MSTART] + SEPS + cells(['-', 'o']), 'R')
                for kk in KINDS:
                    for b in (0, 1):
                        if s0 == 0:
                            self.tr(q, CELL[(kk, b, 'Po')], f'rd_{word}{k}_1_{b}', None, 'R')
                        else:
                            self.tr(q, CELL[(kk, b, 'Po')], f'sk_{word}{k}_{s0 - 1}', None, 'R')
                # Zellen überspringen
                for r in range(s0):
                    q = f'sk_{word}{k}_{r}'
                    self.skip(q, SEPS, 'R')
                    for kk in KINDS:
                        for b in (0, 1):
                            s = CELL[(kk, b, 'o')]
                            if r == 0:
                                self.tr(q, s, f'rd_{word}{k}_1_{b}', None, 'R')
                            else:
                                self.tr(q, s, f'sk_{word}{k}_{r - 1}', None, 'R')
                # 4 Bit lesen
                for j in range(1, 4):
                    for v in range(1 << j):
                        q = f'rd_{word}{k}_{j}_{v}'
                        self.skip(q, SEPS, 'R')
                        for kk in KINDS:
                            for b in (0, 1):
                                v2 = v | (b << j)
                                nxt = f'bk_{word}{k}_{v2}' if j == 3 else f'rd_{word}{k}_{j + 1}_{v2}'
                                self.tr(q, CELL[(kk, b, 'o')], nxt, None, 'L' if j == 3 else 'R')
                # zurück ins Register, erste freie Stelle von links
                for v in range(16):
                    q = f'bk_{word}{k}_{v}'
                    self.skip(q, cells(OP) + SEPS + [MSTART, EMPTY], 'L')
                    for s in HEX + [FLAG0, FLAG1]:
                        self.tr(q, s, f'wr_{word}{k}_{v}', None, 'R')
                    q = f'wr_{word}{k}_{v}'
                    if k + 1 < C:
                        nxt, d = f'cpR_{word}{k + 1}', 'R'
                    elif word == 'F':
                        nxt, d = f'st_F{L}', 'R'
                    else:
                        nxt, d = 'clr_go', 'R'
                    self.tr(q, EMPTY, nxt, HEX[v], d)

        # ================= MARKIERUNGEN LÖSCHEN (nach dem Kopieren von J) =================
        q = 'clr_go'
        self.skip(q, HEX + [MSTART] + SEPS + cells(['-', 'o']), 'R')
        for k in KINDS:
            for b in (0, 1):
                self.tr(q, CELL[(k, b, 'Po')], 'clr1', CELL[(k, b, 'P')], 'R')
        for c in range(1, dw):
            q = f'clr{c}'
            self.skip(q, SEPS, 'R')
            for k in KINDS:
                for b in (0, 1):
                    if c + 1 == dw:
                        self.tr(q, CELL[(k, b, 'o')], f'st_J{L}', CELL[(k, b, '-')], 'L')
                    else:
                        self.tr(q, CELL[(k, b, 'o')], f'clr{c + 1}', CELL[(k, b, '-')], 'R')

        # ================= ADRESSE SUCHEN =================
        for X, MS in (('F', OP), ('J', PJ)):
            mem = cells(MS)
            # st: Ziffer holen (von rechts), Stufe j
            for j in range(L, -1, -1):
                q = f'st_{X}{j}'
                self.skip(q, mem + SEPS + SEPHS + [MSTART, MSTART_H, EMPTY], 'L')
                for d in range(16):
                    self.tr(q, HEX[d], f'sg_{X}{j}_{d}', EMPTY, 'R')
                # sg: zum Startpunkt laufen
                for c in range(16):
                    q = f'sg_{X}{j}_{c}'
                    if j == L:
                        self.skip(q, [EMPTY] + mem + SEPS, 'R')
                        if c == 0:
                            self.tr(q, MSTART, f'st_{X}{j - 1}', MSTART_H, 'L')
                        else:
                            self.tr(q, MSTART, f'sc_{X}{j}_{c}', None, 'R')
                    else:
                        self.skip(q, [EMPTY, MSTART] + mem + SEPS, 'R')
                        marks = [(MSTART_H, MSTART)] + [(SEPH[l], SEP[l]) for l in range(1, L + 1)]
                        for hm, um in marks:
                            if j == 0:
                                self.tr(q, hm, f'sx_{X}{c}', um, 'R')
                            elif c == 0:
                                self.tr(q, hm, f'st_{X}{j - 1}', hm, 'L')
                            else:
                                self.tr(q, hm, f'sc_{X}{j}_{c}', um, 'R')
                # sc: Trenner der Stufe >= j abzählen
                if j >= 1:
                    for c in range(1, 16):
                        q = f'sc_{X}{j}_{c}'
                        self.skip(q, mem + [SEP[l] for l in range(1, j)], 'R')
                        self.tr(q, MEND, 'FEHLER_SPEICHER')
                        for l in range(j, L + 1):
                            if c == 1:
                                self.tr(q, SEP[l], f'st_{X}{j - 1}', SEPH[l], 'L')
                            else:
                                self.tr(q, SEP[l], f'sc_{X}{j}_{c - 1}', None, 'R')
            # sx: Zellen abzählen
            for c in range(16):
                q = f'sx_{X}{c}'
                self.tr(q, MEND, 'FEHLER_SPEICHER')
                for k in KINDS:
                    for b in (0, 1):
                        for m in MS:
                            s = CELL[(k, b, m)]
                            if c > 0:
                                self.tr(q, s, f'sx_{X}{c - 1}', None, 'R')
                            elif X == 'F':
                                self.flip_action(q, k, b, m)
                            else:
                                self.jump_action(q, k, b, m)

        # ================= NACH DEM FLIP: Merker, Ausgabe =================
        for out in ('', '0', '1'):
            q = f'fl_flag{out}'
            self.skip(q, cells(OP) + SEPS + [MSTART, EMPTY], 'L')
            self.tr(q, FLAG0, f'out_go{out}' if out else 'cpR_J0', FLAG1, 'R')
        for out in ('0', '1'):
            q = f'out_go{out}'
            self.skip(q, [FLAG1, EMPTY, MSTART] + cells(OP) + SEPS + [MEND] + self.INSYM, 'R')
            self.tr(q, OUT_L, f'out_find{out}', None, 'R')
            q = f'out_find{out}'
            self.skip(q, [PB0, PB1] + OUTCHARS, 'R')
            self.tr(q, BLANK, 'oc1', PB0 if out == '0' else PB1, 'L')
        # anstehende Bits zählen
        for c in range(1, 8):
            q = f'oc{c}'
            for s in [OUT_L] + OUTCHARS:
                self.tr(q, s, 'cpL_J0', None, 'N')
            for s in (PB0, PB1):
                if c + 1 == 8:
                    self.tr(q, s, 'pr6', None, 'R')
                else:
                    self.tr(q, s, f'oc{c + 1}', None, 'L')
        for n in range(7):
            q = f'pr{n}'
            for s in (PB0, PB1):
                self.tr(q, s, 'pa_0_0' if n == 0 else f'pr{n - 1}', None, 'N' if n == 0 else 'R')
        # von rechts nach links einsammeln (höchstwertiges Bit zuerst)
        for k in range(8):
            for v in range(1 << k):
                q = f'pa_{k}_{v}'
                for b, s in ((0, PB0), (1, PB1)):
                    v2 = v * 2 + b
                    if k == 7:
                        self.tr(q, s, 'cpL_J0', outchar(v2), 'N')
                    else:
                        self.tr(q, s, f'pa_{k + 1}_{v2}', BLANK, 'L')

        # ================= IP VERSETZEN =================
        q = 'jj_flag'
        self.skip(q, cells(PJ) + SEPS + [MSTART, EMPTY], 'L')
        self.tr(q, FLAG0, 'fin_HALT', None, 'R')
        self.tr(q, FLAG1, 'scan', FLAG0, 'R')
        q = 'mv_left'
        self.skip(q, cells(['-', 'P', 'N']) + SEPS + [MSTART, EMPTY], 'L')
        self.tr(q, FLAG0, 'mv_clr', FLAG0, 'R')
        self.tr(q, FLAG1, 'mv_clr', FLAG0, 'R')
        q = 'mv_clr'
        self.skip(q, [EMPTY, MSTART] + SEPS + cells(['-', 'N']), 'R')
        for k in KINDS:
            for b in (0, 1):
                self.tr(q, CELL[(k, b, 'P')], 'mv_back', CELL[(k, b, '-')], 'L')
        q = 'mv_back'
        self.skip(q, SEPS + cells(['-', 'N']), 'L')
        self.tr(q, MSTART, 'mv_set', None, 'R')
        q = 'mv_set'
        self.skip(q, SEPS + cells(['-']), 'R')
        for k in KINDS:
            for b in (0, 1):
                self.tr(q, CELL[(k, b, 'N')], 'scan', CELL[(k, b, 'P')], 'N')

        # ================= ENDE: Kopf zur Ausgabe, damit sie im Bild steht =================
        anywhere = ([LEND] + self.REG + [MSTART, MSTART_H, MEND] + SEPS + SEPHS +
                    cells(MARKS) + self.INSYM)
        for fin in ('HALT', 'EOF'):
            q = f'fin_{fin}'
            self.skip(q, anywhere, 'R')
            self.tr(q, OUT_L, f'fin_{fin}_1', None, 'R')
            for n in range(1, 10):
                q = f'fin_{fin}_{n}'
                for s in [PB0, PB1, BLANK] + OUTCHARS:
                    self.tr(q, s, fin if n == 9 else f'fin_{fin}_{n + 1}', None, 'N' if n == 9 else 'R')

    def flip_action(self, q, k, b, m):
        s2 = CELL[(k, 1 - b, m)]
        out = '0' if k == 'O0' else '1' if k == 'O1' else ''
        if m in ('o', 'Po'):
            self.tr(q, CELL[(k, b, m)], f'fl_flag{out}', s2, 'L')
        elif out:
            self.tr(q, CELL[(k, b, m)], f'out_go{out}', s2, 'R')
        else:
            self.tr(q, CELL[(k, b, m)], 'cpL_J0', s2, 'N')

    def jump_action(self, q, k, b, m):
        s = CELL[(k, b, m)]
        if m == 'P':
            self.tr(q, s, 'jj_flag', None, 'L')
        elif k == 'L':
            self.tr(q, s, 'FEHLER_SPRUNG')
        else:
            self.tr(q, s, 'mv_left', CELL[(k, b, 'N')], 'L')

    # --- Band ---
    def tape(self, bits, inp):
        w, dw = self.w, self.dw
        in_addr = 3 * w + w.bit_length()
        t = [LEND, FLAG0] + [EMPTY] * self.C + [MSTART]
        for i, ch in enumerate(bits):
            if i and i % 16 == 0:
                lvl, x = 0, i
                while x % 16 == 0 and lvl < self.L:
                    lvl += 1
                    x //= 16
                t.append(SEP[lvl])
            kind = 'L' if i < dw else 'O0' if i == dw else 'O1' if i == dw + 1 else 'I' if i == in_addr else 'N'
            t.append(CELL[(kind, int(ch), 'P' if i == 0 else '-')])
        t.append(MEND)
        t.append(IN_L)
        t += [IN1 if (byte >> i) & 1 else IN0 for byte in inp for i in range(8)]
        t.append(IN_R)
        t.append(OUT_L)
        return ''.join(t)

    def to_tm(self, bits, inp, comment):
        lines = [f'# {comment}',
                 f'# FlipJump-Interpreter als Turingmaschine, w = {self.w}, erzeugt von fj2tm.py',
                 '# Band: ⊢ Merker Register [ Speicher ] { Eingabebits } » Ausgabe',
                 '# Zellen: 0/1 Bit, o/O im Befehl, p/P IP, q/Q IP im Befehl, n/N neue IP;',
                 '#   l..h unter 2w, a..e Ausgabe-0-Zelle, f..t Ausgabe-1-Zelle, u..y Eingabezelle (klein = 0, groß = 1)',
                 '# Trenner . : | markieren 16er-, 256er-, 4096er-Grenzen; ○● Ausgabebits, ◇◆ Eingabebits',
                 '# Halt-Zustände: HALT (Selbstschleife), EOF, FEHLER_SPEICHER, FEHLER_SPRUNG',
                 '',
                 '(scan,0)', '',
                 f'({self.tape(bits, inp)})', '']
        groups = {}
        for (q, s), (q2, s2, d) in self.T.items():
            groups.setdefault(q, []).append(f'({q},{s},{q2},{s2},{d})')
        for q in groups:
            lines.append(' '.join(groups[q]))
        return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------------------
# kleiner TM-Interpreter zum Testen
# ---------------------------------------------------------------------------
def run_tm(T, tape, state='scan', head=0, max_steps=10**9):
    tape = list(tape)
    steps = 0
    get = T.get
    while steps < max_steps:
        if head >= len(tape):
            tape.extend(BLANK * 1024)
        tr = get((state, tape[head]))
        if tr is None:
            break
        state, tape[head], d = tr
        head += 1 if d == 'R' else -1 if d == 'L' else 0
        steps += 1
    return state, ''.join(tape).rstrip(BLANK), steps


def decode_tape(tape):
    """Speicherbits und Ausgabe aus dem Band lesen"""
    mem = tape[tape.index(MSTART_H if MSTART_H in tape else MSTART) + 1: tape.index(MEND)]
    bits = ''.join(str(DECODE[c][1]) for c in mem if c in DECODE)
    out = tape[tape.index(OUT_L) + 1:]
    return bits, out


def main():
    ap = argparse.ArgumentParser(description='FlipJump-Speicherabbild -> Turingmaschine (.tm)')
    ap.add_argument('datei', help='Bitstring-Datei (Export aus dem FlipJump-Simulator)')
    ap.add_argument('-w', type=int, default=16, help='Wortbreite (Standard 16)')
    ap.add_argument('-i', '--input', default='', help='Eingabetext')
    ap.add_argument('-o', '--out', help='.tm-Datei schreiben')
    ap.add_argument('-c', '--comment', default='FlipJump auf der Turingmaschine', help='Kommentarzeile')
    ap.add_argument('--run', action='store_true', help='Maschine hier ausführen')
    args = ap.parse_args()

    with open(args.datei, encoding='ascii') as fh:
        bits = ''.join(fh.read().split())
    g = Gen(args.w)
    inp = args.input.encode('utf-8')
    states = {q for q, _ in g.T} | {q2 for q2, _, _ in g.T.values()}
    print(f'{len(g.T)} Übergänge, {len(states)} Zustände, Band {len(g.tape(bits, inp))} Zellen', file=sys.stderr)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as fh:
            fh.write(g.to_tm(bits, inp, args.comment))
    if args.run:
        state, tape, steps = run_tm(g.T, g.tape(bits, inp))
        mem, out = decode_tape(tape)
        print(f'Halt in Zustand {state} nach {steps:,} Schritten'.replace(',', '.'))
        print(f'Ausgabe auf dem Band: {out}')


if __name__ == '__main__':
    main()
