# =========================
# Bit-Hilfsfunktionen
# =========================

def get_bit(mem, f):
    """Liest Bit f aus dem Speicher"""
    return (mem[f // 8] >> (f % 8)) & 1


def set_bit(mem, f, value):
    """Setzt Bit f auf 0 oder 1"""
    byte = f // 8
    bit = f % 8
    if value:
        mem[byte] |= (1 << bit)
    else:
        mem[byte] &= ~(1 << bit)


def flip_bit(mem, f):
    """Invertiert Bit f"""
    mem[f // 8] ^= (1 << (f % 8))


def read_bits(mem, start, n):
    """Liest n Bits ab Position start (LSB first)"""
    value = 0
    for i in range(n):
        value |= get_bit(mem, start + i) << i
    return value


def write_bits(mem, start, n, value):
    """Schreibt value in n Bits ab Position start (LSB first)"""
    for i in range(n):
        set_bit(mem, start + i, (value >> i) & 1)


# =========================
# FlipJump-Simulator
# =========================

def flipjump(mem, start_ip=0, addr_bits=8, steps=20):
    ip = start_ip

    for step in range(steps):
        print(f"\nStep {step}")
        print(f" IP = {ip}")

        # 1. Flip
        flip_bit(mem, ip)

        # 2. Jump-Adresse lesen
        next_ip = read_bits(mem, ip + 1, addr_bits)

        print(f" Jump -> {next_ip}")
        ip = next_ip


# =========================
# Beispielprogramm
# =========================
#
# Programm:
# - Start bei IP = 0
# - Flip Bit 0
# - Springe IMMER zurück zu 0
#
# Speicherlayout:
# Bit 0       : Instruction
# Bit 1–8     : Jump-Adresse (0)
#

MEM_BITS = 16
mem = bytearray(MEM_BITS // 8)

# Jump-Adresse = 0 (Bits 1–8 sind 00000000)
write_bits(mem, start=1, n=8, value=0)

print("Initialer Speicher:")
print(list(mem))

# Simulator starten
flipjump(mem, start_ip=0, addr_bits=8, steps=10)
