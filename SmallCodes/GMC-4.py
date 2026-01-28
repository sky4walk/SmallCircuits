#!/usr/bin/env python3
"""
GMC-4 (Gakken Micro Computer 4) Simulator
Authentische Implementierung basierend auf der offiziellen Spezifikation

Speicher-Layout:
- 96 Bytes Programmspeicher (0x00-0x5F)
- 16 Bytes Datenspeicher (0x50-0x5F)
- 16 Bytes Register-Speicher
- Gesamt: 128 Bytes

Register:
- Haupt-Register: A, B, Y, Z (je 4-bit)
- Aux-Register: A', B', Y', Z' (je 4-bit)
- Flag: 1-bit
- Program Counter: 7-bit (0-95 für Programmspeicher)
"""

import sys
import time

class GMC4:
    def __init__(self):
        # 4-Bit Haupt-Register
        self.A = 0  # Akkumulator
        self.B = 0  # Register B
        self.Y = 0  # Register Y (für Memory-Adressierung)
        self.Z = 0  # Register Z

        # 4-Bit Aux-Register
        self.A_prime = 0
        self.B_prime = 0
        self.Y_prime = 0
        self.Z_prime = 0

        # Flag und Steuerung
        self.flag = 1  # Flag-Register (1-bit)
        self.program_counter = 0  # PC (7-bit, 0-95)

        # Speicher (128 Bytes total)
        # 0x00-0x5F: Programmspeicher (96 bytes)
        # 0x50-0x5F: Datenspeicher (16 bytes, überlappend!)
        self.memory = [0xF] * 128  # Initialisiert mit 0xF wie das echte GMC-4

        # 7-Segment Display
        self.display = 0

        # 7x 2-Pin LEDs (0-6)
        self.leds = [False] * 7

        # Sound
        self.sound_active = False

        # Steuerung
        self.running = False
        self.halted = False

        # Tastatur-Puffer für KA Befehl
        self.key_pressed = None

    def reset(self):
        """Soft Reset - setzt PC auf 0, behält Speicher"""
        self.program_counter = 0
        self.flag = 1

    def hard_reset(self):
        """Hard Reset - löscht alles"""
        self.A = 0
        self.B = 0
        self.Y = 0
        self.Z = 0
        self.A_prime = 0
        self.B_prime = 0
        self.Y_prime = 0
        self.Z_prime = 0
        self.flag = 1
        self.program_counter = 0
        self.memory = [0xF] * 128
        self.display = 0
        self.leds = [False] * 7
        self.sound_active = False
        self.running = False
        self.halted = False
        self.key_pressed = None

    def load_program(self, program, start_address=0):
        """Lädt ein Programm in den Speicher"""
        for i, byte in enumerate(program):
            addr = start_address + i
            if addr < 96:  # Nur in Programmspeicher laden
                self.memory[addr] = byte & 0xF

    def get_data_memory_address(self, offset):
        """Berechnet Datenspeicher-Adresse: 0x50 + offset"""
        return 0x50 + (offset & 0xF)

    def fetch(self):
        """Holt den nächsten Befehl"""
        if self.program_counter >= 96:
            self.halted = True
            return 0xF
        instruction = self.memory[self.program_counter]
        self.program_counter += 1
        return instruction

    def execute(self, opcode):
        """Führt einen Befehl aus"""

        # 0: KA - Key to A Register
        if opcode == 0x0:
            if self.key_pressed is not None:
                self.A = self.key_pressed & 0xF
                self.flag = 0
                self.key_pressed = None
            else:
                self.flag = 1

        # 1: AO - A to Output (7-segment display)
        elif opcode == 0x1:
            self.display = self.A
            self.flag = 1

        # 2: CH - Change: A<->B, Y<->Z
        elif opcode == 0x2:
            self.A, self.B = self.B, self.A
            self.Y, self.Z = self.Z, self.Y
            self.flag = 1

        # 3: CY - Change: A<->Y
        elif opcode == 0x3:
            self.A, self.Y = self.Y, self.A
            self.flag = 1

        # 4: AM - A to Memory
        elif opcode == 0x4:
            addr = self.get_data_memory_address(self.Y)
            self.memory[addr] = self.A
            self.flag = 1

        # 5: MA - Memory to A
        elif opcode == 0x5:
            addr = self.get_data_memory_address(self.Y)
            self.A = self.memory[addr]
            self.flag = 1

        # 6: M+ - Memory plus A to A
        elif opcode == 0x6:
            addr = self.get_data_memory_address(self.Y)
            result = self.memory[addr] + self.A
            self.flag = 1 if result > 0xF else 0
            self.A = result & 0xF

        # 7: M- - Memory minus A to A
        elif opcode == 0x7:
            addr = self.get_data_memory_address(self.Y)
            result = self.memory[addr] - self.A
            self.flag = 1 if result < 0 else 0
            self.A = result & 0xF

        # 8: TIA [n] - Transfer Immediate to A
        elif opcode == 0x8:
            immediate = self.fetch()
            self.A = immediate & 0xF
            self.flag = 1

        # 9: AIA [n] - Add Immediate to A
        elif opcode == 0x9:
            immediate = self.fetch()
            result = self.A + immediate
            self.flag = 1 if result > 0xF else 0
            self.A = result & 0xF

        # A: TIY [n] - Transfer Immediate to Y
        elif opcode == 0xA:
            immediate = self.fetch()
            self.Y = immediate & 0xF
            self.flag = 1

        # B: AIY [n] - Add Immediate to Y
        elif opcode == 0xB:
            immediate = self.fetch()
            result = self.Y + immediate
            self.flag = 1 if result > 0xF else 0
            self.Y = result & 0xF

        # C: CIA [n] - Compare Immediate with A
        elif opcode == 0xC:
            immediate = self.fetch()
            if self.A == immediate:
                self.flag = 0
            else:
                self.flag = 1

        # D: CIY [n] - Compare Immediate with Y
        elif opcode == 0xD:
            immediate = self.fetch()
            if self.Y == immediate:
                self.flag = 0
            else:
                self.flag = 1

        # E: Extended Instructions (E0-EF)
        elif opcode == 0xE:
            ext_code = self.fetch()
            self.execute_extended(ext_code)

        # F: JUMP [addr_hi] [addr_lo] - Conditional Jump
        elif opcode == 0xF:
            addr_hi = self.fetch()
            addr_lo = self.fetch()
            target = (addr_hi << 4) | addr_lo

            if self.flag == 1:
                self.program_counter = target & 0x7F
            self.flag = 1

    def execute_extended(self, ext_code):
        """Führt erweiterte Befehle aus (E0-EF)"""

        # E0: CAL RSTO - Clear 7-segment display
        if ext_code == 0x0:
            self.display = 0
            self.flag = 1

        # E1: CAL SETR - Set LED (Y register selects 0-6)
        elif ext_code == 0x1:
            if 0 <= self.Y <= 6:
                self.leds[self.Y] = True
            self.flag = 1

        # E2: CAL RSTR - Reset LED (Y register selects 0-6)
        elif ext_code == 0x2:
            if 0 <= self.Y <= 6:
                self.leds[self.Y] = False
            self.flag = 1

        # E3: Not used
        elif ext_code == 0x3:
            self.flag = 1

        # E4: CAL CMPL - Complement A (invert bits)
        elif ext_code == 0x4:
            self.A = (~self.A) & 0xF
            self.flag = 1

        # E5: CAL CHNG - Change: Swap main and aux registers
        elif ext_code == 0x5:
            self.A, self.A_prime = self.A_prime, self.A
            self.B, self.B_prime = self.B_prime, self.B
            self.Y, self.Y_prime = self.Y_prime, self.Y
            self.Z, self.Z_prime = self.Z_prime, self.Z
            self.flag = 1

        # E6: CAL SIFT - Shift A right 1 bit
        elif ext_code == 0x6:
            # Flag = 1 if bit 0 was 0 (even), else 0
            self.flag = 1 if (self.A & 1) == 0 else 0
            self.A = self.A >> 1

        # E7: CAL ENDS - End sound
        elif ext_code == 0x7:
            print("[SOUND: End]")
            self.flag = 1

        # E8: CAL ERRS - Error sound
        elif ext_code == 0x8:
            print("[SOUND: Error]")
            self.flag = 1

        # E9: CAL SHTS - Short beep
        elif ext_code == 0x9:
            print("[SOUND: Short beep]")
            self.flag = 1

        # EA: CAL LONS - Long beep
        elif ext_code == 0xA:
            print("[SOUND: Long beep]")
            self.flag = 1

        # EB: CAL SUND - Sound based on A (1-E)
        elif ext_code == 0xB:
            print(f"[SOUND: Note {self.A:X}]")
            self.flag = 1

        # EC: CAL TIMR - Timer: (A+1) * 0.1 seconds
        elif ext_code == 0xC:
            delay = (self.A + 1) * 0.1
            if hasattr(self, 'enable_delays') and self.enable_delays:
                time.sleep(delay)
            self.flag = 1

        # ED: CAL DSPR - Display on 2-pin LEDs
        elif ext_code == 0xD:
            # Upper 3 bits from 0x5F, lower 4 from 0x5E
            upper = self.memory[0x5F] & 0x7
            lower = self.memory[0x5E] & 0xF
            pattern = (upper << 4) | lower
            for i in range(7):
                self.leds[i] = bool(pattern & (1 << i))
            self.flag = 1

        # EE: CAL DEM- - Decimal subtract, decrement Y
        elif ext_code == 0xE:
            addr = self.get_data_memory_address(self.Y)
            result = self.memory[addr] - self.A
            self.memory[addr] = result & 0xF
            self.Y = (self.Y - 1) & 0xF
            self.flag = 1

        # EF: CAL DEM+ - Decimal add, decrement Y
        elif ext_code == 0xF:
            addr = self.get_data_memory_address(self.Y)
            result = self.memory[addr] + self.A
            if result > 0xF:
                # Overflow handling
                self.memory[addr] = result & 0xF
            else:
                self.memory[addr] = result
            self.Y = (self.Y - 1) & 0xF
            self.flag = 1

    def step(self):
        """Führt einen Befehlszyklus aus"""
        if self.halted:
            return False
        opcode = self.fetch()
        self.execute(opcode)
        return True

    def run(self, max_steps=100000):
        """Führt das Programm aus"""
        self.running = True
        self.halted = False
        steps = 0

        while self.running and not self.halted and steps < max_steps:
            if not self.step():
                break
            steps += 1

        return steps

    def print_state(self):
        """Gibt den aktuellen Zustand aus"""
        print(f"\n{'='*70}")
        print(f"GMC-4 State")
        print(f"{'='*70}")
        print(f"Main Registers:     A={self.A:X}  B={self.B:X}  Y={self.Y:X}  Z={self.Z:X}")
        print(f"Aux Registers:      A'={self.A_prime:X} B'={self.B_prime:X} Y'={self.Y_prime:X} Z'={self.Z_prime:X}")
        print(f"Flag: {self.flag}  PC: 0x{self.program_counter:02X} ({self.program_counter})")
        print(f"\n7-Segment Display: {self.display:X}")

        # LED Anzeige
        led_str = "LEDs: "
        for i in range(7):
            led_str += "●" if self.leds[i] else "○"
            led_str += " "
        print(led_str)

        # Datenspeicher (0x50-0x5F)
        print(f"\nData Memory (0x50-0x5F):")
        print(f"  [50-57]: {' '.join([f'{self.memory[i]:X}' for i in range(0x50, 0x58)])}")
        print(f"  [58-5F]: {' '.join([f'{self.memory[i]:X}' for i in range(0x58, 0x60)])}")

        # Programmspeicher um PC herum
        print(f"\nProgram Memory around PC:")
        start = max(0, self.program_counter - 4)
        end = min(96, self.program_counter + 4)
        print(f"  [{start:02X}-{end-1:02X}]: ", end="")
        for i in range(start, end):
            if i == self.program_counter - 1:
                print(f"[{self.memory[i]:X}]", end=" ")
            else:
                print(f"{self.memory[i]:X}", end=" ")
        print()
        print(f"{'='*70}\n")


