import math
import random


class NeuralNetwork:
    """
    Ein mehrschichtiges neuronales Netz mit Backpropagation.
    Verwendet nur Python Standard-Bibliothek - keine numpy, tensorflow, etc.
    """

    def __init__(self, layer_sizes):
        """
        Initialisiert das neuronale Netz.

        Args:
            layer_sizes: Liste mit der Anzahl der Neuronen pro Schicht
                        z.B. [2, 3, 1] = 2 Input, 3 Hidden, 1 Output Neuronen
        """
        self.num_layers = len(layer_sizes)
        self.layer_sizes = layer_sizes

        # Gewichte und Bias initialisieren
        self.weights = []
        self.biases = []

        for i in range(len(layer_sizes) - 1):
            layer_weights = []
            for j in range(layer_sizes[i + 1]):
                neuron_weights = []
                for k in range(layer_sizes[i]):
                    weight = random.uniform(-1, 1) / math.sqrt(layer_sizes[i])
                    neuron_weights.append(weight)
                layer_weights.append(neuron_weights)
            self.weights.append(layer_weights)

            layer_biases = [random.uniform(-0.1, 0.1) for _ in range(layer_sizes[i + 1])]
            self.biases.append(layer_biases)

    def sigmoid(self, x):
        """Sigmoid Aktivierungsfunktion"""
        if x < -500:
            return 0.0
        elif x > 500:
            return 1.0
        return 1.0 / (1.0 + math.exp(-x))

    def sigmoid_derivative(self, sigmoid_output):
        """Ableitung der Sigmoid-Funktion"""
        return sigmoid_output * (1.0 - sigmoid_output)

    def feedforward(self, inputs):
        """Führt einen Forward Pass durch das Netzwerk durch."""
        activations = inputs

        for layer_idx in range(len(self.weights)):
            next_activations = []

            for neuron_idx in range(len(self.weights[layer_idx])):
                weighted_sum = self.biases[layer_idx][neuron_idx]

                for prev_neuron_idx in range(len(activations)):
                    weighted_sum += (activations[prev_neuron_idx] *
                                   self.weights[layer_idx][neuron_idx][prev_neuron_idx])

                activation = self.sigmoid(weighted_sum)
                next_activations.append(activation)

            activations = next_activations

        return activations

    def train(self, inputs, targets, learning_rate=0.5, verbose=False):
        """
        Trainiert das Netzwerk mit einem einzelnen Beispiel mittels Backpropagation.

        Args:
            inputs: Liste der Input-Werte
            targets: Liste der gewünschten Output-Werte
            learning_rate: Lernrate (typisch 0.1 bis 0.5)
            verbose: Wenn True, gibt detaillierte Informationen aus

        Returns:
            Fehler (MSE) für dieses Beispiel
        """
        if verbose:
            print("\n" + "="*70)
            print("TRAINING SCHRITT - DETAILLIERTE AUSGABE")
            print("="*70)
            print(f"Input: {[f'{x:.4f}' for x in inputs]}")
            print(f"Target: {[f'{t:.4f}' for t in targets]}")

        # 1. FORWARD PASS
        all_activations = [inputs]
        all_weighted_sums = []

        activations = inputs

        if verbose:
            print("\n--- FORWARD PASS ---")
            print(f"Layer 0 (Input): {[f'{a:.4f}' for a in activations]}")

        for layer_idx in range(len(self.weights)):
            weighted_sums = []
            next_activations = []

            if verbose:
                print(f"\nLayer {layer_idx + 1}:")

            for neuron_idx in range(len(self.weights[layer_idx])):
                weighted_sum = self.biases[layer_idx][neuron_idx]

                if verbose:
                    print(f"  Neuron {neuron_idx}:")
                    print(f"    Bias: {self.biases[layer_idx][neuron_idx]:.4f}")

                for prev_neuron_idx in range(len(activations)):
                    contribution = activations[prev_neuron_idx] * self.weights[layer_idx][neuron_idx][prev_neuron_idx]
                    weighted_sum += contribution

                    if verbose:
                        print(f"    Gewicht[{prev_neuron_idx}]: {self.weights[layer_idx][neuron_idx][prev_neuron_idx]:.4f} " +
                              f"× Aktivierung[{prev_neuron_idx}]: {activations[prev_neuron_idx]:.4f} " +
                              f"= {contribution:.4f}")

                weighted_sums.append(weighted_sum)
                activation = self.sigmoid(weighted_sum)
                next_activations.append(activation)

                if verbose:
                    print(f"    Summe: {weighted_sum:.4f}")
                    print(f"    Aktivierung (nach Sigmoid): {activation:.4f}")

            all_weighted_sums.append(weighted_sums)
            activations = next_activations
            all_activations.append(activations)

        # 2. FEHLER BERECHNEN
        outputs = all_activations[-1]
        error = 0
        for i in range(len(outputs)):
            error += (targets[i] - outputs[i]) ** 2
        error /= len(outputs)

        if verbose:
            print(f"\n--- FEHLERBERECHNUNG ---")
            print(f"Output: {[f'{o:.4f}' for o in outputs]}")
            print(f"Target: {[f'{t:.4f}' for t in targets]}")
            print(f"Fehler (MSE): {error:.6f}")

        # 3. BACKWARD PASS
        if verbose:
            print(f"\n--- BACKWARD PASS ---")

        deltas = [None] * len(self.weights)

        # Output-Schicht
        output_deltas = []
        if verbose:
            print(f"Output Layer Deltas:")

        for i in range(len(outputs)):
            output_error = targets[i] - outputs[i]
            delta = output_error * self.sigmoid_derivative(outputs[i])
            output_deltas.append(delta)

            if verbose:
                print(f"  Neuron {i}: Fehler={output_error:.4f}, " +
                      f"Sigmoid'={self.sigmoid_derivative(outputs[i]):.4f}, " +
                      f"Delta={delta:.4f}")

        deltas[-1] = output_deltas

        # Hidden Layers
        for layer_idx in range(len(self.weights) - 2, -1, -1):
            layer_deltas = []

            if verbose:
                print(f"\nHidden Layer {layer_idx + 1} Deltas:")

            for neuron_idx in range(self.layer_sizes[layer_idx + 1]):
                error_sum = 0

                if verbose:
                    print(f"  Neuron {neuron_idx}:")

                for next_neuron_idx in range(len(deltas[layer_idx + 1])):
                    contribution = deltas[layer_idx + 1][next_neuron_idx] * self.weights[layer_idx + 1][next_neuron_idx][neuron_idx]
                    error_sum += contribution

                    if verbose:
                        print(f"    Delta[{next_neuron_idx}]={deltas[layer_idx + 1][next_neuron_idx]:.4f} " +
                              f"× Gewicht={self.weights[layer_idx + 1][next_neuron_idx][neuron_idx]:.4f} " +
                              f"= {contribution:.4f}")

                activation = all_activations[layer_idx + 1][neuron_idx]
                delta = error_sum * self.sigmoid_derivative(activation)
                layer_deltas.append(delta)

                if verbose:
                    print(f"    Fehler-Summe: {error_sum:.4f}")
                    print(f"    Sigmoid'({activation:.4f}): {self.sigmoid_derivative(activation):.4f}")
                    print(f"    Delta: {delta:.4f}")

            deltas[layer_idx] = layer_deltas

        # 4. GEWICHTE UND BIAS AKTUALISIEREN
        if verbose:
            print(f"\n--- GEWICHTS-UPDATE ---")

        for layer_idx in range(len(self.weights)):
            if verbose:
                print(f"\nLayer {layer_idx + 1}:")

            for neuron_idx in range(len(self.weights[layer_idx])):
                # Bias aktualisieren
                old_bias = self.biases[layer_idx][neuron_idx]
                bias_update = learning_rate * deltas[layer_idx][neuron_idx]
                self.biases[layer_idx][neuron_idx] += bias_update

                if verbose:
                    print(f"  Neuron {neuron_idx}:")
                    print(f"    Bias: {old_bias:.4f} → {self.biases[layer_idx][neuron_idx]:.4f} " +
                          f"(Δ={bias_update:.4f})")

                # Gewichte aktualisieren
                for prev_neuron_idx in range(len(self.weights[layer_idx][neuron_idx])):
                    old_weight = self.weights[layer_idx][neuron_idx][prev_neuron_idx]
                    prev_activation = all_activations[layer_idx][prev_neuron_idx]
                    gradient = deltas[layer_idx][neuron_idx] * prev_activation
                    weight_update = learning_rate * gradient
                    self.weights[layer_idx][neuron_idx][prev_neuron_idx] += weight_update

                    if verbose:
                        print(f"    Gewicht[{prev_neuron_idx}]: {old_weight:.4f} → " +
                              f"{self.weights[layer_idx][neuron_idx][prev_neuron_idx]:.4f} " +
                              f"(Δ={weight_update:.4f})")

        return error

    def print_network_structure(self):
        """Gibt die Netzwerkstruktur aus"""
        print("\n" + "="*70)
        print("NETZWERK-STRUKTUR")
        print("="*70)
        print(f"Anzahl der Schichten: {self.num_layers}")
        print(f"Neuronen pro Schicht: {self.layer_sizes}")
        print()

        for layer_idx in range(len(self.weights)):
            print(f"Verbindungen Layer {layer_idx} → Layer {layer_idx + 1}:")
            print(f"  Anzahl Gewichte: {len(self.weights[layer_idx])} × {len(self.weights[layer_idx][0])} " +
                  f"= {len(self.weights[layer_idx]) * len(self.weights[layer_idx][0])}")
            print(f"  Anzahl Biases: {len(self.biases[layer_idx])}")

        total_params = sum(len(layer) * len(layer[0]) for layer in self.weights) + sum(len(layer) for layer in self.biases)
        print(f"\nGesamtanzahl trainierbarer Parameter: {total_params}")
        print("="*70)


