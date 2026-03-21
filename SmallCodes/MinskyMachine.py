class MinskyMachine:
    def __init__(self, program, registers):
        self.program = program
        self.registers = registers
        self.pc = 0

    def run(self, verbose=True):
        while True:
            if self.pc >= len(self.program):
                break

            instr = self.program[self.pc]
            op = instr[0]

            if verbose:
                print(f"[{self.pc:2}] {str(instr):<35} | {self.registers}")

            if op == "INC":
                _, reg = instr
                self.registers[reg] += 1
                self.pc += 1

            elif op == "DEC":
                _, reg, goto = instr
                if self.registers[reg] > 0:
                    self.registers[reg] -= 1
                    self.pc += 1
                else:
                    self.pc = goto

            elif op == "GOTO":
                _, goto = instr
                self.pc = goto

            elif op == "HALT":
                if verbose:
                    print(f"[HALT] Ergebnis: {self.registers}")
                break

        return self.registers


# --- Programm 1: A + B (Ergebnis in B) ---
#
# Idee: dekrementiere A, inkrementiere B, bis A = 0
#
# 0: DEC A → falls A=0, springe zu 3
# 1: INC B
# 2: GOTO 0
# 3: HALT

def add(a, b):
    program = [
        ("DEC", "A", 3),
        ("INC", "B"),
        ("GOTO", 0),
        ("HALT",),
    ]
    m = MinskyMachine(program, {"A": a, "B": b})
    result = m.run()
    return result["B"]


# --- Programm 2: A nach B kopieren (A bleibt erhalten) ---
#
# Idee: verschiebe A nach B und C gleichzeitig,
#       dann verschiebe C zurück nach A
#
# 0: DEC A → falls A=0, springe zu 4
# 1: INC B
# 2: INC C
# 3: GOTO 0
# 4: DEC C → falls C=0, springe zu 7
# 5: INC A
# 6: GOTO 4
# 7: HALT

def copy_a_to_b(a):
    program = [
        ("DEC", "A", 4),
        ("INC", "B"),
        ("INC", "C"),
        ("GOTO", 0),
        ("DEC", "C", 7),
        ("INC", "A"),
        ("GOTO", 4),
        ("HALT",),
    ]
    m = MinskyMachine(program, {"A": a, "B": 0, "C": 0})
    result = m.run()
    return result


# --- Programm 3: A * B (Ergebnis in C) ---
#
# Idee: für jedes Element in A, addiere B zu C
#       dabei wird B mit Hilfszähler D wiederhergestellt
#
# 0:  DEC A  → falls A=0, springe zu 9   (äußere Schleife)
# 1:  DEC B  → falls B=0, springe zu 5   (innere Schleife: B nach C und D)
# 2:  INC C
# 3:  INC D
# 4:  GOTO 1
# 5:  DEC D  → falls D=0, springe zu 0   (D zurück nach B)
# 6:  INC B
# 7:  GOTO 5
# 8:  GOTO 0
# 9:  HALT

def multiply(a, b):
    program = [
        ("DEC", "A", 9),
        ("DEC", "B", 5),
        ("INC", "C"),
        ("INC", "D"),
        ("GOTO", 1),
        ("DEC", "D", 0),
        ("INC", "B"),
        ("GOTO", 5),
        ("GOTO", 0),
        ("HALT",),
    ]
    m = MinskyMachine(program, {"A": a, "B": b, "C": 0, "D": 0})
    result = m.run(verbose=True)
    return result["C"]


if __name__ == "__main__":
    print("=" * 50)
    print("Programm 1: Addition  3 + 4")
    print("=" * 50)
    result = add(3, 4)
    print(f"\n3 + 4 = {result}\n")

    print("=" * 50)
    print("Programm 2: Kopieren  A=5 nach B")
    print("=" * 50)
    result = copy_a_to_b(5)
    print(f"\nErgebnis: {result}\n")

    print("=" * 50)
    print("Programm 3: Multiplikation  3 * 4")
    print("=" * 50)
    result = multiply(3, 4)
    print(f"\n3 * 4 = {result}\n")
