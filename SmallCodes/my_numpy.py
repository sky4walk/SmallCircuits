"""
my_numpy.py - Eigene Implementierung der in SmallGPT verwendeten NumPy-Funktionen

Zeigt was NumPy intern (vereinfacht) berechnet.
Nur mit Python-Standardfunktionen — kein externes Paket nötig.

WICHTIG: Diese Implementierung ist für Lernzwecke, nicht für Performance.
         Ein Forward Pass dauert damit deutlich länger als mit NumPy.

Verwendung in SmallGPT.py:
    import my_numpy as np   # <- eigene Implementierung (langsam, transparent)
    import numpy as np      # <- original NumPy (schnell, empfohlen)
"""

import math


# =============================================================================
# INTERNE HILFSKLASSE: n-dimensionales Array
# =============================================================================

class ndarray:
    """
    Vereinfachtes n-dimensionales Array.
    Speichert Daten als verschachtelte Python-Listen,
    kennt seine eigene Shape und unterstützt grundlegende Operationen.
    """

    def __init__(self, data, shape=None):
        if isinstance(data, ndarray):
            self.data = data.data
            self.shape = data.shape
        else:
            self.data = data
            self.shape = shape or _get_shape(data)

    def __repr__(self):
        return f"ndarray(shape={self.shape})"

    # Indexierung: arr[i] oder arr[i, j]
    def __getitem__(self, idx):
        if isinstance(idx, tuple):
            result = self.data
            for i in idx:
                if isinstance(i, ndarray):
                    # Fancy Indexing: arr[[1,2,3]]
                    result = [result[j] for j in _flatten(i.data)]
                else:
                    result = result[i]
            return ndarray(result) if isinstance(result, list) else result
        elif isinstance(idx, ndarray):
            # Fancy Indexing: arr[ndarray]
            flat = _flatten(idx.data)
            result = [self.data[i] for i in flat]
            new_shape = idx.shape + (self.shape[-1],) if len(self.shape) > 1 else idx.shape
            return ndarray(result, new_shape)
        elif isinstance(idx, slice):
            return ndarray(self.data[idx])
        else:
            result = self.data[idx]
            if isinstance(result, list):
                return ndarray(result)
            return result

    def __setitem__(self, idx, value):
        if isinstance(value, ndarray):
            value = value.data
        self.data[idx] = value

    # Arithmetik: element-wise
    def __add__(self, other):
        return _elementwise(self, other, lambda a, b: a + b)

    def __radd__(self, other):
        return _elementwise(other, self, lambda a, b: a + b)

    def __sub__(self, other):
        return _elementwise(self, other, lambda a, b: a - b)

    def __rsub__(self, other):
        return _elementwise(other, self, lambda a, b: a - b)

    def __mul__(self, other):
        return _elementwise(self, other, lambda a, b: a * b)

    def __rmul__(self, other):
        return _elementwise(self, other, lambda a, b: a * b)

    def __truediv__(self, other):
        return _elementwise(self, other, lambda a, b: a / b)

    def __rtruediv__(self, other):
        return _elementwise(other, self, lambda a, b: a / b)

    def __neg__(self):
        return _apply(self, lambda x: -x)

    def __pow__(self, other):
        return _elementwise(self, other, lambda a, b: a ** b)

    # Matrix-Multiplikation: arr @ other
    def __matmul__(self, other):
        return matmul(self, other)

    def transpose(self, *axes):
        return transpose(self, axes if axes else None)

    def reshape(self, *shape):
        if len(shape) == 1 and isinstance(shape[0], tuple):
            shape = shape[0]
        flat = _flatten(self.data)
        return ndarray(_unflatten(flat, shape), shape)

    def sum(self, axis=None, keepdims=False):
        return sum(self, axis=axis, keepdims=keepdims)

    def mean(self):
        flat = _flatten(self.data)
        return builtins_sum(flat) / len(flat)

    def max(self):
        return builtins_max(_flatten(self.data))

    def var(self):
        flat = _flatten(self.data)
        m = builtins_sum(flat) / len(flat)
        return builtins_sum((x - m) ** 2 for x in flat) / len(flat)

    def tolist(self):
        return self.data

    @property
    def T(self):
        return transpose(self)

    @property
    def size(self):
        result = 1
        for s in self.shape:
            result *= s
        return result


