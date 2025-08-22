import math
import matplotlib.pyplot as plt

def dft(signal):
    N = len(signal)
    real_parts = []
    imag_parts = []

    for t in range(N):
        real_k = 0.0
        imag_k = 0.0
        for f in range(N):
            angle = 2 * math.pi * f * t / N
            real_k += signal[f] * math.cos(-angle)
            imag_k += signal[f] * math.sin(-angle)
        real_parts.append(real_k)
        imag_parts.append(imag_k)

    return real_parts, imag_parts

def idft(real_parts, imag_parts):
    N = len(real_parts)
    signal = []

    for t in range(N):
        real = 0.0
        imag = 0.0
        for f in range(N):
            angle = 2 * math.pi * f * t / N
            real += real_parts[f] * math.cos(angle) - imag_parts[f] * math.sin(angle)
            imag += real_parts[f] * math.sin(angle) + imag_parts[f] * math.cos(angle)
        # Normalisierung durch 1/N (wie es in der Formel der IDFT steht)
        signal.append((real + imag) / N)

    return signal
    
def plot_amplituden(amplituden):
    N = len(amplituden)
    freq_indices = list(range(N))

    plt.figure(figsize=(10, 4))
    plt.stem(freq_indices, amplituden)
    plt.title("Amplitudenspektrum (DFT)")
    plt.xlabel("Frequenzindex")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_frequencies(frequencies):
  N = len(frequencies)
  plt.stem(list(range(N)), frequencies)
  plt.tight_layout()
  plt.show()

# Beispielsignal: Sinus mit Frequenz 2 HZ
samples = 40
freq = 2
signal = [math.sin(freq * math.pi * 2 * n / samples) for n in range(samples)]
plot_frequencies(signal)
    
real, imag = dft(signal)
amplituden = [math.sqrt(r**2 + i**2) for r, i in zip(real, imag)]

# Ausgabe
for k in range(len(signal)):
  print(f"Frequenzindex {k}: Real = {real[k]:.2f}, Imag = {imag[k]:.2f}, Amplitude = {amplituden[k]:.2f}")

# Plot anzeigen
plot_amplituden(amplituden)

signal2 = idft(real, imag)
plot_frequencies(signal2)
