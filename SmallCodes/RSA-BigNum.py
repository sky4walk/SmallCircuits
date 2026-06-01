"""
bignum.py – Beliebig große Ganzzahlen + RSA, alles in einer Datei.

Verwendung:
    from bignum import BigInt, FixedInt
    from bignum import gcd, mod_inverse, is_prime, random_prime
    from bignum import generate_keypair, encrypt, decrypt, sign, verify

Schnellbeispiel RSA:
    pub, priv = generate_keypair(bits=512)
    c = encrypt(BigInt(42), pub)
    print(decrypt(c, priv))   # → 42
"""

from __future__ import annotations

import math
import os
import random as _random
from dataclasses import dataclass
from typing import List, Union


# ============================================================================
#  TEIL 1 – INTERNE LIMB-ARITHMETIK
#  Zahlen werden als Listen von Ziffern zur Basis 10_000 gespeichert
#  (little-endian, d.h. niedrigstwertiges Element zuerst).
# ============================================================================

BASE       = 10_000   # 10^4
BASE_DIGITS = 4       # Dezimalstellen pro Limb

Numeric = Union["BigInt", int, str]


def _trim(limbs: List[int]) -> List[int]:
    """Entferne führende Nullen; ergibt mindestens [0]."""
    while len(limbs) > 1 and limbs[-1] == 0:
        limbs.pop()
    return limbs


def _cmp_limbs(a: List[int], b: List[int]) -> int:
    """Vergleich zweier positiver Limb-Listen. Gibt -1, 0 oder 1 zurück."""
    if len(a) != len(b):
        return 1 if len(a) > len(b) else -1
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            return 1 if x > y else -1
    return 0


def _add_limbs(a: List[int], b: List[int]) -> List[int]:
    result, carry = [], 0
    for i in range(max(len(a), len(b))):
        s = carry + (a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0)
        result.append(s % BASE)
        carry = s // BASE
    if carry:
        result.append(carry)
    return result


def _sub_limbs(a: List[int], b: List[int]) -> List[int]:
    """a - b, setzt voraus |a| >= |b|."""
    result, borrow = [], 0
    for i in range(len(a)):
        d = a[i] - borrow - (b[i] if i < len(b) else 0)
        if d < 0:
            d += BASE
            borrow = 1
        else:
            borrow = 0
        result.append(d)
    return _trim(result)


def _mul_limbs(a: List[int], b: List[int]) -> List[int]:
    result = [0] * (len(a) + len(b))
    for i, ai in enumerate(a):
        carry = 0
        for j, bj in enumerate(b):
            cur = result[i + j] + ai * bj + carry
            result[i + j] = cur % BASE
            carry = cur // BASE
        if carry:
            result[i + len(b)] += carry
    return _trim(result)


def _divmod_limbs(a: List[int], b: List[int]):
    """
    Ganzzahldivision: gibt (quotient_limbs, remainder_limbs) zurück.
    Klassischer Long-Division-Algorithmus (Knuth D) mit binärer Suche.
    """
    if _cmp_limbs(a, b) < 0:
        return [0], list(a)

    quotient  = [0] * len(a)
    remainder: List[int] = []

    for i in reversed(range(len(a))):
        remainder = [a[i]] + remainder
        _trim(remainder)
        lo, hi = 0, BASE - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if _cmp_limbs(_mul_limbs(b, [mid]), remainder) <= 0:
                lo = mid
            else:
                hi = mid - 1
        quotient[i] = lo
        if lo:
            remainder = _sub_limbs(remainder, _mul_limbs(b, [lo]))

    return _trim(quotient), _trim(remainder)


def _from_int(n: int) -> List[int]:
    if n == 0:
        return [0]
    limbs = []
    while n:
        limbs.append(n % BASE)
        n //= BASE
    return limbs


def _from_str(s: str) -> List[int]:
    pad = (-len(s)) % BASE_DIGITS
    s = "0" * pad + s
    limbs = []
    for i in range(len(s), 0, -BASE_DIGITS):
        limbs.append(int(s[i - BASE_DIGITS:i]))
    return _trim(limbs)


def _to_str(limbs: List[int]) -> str:
    if not limbs or limbs == [0]:
        return "0"
    parts = [str(limbs[-1])]
    for lmb in reversed(limbs[:-1]):
        parts.append(f"{lmb:0{BASE_DIGITS}d}")
    return "".join(parts)


# ============================================================================
#  TEIL 2 – BigInt  (öffentliche Klasse)
# ============================================================================