# Damit sum() und max() intern nicht mit den eigenen Funktionen kollidieren
import builtins
builtins_sum = builtins.sum
builtins_max = builtins.max


# =============================================================================
# INTERNE HILFSFUNKTIONEN
# =============================================================================

def _get_shape(data):
    """Ermittelt die Shape einer verschachtelten Liste."""
    if not isinstance(data, list):
        return ()
    if len(data) == 0:
        return (0,)
    return (len(data),) + _get_shape(data[0])


def _flatten(data):
    """Macht aus verschachtelten Listen eine flache Liste."""
    if isinstance(data, ndarray):
        data = data.data
    if not isinstance(data, list):
        return [data]
    result = []
    for item in data:
        result.extend(_flatten(item))
    return result


def _unflatten(flat, shape):
    """Baut aus einer flachen Liste eine verschachtelte Liste mit gegebener Shape."""
    if len(shape) == 1:
        return flat[:shape[0]]
    size = 1
    for s in shape[1:]:
        size *= s
    return [_unflatten(flat[i*size:(i+1)*size], shape[1:]) for i in range(shape[0])]


def _apply(arr, func):
    """Wendet func auf jedes Element an."""
    if isinstance(arr, ndarray):
        flat = _flatten(arr.data)
        result = [func(x) for x in flat]
        return ndarray(_unflatten(result, arr.shape), arr.shape)
    return func(arr)


def _elementwise(a, b, func):
    """Element-weise Operation zwischen zwei Arrays oder Array und Skalar."""
    if isinstance(a, ndarray) and isinstance(b, ndarray):
        flat_a = _flatten(a.data)
        flat_b = _flatten(b.data)
        # Broadcasting: wenn b kleiner ist, wiederholen
        if len(flat_b) < len(flat_a):
            reps = len(flat_a) // len(flat_b)
            flat_b = flat_b * reps
        result = [func(x, y) for x, y in zip(flat_a, flat_b)]
        return ndarray(_unflatten(result, a.shape), a.shape)
    elif isinstance(a, ndarray):
        flat = _flatten(a.data)
        result = [func(x, b) for x in flat]
        return ndarray(_unflatten(result, a.shape), a.shape)
    elif isinstance(b, ndarray):
        flat = _flatten(b.data)
        result = [func(a, x) for x in flat]
        return ndarray(_unflatten(result, b.shape), b.shape)
    else:
        return func(a, b)


# =============================================================================
# NUMPY-KOMPATIBLE FUNKTIONEN
# =============================================================================

def array(data):
    """Erstellt ein ndarray aus einer Liste."""
    if isinstance(data, ndarray):
        return data
    return ndarray(data)


def zeros(shape):
    """Array gefüllt mit Nullen."""
    if isinstance(shape, int):
        shape = (shape,)
    flat = [0.0] * (builtins_sum(1 for _ in range(1)) and
                    __import__('functools').reduce(lambda a, b: a*b, shape))
    return ndarray(_unflatten(flat, shape), shape)


def ones(shape):
    """Array gefüllt mit Einsen."""
    if isinstance(shape, int):
        shape = (shape,)
    import functools
    size = functools.reduce(lambda a, b: a * b, shape)
    flat = [1.0] * size
    return ndarray(_unflatten(flat, shape), shape)


def arange(n):
    """Erstellt Array [0, 1, 2, ..., n-1]."""
    return ndarray(list(range(n)), (n,))


def triu(arr, k=0):
    """
    Obere Dreiecksmatrix.
    Alle Elemente unterhalb der k-ten Diagonale werden auf 0 gesetzt.
    """
    if isinstance(arr, ndarray):
        data = arr.data
        shape = arr.shape
    else:
        data = arr
        shape = _get_shape(data)

    rows, cols = shape
    result = []
    for i in range(rows):
        row = []
        for j in range(cols):
            if j - i >= k:
                row.append(data[i][j] if isinstance(data[i], list) else 1.0)
            else:
                row.append(0.0)
        result.append(row)
    return ndarray(result, shape)