def load_knight_rider_example():
    """Lädt das Knight Rider Beispielprogramm von der Website"""
    program = [
        0x8, 0x0,  # TIA 0
        0x2,       # CH
        0xA, 0x0,  # TIY 0
        0xE, 0x1,  # CAL SETR
        0xA, 0x1,  # TIY 1
        0xE, 0x1,  # CAL SETR
        0xA, 0x2,  # TIY 2
        0xE, 0x1,  # CAL SETR
        # loop:
        0xA, 0x0,  # TIY 0
        0x8, 0x3,  # TIA 3
        # left:
        0xE, 0x2,  # CAL RSTR
        0x3,       # CY
        0xE, 0x1,  # CAL SETR
        0x3,       # CY
        0x2,       # CH
        0xE, 0xC,  # CAL TIMR
        0x2,       # CH
        0x9, 0x1,  # AIA 1
        0xB, 0x1,  # AIY 1
        0xC, 0x7,  # CIA 7
        0xF, 0x1, 0x3,  # JUMP 0x13 (left)
        0x3,       # CY
        0x9, 0xF,  # AIA F
        0xB, 0xF,  # AIY F
        # right:
        0xE, 0x2,  # CAL RSTR
        0x3,       # CY
        0xE, 0x1,  # CAL SETR
        0x3,       # CY
        0x2,       # CH
        0xE, 0xC,  # CAL TIMR
        0x2,       # CH
        0x9, 0xF,  # AIA F
        0xB, 0xF,  # AIY F
        0xC, 0xF,  # CIA F
        0xF, 0x2, 0xB,  # JUMP 0x2B (right)
        0xF, 0x0, 0xF,  # JUMP 0x0F (loop)
    ]
    return program