class BigInt:
    """
    Beliebig große vorzeichenbehaftete Ganzzahl.

    Erstellen:
        BigInt(42)
        BigInt("-123456789012345678901234567890")
        BigInt("0xFF", base=16)

    Operatoren: + - * // % ** == != < <= > >= abs() neg()
    """

    __slots__ = ("_limbs", "_negative")

    # ------------------------------------------------------------------ init

    def __init__(self, value: Numeric = 0, *, base: int = 10):
        if isinstance(value, BigInt):
            self._limbs: List[int] = list(value._limbs)
            self._negative: bool   = value._negative
            return
        if isinstance(value, int):
            self._negative = value < 0
            self._limbs    = _from_int(abs(value))
            return
        if isinstance(value, str):
            s = value.strip()
            self._negative = s.startswith("-")
            s = s.lstrip("+-")
            if base != 10:
                self._limbs = _from_int(int(s, base))
            else:
                if not s.isdigit():
                    raise ValueError(f"Ungültiger Dezimalstring: {value!r}")
                self._limbs = _from_str(s)
            if self._limbs == [0]:
                self._negative = False
            return
        raise TypeError(f"Kann {type(value).__name__!r} nicht in BigInt konvertieren")

    @classmethod
    def _from_parts(cls, limbs: List[int], negative: bool) -> "BigInt":
        obj = object.__new__(cls)
        obj._limbs    = limbs
        obj._negative = negative if limbs != [0] else False
        return obj

    def _is_zero(self) -> bool:
        return self._limbs == [0]

    # ---------------------------------------------------------------- Ausgabe

    def __repr__(self) -> str:  return f"BigInt('{self}')"
    def __str__(self)  -> str:
        s = _to_str(self._limbs)
        return ("-" + s) if self._negative else s
    def __format__(self, spec: str) -> str:
        return format(str(self), spec)

    # ----------------------------------------------------------- Konvertierung

    def __int__(self) -> int:
        n = 0
        for limb in reversed(self._limbs):
            n = n * BASE + limb
        return -n if self._negative else n

    def __bool__(self) -> bool:
        return not self._is_zero()

    # ---------------------------------------------------------------- Betrag / Vorzeichen

    def __abs__(self)  -> "BigInt":
        return BigInt._from_parts(list(self._limbs), False)
    def __neg__(self)  -> "BigInt":
        if self._is_zero():
            return BigInt(0)
        return BigInt._from_parts(list(self._limbs), not self._negative)
    def __pos__(self)  -> "BigInt":
        return BigInt(self)

    # ----------------------------------------------------------- Vergleich

    def __eq__(self, other) -> bool:
        o = _coerce(other)
        return self._negative == o._negative and self._limbs == o._limbs
    def __lt__(self, other) -> bool:
        o = _coerce(other)
        if self._negative != o._negative:
            return self._negative
        cmp = _cmp_limbs(self._limbs, o._limbs)
        return (cmp < 0) if not self._negative else (cmp > 0)
    def __le__(self, other) -> bool: return self == other or self < other
    def __gt__(self, other) -> bool: return not self <= other
    def __ge__(self, other) -> bool: return not self < other
    def __ne__(self, other) -> bool: return not self == other
    def __hash__(self)      -> int:  return hash(str(self))

    # ----------------------------------------------------------- Addition

    def __add__(self, other) -> "BigInt":
        b = _coerce(other)
        if self._negative == b._negative:
            return BigInt._from_parts(_add_limbs(self._limbs, b._limbs), self._negative)
        cmp = _cmp_limbs(self._limbs, b._limbs)
        if cmp == 0:
            return BigInt(0)
        if cmp > 0:
            return BigInt._from_parts(_sub_limbs(self._limbs, b._limbs), self._negative)
        return BigInt._from_parts(_sub_limbs(b._limbs, self._limbs), b._negative)
    def __radd__(self, other) -> "BigInt": return _coerce(other) + self

    # --------------------------------------------------------- Subtraktion

    def __sub__(self, other)  -> "BigInt": return self + (-_coerce(other))
    def __rsub__(self, other) -> "BigInt": return _coerce(other) - self

    # ------------------------------------------------------- Multiplikation

    def __mul__(self, other) -> "BigInt":
        b = _coerce(other)
        return BigInt._from_parts(_mul_limbs(self._limbs, b._limbs), self._negative ^ b._negative)
    def __rmul__(self, other) -> "BigInt": return _coerce(other) * self

    # ----------------------------------------------------------- Division

    def __floordiv__(self, other)  -> "BigInt":
        q, _ = divmod(self, other); return q
    def __rfloordiv__(self, other) -> "BigInt": return _coerce(other) // self
    def __mod__(self, other)       -> "BigInt":
        _, r = divmod(self, other); return r
    def __rmod__(self, other)      -> "BigInt": return _coerce(other) % self

    def __divmod__(self, other):
        b = _coerce(other)
        if b._is_zero():
            raise ZeroDivisionError("BigInt Division durch Null")
        q_limbs, r_limbs = _divmod_limbs(self._limbs, b._limbs)
        q = BigInt._from_parts(q_limbs, self._negative ^ b._negative)
        r = BigInt._from_parts(r_limbs, self._negative)
        if r and r._negative != b._negative:
            r = r + b
            q = q - BigInt(1)
        return q, r

    def __rdivmod__(self, other):    return divmod(_coerce(other), self)
    def __truediv__(self, other)  -> "BigInt": return self.__floordiv__(other)
    def __rtruediv__(self, other) -> "BigInt": return _coerce(other).__floordiv__(self)

    # ------------------------------------------------------------ Potenz

    def __pow__(self, exp, mod=None) -> "BigInt":
        e = _coerce(exp)
        if e._negative:
            raise ValueError("Negativer Exponent nicht unterstützt")
        if mod is not None:
            return _pow_mod(self, e, _coerce(mod))
        return _pow_fast(self, e)
    def __rpow__(self, other): return _coerce(other) ** self

    # ------------------------------------------------------------ Hilfsmethoden

    def bit_length(self) -> int:
        """Anzahl der benötigten Bits."""
        if self._is_zero():
            return 0
        n = 0
        for limb in reversed(self._limbs):
            n = n * BASE + limb
        return n.bit_length()

    def digits(self) -> int:
        """Anzahl der Dezimalstellen."""
        return len(str(self).lstrip("-"))


# ============================================================================
#  TEIL 3 – FixedInt  (BigInt mit Größenbeschränkung)
# ============================================================================

