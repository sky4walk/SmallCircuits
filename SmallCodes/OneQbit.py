import numpy as np
import matplotlib.pyplot as plt

# Visualisierung der Bloch-Kugel
# Der Zustand des Qubits kann durch einen Vektor auf der Bloch-Kugel dargestellt werden
def plot_bloch_vector(qubit):
    # Normalisiere den Zustand
    qubit = qubit / np.linalg.norm(qubit)

    # Berechne die Komponenten fuer den Bloch-Vektor
    x = 2 * np.real(qubit[0] * np.conj(qubit[1]))
    y = 2 * np.imag(qubit[0] * np.conj(qubit[1]))
    z = np.abs(qubit[0])**2 - np.abs(qubit[1])**2

    # Erstelle die 3D-Darstellung der Bloch-Kugel
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Zeichne die Kugel
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x_sphere = np.outer(np.cos(u), np.sin(v))
    y_sphere = np.outer(np.sin(u), np.sin(v))
    z_sphere = np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_surface(x_sphere, y_sphere, z_sphere, color='c', alpha=0.3)

    # Plot des Bloch-Vektors
    ax.quiver(0, 0, 0, x, y, z, length=1, color='r', linewidth=2)

    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])

    plt.show()
    
# Initialisiere das Qubit im Zustand |0> (das ist der Vektor [1, 0])
qubit = np.array([1, 0], dtype=complex)

# Funktion, um das Hadamard-Gate auf das Qubit anzuwenden
def apply_hadamard(qubit):
    H = 1/np.sqrt(2) * np.array([[1, 1], [1, -1]])  # Hadamard-Gate
    print("Hadamard: ",H)
    return np.dot(H, qubit)

# Funktion, um das X-Gate auf das Qubit anzuwenden
def apply_x_gate(qubit):
    X = np.array([[0, 1], [1, 0]])  # X-Gate (Pauli-X)
    return np.dot(X, qubit)

# Funktion, um das Y-Gate auf das Qubit anzuwenden
def apply_y_gate(qubit):
    Y = np.array([[0, -1j], [1j, 0]])  # Y-Gate (Pauli-X)
    return np.dot(Y, qubit)

# Funktion, um das Z-Gate auf das Qubit anzuwenden
def apply_z_gate(qubit):
    Z = np.array([[1, 0], [0, -1]])  # Z-Gate (Pauli-X)
    return np.dot(Z, qubit)

# Qubit im Zustand |0>
print("Initialer Zustand des Qubits (|0>):", qubit)
plot_bloch_vector(qubit)

# Anwenden des Hadamard-Gates auf das Qubit (setzt es in eine Ueberlagerung)
qubit = apply_hadamard(qubit)
print("Zustand nach Hadamard-Operation:", qubit)
plot_bloch_vector(qubit)

# Anwenden eines X-Gates auf das Qubit
qubit = apply_y_gate(qubit)
print("Zustand nach X-Gate:", qubit)
plot_bloch_vector(qubit)