def exp(x):
    """Element-weise e^x."""
    return _apply(x, math.exp)


def sqrt(x):
    """Element-weise Wurzel."""
    if isinstance(x, ndarray):
        return _apply(x, math.sqrt)
    return math.sqrt(x)


def tanh(x):
    """Element-weise tanh."""
    return _apply(x, math.tanh)


def log(x):
    """Element-weise natürlicher Logarithmus."""
    return _apply(x, math.log)


def max(x, axis=None, keepdims=False):
    """Maximum entlang einer Achse."""
    if not isinstance(x, ndarray):
        return builtins_max(x)

    if axis is None:
        return builtins_max(_flatten(x.data))

    shape = x.shape
    if axis == -1:
        axis = len(shape) - 1

    # Rekursiv entlang der gewünschten Achse reduzieren
    result_data = _reduce_axis(x.data, shape, axis, builtins_max)
    new_shape = tuple(s for i, s in enumerate(shape) if i != axis)

    if keepdims:
        new_shape = tuple(1 if i == axis else s for i, s in enumerate(shape))
        result_data = _add_dim(result_data, axis, len(shape))

    return ndarray(result_data, new_shape if not keepdims else new_shape)


def sum(x, axis=None, keepdims=False):
    """Summe entlang einer Achse."""
    if not isinstance(x, ndarray):
        return builtins_sum(x)

    if axis is None:
        return builtins_sum(_flatten(x.data))

    shape = x.shape
    if axis == -1:
        axis = len(shape) - 1

    result_data = _reduce_axis(x.data, shape, axis, builtins_sum)
    new_shape = tuple(s for i, s in enumerate(shape) if i != axis)

    if keepdims:
        result_data = _add_dim(result_data, axis, len(shape))
        new_shape = tuple(1 if i == axis else s for i, s in enumerate(shape))

    return ndarray(result_data, new_shape)


def mean(x, axis=None, keepdims=False):
    """Mittelwert entlang einer Achse."""
    if not isinstance(x, ndarray):
        flat = list(x)
        return builtins_sum(flat) / len(flat)

    if axis is None:
        flat = _flatten(x.data)
        return builtins_sum(flat) / len(flat)

    shape = x.shape
    if axis == -1:
        axis = len(shape) - 1

    n = shape[axis]
    result_data = _reduce_axis(x.data, shape, axis, lambda vals: builtins_sum(vals) / n)
    new_shape = tuple(s for i, s in enumerate(shape) if i != axis)

    if keepdims:
        result_data = _add_dim(result_data, axis, len(shape))
        new_shape = tuple(1 if i == axis else s for i, s in enumerate(shape))

    return ndarray(result_data, new_shape)


def var(x, axis=None, keepdims=False):
    """Varianz entlang einer Achse."""
    m = mean(x, axis=axis, keepdims=True)
    diff = x - m
    return mean(diff * diff, axis=axis, keepdims=keepdims)