def demo_simple():
    """Einfaches Demo-Programm"""
    print("\n" + "="*70)
    print("GMC-4 Demo: Einfache LED-Anzeige")
    print("="*70 + "\n")

    computer = GMC4()

    # Einfaches Programm: Schalte LEDs 0, 1, 2 ein
    program = [
        0xA, 0x0,  # TIY 0
        0xE, 0x1,  # CAL SETR - LED 0 an
        0xA, 0x1,  # TIY 1
        0xE, 0x1,  # CAL SETR - LED 1 an
        0xA, 0x2,  # TIY 2
        0xE, 0x1,  # CAL SETR - LED 2 an
        0x8, 0x5,  # TIA 5
        0x1,       # AO - Zeige 5 auf Display
    ]

    computer.load_program(program)

    print("Programm: Schalte die ersten 3 LEDs ein und zeige 5 auf dem Display\n")

    for i in range(len(program) + 2):
        computer.print_state()
        print(f"Schritt {i+1} - Drücke Enter...")
        input()

        if not computer.step():
            print("Programm beendet.")
            break

    computer.print_state()


def interactive_mode():
    """Interaktiver Modus"""
    computer = GMC4()

    print("\n" + "="*70)
    print("GMC-4 Simulator - Interaktiver Modus")
    print("="*70)
    print("\nBefehle:")
    print("  load <addr> <hex> <hex> ...  - Lade Programm")
    print("  run                          - Führe Programm aus")
    print("  step [n]                     - Führe n Schritte aus (default: 1)")
    print("  reset                        - Soft Reset (PC=0)")
    print("  hardreset                    - Hard Reset (alles löschen)")
    print("  state                        - Zeige Zustand")
    print("  mem <start> <end>            - Zeige Speicher")
    print("  set <reg> <value>            - Setze Register (a, b, y, z)")
    print("  setflag <0|1>                - Setze Flag")
    print("  example                      - Lade Knight Rider Beispiel")
    print("  opcodes                      - Zeige Opcode-Tabelle")
    print("  quit                         - Beenden")
    print()

    while True:
        try:
            cmd = input("GMC-4> ").strip().split()

            if not cmd:
                continue

            if cmd[0] == 'quit':
                break

            elif cmd[0] == 'load' and len(cmd) >= 3:
                addr = int(cmd[1], 16)
                program = [int(b, 16) for b in cmd[2:]]
                computer.load_program(program, addr)
                print(f"✓ {len(program)} Bytes geladen ab 0x{addr:02X}")

            elif cmd[0] == 'run':
                steps = computer.run()
                print(f"✓ Programm ausgeführt ({steps} Schritte)")
                computer.print_state()

            elif cmd[0] == 'step':
                n = int(cmd[1]) if len(cmd) > 1 else 1
                for _ in range(n):
                    if not computer.step():
                        print("Programm angehalten")
                        break
                computer.print_state()

            elif cmd[0] == 'reset':
                computer.reset()
                print("✓ Soft Reset durchgeführt")

            elif cmd[0] == 'hardreset':
                computer.hard_reset()
                print("✓ Hard Reset durchgeführt")

            elif cmd[0] == 'state':
                computer.print_state()

            elif cmd[0] == 'mem' and len(cmd) >= 3:
                start = int(cmd[1], 16)
                end = int(cmd[2], 16)
                print(f"\nMemory [0x{start:02X}-0x{end:02X}]:")
                for i in range(start, end + 1, 8):
                    line_end = min(i + 8, end + 1)
                    mem_str = ' '.join([f'{computer.memory[j]:X}' for j in range(i, line_end)])
                    print(f"  [{i:02X}]: {mem_str}")
                print()

            elif cmd[0] == 'set' and len(cmd) == 3:
                reg = cmd[1].upper()
                val = int(cmd[2], 16) & 0xF
                if reg == 'A':
                    computer.A = val
                elif reg == 'B':
                    computer.B = val
                elif reg == 'Y':
                    computer.Y = val
                elif reg == 'Z':
                    computer.Z = val
                else:
                    print("Unbekanntes Register (a, b, y, z)")
                    continue
                print(f"✓ {reg} = 0x{val:X}")

            elif cmd[0] == 'setflag' and len(cmd) == 2:
                computer.flag = int(cmd[1]) & 1
                print(f"✓ Flag = {computer.flag}")

            elif cmd[0] == 'example':
                program = load_knight_rider_example()
                computer.load_program(program)
                print(f"✓ Knight Rider Beispiel geladen ({len(program)} Bytes)")
                print("  Hinweis: Nutze 'step' für Schritt-für-Schritt Ausführung")

            elif cmd[0] == 'opcodes':
                print_opcodes()

            else:
                print("❌ Unbekannter Befehl. Tippe 'opcodes' für Hilfe.")

        except Exception as e:
            print(f"❌ Fehler: {e}")


