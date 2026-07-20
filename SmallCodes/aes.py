#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aes.py — Eigenständige AES-Implementierung zu Demonstrationszwecken.

Reines Python, nur Standardbibliothek. Unterstützt AES-128/192/256 und die
Betriebsmodi CBC, CTR und GCM. Alles wird von Grund auf aufgebaut:
GF(2^8)-Arithmetik, S-Box aus der multiplikativen Inversen + affiner Abbildung,
Key-Expansion, die vier Rundentransformationen und ihre Inversen, GHASH über
GF(2^128), SHA-256/HMAC/PBKDF2 für die Passwort-Schlüsselableitung, sowie eine
CLI zum Ver-/Entschlüsseln beliebiger Dateien.

WICHTIG: Dies ist Lehrcode. Er ist *nicht* seitenkanalresistent
(Table-Lookups, datenabhängige Zeiten). Für echte Anwendungen gehört
eine geprüfte Bibliothek her (z.B. `cryptography` / OpenSSL).

Referenz: FIPS 197 (Advanced Encryption Standard).
"""

from __future__ import annotations
import os
import sys
import getpass    # Passwort-Eingabe ohne Echo
import argparse   # Kommandozeilen-Schnittstelle

# ---------------------------------------------------------------------------
# 1. Arithmetik im endlichen Körper GF(2^8)
# ---------------------------------------------------------------------------
# AES rechnet in GF(2^8) modulo dem irreduziblen Polynom
#   m(x) = x^8 + x^4 + x^3 + x + 1   ->   0x11B
# Bytes sind Polynome: 0x53 = x^6 + x^4 + x + 1.

def gf_mul(a: int, b: int) -> int:
    """Multiplikation zweier Bytes in GF(2^8) (russische Bauernmultiplikation)."""
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80          # oberstes Bit vor dem Shift merken
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B          # Reduktion mod 0x11B (das 0x100-Bit fiel schon raus)
        b >>= 1
    return p


def gf_inverse(a: int) -> int:
    """Multiplikatives Inverses in GF(2^8). 0 ist per Konvention auf sich abgebildet."""
    if a == 0:
        return 0
    # Brute Force reicht für die Demo (256 Elemente); a^254 wäre die Alternative.
    for x in range(256):
        if gf_mul(a, x) == 1:
            return x
    raise AssertionError("kein Inverses gefunden – GF(2^8) kaputt")


# ---------------------------------------------------------------------------
# 2. S-Box aus multiplikativem Inversen + affiner Transformation
# ---------------------------------------------------------------------------
# S(a) = affine( inverse(a) ). Die affine Abbildung über GF(2):
#   b_i = a_i XOR a_(i+4) XOR a_(i+5) XOR a_(i+6) XOR a_(i+7) XOR c_i,  c = 0x63

def _rotl8(x: int, n: int) -> int:
    return ((x << n) | (x >> (8 - n))) & 0xFF


def _build_sbox() -> tuple[list[int], list[int]]:
    sbox = [0] * 256
    for a in range(256):
        inv = gf_inverse(a)
        s = inv ^ _rotl8(inv, 1) ^ _rotl8(inv, 2) ^ _rotl8(inv, 3) ^ _rotl8(inv, 4) ^ 0x63
        sbox[a] = s & 0xFF
    inv_sbox = [0] * 256
    for i, v in enumerate(sbox):
        inv_sbox[v] = i
    return sbox, inv_sbox


SBOX, INV_SBOX = _build_sbox()

# Rundenkonstanten: Rcon[i] = x^(i-1) in GF(2^8), nur das erste Byte ist relevant.
def _build_rcon(n: int) -> list[int]:
    rcon = [0x01]
    for _ in range(1, n):
        rcon.append(gf_mul(rcon[-1], 0x02))
    return rcon

RCON = _build_rcon(15)


# ---------------------------------------------------------------------------
# 3. Zustand (State) — 4x4-Bytematrix, spaltenweise befüllt
# ---------------------------------------------------------------------------
# Der 16-Byte-Block b0..b15 füllt die Matrix spaltenweise:
#   b0 b4 b8  b12
#   b1 b5 b9  b13
#   b2 b6 b10 b14
#   b3 b7 b11 b15
# Wir halten den State intern als flache Liste von 16 Bytes in genau dieser
# spaltenweisen Reihenfolge (= Eingabereihenfolge), was die Indizierung simpel hält.

def sub_bytes(s, box):
    return [box[b] for b in s]


def shift_rows(s):
    # Zeile r wird um r nach links rotiert. Zeile r, Spalte c liegt bei index r + 4*c.
    out = [0] * 16
    for r in range(4):
        for c in range(4):
            out[r + 4 * c] = s[r + 4 * ((c + r) % 4)]
    return out


def inv_shift_rows(s):
    out = [0] * 16
    for r in range(4):
        for c in range(4):
            out[r + 4 * c] = s[r + 4 * ((c - r) % 4)]
    return out


def mix_columns(s):
    out = [0] * 16
    for c in range(4):
        col = s[4 * c:4 * c + 4]
        out[4 * c + 0] = gf_mul(col[0], 2) ^ gf_mul(col[1], 3) ^ col[2] ^ col[3]
        out[4 * c + 1] = col[0] ^ gf_mul(col[1], 2) ^ gf_mul(col[2], 3) ^ col[3]
        out[4 * c + 2] = col[0] ^ col[1] ^ gf_mul(col[2], 2) ^ gf_mul(col[3], 3)
        out[4 * c + 3] = gf_mul(col[0], 3) ^ col[1] ^ col[2] ^ gf_mul(col[3], 2)
    return out


def inv_mix_columns(s):
    out = [0] * 16
    for c in range(4):
        col = s[4 * c:4 * c + 4]
        out[4 * c + 0] = gf_mul(col[0], 14) ^ gf_mul(col[1], 11) ^ gf_mul(col[2], 13) ^ gf_mul(col[3], 9)
        out[4 * c + 1] = gf_mul(col[0], 9) ^ gf_mul(col[1], 14) ^ gf_mul(col[2], 11) ^ gf_mul(col[3], 13)
        out[4 * c + 2] = gf_mul(col[0], 13) ^ gf_mul(col[1], 9) ^ gf_mul(col[2], 14) ^ gf_mul(col[3], 11)
        out[4 * c + 3] = gf_mul(col[0], 11) ^ gf_mul(col[1], 13) ^ gf_mul(col[2], 9) ^ gf_mul(col[3], 14)
    return out


def add_round_key(s, round_key):
    return [a ^ b for a, b in zip(s, round_key)]


# ---------------------------------------------------------------------------
# 4. Key-Expansion
# ---------------------------------------------------------------------------
# Der Schlüssel wird in Nk 4-Byte-Wörter zerlegt und auf 4*(Nr+1) Wörter
# expandiert. Ausgegeben wird eine Liste von Rundenschlüsseln zu je 16 Bytes.

def _sub_word(w):
    return [SBOX[b] for b in w]


def _rot_word(w):
    return w[1:] + w[:1]


def expand_key(key: bytes) -> list[list[int]]:
    nk = len(key) // 4                 # 4, 6 oder 8 Wörter
    nr = {4: 10, 6: 12, 8: 14}[nk]     # Rundenzahl
    words = [list(key[4 * i:4 * i + 4]) for i in range(nk)]

    for i in range(nk, 4 * (nr + 1)):
        temp = words[i - 1][:]
        if i % nk == 0:
            temp = _sub_word(_rot_word(temp))
            temp[0] ^= RCON[i // nk - 1]
        elif nk > 6 and i % nk == 4:   # zusätzlicher SubWord-Schritt nur bei AES-256
            temp = _sub_word(temp)
        words.append([a ^ b for a, b in zip(words[i - nk], temp)])

    # Je 4 Wörter zu einem 16-Byte-Rundenschlüssel zusammenfassen.
    return [sum(words[4 * r:4 * r + 4], []) for r in range(nr + 1)]


# ---------------------------------------------------------------------------
# 5. Block-Chiffre: ein 16-Byte-Block
# ---------------------------------------------------------------------------

def encrypt_block(block: bytes, round_keys: list[list[int]]) -> bytes:
    nr = len(round_keys) - 1
    s = list(block)
    s = add_round_key(s, round_keys[0])
    for rnd in range(1, nr):
        s = sub_bytes(s, SBOX)
        s = shift_rows(s)
        s = mix_columns(s)
        s = add_round_key(s, round_keys[rnd])
    # Schlussrunde ohne MixColumns
    s = sub_bytes(s, SBOX)
    s = shift_rows(s)
    s = add_round_key(s, round_keys[nr])
    return bytes(s)


def decrypt_block(block: bytes, round_keys: list[list[int]]) -> bytes:
    nr = len(round_keys) - 1
    s = list(block)
    s = add_round_key(s, round_keys[nr])
    for rnd in range(nr - 1, 0, -1):
        s = inv_shift_rows(s)
        s = sub_bytes(s, INV_SBOX)
        s = add_round_key(s, round_keys[rnd])
        s = inv_mix_columns(s)
    s = inv_shift_rows(s)
    s = sub_bytes(s, INV_SBOX)
    s = add_round_key(s, round_keys[0])
    return bytes(s)


# ---------------------------------------------------------------------------
# 6. PKCS#7-Padding + CBC-Betriebsmodus
# ---------------------------------------------------------------------------
# ECB wäre der simpelste Modus, verrät aber Muster (gleiche Klartextblöcke ->
# gleiche Chiffreblöcke). Deshalb hier CBC: jeder Block wird vor dem
# Verschlüsseln mit dem vorherigen Chiffreblock (bzw. dem IV) XOR-verknüpft.

def pkcs7_pad(data: bytes, block=16) -> bytes:
    n = block - (len(data) % block)    # immer 1..block Bytes anhängen
    return data + bytes([n]) * n


def pkcs7_unpad(data: bytes) -> bytes:
    if not data or len(data) % 16 != 0:
        raise ValueError("ungültige Länge")
    n = data[-1]
    if n < 1 or n > 16 or data[-n:] != bytes([n]) * n:
        raise ValueError("ungültiges Padding")
    return data[:-n]


def _xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def cbc_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    rk = expand_key(key)
    data = pkcs7_pad(plaintext)
    out, prev = bytearray(), iv
    for i in range(0, len(data), 16):
        block = _xor(data[i:i + 16], prev)
        enc = encrypt_block(block, rk)
        out += enc
        prev = enc
    return bytes(out)


def cbc_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    if len(ciphertext) % 16 != 0:
        raise ValueError("Chiffretextlänge kein Vielfaches von 16")
    rk = expand_key(key)
    out, prev = bytearray(), iv
    for i in range(0, len(ciphertext), 16):
        block = ciphertext[i:i + 16]
        out += _xor(decrypt_block(block, rk), prev)
        prev = block
    return pkcs7_unpad(bytes(out))


# ---------------------------------------------------------------------------
# 7. CTR-Modus (Counter)
# ---------------------------------------------------------------------------
# CTR macht aus der Blockchiffre eine Stromchiffre: man verschlüsselt nicht die
# Daten, sondern eine Folge von Zählerblöcken und XOR-t das Ergebnis (den
# "Keystream") mit dem Klartext. Folgen:
#   * kein Padding nötig, beliebige Länge
#   * Ver- und Entschlüsseln sind dieselbe Operation
#   * blockweise parallelisierbar
# ZWINGEND: derselbe (Schlüssel, Startzähler) darf nie zweimal verwendet
# werden – sonst hebt sich der Keystream per XOR heraus.

def _inc_be(block: bytes, width: int = 16) -> bytes:
    """Die letzten `width` Bytes als Big-Endian-Zähler um 1 erhöhen (mit Überlauf)."""
    head, tail = block[:len(block) - width], block[len(block) - width:]
    n = (int.from_bytes(tail, "big") + 1) & ((1 << (8 * width)) - 1)
    return head + n.to_bytes(width, "big")


def _ctr_keystream(rk, counter_block: bytes, nbytes: int):
    """Keystream erzeugen, indem fortlaufende Zählerblöcke verschlüsselt werden."""
    out, cb = bytearray(), counter_block
    while len(out) < nbytes:
        out += encrypt_block(cb, rk)
        cb = _inc_be(cb, 16)          # voller 128-Bit-Zähler
    return bytes(out[:nbytes])


def ctr_crypt(data: bytes, key: bytes, counter_block: bytes) -> bytes:
    """CTR ver-/entschlüsseln. `counter_block` ist der 16-Byte-Startzähler.
    Da XOR symmetrisch ist, dient dieselbe Funktion für beide Richtungen."""
    if len(counter_block) != 16:
        raise ValueError("counter_block muss 16 Bytes sein")
    rk = expand_key(key)
    ks = _ctr_keystream(rk, counter_block, len(data))
    return _xor(data, ks)


# ---------------------------------------------------------------------------
# 8. GCM-Modus (Galois/Counter) – authentifizierte Verschlüsselung
# ---------------------------------------------------------------------------
# GCM = CTR-Verschlüsselung + GHASH-Authentifizierung. GHASH rechnet in einem
# ZWEITEN endlichen Körper, GF(2^128), modulo
#   x^128 + x^7 + x^2 + x + 1.
# GCM benutzt eine gespiegelte ("reflected") Bitkonvention: das erste
# übertragene Bit ist der Koeffizient von x^0. Deshalb ist das Reduktionsbyte
# hier 0xE1 (= 11100001, gespiegeltes 10000111) am oberen Ende, und die
# Multiplikation schiebt nach rechts. Das ist der klassische Stolperstein bei
# GCM-Implementierungen.

_R128 = 0xE1 << 120                     # Reduktionspolynom in GCM-Bitordnung


def _gf128_mul(x: int, y: int) -> int:
    """Multiplikation zweier 128-Bit-Blöcke in GF(2^128), GCM-Konvention."""
    z, v = 0, y
    for i in range(128):
        if (x >> (127 - i)) & 1:        # Bits von x von links (MSB=x^0) durchgehen
            z ^= v
        if v & 1:
            v = (v >> 1) ^ _R128
        else:
            v >>= 1
    return z


def _ghash(h: int, data: bytes, tracer=None, label: str = "GHASH") -> int:
    """GHASH_H über bereits auf Blockgröße aufgefüllte Daten.
    Optionaler `tracer(name, hexstr)` protokolliert Y nach jedem Block."""
    y = 0
    for i in range(0, len(data), 16):
        block = int.from_bytes(data[i:i + 16], "big")
        y = _gf128_mul(y ^ block, h)    # y := (y XOR block) * H
        if tracer:
            tracer(f"{label} Y[{i // 16 + 1}]", y.to_bytes(16, "big").hex())
    return y


def _pad16(data: bytes) -> bytes:
    """Mit Nullbytes auf ein Vielfaches von 16 auffüllen."""
    r = len(data) % 16
    return data if r == 0 else data + b"\x00" * (16 - r)


def _gcm_j0(h: int, iv: bytes, tracer=None) -> bytes:
    """Startzählerblock J0 aus dem IV ableiten."""
    if len(iv) == 12:                   # empfohlener 96-Bit-IV: schneller Sonderfall
        return iv + b"\x00\x00\x00\x01"
    # beliebige IV-Länge: J0 = GHASH_H(IV-gepadded || 0^64 || len(IV)_in_bits_64)
    data = _pad16(iv) + (b"\x00" * 8) + (len(iv) * 8).to_bytes(8, "big")
    return _ghash(h, data, tracer, "J0-GHASH").to_bytes(16, "big")


def _gcm_tag(rk, h: int, j0: bytes, aad: bytes, ct: bytes, tag_len: int, tracer=None) -> bytes:
    """Authentifizierungs-Tag über AAD und Chiffretext berechnen."""
    s_data = (_pad16(aad) + _pad16(ct)
              + (len(aad) * 8).to_bytes(8, "big")
              + (len(ct) * 8).to_bytes(8, "big"))
    s = _ghash(h, s_data, tracer).to_bytes(16, "big")
    ek_j0 = encrypt_block(j0, rk)
    if tracer:
        tracer("S = GHASH_H(A||C||len)", s.hex())
        tracer("E_K(J0)", ek_j0.hex())
    # Tag = E_K(J0) XOR S  (= GCTR mit Startzähler J0 auf S)
    return _xor(ek_j0, s)[:tag_len]


def gcm_encrypt(plaintext: bytes, key: bytes, iv: bytes,
                aad: bytes = b"", tag_len: int = 16, tracer=None):
    """Authentifiziert verschlüsseln. Liefert (ciphertext, tag).
    `aad` sind mitauthentifizierte, aber unverschlüsselte Zusatzdaten.
    `tracer(name, hexstr)` protokolliert optional die Zwischenwerte."""
    rk = expand_key(key)
    h_block = encrypt_block(b"\x00" * 16, rk)                    # Hash-Subkey H = E_K(0)
    h = int.from_bytes(h_block, "big")
    if tracer:
        tracer("H = E_K(0^128)", h_block.hex())
    j0 = _gcm_j0(h, iv, tracer)
    if tracer:
        tracer("J0", j0.hex())
        tracer("inc32(J0) [CTR-Start]", _inc_be(j0, 4).hex())
    ct = ctr_crypt(plaintext, key, _inc_be(j0, 4))              # CTR ab inc32(J0)
    tag = _gcm_tag(rk, h, j0, aad, ct, tag_len, tracer)
    if tracer:
        tracer("Tag", tag.hex())
    return ct, tag


def _ct_equal(a: bytes, b: bytes) -> bool:
    """Konstantzeit-Vergleich zweier Bytefolgen. Ersatz für hmac.compare_digest.
    Entscheidend ist, dass NICHT beim ersten unterschiedlichen Byte abgebrochen
    wird: alle Bytes werden per XOR in `diff` verodert, sodass die Laufzeit nicht
    verrät, an welcher Stelle (und ab wie vielen korrekten Bytes) es abweicht.
    Ohne das könnte ein Angreifer über die Antwortzeit einen gültigen Tag Byte
    für Byte erraten. (In reinem Python ist echte Konstantzeit nicht strikt
    garantiert, aber der gefährliche vorzeitige Abbruch ist damit ausgeschlossen.)"""
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        diff |= x ^ y
    return diff == 0


def gcm_decrypt(ciphertext: bytes, key: bytes, iv: bytes, tag: bytes,
                aad: bytes = b"", tracer=None) -> bytes:
    """Tag prüfen und entschlüsseln. Wirft ValueError bei ungültigem Tag –
    dann wird KEIN Klartext zurückgegeben (die zentrale GCM-Garantie)."""
    rk = expand_key(key)
    h_block = encrypt_block(b"\x00" * 16, rk)
    h = int.from_bytes(h_block, "big")
    if tracer:
        tracer("H = E_K(0^128)", h_block.hex())
    j0 = _gcm_j0(h, iv, tracer)
    if tracer:
        tracer("J0", j0.hex())
    expected = _gcm_tag(rk, h, j0, aad, ciphertext, len(tag), tracer)
    # Konstantzeit-Vergleich: niemals `==` auf Tags (verrät Bytes per Timing).
    if not _ct_equal(expected, tag):
        raise ValueError("Authentifizierung fehlgeschlagen – Tag ungültig")
    return ctr_crypt(ciphertext, key, _inc_be(j0, 4))


# ---------------------------------------------------------------------------
# 9. Selbsttest gegen die FIPS-197-Vektoren + CBC-Roundtrip
# ---------------------------------------------------------------------------

def _selftest() -> None:
    h = bytes.fromhex
    pt = h("00112233445566778899aabbccddeeff")
    vectors = {
        "AES-128": ("000102030405060708090a0b0c0d0e0f",
                    "69c4e0d86a7b0430d8cdb78070b4c55a"),
        "AES-192": ("000102030405060708090a0b0c0d0e0f1011121314151617",
                    "dda97ca4864cdfe06eaf70a0ec0d7191"),
        "AES-256": ("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
                    "8ea2b7ca516745bfeafc49904b496089"),
    }
    for name, (key_hex, ct_hex) in vectors.items():
        rk = expand_key(h(key_hex))
        ct = encrypt_block(pt, rk)
        assert ct == h(ct_hex), f"{name}: Verschlüsselung falsch"
        assert decrypt_block(ct, rk) == pt, f"{name}: Entschlüsselung falsch"
        print(f"  {name}: OK  ({pt.hex()} -> {ct.hex()})")

    # S-Box-Stichprobe: S(0x00)=0x63, S(0x53)=0xed
    assert SBOX[0x00] == 0x63 and SBOX[0x53] == 0xed, "S-Box falsch"

    # CBC-Roundtrip mit ungerader Länge (Padding-Pfad)
    key = h("2b7e151628aed2a6abf7158809cf4f3c")
    iv = h("000102030405060708090a0b0c0d0e0f")
    msg = "Hallo AES – Demonstration mit CBC und PKCS#7!".encode("utf-8")
    ct = cbc_encrypt(msg, key, iv)
    assert cbc_decrypt(ct, key, iv) == msg, "CBC-Roundtrip falsch"
    print(f"  CBC-Roundtrip: OK  ({len(msg)} Bytes Klartext -> {len(ct)} Bytes Chiffre)")

    # CTR gegen NIST SP 800-38A F.5.1 (AES-128)
    ctr_key = h("2b7e151628aed2a6abf7158809cf4f3c")
    ctr_ctr = h("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff")
    ctr_pt = h("6bc1bee22e409f96e93d7e117393172a"
               "ae2d8a571e03ac9c9eb76fac45af8e51"
               "30c81c46a35ce411e5fbc1191a0a52ef"
               "f69f2445df4f9b17ad2b417be66c3710")
    ctr_ct = h("874d6191b620e3261bef6864990db6ce"
               "9806f66b7970fdff8617187bb9fffdff"
               "5ae4df3edbd5d35e5b4f09020db03eab"
               "1e031dda2fbe03d1792170a0f3009cee")
    assert ctr_crypt(ctr_pt, ctr_key, ctr_ctr) == ctr_ct, "CTR-Vektor falsch"
    assert ctr_crypt(ctr_ct, ctr_key, ctr_ctr) == ctr_pt, "CTR-Roundtrip falsch"
    print("  CTR (SP 800-38A F.5.1): OK")

    # GCM gegen McGrew/Viega Test Case 3 (AES-128, ohne AAD)
    g_key = h("feffe9928665731c6d6a8f9467308308")
    g_iv = h("cafebabefacedbaddecaf888")
    g_pt = h("d9313225f88406e5a55909c5aff5269a86a7a9531534f7da2e4c303d8a318a72"
             "1c3c0c95956809532fcf0e2449a6b525b16aedf5aa0de657ba637b391aafd255")
    g_ct = h("42831ec2217774244b7221b784d0d49ce3aa212f2c02a4e035c17e2329aca12e"
             "21d514b25466931c7d8f6a5aac84aa051ba30b396a0aac973d58e091473f5985")
    g_tag = h("4d5c2af327cd64a62cf35abd2ba6fab4")
    ct, tag = gcm_encrypt(g_pt, g_key, g_iv)
    assert ct == g_ct and tag == g_tag, "GCM Test Case 3 falsch"
    assert gcm_decrypt(ct, g_key, g_iv, tag) == g_pt, "GCM-Entschlüsselung falsch"
    print("  GCM Test Case 3 (ohne AAD):  OK")

    # GCM gegen Test Case 4 (AES-128, mit AAD, unvollständiger Schlussblock)
    a_pt = h("d9313225f88406e5a55909c5aff5269a86a7a9531534f7da2e4c303d8a318a72"
             "1c3c0c95956809532fcf0e2449a6b525b16aedf5aa0de657ba637b39")
    a_aad = h("feedfacedeadbeeffeedfacedeadbeefabaddad2")
    a_ct = h("42831ec2217774244b7221b784d0d49ce3aa212f2c02a4e035c17e2329aca12e"
             "21d514b25466931c7d8f6a5aac84aa051ba30b396a0aac973d58e091")
    a_tag = h("5bc94fbc3221a5db94fae95ae7121a47")
    ct, tag = gcm_encrypt(a_pt, g_key, g_iv, aad=a_aad)
    assert ct == a_ct and tag == a_tag, "GCM Test Case 4 (AAD) falsch"
    assert gcm_decrypt(ct, g_key, g_iv, tag, aad=a_aad) == a_pt, "GCM+AAD-Entschlüsselung falsch"
    print("  GCM Test Case 4 (mit AAD):   OK")

    # Tamper-Test: ein gekipptes Bit im Chiffretext muss die Prüfung sprengen
    bad = bytearray(ct); bad[0] ^= 0x01
    try:
        gcm_decrypt(bytes(bad), g_key, g_iv, tag, aad=a_aad)
        raise AssertionError("GCM hat manipulierten Chiffretext akzeptiert!")
    except ValueError:
        print("  GCM-Manipulation korrekt abgewiesen: OK")

    # SHA-256 gegen FIPS-180-4-Beispiele
    assert sha256(b"").hex() == \
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert sha256(b"abc").hex() == \
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    print("  SHA-256 (FIPS 180-4): OK")

    # HMAC-SHA-256 gegen RFC 4231 Test Case 2
    assert hmac_sha256(b"Jefe", b"what do ya want for nothing?").hex() == \
        "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
    print("  HMAC-SHA-256 (RFC 4231): OK")

    # PBKDF2-HMAC-SHA-256 gegen bekannten Vektor (P=password, S=salt, c=4096)
    assert pbkdf2_sha256(b"password", b"salt", 4096, 32).hex() == \
        "c5e478d59288c841aa530db6845c4c8d962893a001ce4e11a4963873aa98134a"
    print("  PBKDF2-HMAC-SHA-256 (c=4096): OK")

    # Datei-KDF-Roundtrip: Ableiten + AES-256-GCM mit kleiner Iterationszahl
    dk = _derive_key("pw", b"0123456789abcdef", 1000, 32)
    assert len(dk) == 32
    ct2, tag2 = gcm_encrypt(b"kurzer test", dk, b"n" * 12)
    assert gcm_decrypt(ct2, dk, b"n" * 12, tag2) == b"kurzer test"
    print("  Datei-KDF -> GCM-Roundtrip: OK")

    print("Alle Tests bestanden.")


# ---------------------------------------------------------------------------
# 8. Kleine Kommandozeilen-Demo
# ---------------------------------------------------------------------------

def _demo() -> None:
    key = os.urandom(32)               # AES-256-Schlüssel
    iv = os.urandom(16)
    msg = "Angriff bei Morgengrauen. Treffpunkt an der alten Mühle.".encode("utf-8")

    print("\n--- CBC-Demo (AES-256) ---")
    print("Schlüssel :", key.hex())
    print("IV        :", iv.hex())
    print("Klartext  :", msg.decode("utf-8"))
    ct = cbc_encrypt(msg, key, iv)
    print("Chiffre   :", ct.hex())
    print("Entschl.  :", cbc_decrypt(ct, key, iv).decode("utf-8"))

    print("\n--- CTR-Demo (AES-256, kein Padding) ---")
    ctr0 = os.urandom(16)
    ct = ctr_crypt(msg, key, ctr0)
    print("Startzähler:", ctr0.hex())
    print("Chiffre   :", ct.hex(), f"({len(ct)} Bytes, = Klartextlänge)")
    print("Entschl.  :", ctr_crypt(ct, key, ctr0).decode("utf-8"))

    print("\n--- GCM-Demo (AES-256, authentifiziert) ---")
    nonce = os.urandom(12)             # 96-Bit-Nonce (empfohlen)
    aad = b"absender=andre;version=1"  # mitauthentifiziert, aber unverschlüsselt
    ct, tag = gcm_encrypt(msg, key, nonce, aad=aad)
    print("Nonce     :", nonce.hex())
    print("AAD       :", aad.decode())
    print("Chiffre   :", ct.hex())
    print("Tag       :", tag.hex())
    print("Entschl.  :", gcm_decrypt(ct, key, nonce, tag, aad=aad).decode("utf-8"))


# ---------------------------------------------------------------------------
# 10. Hash-Primitive: SHA-256, HMAC-SHA-256, PBKDF2 (alles selbst)
# ---------------------------------------------------------------------------
# SHA-256 nach FIPS 180-4. Die Konstanten sind "nothing-up-my-sleeve"-Zahlen:
# H = Nachkommateil der Quadratwurzeln der ersten 8 Primzahlen, K = Nachkomma-
# teil der Kubikwurzeln der ersten 64 Primzahlen, jeweils die oberen 32 Bit.
# Wir berechnen sie (wie schon die S-Box), damit keine magischen Tabellen bleiben.

def _first_primes(n: int):
    primes, c = [], 2
    while len(primes) < n:
        if all(c % p for p in primes if p * p <= c):
            primes.append(c)
        c += 1
    return primes


def _iroot(n: int, k: int) -> int:
    """Ganzzahlige k-te Wurzel floor(n**(1/k)), rein ganzzahlig per Newton."""
    if n == 0:
        return 0
    x = 1 << ((n.bit_length() + k - 1) // k)
    while True:
        y = ((k - 1) * x + n // x ** (k - 1)) // k
        if y >= x:
            return x
        x = y


_PRIMES = _first_primes(64)
SHA256_H = [_iroot(p << 64, 2) & 0xFFFFFFFF for p in _PRIMES[:8]]   # frac(sqrt(p))
SHA256_K = [_iroot(p << 96, 3) & 0xFFFFFFFF for p in _PRIMES]       # frac(cbrt(p))


def _rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


def sha256(msg: bytes) -> bytes:
    """SHA-256-Digest (32 Byte) einer Bytefolge."""
    h = list(SHA256_H)
    # Padding: 0x80, dann Nullen bis Länge ≡ 56 (mod 64), dann 64-Bit-Bitlänge.
    ml = len(msg) * 8
    msg = msg + b"\x80"
    while len(msg) % 64 != 56:
        msg += b"\x00"
    msg += ml.to_bytes(8, "big")
    for off in range(0, len(msg), 64):                 # je 512-Bit-Block
        blk = msg[off:off + 64]
        w = [int.from_bytes(blk[i:i + 4], "big") for i in range(0, 64, 4)]
        for t in range(16, 64):                        # Message Schedule erweitern
            s0 = _rotr(w[t-15], 7) ^ _rotr(w[t-15], 18) ^ (w[t-15] >> 3)
            s1 = _rotr(w[t-2], 17) ^ _rotr(w[t-2], 19) ^ (w[t-2] >> 10)
            w.append((w[t-16] + s0 + w[t-7] + s1) & 0xFFFFFFFF)
        a, b, c, d, e, f, g, hh = h
        for t in range(64):                            # 64 Kompressionsrunden
            S1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
            ch = (e & f) ^ ((e ^ 0xFFFFFFFF) & g)
            t1 = (hh + S1 + ch + SHA256_K[t] + w[t]) & 0xFFFFFFFF
            S0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            t2 = (S0 + maj) & 0xFFFFFFFF
            hh, g, f, e, d, c, b, a = (g, f, e, (d + t1) & 0xFFFFFFFF,
                                       c, b, a, (t1 + t2) & 0xFFFFFFFF)
        h = [(x + y) & 0xFFFFFFFF for x, y in zip(h, (a, b, c, d, e, f, g, hh))]
    return b"".join(x.to_bytes(4, "big") for x in h)


def hmac_sha256(key: bytes, msg: bytes) -> bytes:
    """HMAC-SHA-256 nach RFC 2104."""
    B = 64                                             # SHA-256-Blockgröße
    if len(key) > B:
        key = sha256(key)
    key = key + b"\x00" * (B - len(key))
    ipad = bytes(k ^ 0x36 for k in key)
    opad = bytes(k ^ 0x5c for k in key)
    return sha256(opad + sha256(ipad + msg))


def pbkdf2_sha256(password: bytes, salt: bytes, iters: int, dklen: int) -> bytes:
    """PBKDF2-HMAC-SHA-256 nach RFC 8018. Streckt ein Passwort zu dklen Byten,
    indem HMAC iters-mal iteriert und die Zwischenergebnisse ge-XOR-t werden."""
    HLEN = 32
    out, i = bytearray(), 1
    while len(out) < dklen:
        u = hmac_sha256(password, salt + i.to_bytes(4, "big"))   # U_1
        t = bytearray(u)
        for _ in range(iters - 1):
            u = hmac_sha256(password, u)                         # U_2 .. U_c
            for j in range(HLEN):
                t[j] ^= u[j]                                     # T_i = XOR aller U
        out += t
        i += 1
    return bytes(out[:dklen])


# ---------------------------------------------------------------------------
# 11. Datei-Container: AES-GCM mit passwortbasierter Schlüsselableitung
# ---------------------------------------------------------------------------
# Dateiformat (alles binär, hintereinander):
#   MAGIC (8) | keylen (1) | iters (4) | salt (16) | nonce (12) | tag (16) | ciphertext
# keylen = Schlüssellänge in Byte (16/24/32 = AES-128/192/256), iters = PBKDF2-
# Iterationszahl (Big-Endian). Beide stehen im Header, damit die Entschlüsselung
# sie automatisch kennt und du die Iterationszahl später ändern kannst, ohne
# alte Dateien unlesbar zu machen. Der ganze Header wird als AAD mitauthentifiziert
# – jede Änderung (auch an keylen oder iters) lässt die Tag-Prüfung fehlschlagen.
#
# HINWEIS zur Iterationszahl: In reinem Python ist PBKDF2 sehr langsam (~0,7 ms
# pro Iteration). Der Default ist deshalb bewusst niedrig gehalten, damit das
# Tool interaktiv nutzbar bleibt. Für echten Schutz bräuchte man eine schnelle
# (C-)Implementierung mit 600.000+ Iterationen; siehe --iters.

_MAGIC = b"AESGCM03"           # 03: Format mit keylen- und iters-Feld
_KDF_ITERS_DEFAULT = 10_000    # Kompromiss für die langsame Python-KDF
_HEADER_LEN = 8 + 1 + 4 + 16 + 12   # MAGIC + keylen + iters + salt + nonce
_VALID_KEYLEN = (16, 24, 32)   # AES-128 / AES-192 / AES-256


def _derive_key(password: str, salt: bytes, iters: int, keylen: int = 32) -> bytes:
    """AES-Schlüssel (keylen Byte) aus Passwort + Salt via eigener PBKDF2."""
    if keylen not in _VALID_KEYLEN:
        raise ValueError(f"ungültige Schlüssellänge: {keylen} Byte")
    return pbkdf2_sha256(password.encode("utf-8"), salt, iters, keylen)


def encrypt_file(infile: str, outfile: str, password: str, keylen: int = 32,
                 iters: int = _KDF_ITERS_DEFAULT, tracer=None) -> None:
    if keylen not in _VALID_KEYLEN:
        raise ValueError(f"ungültige Schlüssellänge: {keylen} Byte")
    with open(infile, "rb") as f:
        plaintext = f.read()
    salt = os.urandom(16)
    nonce = os.urandom(12)
    header = _MAGIC + bytes([keylen]) + iters.to_bytes(4, "big") + salt + nonce
    key = _derive_key(password, salt, iters, keylen)
    ct, tag = gcm_encrypt(plaintext, key, nonce, aad=header, tracer=tracer)
    with open(outfile, "wb") as f:
        f.write(header + tag + ct)


def decrypt_file(infile: str, outfile: str, password: str, tracer=None) -> None:
    with open(infile, "rb") as f:
        blob = f.read()
    if len(blob) < _HEADER_LEN + 16 or blob[:8] != _MAGIC:
        raise ValueError("kein gültiger AESGCM03-Container")
    keylen = blob[8]
    if keylen not in _VALID_KEYLEN:
        raise ValueError(f"ungültige Schlüssellänge im Header: {keylen}")
    iters = int.from_bytes(blob[9:13], "big")
    header = blob[:_HEADER_LEN]
    salt = blob[13:29]
    nonce = blob[29:41]
    tag = blob[_HEADER_LEN:_HEADER_LEN + 16]
    ct = blob[_HEADER_LEN + 16:]
    key = _derive_key(password, salt, iters, keylen)
    # Wirft ValueError bei falschem Passwort ODER manipulierten Daten/Header.
    plaintext = gcm_decrypt(ct, key, nonce, tag, aad=header, tracer=tracer)
    with open(outfile, "wb") as f:
        f.write(plaintext)


# ---------------------------------------------------------------------------
# 11. Kommandozeilen-Schnittstelle
# ---------------------------------------------------------------------------

def _print_tracer(name: str, hexstr: str) -> None:
    """Einfacher Tracer: gibt Zwischenwerte formatiert aus."""
    print(f"    {name:<26} = {hexstr}")


def _get_password(args, confirm: bool) -> str:
    """Passwort aus --password oder interaktiv (ohne Echo) holen."""
    if args.password is not None:
        return args.password
    pw = getpass.getpass("Passwort: ")
    if confirm and pw != getpass.getpass("Passwort wiederholen: "):
        print("Passwörter stimmen nicht überein.", file=sys.stderr)
        sys.exit(2)
    return pw


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="AES-Demonstration (128/192/256; CBC/CTR/GCM). "
                    "Datei-Ver-/Entschlüsselung nutzt AES-256-GCM mit PBKDF2.")
    sub = p.add_subparsers(dest="cmd")

    for name, help_ in (("encrypt", "Datei verschlüsseln (AES-256-GCM)"),
                        ("decrypt", "Datei entschlüsseln")):
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("infile", help="Eingabedatei")
        sp.add_argument("-o", "--out", help="Ausgabedatei "
                        "(Standard: .aes anhängen bzw. entfernen)")
        sp.add_argument("-p", "--password", help="Passwort direkt angeben "
                        "(unsicher – landet in der Shell-History; sonst interaktiv)")
        sp.add_argument("--trace", action="store_true",
                        help="GCM-Zwischenwerte (H, J0, GHASH-Y, Tag) ausgeben")
        if name == "encrypt":
            sp.add_argument("--bits", type=int, choices=(128, 192, 256), default=256,
                            help="AES-Schlüssellänge in Bit (Standard: 256). "
                                 "Beim Entschlüsseln automatisch aus der Datei erkannt.")
            sp.add_argument("--iters", type=int, default=_KDF_ITERS_DEFAULT,
                            help=f"PBKDF2-Iterationen (Standard: {_KDF_ITERS_DEFAULT}). "
                                 "Höher = sicherer, aber in reinem Python spürbar langsamer. "
                                 "Wird in der Datei gespeichert.")

    sub.add_parser("selftest", help="Testvektoren prüfen")
    sub.add_parser("demo", help="CBC/CTR/GCM-Demo mit Zufallsschlüssel")
    return p


def main(argv=None) -> None:
    args = _build_parser().parse_args(argv)
    tracer = _print_tracer if getattr(args, "trace", False) else None

    if args.cmd == "encrypt":
        out = args.out or args.infile + ".aes"
        pw = _get_password(args, confirm=True)
        encrypt_file(args.infile, out, pw, keylen=args.bits // 8,
                     iters=args.iters, tracer=tracer)
        print(f"Verschlüsselt (AES-{args.bits}, {args.iters} PBKDF2-Iter): "
              f"{args.infile} -> {out}")

    elif args.cmd == "decrypt":
        if args.out:
            out = args.out
        elif args.infile.endswith(".aes"):
            out = args.infile[:-4]
        else:
            out = args.infile + ".dec"
        pw = _get_password(args, confirm=False)
        try:
            decrypt_file(args.infile, out, pw, tracer=tracer)
        except ValueError as e:
            print(f"Fehler: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Entschlüsselt: {args.infile} -> {out}")

    elif args.cmd == "demo":
        _demo()

    else:   # "selftest" oder kein Kommando -> Standardverhalten
        print("=== AES-Selbsttest (FIPS 197) ===")
        _selftest()
        if args.cmd is None:
            _demo()


if __name__ == "__main__":
    main()