def matmul(a, b):
    """
    Matrix-Multiplikation: a @ b
    Unterstützt 2D und batched (3D, 4D) Matrizen.
    """
    def _matmul_2d(a_data, b_data, m, k, n):
        """Einfache 2D Matrix-Multiplikation: (m,k) @ (k,n) -> (m,n)"""
        result = [[0.0] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                s = 0.0
                for l in range(k):
                    s += a_data[i][l] * b_data[l][j]
                result[i][j] = s
        return result

    def _matmul_nd(a_data, b_data, a_shape, b_shape):
        """Rekursive batched Matrix-Multiplikation."""
        if len(a_shape) == 2:
            m, k = a_shape
            k2, n = b_shape
            assert k == k2, f"Shape mismatch: {a_shape} @ {b_shape}"
            return _matmul_2d(a_data, b_data, m, k, n)
        else:
            return [_matmul_nd(a_data[i], b_data[i], a_shape[1:], b_shape[1:])
                    for i in range(a_shape[0])]

    a_shape = a.shape if isinstance(a, ndarray) else _get_shape(a)
    b_shape = b.shape if isinstance(b, ndarray) else _get_shape(b)
    a_data = a.data if isinstance(a, ndarray) else a
    b_data = b.data if isinstance(b, ndarray) else b

    result_data = _matmul_nd(a_data, b_data, a_shape, b_shape)
    result_shape = a_shape[:-1] + (b_shape[-1],)
    return ndarray(result_data, result_shape)


def transpose(arr, axes=None):
    """
    Transponiert ein Array entlang gegebener Achsen.
    Standard (kein axes): kehrt alle Achsen um.
    """
    if isinstance(arr, ndarray):
        shape = arr.shape
        data = arr.data
    else:
        shape = _get_shape(arr)
        data = arr

    ndim = len(shape)

    if axes is None:
        axes = tuple(range(ndim - 1, -1, -1))
    elif isinstance(axes, (list, tuple)) and len(axes) == 1 and isinstance(axes[0], tuple):
        axes = axes[0]

    new_shape = tuple(shape[i] for i in axes)

    # Flach machen, transponieren, neu aufbauen
    flat = _flatten(data)
    old_strides = _compute_strides(shape)
    new_strides = _compute_strides(new_shape)

    size = len(flat)
    result_flat = [0.0] * size

    for old_idx in range(size):
        # Alten Multi-Index berechnen
        multi = _flat_to_multi(old_idx, shape, old_strides)
        # Neuen Multi-Index durch Achsentausch
        new_multi = tuple(multi[axes[i]] for i in range(ndim))
        # Neuen flachen Index berechnen
        new_idx = _multi_to_flat(new_multi, new_strides)
        result_flat[new_idx] = flat[old_idx]

    return ndarray(_unflatten(result_flat, new_shape), new_shape)


def append(arr, values, axis=None):
    """Hängt values an arr an."""
    if isinstance(arr, ndarray):
        arr_data = arr.data
        arr_shape = arr.shape
    else:
        arr_data = arr
        arr_shape = _get_shape(arr)

    if isinstance(values, ndarray):
        val_data = values.data
    else:
        val_data = values

    if axis is None:
        flat = _flatten(arr_data) + _flatten(val_data)
        return ndarray(flat, (len(flat),))
    elif axis == 1:
        result = [arr_data[0][i] for i in range(arr_shape[1])] + _flatten(val_data)
        new_shape = (arr_shape[0], arr_shape[1] + (_get_shape(val_data)[-1] if isinstance(val_data[0], list) else 1))
        return ndarray([result], new_shape)

    raise NotImplementedError(f"append mit axis={axis} nicht implementiert")


def savez(path, **arrays):
    """Speichert Arrays als .npz (delegiert an numpy für Kompatibilität)."""
    import numpy as _np
    converted = {k: _np.array(_flatten(v.data)).reshape(v.shape)
                 if isinstance(v, ndarray) else v
                 for k, v in arrays.items()}
    _np.savez(path, **converted)


def load(path, allow_pickle=False):
    """Lädt .npz Datei (delegiert an numpy)."""
    import numpy as _np
    data = _np.load(path, allow_pickle=allow_pickle)
    return {k: ndarray(v.tolist(), v.shape) for k, v in data.items()}


def zeros_like(arr):
    """Array mit Nullen in gleicher Shape wie arr."""
    if isinstance(arr, ndarray):
        shape = arr.shape
    else:
        shape = _get_shape(arr)
    import functools
    size = functools.reduce(lambda a, b: a * b, shape)
    flat = [0.0] * size
    return ndarray(_unflatten(flat, shape), shape)


def maximum(a, b):
    """
    Element-weises Maximum zweier Arrays oder Array und Skalar.
    Entspricht np.maximum(a, b) — nicht np.max(a).
    """
    return _elementwise(a, b, lambda x, y: x if x > y else y)


def argmax(x, axis=None):
    """
    Index des größten Elements.
    Ohne axis: globales Argmax als Integer.
    """
    if isinstance(x, ndarray):
        flat = _flatten(x.data)
    else:
        flat = list(x)

    if axis is None:
        best_idx = 0
        best_val = flat[0]
        for i, v in enumerate(flat):
            if v > best_val:
                best_val = v
                best_idx = i
        return best_idx

    raise NotImplementedError("argmax mit axis ist noch nicht implementiert")


class random:
    @staticmethod
    def choice(n, p=None):
        """Wählt zufällig einen Index basierend auf Wahrscheinlichkeiten p."""
        if p is None:
            import random as _r
            return _r.randint(0, n - 1)

        if isinstance(p, ndarray):
            p = _flatten(p.data)

        # Kumulierte Summe
        cumsum = []
        s = 0.0
        for prob in p:
            s += prob
            cumsum.append(s)

        # Zufallszahl zwischen 0 und 1
        import random as _r
        r = _r.random()

        # Ersten Index finden wo kumulative Summe > r
        for i, cs in enumerate(cumsum):
            if r <= cs:
                return i
        return n - 1

    @staticmethod
    def seed(s):
        """Setzt den Zufallszahlenseed für Reproduzierbarkeit."""
        import random as _r
        _r.seed(s)

    @staticmethod
    def shuffle(lst):
        """
        Mischst eine Liste in-place (wie np.random.shuffle).
        Arbeitet direkt auf der Liste, kein Rückgabewert.
        Fisher-Yates Algorithmus.
        """
        import random as _r
        n = len(lst)
        for i in range(n - 1, 0, -1):
            j = _r.randint(0, i)
            lst[i], lst[j] = lst[j], lst[i]

    @staticmethod
    def randn(*shape):
        """
        Normalverteilte Zufallswerte (Mittelwert=0, Std=1).
        Verwendet Box-Muller-Transformation.
        Beispiel: random.randn(3, 4) -> ndarray mit shape (3, 4)
        """
        import random as _r

        def _box_muller():
            """Erzeugt eine standardnormalverteilte Zahl via Box-Muller."""
            while True:
                u1 = _r.random()
                u2 = _r.random()
                if u1 > 0:
                    break
            z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
            return z

        if len(shape) == 1 and isinstance(shape[0], tuple):
            shape = shape[0]

        import functools
        size = functools.reduce(lambda a, b: a * b, shape)
        flat = [_box_muller() for _ in range(size)]
        return ndarray(_unflatten(flat, shape), shape)


# =============================================================================
# INTERNE HILFSFUNKTIONEN FÜR TRANSPOSE
# =============================================================================

def _compute_strides(shape):
    """Berechnet Strides für einen C-order Array."""
    strides = []
    s = 1
    for dim in reversed(shape):
        strides.append(s)
        s *= dim
    return list(reversed(strides))


def _flat_to_multi(flat_idx, shape, strides):
    """Konvertiert flachen Index in Multi-Index."""
    multi = []
    for i, stride in enumerate(strides):
        multi.append(flat_idx // stride)
        flat_idx %= stride
    return tuple(multi)


def _multi_to_flat(multi, strides):
    """Konvertiert Multi-Index in flachen Index."""
    return builtins_sum(m * s for m, s in zip(multi, strides))


def _reduce_axis(data, shape, axis, func):
    """Reduziert ein Array entlang einer Achse mit func."""
    if len(shape) == 1:
        return func(data)
    if axis == 0:
        # Über erste Dimension reduzieren
        if len(shape) == 2:
            cols = shape[1]
            return [func([data[i][j] for i in range(shape[0])]) for j in range(cols)]
        else:
            return [_reduce_axis([data[i][j] for i in range(shape[0])],
                                  shape[1:], axis - 1, func)
                    for j in range(shape[1])]
    else:
        return [_reduce_axis(data[i], shape[1:], axis - 1, func)
                for i in range(shape[0])]


def _add_dim(data, axis, ndim):
    """Fügt eine Dimension an Position axis ein (für keepdims)."""
    if axis == 0:
        return [data]
    if isinstance(data, list):
        return [_add_dim(item, axis - 1, ndim - 1) for item in data]
    return [data]


# Damit np.random.choice funktioniert
random = random()