def print_opcodes():
    """Zeigt die Opcode-Tabelle"""
    print("\n" + "="*70)
    print("GMC-4 Instruction Set")
    print("="*70)
    print("\nBasic Instructions (Single Byte):")
    print("  0     KA          - Key to A (read keypad)")
    print("  1     AO          - A to Output (7-segment display)")
    print("  2     CH          - Change: A<->B, Y<->Z")
    print("  3     CY          - Change: A<->Y")
    print("  4     AM          - A to Memory[0x50+Y]")
    print("  5     MA          - Memory[0x50+Y] to A")
    print("  6     M+          - Memory + A -> A (with carry flag)")
    print("  7     M-          - Memory - A -> A (with borrow flag)")
    print("  8 n   TIA [n]     - Transfer Immediate to A")
    print("  9 n   AIA [n]     - Add Immediate to A")
    print("  A n   TIY [n]     - Transfer Immediate to Y")
    print("  B n   AIY [n]     - Add Immediate to Y")
    print("  C n   CIA [n]     - Compare Immediate with A")
    print("  D n   CIY [n]     - Compare Immediate with Y")
    print("  E x   ---         - Extended instructions (see below)")
    print("  F h l JUMP [h][l] - Conditional jump if Flag=1")
    print("\nExtended Instructions (E0-EF):")
    print("  E0    CAL RSTO    - Clear 7-segment display")
    print("  E1    CAL SETR    - Set LED Y (0-6)")
    print("  E2    CAL RSTR    - Reset LED Y (0-6)")
    print("  E3    ---         - Not used")
    print("  E4    CAL CMPL    - Complement A (invert bits)")
    print("  E5    CAL CHNG    - Change: Swap main/aux registers")
    print("  E6    CAL SIFT    - Shift A right 1 bit")
    print("  E7    CAL ENDS    - End sound")
    print("  E8    CAL ERRS    - Error sound")
    print("  E9    CAL SHTS    - Short beep")
    print("  EA    CAL LONS    - Long beep")
    print("  EB    CAL SUND    - Sound based on A (1-E)")
    print("  EC    CAL TIMR    - Timer: (A+1) * 0.1 seconds")
    print("  ED    CAL DSPR    - Display pattern on LEDs")
    print("  EE    CAL DEM-    - Decimal subtract, Y--")
    print("  EF    CAL DEM+    - Decimal add, Y--")
    print("\nMemory Layout:")
    print("  0x00-0x5F: Program memory (96 bytes)")
    print("  0x50-0x5F: Data memory (16 bytes, overlapping!)")
    print("="*70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'demo':
            demo_simple()
        elif sys.argv[1] == 'knight':
            computer = GMC4()
            program = load_knight_rider_example()
            computer.load_program(program)
            computer.enable_delays = True
            print("Running Knight Rider (drücke Ctrl+C zum Stoppen)...")
            try:
                computer.run()
            except KeyboardInterrupt:
                print("\nStopped.")
        else:
            print("Optionen: demo, knight, oder ohne Argument für interaktiven Modus")
    else:
        interactive_mode()