def detailed_training_demo():
    """
    Demonstriert das Training mit detaillierter Ausgabe
    """
    print("="*70)
    print("DETAILLIERTE TRAININGS-DEMONSTRATION")
    print("="*70)

    # Kleines Netzwerk für bessere Übersicht: 2 Input, 2 Hidden, 1 Output
    nn = NeuralNetwork([2, 2, 1])
    nn.print_network_structure()

    # Einfaches Trainingsbeispiel: AND-Funktion
    print("\n\nTrainiere AND-Funktion: [1, 1] → [1]")
    print("(Nur die ersten 3 Schritte werden detailliert angezeigt)")

    inputs = [1, 1]
    targets = [1]
    learning_rate = 0.5

    # Zeige die ersten 3 Trainingsschritte im Detail
    for step in range(3):
        print(f"\n\n{'#'*70}")
        print(f"TRAININGSSCHRITT {step + 1}")
        print(f"{'#'*70}")
        error = nn.train(inputs, targets, learning_rate, verbose=True)

    # Weitere Schritte ohne Details
    print("\n\nTrainiere weitere 97 Schritte...")
    for step in range(97):
        error = nn.train(inputs, targets, learning_rate, verbose=False)
        if (step + 4) % 20 == 0:
            print(f"Schritt {step + 4}: Fehler = {error:.6f}")

    # Test
    print("\n" + "="*70)
    print("FINALES TESTERGEBNIS")
    print("="*70)
    output = nn.feedforward(inputs)
    print(f"Input: {inputs} → Output: {output[0]:.4f} (Target: {targets[0]})")


