"""
LSTM – Long Short-Term Memory
Implementierung basierend auf: Hochreiter & Schmidhuber (1997)
"Long Short-Term Memory", Neural Computation 9(8):1735–1780

Ausführen:
    python lstm_implementation.py

Ausgabe:
    lstm_diagram.png   – Schaubild der LSTM-Architektur
    lstm_training.png  – Trainingsverlauf
    (beide im selben Ordner wie dieses Skript)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from typing import Tuple, Dict

# Alle Ausgabedateien landen neben diesem Skript
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ──────────────────────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ──────────────────────────────────────────────────────────────────────────────

def sigmoid(x: np.ndarray) -> np.ndarray:
    """Logistische Sigmoid-Funktion, Output-Range [0, 1]"""
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

def tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)


# ──────────────────────────────────────────────────────────────────────────────
# LSTM Zelle
# ──────────────────────────────────────────────────────────────────────────────

class LSTMCell:
    """
    Eine LSTM-Zelle gemäß dem Original-Paper.

    Kerngleichungen:
      f(t) = sigmoid(W_f · [h_{t-1}, x_t] + b_f)    ← Forget Gate
      i(t) = sigmoid(W_i · [h_{t-1}, x_t] + b_i)    ← Input Gate
      g(t) = tanh   (W_c · [h_{t-1}, x_t] + b_c)    ← Kandidatenwerte
      c(t) = f(t) * c(t-1) + i(t) * g(t)             ← Cell State (CEC)
      o(t) = sigmoid(W_o · [h_{t-1}, x_t] + b_o)    ← Output Gate
      h(t) = o(t) * tanh(c(t))                        ← Hidden State
    """

    def __init__(self, input_size: int, hidden_size: int):
        self.input_size  = input_size
        self.hidden_size = hidden_size
        n = hidden_size
        d = input_size + hidden_size

        # Alle 4 Gates in einer Matrix [Forget | Input | Kandidat | Output]
        self.W = np.random.randn(4 * n, d) * 0.1
        self.b = np.zeros((4 * n, 1))

        # Output-Gate-Bias negativ: verhindert "abuse problem" (Paper, Abschnitt 4)
        self.b[3 * n:] = -1.0

        self.dW = np.zeros_like(self.W)
        self.db = np.zeros_like(self.b)

    def forward(self, x: np.ndarray, h_prev: np.ndarray,
                c_prev: np.ndarray) -> Tuple[np.ndarray, np.ndarray, dict]:
        n      = self.hidden_size
        concat = np.vstack([h_prev, x])
        gates  = self.W @ concat + self.b

        f = sigmoid(gates[0*n : 1*n])   # Forget Gate
        i = sigmoid(gates[1*n : 2*n])   # Input Gate
        g =    tanh(gates[2*n : 3*n])   # Kandidatenwerte
        o = sigmoid(gates[3*n : 4*n])   # Output Gate

        c = f * c_prev + i * g          # Cell State (CEC – kein Vanishing!)
        h = o * tanh(c)                 # Hidden State

        cache = dict(x=x, h_prev=h_prev, c_prev=c_prev,
                     f=f, i=i, g=g, o=o, c=c, h=h, concat=concat)
        return h, c, cache

    def backward(self, dh: np.ndarray, dc: np.ndarray,
                 cache: dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        n = self.hidden_size
        f, i, g, o = cache['f'], cache['i'], cache['g'], cache['o']
        c, c_prev  = cache['c'], cache['c_prev']
        concat     = cache['concat']

        tanh_c = tanh(c)

        do      = dh * tanh_c
        dc     += dh * o * (1 - tanh_c**2)

        df      = dc * c_prev
        di      = dc * g
        dg      = dc * i
        dc_prev = dc * f               # Konstanter Fehlerfluss durch den CEC

        d_gates = np.vstack([
            df * f * (1 - f),          # Sigmoid-Ableitung Forget
            di * i * (1 - i),          # Sigmoid-Ableitung Input
            dg * (1 - g**2),           # tanh-Ableitung Kandidat
            do * o * (1 - o),          # Sigmoid-Ableitung Output
        ])

        self.dW += d_gates @ concat.T
        self.db += d_gates

        d_concat = self.W.T @ d_gates
        dh_prev  = d_concat[:n]
        dx       = d_concat[n:]

        return dh_prev, dc_prev, dx

    def update(self, lr: float):
        self.W -= lr * np.clip(self.dW, -5, 5)
        self.b -= lr * np.clip(self.db, -5, 5)
        self.dW[:] = 0
        self.db[:] = 0


# ──────────────────────────────────────────────────────────────────────────────
# Vollständiges LSTM-Netz mit linearer Ausgabeschicht
# ──────────────────────────────────────────────────────────────────────────────

class LSTMNetwork:
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        self.cell        = LSTMCell(input_size, hidden_size)
        self.hidden_size = hidden_size
        self.W_out       = np.random.randn(output_size, hidden_size) * 0.1
        self.b_out       = np.zeros((output_size, 1))
        self.dW_out      = np.zeros_like(self.W_out)
        self.db_out      = np.zeros_like(self.b_out)

    def forward(self, inputs: list) -> Tuple[np.ndarray, list]:
        n      = self.hidden_size
        h      = np.zeros((n, 1))
        c      = np.zeros((n, 1))
        caches = []

        for x in inputs:
            h, c, cache = self.cell.forward(x, h, c)
            caches.append(cache)

        y = self.W_out @ h + self.b_out
        return y, caches

    def backward(self, dy: np.ndarray, caches: list):
        n      = self.hidden_size
        last_h = caches[-1]['h']

        self.dW_out += dy @ last_h.T
        self.db_out += dy
        dh = self.W_out.T @ dy
        dc = np.zeros((n, 1))

        for cache in reversed(caches):
            dh, dc, _ = self.cell.backward(dh, dc, cache)

    def update(self, lr: float):
        self.cell.update(lr)
        self.W_out -= lr * np.clip(self.dW_out, -5, 5)
        self.b_out -= lr * np.clip(self.db_out, -5, 5)
        self.dW_out[:] = 0
        self.db_out[:] = 0


# ──────────────────────────────────────────────────────────────────────────────
# Das "Adding Problem" (Experiment 4 aus dem Paper)
# ──────────────────────────────────────────────────────────────────────────────

def generate_adding_problem(T: int) -> Tuple[list, float]:
    seq_len = T + np.random.randint(0, T // 10 + 1)
    values  = np.random.uniform(-1, 1, seq_len)
    markers = np.zeros(seq_len)

    idx1 = np.random.randint(0, min(10, seq_len))
    idx2 = np.random.randint(idx1 + 1, max(idx1 + 2, seq_len // 2))
    markers[idx1] = 1.0
    markers[idx2] = 1.0

    target = 0.5 + (values[idx1] + values[idx2]) / 4.0
    inputs = [np.array([[values[t]], [markers[t]]]) for t in range(seq_len)]
    return inputs, target


def train(T: int = 50, n_iter: int = 2000, hidden_size: int = 12,
          lr: float = 0.05) -> Dict:
    net    = LSTMNetwork(input_size=2, hidden_size=hidden_size, output_size=1)
    losses = []

    print(f"\n{'='*55}")
    print(f"  Training: LSTM auf dem Adding Problem (T={T})")
    print(f"  Hochreiter & Schmidhuber (1997), Experiment 4")
    print(f"{'='*55}")
    print(f"  {'Iteration':>10}  {'Loss (MSE)':>12}  {'Status':>8}")
    print(f"  {'-'*42}")

    for step in range(1, n_iter + 1):
        inputs, target = generate_adding_problem(T)
        target_arr     = np.array([[target]])

        y, caches = net.forward(inputs)
        loss      = 0.5 * float(np.sum((y - target_arr) ** 2))
        losses.append(loss)

        dy = y - target_arr
        net.backward(dy, caches)
        net.update(lr)

        if step % 200 == 0:
            avg    = np.mean(losses[-200:])
            status = "✓ gut" if avg < 0.04 else "..."
            print(f"  {step:>10}  {avg:>12.4f}  {status:>8}")

    print(f"{'='*55}\n")
    return {"losses": losses, "network": net}


def demo_inference(net: LSTMNetwork, T: int = 50, n_samples: int = 200):
    errors = []
    for _ in range(n_samples):
        inputs, target = generate_adding_problem(T)
        y, _           = net.forward(inputs)
        errors.append(abs(float(y.flat[0]) - target))

    print(f"Inferenz auf {n_samples} neuen Sequenzen:")
    print(f"  Mittlerer absoluter Fehler : {np.mean(errors):.4f}")
    print(f"  Anteil korrekt (< 0.04)    : {np.mean(np.array(errors) < 0.04)*100:.1f}%")
    return errors


# ──────────────────────────────────────────────────────────────────────────────
# Schaubilder
# ──────────────────────────────────────────────────────────────────────────────

def save_diagram():
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))
    fig.patch.set_facecolor('#0f1117')

    # ── Links: Vanishing Gradient ──────────────────────────────────
    ax = axes[0]
    ax.set_facecolor('#0f1117')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')

    ax.text(5, 9.5, 'Das Problem: Vanishing Gradient', fontsize=14,
            fontweight='bold', color='#ff6b6b', ha='center', fontfamily='monospace')
    ax.text(5, 8.9, 'Fehlersignal zerfällt exponentiell beim Rückwärtsdurchlauf',
            fontsize=9, color='#aaaaaa', ha='center')

    xs    = np.linspace(1, 9, 6)
    y_rnn = 6.5
    for idx, x in enumerate(xs):
        ax.add_patch(Circle((x, y_rnn), 0.45, color='#333355',
                            ec='#5555aa', linewidth=2, zorder=3))
        ax.text(x, y_rnn, f'h{idx+1}', color='white', ha='center',
                va='center', fontsize=9, fontweight='bold', zorder=4)
        if idx < 5:
            ax.annotate('', xy=(xs[idx+1]-0.45, y_rnn), xytext=(x+0.45, y_rnn),
                        arrowprops=dict(arrowstyle='->', color='#5555aa', lw=2))

    strengths = [1.0, 0.6, 0.35, 0.18, 0.08, 0.03]
    colors_g  = ['#ff4444','#ff7744','#ffaa44','#dddd44','#88dd44','#44dd88']
    for x, s, c in zip(xs, strengths, colors_g):
        alpha = max(0.15, s)
        ax.annotate('', xy=(x, y_rnn-0.45), xytext=(x, y_rnn-0.45-1.2*s),
                    arrowprops=dict(arrowstyle='<-', color=c, lw=3*s+0.5, alpha=alpha))
        ax.text(x, y_rnn-0.45-1.2*s-0.25, f'∂E\n×{s:.2f}',
                color=c, ha='center', va='top', fontsize=7, alpha=max(0.3, alpha))

    ax.text(5, 3.5, '→  Gradient nach 6 Schritten: nur noch 3% ←',
            color='#ff6b6b', ha='center', fontsize=9, style='italic')
    ax.text(5, 3.0, 'Das LSTM löst dies mit dem Constant Error Carousel (CEC)',
            color='#88dd88', ha='center', fontsize=9)

    # ── Rechts: LSTM Memory Cell ────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor('#0f1117')
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis('off')

    ax2.text(5, 9.6, 'LSTM Memory Cell (Hochreiter & Schmidhuber, 1997)',
             fontsize=13, fontweight='bold', color='#61dafb',
             ha='center', fontfamily='monospace')

    ax2.add_patch(FancyBboxPatch((0.8, 6.8), 8.4, 1.0, boxstyle='round,pad=0.1',
                                  facecolor='#1a2744', edgecolor='#61dafb', linewidth=2.5))
    ax2.text(5, 7.3, 'Cell State  c(t)  —  Constant Error Carousel (CEC)',
             color='#61dafb', ha='center', va='center', fontsize=10, fontweight='bold')
    ax2.annotate('', xy=(9.1, 7.3), xytext=(0.9, 7.3),
                 arrowprops=dict(arrowstyle='->', color='#61dafb', lw=3))
    ax2.text(5, 7.75, 'konstanter Fehlerfluss (kein Vanishing!)',
             color='#61dafb', ha='center', fontsize=8, alpha=0.8)

    gate_configs = [
        (2.0, 'Forget\nGate', 'f(t)', '#ff6b6b', '#2a1111', 'Vergiss alten\nCell State?'),
        (5.0, 'Input\nGate',  'i(t)', '#ffd166', '#1a1a00', 'Neue Info\nspeichern?'),
        (8.0, 'Output\nGate', 'o(t)', '#06d6a0', '#001a11', 'Was ausgeben\njetzt?'),
    ]
    for gx, name, sym, ec, fc, desc in gate_configs:
        ax2.add_patch(FancyBboxPatch((gx-0.75, 4.45), 1.5, 1.1,
                                     boxstyle='round,pad=0.08',
                                     facecolor=fc, edgecolor=ec, linewidth=2))
        ax2.text(gx, 5.1,  name, color=ec, ha='center', va='center',
                 fontsize=9, fontweight='bold')
        ax2.text(gx, 4.75, f'σ → {sym}', color='white', ha='center',
                 va='center', fontsize=8)
        ax2.text(gx, 3.9,  desc, color='#aaaaaa', ha='center',
                 va='center', fontsize=8, style='italic')
        ax2.annotate('', xy=(gx, 6.8), xytext=(gx, 5.55),
                     arrowprops=dict(arrowstyle='->', color=ec, lw=2))

    ax2.add_patch(FancyBboxPatch((4.2, 2.8), 1.6, 0.8, boxstyle='round,pad=0.08',
                                  facecolor='#1a0a2a', edgecolor='#bb88ff', linewidth=2))
    ax2.text(5.0, 3.2, 'tanh / g(t)', color='#bb88ff', ha='center',
             va='center', fontsize=9, fontweight='bold')
    ax2.annotate('', xy=(5.0, 4.45), xytext=(5.0, 3.6),
                 arrowprops=dict(arrowstyle='->', color='#bb88ff', lw=1.5))

    ax2.add_patch(FancyBboxPatch((4.2, 1.2), 1.6, 0.8, boxstyle='round,pad=0.08',
                                  facecolor='#001a11', edgecolor='#06d6a0', linewidth=2))
    ax2.text(5.0, 1.6, 'h(t) Output', color='#06d6a0', ha='center',
             va='center', fontsize=9, fontweight='bold')
    ax2.annotate('', xy=(5.0, 1.2), xytext=(5.0, 4.45),
                 arrowprops=dict(arrowstyle='->', color='#06d6a0', lw=2))

    ax2.annotate('', xy=(5.0, 2.8), xytext=(5.0, 2.05),
                 arrowprops=dict(arrowstyle='->', color='#aaaaaa', lw=1.5))
    ax2.text(5.0, 1.92, 'x(t) + h(t-1)', color='#aaaaaa',
             ha='center', va='center', fontsize=8)

    plt.tight_layout(pad=1.0)
    path = os.path.join(OUTPUT_DIR, 'lstm_diagram.png')
    plt.savefig(path, dpi=180, bbox_inches='tight', facecolor='#0f1117')
    plt.close()
    print(f"Schaubild gespeichert:    {path}")


def save_training_plot(losses: list, errors: list):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor('#0f1117')

    for ax in (ax1, ax2):
        ax.set_facecolor('#161b27')
        for spine in ax.spines.values():
            spine.set_color('#333355')
        ax.tick_params(colors='#aaaaaa')
        ax.xaxis.label.set_color('#aaaaaa')
        ax.yaxis.label.set_color('#aaaaaa')
        ax.title.set_color('#61dafb')

    window = 50
    smooth = np.convolve(losses, np.ones(window)/window, mode='valid')
    ax1.plot(losses, alpha=0.2, color='#5555aa', linewidth=0.5)
    ax1.plot(range(window-1, len(losses)), smooth, color='#61dafb', linewidth=2)
    ax1.axhline(0.04, color='#06d6a0', linestyle='--', linewidth=1.5,
                label='Erfolgsschwelle (< 0.04)')
    ax1.set_xlabel('Trainingsschritt')
    ax1.set_ylabel('MSE Loss')
    ax1.set_title('Trainingsverlauf – Adding Problem')
    ax1.legend(fontsize=8, facecolor='#1a2744', labelcolor='#aaaaaa')

    ax2.hist(errors, bins=30, color='#61dafb', alpha=0.7, edgecolor='#1a2744')
    ax2.axvline(0.04, color='#ff6b6b', linestyle='--', linewidth=2, label='Schwelle 0.04')
    ax2.set_xlabel('Absoluter Fehler')
    ax2.set_ylabel('Anzahl Sequenzen')
    ax2.set_title('Fehlerverteilung auf Testdaten')
    ax2.legend(fontsize=8, facecolor='#1a2744', labelcolor='#aaaaaa')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'lstm_training.png')
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0f1117')
    plt.close()
    print(f"Trainings-Plot gespeichert: {path}")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    np.random.seed(42)

    save_diagram()

    result = train(T=50, n_iter=2000, hidden_size=12, lr=0.05)
    errors = demo_inference(result["network"], T=50, n_samples=200)
    save_training_plot(result["losses"], errors)

    print("\nKern-Konzepte des Papers:")
    print("  • Vanishing Gradient : Fehler zerfällt exponentiell beim Rückwärtsdurchlauf")
    print("  • CEC                : c(t) = f·c(t-1) + i·g  → kein Vanishing!")
    print("  • Forget Gate        : Wieviel altes Gedächtnis behalten?")
    print("  • Input Gate         : Schützt Cell State vor irrelevanten Eingaben")
    print("  • Output Gate        : Schützt andere Einheiten vor irrelevantem Gedächtnis")