class FixedInt:
    """
    Vorzeichenbehaftete Ganzzahl mit fixer Maximalbreite.

    FixedInt(200, max_bits=8)     → max 8 Bit
    FixedInt("999", max_digits=3) → max 3 Dezimalstellen

    Jede Operation wirft OverflowError wenn das Ergebnis die Grenze überschreitet.
    """

    def __init__(self, value: Numeric = 0, *, max_bits: int | None = None, max_digits: int | None = None):
        if max_bits is None and max_digits is None:
            max_bits = 256
        if max_bits is not None and max_digits is not None:
            raise ValueError("Nur eines von max_bits oder max_digits angeben")
        self._max_bits   = max_bits
        self._max_digits = max_digits
        self._inner      = BigInt(value) if not isinstance(value, BigInt) else value
        self._check(self._inner)

    def _check(self, v: BigInt) -> None:
        if self._max_bits is not None:
            bl = abs(v).bit_length()
            if bl > self._max_bits:
                raise OverflowError(f"Ergebnis benötigt {bl} Bits, Maximum ist {self._max_bits}")
        else:
            d = abs(v).digits()
            if d > self._max_digits:
                raise OverflowError(f"Ergebnis hat {d} Stellen, Maximum ist {self._max_digits}")

    def _wrap(self, result: BigInt) -> "FixedInt":
        return FixedInt(result, max_bits=self._max_bits, max_digits=self._max_digits)

    def __repr__(self) -> str:
        limit = f"max_bits={self._max_bits}" if self._max_bits else f"max_digits={self._max_digits}"
        return f"FixedInt('{self._inner}', {limit})"
    def __str__(self)  -> str: return str(self._inner)
    def __int__(self)  -> int: return int(self._inner)
    def __bool__(self) -> bool: return bool(self._inner)

    def _ci(self, other) -> BigInt:
        return other._inner if isinstance(other, FixedInt) else _coerce(other)

    def __add__(self, o):       return self._wrap(self._inner + self._ci(o))
    def __radd__(self, o):      return self._wrap(_coerce(o) + self._inner)
    def __sub__(self, o):       return self._wrap(self._inner - self._ci(o))
    def __rsub__(self, o):      return self._wrap(_coerce(o) - self._inner)
    def __mul__(self, o):       return self._wrap(self._inner * self._ci(o))
    def __rmul__(self, o):      return self._wrap(_coerce(o) * self._inner)
    def __floordiv__(self, o):  return self._wrap(self._inner // self._ci(o))
    def __rfloordiv__(self, o): return self._wrap(_coerce(o) // self._inner)
    def __truediv__(self, o):   return self.__floordiv__(o)
    def __mod__(self, o):       return self._wrap(self._inner % self._ci(o))
    def __rmod__(self, o):      return self._wrap(_coerce(o) % self._inner)
    def __pow__(self, e, m=None):
        return self._wrap(pow(self._inner, self._ci(e), self._ci(m) if m else None))
    def __neg__(self):  return self._wrap(-self._inner)
    def __abs__(self):  return self._wrap(abs(self._inner))
    def __eq__(self, o): return self._inner == self._ci(o)
    def __lt__(self, o): return self._inner < self._ci(o)
    def __le__(self, o): return self._inner <= self._ci(o)
    def __gt__(self, o): return self._inner > self._ci(o)
    def __ge__(self, o): return self._inner >= self._ci(o)
    def __ne__(self, o): return self._inner != self._ci(o)
    def __hash__(self):  return hash(self._inner)


# ============================================================================
#  TEIL 4 – Hilfsfunktionen (intern)
# ============================================================================

def _coerce(x) -> BigInt:
    return x if isinstance(x, BigInt) else BigInt(x)


def _pow_fast(base: BigInt, exp: BigInt) -> BigInt:
    """Schnelle Exponentiation durch Quadrieren (Square-and-Multiply)."""
    result = BigInt(1)
    b      = BigInt(base)
    e_int  = int(exp)
    while e_int > 0:
        if e_int & 1:
            result = result * b
        b      = b * b
        e_int >>= 1
    return result


def _pow_mod(base: BigInt, exp: BigInt, mod: BigInt) -> BigInt:
    result = BigInt(1)
    b      = base % mod
    e_int  = int(exp)
    while e_int > 0:
        if e_int & 1:
            result = (result * b) % mod
        b      = (b * b) % mod
        e_int >>= 1
    return result


# ============================================================================
#  TEIL 5 – ZAHLENTHEORIE  (gcd, mod_inverse, Jacobi, Miller-Rabin, ...)
# ============================================================================

def gcd(a: Numeric, b: Numeric) -> BigInt:
    """
    Größter gemeinsamer Teiler (Euklidischer Algorithmus).

        gcd(12, 8)  → 4
        gcd(0, 5)   → 5
    """
    a, b = abs(_coerce(a)), abs(_coerce(b))
    while b:
        a, b = b, a % b
    return a


def extended_gcd(a: Numeric, b: Numeric) -> tuple[BigInt, BigInt, BigInt]:
    """
    Erweiterter Euklidischer Algorithmus.

    Gibt (g, x, y) zurück sodass:  a·x + b·y = g = gcd(a, b)

        g, x, y = extended_gcd(3, 11)   # g=1, x=4, y=-1
    """
    a, b = _coerce(a), _coerce(b)
    old_r, r     = a,        b
    old_s, s     = BigInt(1), BigInt(0)
    old_t, t     = BigInt(0), BigInt(1)
    while not r._is_zero():
        q        = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    return old_r, old_s, old_t


def mod_inverse(a: Numeric, m: Numeric) -> BigInt:
    """
    Modulares Inverses von a modulo m.

    Gibt x zurück sodass:  a·x ≡ 1 (mod m)
    Wirft ValueError wenn gcd(a, m) ≠ 1.

        mod_inverse(3, 11)          → 4      (3·4 = 12 ≡ 1 mod 11)
        mod_inverse(65537, phi_n)   → privater RSA-Schlüssel d
    """
    a, m = _coerce(a), _coerce(m)
    if m <= BigInt(1):
        raise ValueError("Modulus muss > 1 sein")
    g, x, _ = extended_gcd(a % m, m)
    if g != BigInt(1):
        raise ValueError(f"Inverses existiert nicht: gcd({a}, {m}) = {g}")
    return x % m


def jacobi(a: Numeric, n: Numeric) -> int:
    """
    Jacobi-Symbol (a/n).  n muss positiv und ungerade sein.

    Gibt -1, 0 oder 1 zurück.
    Verallgemeinerung des Legendre-Symbols; Grundlage für den Lucas-Primtest.
    """
    a, n = _coerce(a), _coerce(n)
    if n <= BigInt(0) or n % BigInt(2) == BigInt(0):
        raise ValueError("n muss eine positive ungerade Zahl sein")
    a      = a % n
    result = 1
    while a != BigInt(0):
        while a % BigInt(2) == BigInt(0):
            a       = a // BigInt(2)
            n_mod8  = int(n % BigInt(8))
            if n_mod8 in (3, 5):
                result = -result
        a, n = n, a
        if int(a % BigInt(4)) == 3 and int(n % BigInt(4)) == 3:
            result = -result
        a = a % n
    return result if n == BigInt(1) else 0


# Deterministisch korrekte Witness-Mengen für n < 2^64
# Quelle: Sorenson & Webster (2015), Wikipedia: Miller–Rabin primality test
_DETERMINISTIC_WITNESSES = [
    (3_215_031_751,             [2, 3, 5, 7]),
    (3_474_749_660_383,         [2, 3, 5, 7, 11, 13]),
    (341_550_071_728_321,       [2, 3, 5, 7, 11, 13, 17]),
    (3_825_123_056_546_413_051, [2, 3, 5, 7, 11, 13, 17, 19, 23]),
    (2**64,                     [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]),
]


def miller_rabin(n: Numeric, rounds: int = 20) -> bool:
    """
    Miller-Rabin Primtest.

    Für n < 2^64 : deterministisch korrekt.
    Für n ≥ 2^64 : probabilistisch; Fehlerwahrscheinlichkeit ≤ 4^(-rounds).

    rounds=20 → Fehlerwahrscheinlichkeit < 10^(-12)   (Standard für RSA)
    rounds=40 → für maximale Sicherheit
    """
    n = _coerce(n)
    if n < BigInt(2):   return False
    if n == BigInt(2) or n == BigInt(3): return True
    if n % BigInt(2) == BigInt(0):       return False

    # n-1 = 2^r · d  mit d ungerade
    n_minus_1 = n - BigInt(1)
    r, d = 0, n_minus_1
    while d % BigInt(2) == BigInt(0):
        d = d // BigInt(2)
        r += 1

    n_int = int(n)

    if n_int < _DETERMINISTIC_WITNESSES[-1][0]:
        for limit, ws in _DETERMINISTIC_WITNESSES:
            if n_int < limit:
                witness_list = [BigInt(w) for w in ws if w < n_int]
                break
    else:
        witness_list = [BigInt(_random.randint(2, n_int - 2)) for _ in range(rounds)]

    for a in witness_list:
        if a >= n - BigInt(1):
            continue
        x = pow(a, d, n)
        if x == BigInt(1) or x == n_minus_1:
            continue
        composite = True
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n_minus_1:
                composite = False
                break
        if composite:
            return False
    return True


def _sieve_small(limit: int) -> list[int]:
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    return [i for i in range(2, limit + 1) if sieve[i]]


def is_prime(n: Numeric, rounds: int = 20) -> bool:
    """
    Vollständiger Primtest: Probedivision + Miller-Rabin.

        is_prime(97)               → True
        is_prime(BigInt(2)**127-1) → True   (Mersenne-Primzahl)
        is_prime(100)              → False
    """
    n = _coerce(n)
    if n < BigInt(2):            return False
    if n == BigInt(2):           return True
    if n % BigInt(2) == BigInt(0): return False
    if n == BigInt(3):           return True
    if n % BigInt(3) == BigInt(0): return False

    for p in _sieve_small(500):
        bp = BigInt(p)
        if n == bp:           return True
        if n % bp == BigInt(0): return False

    return miller_rabin(n, rounds)


class _CryptoRandom:
    """Wrapper um os.urandom für kryptografisch sichere Zufallszahlen."""
    def randbytes(self, n: int) -> bytes:
        return os.urandom(n)
    def randint(self, a: int, b: int) -> int:
        span     = b - a + 1
        byte_len = (span.bit_length() + 7) // 8
        while True:
            r = int.from_bytes(os.urandom(byte_len), "big")
            if r < span:
                return a + r


def random_prime(bits: int, rng=None) -> BigInt:
    """
    Zufällige Primzahl mit exakt `bits` Bits (kryptografisch sicher).

    Oberstes + unterstes Bit werden auf 1 gesetzt (garantierte Länge + ungerade).

        p = random_prime(512)
        q = random_prime(512)
        n = p * q              # 1024-Bit RSA-Modul
    """
    if bits < 2:
        raise ValueError("bits muss mindestens 2 sein")
    _rng = rng if rng is not None else _CryptoRandom()
    while True:
        raw    = _rng.randbytes((bits + 7) // 8)
        n_int  = int.from_bytes(raw, "big")
        n_int >>= (8 * ((bits + 7) // 8) - bits)
        n_int |=  (1 << (bits - 1))   # oberstes Bit
        n_int |=  1                    # unterstes Bit (ungerade)
        candidate = BigInt(n_int)
        if is_prime(candidate):
            return candidate


# ============================================================================
#  TEIL 6 – RSA
# ============================================================================

@dataclass(frozen=True)
class PublicKey:
    """
    RSA Public Key.

    n : Modulus  (n = p·q)
    e : Öffentlicher Exponent (Standard: 65537)
    """
    n: BigInt
    e: BigInt

    def __post_init__(self):
        object.__setattr__(self, "n", _coerce(self.n))
        object.__setattr__(self, "e", _coerce(self.e))

    def __str__(self)  -> str:
        return f"PublicKey(n={str(self.n)[:30]}…, e={self.e}, bits={self.n.bit_length()})"
    def __repr__(self) -> str: return str(self)


@dataclass(frozen=True)
class PrivateKey:
    """
    RSA Private Key.

    n : Modulus
    d : Privater Exponent
    p : Erster Primfaktor  (optional, aktiviert CRT-Optimierung)
    q : Zweiter Primfaktor (optional, aktiviert CRT-Optimierung)
    """
    n: BigInt
    d: BigInt
    p: BigInt | None = None
    q: BigInt | None = None

    def __post_init__(self):
        object.__setattr__(self, "n", _coerce(self.n))
        object.__setattr__(self, "d", _coerce(self.d))
        if self.p is not None: object.__setattr__(self, "p", _coerce(self.p))
        if self.q is not None: object.__setattr__(self, "q", _coerce(self.q))

    def public_key(self, e: Numeric = 65537) -> PublicKey:
        return PublicKey(self.n, _coerce(e))

    def __str__(self)  -> str:
        return f"PrivateKey(n={str(self.n)[:30]}…, bits={self.n.bit_length()})"
    def __repr__(self) -> str: return str(self)


def generate_keypair(bits: int = 2048, e: Numeric = 65537) -> tuple[PublicKey, PrivateKey]:
    """
    Erzeugt ein RSA-Schlüsselpaar.

        bits : Bitlänge des Modulus n = p·q (Standard: 2048)
        e    : Öffentlicher Exponent       (Standard: 65537)

    Gibt (PublicKey, PrivateKey) zurück.

        pub, priv = generate_keypair(bits=512)   # schnell für Tests
        pub, priv = generate_keypair(bits=2048)  # RSA-2048 (empfohlen)

    Dauer (grob):  512 Bit < 1 s  |  1024 Bit ~2 s  |  2048 Bit ~15 s
    """
    e    = _coerce(e)
    half = bits // 2
    while True:
        p = random_prime(half)
        q = random_prime(half)
        if p == q:
            continue
        n   = p * q
        phi = (p - BigInt(1)) * (q - BigInt(1))
        if gcd(e, phi) != BigInt(1):
            continue
        d    = mod_inverse(e, phi)
        return PublicKey(n, e), PrivateKey(n, d, p, q)


def encrypt(message: Numeric, pub: PublicKey) -> BigInt:
    """
    RSA-Verschlüsselung:  c = m^e mod n

    message muss 0 ≤ m < n sein.

        c = encrypt(BigInt(42), pub)
    """
    m = _coerce(message)
    if m < BigInt(0) or m >= pub.n:
        raise ValueError(f"Nachricht muss 0 ≤ m < n sein (n hat {pub.n.bit_length()} Bits)")
    return pow(m, pub.e, pub.n)


def decrypt(ciphertext: Numeric, priv: PrivateKey) -> BigInt:
    """
    RSA-Entschlüsselung:  m = c^d mod n

    Nutzt automatisch CRT (Chinesischer Restsatz) wenn p und q bekannt sind (~4× schneller).

        m = decrypt(c, priv)
    """
    c = _coerce(ciphertext)
    if priv.p is not None and priv.q is not None:
        return _rsa_crt(c, priv)
    return pow(c, priv.d, priv.n)


def _rsa_crt(c: BigInt, priv: PrivateKey) -> BigInt:
    """Garner's CRT-Algorithmus für schnelle RSA-Entschlüsselung."""
    p, q = priv.p, priv.q
    dp   = priv.d % (p - BigInt(1))
    dq   = priv.d % (q - BigInt(1))
    mp   = pow(c, dp, p)
    mq   = pow(c, dq, q)
    h    = (mod_inverse(q, p) * (mp - mq)) % p
    return (mq + q * h) % priv.n


def sign(message: Numeric, priv: PrivateKey) -> BigInt:
    """
    RSA-Signatur:  sig = m^d mod n

    In der Praxis sollte `message` ein Hash-Wert sein (SHA-256 etc.).

        import hashlib
        h   = int.from_bytes(hashlib.sha256(b"Dokument").digest(), "big")
        sig = sign(BigInt(h), priv)
    """
    m = _coerce(message)
    if m < BigInt(0) or m >= priv.n:
        raise ValueError("Nachricht muss 0 ≤ m < n sein")
    return decrypt(m, priv)


def verify(message: Numeric, signature: Numeric, pub: PublicKey) -> bool:
    """
    Signaturverifikation:  prüft ob sig^e mod n == message.

        ok = verify(BigInt(h), sig, pub)
        print("Gültig" if ok else "Ungültig")
    """
    return encrypt(_coerce(signature), pub) == _coerce(message)


def text_to_int(text: str) -> BigInt:
    """Konvertiert einen UTF-8-String in eine BigInt-Zahl."""
    return BigInt(int.from_bytes(text.encode("utf-8"), "big"))


def int_to_text(n: Numeric) -> str:
    """Konvertiert eine BigInt-Zahl zurück in einen UTF-8-String."""
    n_int    = int(_coerce(n))
    byte_len = (n_int.bit_length() + 7) // 8
    return n_int.to_bytes(byte_len, "big").decode("utf-8")


# ============================================================================
#  Kurzübersicht aller öffentlichen Namen
# ============================================================================

__all__ = [
    # Typen
    "BigInt", "FixedInt", "PublicKey", "PrivateKey",
    # Zahlentheorie
    "gcd", "extended_gcd", "mod_inverse", "jacobi",
    "miller_rabin", "is_prime", "random_prime",
    # RSA
    "generate_keypair", "encrypt", "decrypt", "sign", "verify",
    "text_to_int", "int_to_text",
]


# ============================================================================
#  TEIL 7 – BEISPIELE
#  Ausführen:  python bignum.py demo
# ============================================================================

def _run_demo() -> None:
    import hashlib

    SEP  = "─" * 60
    SEP2 = "═" * 60

    print(SEP2)
    print("  bignum.py  –  Demonstrations-Skript")
    print(SEP2)

    # ------------------------------------------------------------------
    print("\n【 1 】 BigInt – Grundrechenarten")
    print(SEP)
    a = BigInt("123456789012345678901234567890")
    b = BigInt("987654321098765432109876543210")
    print(f"  a   = {a}")
    print(f"  b   = {b}")
    print(f"  a+b = {a + b}")
    print(f"  b-a = {b - a}")
    print(f"  a*b = {a * b}")
    print(f"  b//a= {b // a}")
    print(f"  b%a = {b % a}")
    print(f"  2^200 = {BigInt(2) ** 200}")
    print(f"  Gemischt mit int: BigInt(100) + 42 = {BigInt(100) + 42}")

    # ------------------------------------------------------------------
    print("\n【 2 】 FixedInt – Größenbeschränkung")
    print(SEP)
    fi = FixedInt(200, max_bits=8)
    print(f"  FixedInt(200, max_bits=8) + 55 = {fi + 55}")
    try:
        _ = fi * FixedInt(2, max_bits=8)
    except OverflowError as e:
        print(f"  200 * 2 → OverflowError: {e}")

    fd = FixedInt("999", max_digits=3)
    try:
        _ = fd + FixedInt(1, max_digits=3)
    except OverflowError as e:
        print(f"  999 + 1 → OverflowError: {e}")

    # ------------------------------------------------------------------
    print("\n【 3 】 Zahlentheorie")
    print(SEP)
    print(f"  gcd(252, 105)        = {gcd(252, 105)}")
    g, x, y = extended_gcd(3, 11)
    print(f"  extended_gcd(3, 11)  = g={g}, x={x}, y={y}  →  3·{x} + 11·{y} = {g}")
    print(f"  mod_inverse(3, 11)   = {mod_inverse(3, 11)}   (3·4 = 12 ≡ 1 mod 11)")
    print(f"  jacobi(4, 7)         = {jacobi(4, 7)}   (4 ist QR mod 7)")
    print(f"  jacobi(3, 7)         = {jacobi(3, 7)}  (3 ist kein QR mod 7)")
    print(f"  is_prime(97)         = {is_prime(97)}")
    print(f"  is_prime(100)        = {is_prime(100)}")
    mersenne = BigInt(2) ** 127 - BigInt(1)
    print(f"  is_prime(2^127 - 1)  = {is_prime(mersenne)}  (Mersenne-Primzahl M127)")
    p64 = random_prime(64)
    print(f"  random_prime(64)     = {p64}  ({p64.bit_length()} Bit)")

    # ------------------------------------------------------------------
    print("\n【 4 】 RSA – Schlüsselgenerierung (512 Bit)")
    print(SEP)
    print("  Erzeuge Schlüsselpaar …")
    pub, priv = generate_keypair(bits=512)
    print(f"  {pub}")
    print(f"  {priv}")
    print(f"  p = {str(priv.p)[:40]}…")
    print(f"  q = {str(priv.q)[:40]}…")
    phi = (priv.p - BigInt(1)) * (priv.q - BigInt(1))
    check = (pub.e * priv.d) % phi
    print(f"  e·d mod φ(n) = {check}  ✓" if check == BigInt(1) else f"  FEHLER: e·d mod φ(n) = {check}")

    # ------------------------------------------------------------------
    print("\n【 5 】 RSA – Verschlüsselung & Entschlüsselung")
    print(SEP)
    message = BigInt(42)
    c       = encrypt(message, pub)
    m_back  = decrypt(c, priv)
    print(f"  Nachricht (m)    = {message}")
    print(f"  Verschlüsselt (c)= {str(c)[:50]}…")
    print(f"  Entschlüsselt    = {m_back}  {'✓' if m_back == message else '✗'}")

    # ------------------------------------------------------------------
    print("\n【 6 】 RSA – Text verschlüsseln")
    print(SEP)
    text = "Hallo, Welt!"
    m    = text_to_int(text)
    c    = encrypt(m, pub)
    back = int_to_text(decrypt(c, priv))
    print(f"  Originaltext  : {text!r}")
    print(f"  Als Zahl      : {m}")
    print(f"  Zurück        : {back!r}  {'✓' if back == text else '✗'}")

    # ------------------------------------------------------------------
    print("\n【 7 】 RSA – Digitale Signatur")
    print(SEP)
    dokument = b"Wichtiger Vertrag, Datum 2025-01-01"
    h_int    = int.from_bytes(hashlib.sha256(dokument).digest(), "big")
    h        = BigInt(h_int)
    sig      = sign(h, priv)
    ok       = verify(h, sig, pub)
    tampered = verify(h + BigInt(1), sig, pub)
    print(f"  Dokument      : {dokument.decode()!r}")
    print(f"  SHA-256 (hex) : {h_int:064x}")
    print(f"  Signatur gültig        : {ok}  ✓")
    print(f"  Signatur nach Änderung : {tampered}  ✓")

    print("\n" + SEP2)
    print("  Demo abgeschlossen.")
    print(SEP2)


# ============================================================================
#  TEIL 8 – UNIT-TESTS
#  Ausführen:  python bignum.py test
#          oder: python -m unittest bignum
# ============================================================================

import unittest as _unittest

BIG_A = "123456789012345678901234567890"
BIG_B = "987654321098765432109876543210"


class TestBigIntBasic(_unittest.TestCase):

    def test_zero(self):
        self.assertEqual(str(BigInt(0)), "0")
        self.assertEqual(str(BigInt("0")), "0")
        self.assertFalse(BigInt(0))

    def test_positive(self):
        n = BigInt("42")
        self.assertEqual(str(n), "42")
        self.assertTrue(n)

    def test_negative(self):
        self.assertEqual(str(BigInt("-42")), "-42")

    def test_negative_zero_normalised(self):
        n = BigInt("-0")
        self.assertEqual(str(n), "0")
        self.assertFalse(n._negative)

    def test_from_int(self):
        self.assertEqual(str(BigInt(1_000_000)), "1000000")
        self.assertEqual(str(BigInt(-999)), "-999")

    def test_int_roundtrip(self):
        for v in [0, 1, -1, 10**30, -(10**30)]:
            self.assertEqual(int(BigInt(v)), v)

    def test_repr(self):
        self.assertEqual(repr(BigInt(7)), "BigInt('7')")


class TestBigIntAddition(_unittest.TestCase):

    def _check(self, a, b):
        self.assertEqual(str(BigInt(a) + BigInt(b)), str(a + b))

    def test_small_positive(self):  self._check(12, 34)
    def test_large_positive(self):  self._check(int(BIG_A), int(BIG_B))
    def test_pos_plus_neg(self):    self._check(int(BIG_A), -int(BIG_B))
    def test_neg_plus_pos(self):    self._check(-int(BIG_A), int(BIG_B))
    def test_both_negative(self):   self._check(-int(BIG_A), -int(BIG_B))

    def test_cancel(self):
        n = BigInt(BIG_A)
        self.assertEqual(n + (-n), BigInt(0))

    def test_radd(self):
        self.assertEqual(1 + BigInt(2), BigInt(3))


class TestBigIntSubtraktion(_unittest.TestCase):

    def _check(self, a, b):
        self.assertEqual(str(BigInt(a) - BigInt(b)), str(a - b))

    def test_simple(self):   self._check(100, 42)
    def test_negative(self): self._check(42, 100)
    def test_large(self):    self._check(int(BIG_B), int(BIG_A))

    def test_rsub(self):
        self.assertEqual(10 - BigInt(3), BigInt(7))


class TestBigIntMultiplikation(_unittest.TestCase):

    def _check(self, a, b):
        self.assertEqual(str(BigInt(a) * BigInt(b)), str(a * b))

    def test_small(self):    self._check(6, 7)
    def test_large(self):    self._check(int(BIG_A), int(BIG_B))
    def test_neg_pos(self):  self._check(-int(BIG_A), int(BIG_B))
    def test_both_neg(self): self._check(-int(BIG_A), -int(BIG_B))
    def test_by_zero(self):  self._check(int(BIG_A), 0)

    def test_rmul(self):
        self.assertEqual(3 * BigInt(7), BigInt(21))


class TestBigIntDivision(_unittest.TestCase):

    def _check(self, a, b):
        q, r   = divmod(BigInt(a), BigInt(b))
        pq, pr = divmod(a, b)
        self.assertEqual(str(q), str(pq), f"divmod({a},{b}) Quotient")
        self.assertEqual(str(r), str(pr), f"divmod({a},{b}) Rest")

    def test_simple(self):       self._check(100, 7)
    def test_exact(self):        self._check(100, 5)
    def test_large(self):        self._check(int(BIG_B), int(BIG_A))
    def test_neg_divisor(self):  self._check(100, -7)
    def test_neg_dividend(self): self._check(-100, 7)
    def test_both_neg(self):     self._check(-100, -7)

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            BigInt(1) // BigInt(0)

    def test_truediv_alias(self):
        self.assertEqual(BigInt(10) / BigInt(3), BigInt(10) // BigInt(3))


class TestBigIntPotenz(_unittest.TestCase):

    def _check(self, base, exp):
        self.assertEqual(str(BigInt(base) ** BigInt(exp)), str(base ** exp))

    def test_small(self):    self._check(2, 10)
    def test_large(self):    self._check(2, 100)
    def test_zero_exp(self): self._check(999, 0)
    def test_one_exp(self):  self._check(999, 1)

    def test_pow_mod(self):
        self.assertEqual(
            str(pow(BigInt(3), BigInt(1000), BigInt(997))),
            str(pow(3, 1000, 997)),
        )


class TestBigIntVergleich(_unittest.TestCase):

    def test_eq(self):
        self.assertEqual(BigInt(42), BigInt(42))
        self.assertNotEqual(BigInt(42), BigInt(43))

    def test_lt(self):
        self.assertLess(BigInt(-1), BigInt(0))
        self.assertLess(BigInt(1), BigInt(2))
        self.assertLess(BigInt(BIG_A), BigInt(BIG_B))

    def test_gt(self):
        self.assertGreater(BigInt(BIG_B), BigInt(BIG_A))

    def test_coercion_with_int(self):
        self.assertEqual(BigInt(5), 5)
        self.assertLess(BigInt(3), 10)


class TestFixedInt(_unittest.TestCase):

    def test_creation(self):
        self.assertEqual(str(FixedInt(100, max_bits=8)), "100")

    def test_overflow_on_creation(self):
        with self.assertRaises(OverflowError):
            FixedInt(256, max_bits=8)

    def test_overflow_on_operation(self):
        with self.assertRaises(OverflowError):
            FixedInt(200, max_bits=8) * FixedInt(2, max_bits=8)

    def test_addition_ok(self):
        self.assertEqual(str(FixedInt(100, max_bits=8) + FixedInt(55, max_bits=8)), "155")

    def test_max_digits(self):
        with self.assertRaises(OverflowError):
            FixedInt("999", max_digits=3) + FixedInt(1, max_digits=3)

    def test_repr(self):
        self.assertIn("max_bits=16", repr(FixedInt(7, max_bits=16)))


class TestEdgeCases(_unittest.TestCase):

    def test_very_large_multiplication(self):
        a = BigInt("1" + "0" * 1000)
        self.assertEqual(str(a * a), "1" + "0" * 2000)

    def test_factorial_100(self):
        import math as _math
        result = BigInt(1)
        for i in range(2, 101):
            result = result * BigInt(i)
        self.assertEqual(str(result), str(_math.factorial(100)))

    def test_large_power(self):
        self.assertEqual(str(BigInt(2) ** 1000), str(2 ** 1000))

    def test_str_roundtrip(self):
        for s in [BIG_A, BIG_B, "-" + BIG_A, "0", "1"]:
            self.assertEqual(str(BigInt(s)), str(int(s)))


class TestGcd(_unittest.TestCase):

    def test_basic(self):
        self.assertEqual(gcd(12, 8), BigInt(4))
        self.assertEqual(gcd(100, 75), BigInt(25))

    def test_coprime(self):
        self.assertEqual(gcd(17, 13), BigInt(1))

    def test_zero(self):
        self.assertEqual(gcd(0, 5), BigInt(5))
        self.assertEqual(gcd(5, 0), BigInt(5))

    def test_negative(self):
        self.assertEqual(gcd(-12, 8), BigInt(4))

    def test_large(self):
        import math as _math
        a = BigInt(BIG_A)
        b = BigInt(BIG_B)
        self.assertEqual(int(gcd(a, b)), _math.gcd(int(a), int(b)))


class TestExtendedGcd(_unittest.TestCase):

    def test_basic(self):
        g, x, y = extended_gcd(3, 11)
        self.assertEqual(g, BigInt(1))
        self.assertEqual(BigInt(3) * x + BigInt(11) * y, g)

    def test_identity(self):
        g, x, y = extended_gcd(35, 15)
        self.assertEqual(g, BigInt(5))
        self.assertEqual(BigInt(35) * x + BigInt(15) * y, g)

    def test_large(self):
        a, b = BigInt("65537"), BigInt("3120")
        g, x, y = extended_gcd(a, b)
        self.assertEqual(a * x + b * y, g)


class TestModInverse(_unittest.TestCase):

    def test_basic(self):
        self.assertEqual(mod_inverse(3, 11), BigInt(4))

    def test_large_e(self):
        e, phi = BigInt(65537), BigInt(3120)
        d = mod_inverse(e % phi, phi)
        self.assertEqual((e * d) % phi, BigInt(1))

    def test_no_inverse(self):
        with self.assertRaises(ValueError):
            mod_inverse(4, 6)

    def test_roundtrip(self):
        for a, m in [(3, 7), (5, 11), (7, 13), (11, 17)]:
            inv = mod_inverse(a, m)
            self.assertEqual((BigInt(a) * inv) % BigInt(m), BigInt(1))


class TestJacobi(_unittest.TestCase):

    def test_one(self):
        for n in [3, 5, 7, 9, 11]:
            self.assertEqual(jacobi(1, n), 1)

    def test_quadratic_residue(self):
        self.assertEqual(jacobi(4, 7), 1)

    def test_non_residue(self):
        self.assertEqual(jacobi(3, 7), -1)

    def test_divisible(self):
        self.assertEqual(jacobi(3, 9), 0)


class TestMillerRabin(_unittest.TestCase):

    PRIMES     = [2, 3, 5, 7, 11, 97, 999_999_000_001, 2**31 - 1, 2**61 - 1]
    COMPOSITES = [1, 4, 6, 9, 15, 100, 2**32]
    CARMICHAEL = [561, 1105, 1729, 2465, 8911]

    def test_primes(self):
        for p in self.PRIMES:
            self.assertTrue(miller_rabin(BigInt(p)), f"{p} sollte prim sein")

    def test_composites(self):
        for c in self.COMPOSITES:
            self.assertFalse(miller_rabin(BigInt(c)), f"{c} sollte zusammengesetzt sein")

    def test_carmichael(self):
        for c in self.CARMICHAEL:
            self.assertFalse(miller_rabin(BigInt(c)), f"Carmichael {c} sollte False sein")


class TestIsPrime(_unittest.TestCase):

    def test_small_primes(self):
        for p in [2, 3, 5, 7, 11, 13, 97]:
            self.assertTrue(is_prime(BigInt(p)))

    def test_small_composites(self):
        for c in [0, 1, 4, 6, 8, 9, 10, 25]:
            self.assertFalse(is_prime(BigInt(c)))

    def test_mersenne_prime(self):
        self.assertTrue(is_prime(BigInt(2) ** 127 - BigInt(1)))

    def test_large_composite(self):
        p = BigInt(2) ** 127 - BigInt(1)
        self.assertFalse(is_prime(p * BigInt(3)))


class TestRandomPrime(_unittest.TestCase):

    def test_bit_length_64(self):
        p = random_prime(64)
        self.assertEqual(p.bit_length(), 64)
        self.assertTrue(is_prime(p))

    def test_bit_length_128(self):
        p = random_prime(128)
        self.assertEqual(p.bit_length(), 128)
        self.assertTrue(is_prime(p))

    def test_is_odd(self):
        for _ in range(5):
            self.assertEqual(int(random_prime(64)) % 2, 1)

    def test_uniqueness(self):
        self.assertNotEqual(random_prime(64), random_prime(64))


class TestRSA(_unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pub, cls.priv = generate_keypair(bits=256)

    def test_key_properties(self):
        phi = (self.priv.p - BigInt(1)) * (self.priv.q - BigInt(1))
        self.assertEqual(self.priv.p * self.priv.q, self.priv.n)
        self.assertEqual((self.pub.e * self.priv.d) % phi, BigInt(1))

    def test_encrypt_decrypt_roundtrip(self):
        for m in [0, 1, 42, 12345, 99999]:
            bm = BigInt(m)
            self.assertEqual(decrypt(encrypt(bm, self.pub), self.priv), bm)

    def test_encrypt_changes_value(self):
        m = BigInt(42)
        self.assertNotEqual(encrypt(m, self.pub), m)

    def test_wrong_key_fails(self):
        _, priv2 = generate_keypair(bits=256)
        c = encrypt(BigInt(42), self.pub)
        self.assertNotEqual(decrypt(c, priv2), BigInt(42))

    def test_sign_verify(self):
        h   = BigInt(123456789)
        sig = sign(h, self.priv)
        self.assertTrue(verify(h, sig, self.pub))

    def test_tampered_sig_rejected(self):
        h   = BigInt(123456789)
        sig = sign(h, self.priv)
        self.assertFalse(verify(h, sig + BigInt(1), self.pub))

    def test_text_roundtrip(self):
        self.assertEqual(int_to_text(text_to_int("Hallo")), "Hallo")

    def test_text_encrypt_decrypt(self):
        m = text_to_int("RSA")
        if m < self.pub.n:
            self.assertEqual(int_to_text(decrypt(encrypt(m, self.pub), self.priv)), "RSA")

    def test_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            encrypt(self.pub.n, self.pub)
        with self.assertRaises(ValueError):
            encrypt(BigInt(-1), self.pub)


# ============================================================================
#  Einstiegspunkt
#  python bignum.py        → Demo
#  python bignum.py demo   → Demo
#  python bignum.py test   → Unit-Tests
# ============================================================================

if __name__ == "__main__":
    import sys as _sys

    cmd = _sys.argv[1].lower() if len(_sys.argv) > 1 else "demo"

    if cmd == "test":
        _sys.argv = [_sys.argv[0]]          # unittest mag keine fremden Argumente
        _unittest.main(verbosity=2)
    else:
        _run_demo()