def compare_architectures():
    """
    Vergleicht verschiedene Netzwerk-Architekturen
    """
    print("\n\n")
    print("="*70)
    print("VERGLEICH VERSCHIEDENER ARCHITEKTUREN FÜR XOR")
    print("="*70)

    architectures = [
        [2, 2, 1],      # Klein
        [2, 4, 1],      # Mittel
        [2, 8, 1],      # Größer
        [2, 4, 4, 1],   # Tiefer (2 Hidden Layers)
    ]

    training_data = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0])
    ]

    for arch in architectures:
        print(f"\nArchitektur: {arch}")
        nn = NeuralNetwork(arch)

        # Kurzes Training
        epochs = 2000
        for epoch in range(epochs):
            for inputs, targets in training_data:
                nn.train(inputs, targets, learning_rate=0.5)

        # Test
        print("Ergebnisse:")
        total_error = 0
        for inputs, expected in training_data:
            output = nn.feedforward(inputs)
            error = (expected[0] - output[0]) ** 2
            total_error += error
            print(f"  {inputs} → {output[0]:.4f} (erwartet: {expected[0]}, Fehler: {error:.6f})")

        avg_error = total_error / len(training_data)
        print(f"Durchschnittlicher Fehler: {avg_error:.6f}")


def train_xor_example():
    """
    Trainiert ein neuronales Netz, um die XOR-Funktion zu lernen.
    XOR ist ein klassisches Problem, das nicht linear trennbar ist.
    """
    print("\n\n")
    print("=" * 70)
    print("TRAINING EINES NEURONALEN NETZES FÜR XOR")
    print("=" * 70)

    # Netzwerk erstellen: 2 Input, 4 Hidden, 1 Output Neuronen
    nn = NeuralNetwork([2, 4, 1])
    nn.print_network_structure()

    # XOR Trainingsdaten
    training_data = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0])
    ]

    # Training
    epochs = 10000
    learning_rate = 0.5

    print(f"\nTraining für {epochs} Epochen mit Lernrate {learning_rate}...")
    print()

    for epoch in range(epochs):
        total_error = 0

        # Durch alle Trainingsbeispiele gehen
        for inputs, targets in training_data:
            error = nn.train(inputs, targets, learning_rate)
            total_error += error

        # Durchschnittlichen Fehler berechnen
        avg_error = total_error / len(training_data)

        # Fortschritt anzeigen
        if epoch % 1000 == 0:
            print(f"Epoche {epoch:5d}: Durchschnittlicher Fehler = {avg_error:.6f}")

    # Testen des trainierten Netzwerks
    print("\n" + "=" * 70)
    print("TESTERGEBNISSE:")
    print("=" * 70)

    for inputs, expected in training_data:
        output = nn.feedforward(inputs)
        print(f"Input: {inputs} -> Output: {output[0]:.4f} (Erwartet: {expected[0]})")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    # 1. Detaillierte Demonstration eines einzelnen Trainingsschritts
    detailed_training_demo()

    # 2. XOR Beispiel - das klassische Beispiel
    train_xor_example()

    # 3. Vergleich verschiedener Architekturen
    compare_architectures()
