import math
import random


class MultiLayerRNN:
    """
    Ein mehrschichtiges Recurrent Neural Network.

    Analog zur NeuralNetwork-Klasse mit [2, 4, 1] Architektur,
    aber für Sequenzen und mit rekurrenten Verbindungen!

    Beispiel:
        rnn = MultiLayerRNN([input_size, hidden1, hidden2, output_size])

        Das erstellt:
        - Input Layer
        - RNN Layer 1 (mit Rekurrenz)
        - RNN Layer 2 (mit Rekurrenz)
        - Output Layer
    """

    def __init__(self, layer_sizes):
        """
        Initialisiert ein mehrschichtiges RNN.

        Args:
            layer_sizes: Liste mit Größen [input, hidden1, hidden2, ..., output]
                        Beispiele:
                        [2, 4, 1]        - 1 Hidden Layer
                        [2, 4, 4, 1]     - 2 Hidden Layers
                        [3, 8, 6, 4, 2]  - 3 Hidden Layers
        """
        self.layer_sizes = layer_sizes
        self.num_layers = len(layer_sizes)

        # Gewichte für jede Schicht
        self.weights = []
        self.recurrent_weights = []
        self.biases = []

        # Initialisiere Gewichte für jede Schicht
        for i in range(len(layer_sizes) - 1):
            prev_size = layer_sizes[i]
            curr_size = layer_sizes[i + 1]

            # Standard Gewichte (von vorheriger Schicht)
            layer_weights = [[random.uniform(-1, 1) / math.sqrt(prev_size)
                             for _ in range(prev_size)]
                            for _ in range(curr_size)]
            self.weights.append(layer_weights)

            # Rekurrente Gewichte (von sich selbst im vorherigen Zeitschritt)
            # NUR für Hidden Layers (nicht für Output Layer)
            if i < len(layer_sizes) - 2:  # Nicht die letzte Schicht
                rec_weights = [[random.uniform(-1, 1) / math.sqrt(curr_size)
                               for _ in range(curr_size)]
                              for _ in range(curr_size)]
                self.recurrent_weights.append(rec_weights)
            else:
                # Output Layer hat keine Rekurrenz
                self.recurrent_weights.append(None)

            # Biases
            layer_biases = [random.uniform(-0.1, 0.1) for _ in range(curr_size)]
            self.biases.append(layer_biases)

        print(f"  Multi-Layer RNN erstellt:")
        print(f"   Architektur: {layer_sizes}")
        print(f"   Anzahl RNN-Layers: {len(layer_sizes) - 2}")
        print(f"   Gesamtparameter: {self.count_parameters()}")

    def count_parameters(self):
        """Zählt die Gesamtanzahl der Parameter"""
        total = 0
        for i in range(len(self.layer_sizes) - 1):
            # Standard Gewichte
            total += self.layer_sizes[i] * self.layer_sizes[i + 1]
            # Rekurrente Gewichte
            if i < len(self.layer_sizes) - 2:
                total += self.layer_sizes[i + 1] * self.layer_sizes[i + 1]
            # Biases
            total += self.layer_sizes[i + 1]
        return total

    def tanh(self, x):
        if x > 20: return 1.0
        if x < -20: return -1.0
        return math.tanh(x)

    def tanh_derivative(self, tanh_output):
        return 1.0 - tanh_output ** 2

    def sigmoid(self, x):
        if x < -500: return 0.0
        if x > 500: return 1.0
        return 1.0 / (1.0 + math.exp(-x))

    def sigmoid_derivative(self, sigmoid_output):
        return sigmoid_output * (1.0 - sigmoid_output)

    def forward(self, input_sequence):
        """
        Forward Pass durch alle Schichten über die Zeit.

        Returns:
            Dictionary mit allen States für Backpropagation
        """
        seq_length = len(input_sequence)
        num_hidden_layers = len(self.layer_sizes) - 2

        # Speichere alle Aktivierungen für BPTT
        # all_states[layer][time] = aktivierungen
        all_states = []
        all_raw_values = []

        # Input Layer States (keine Aktivierung nötig)
        input_states = [inp for inp in input_sequence]
        all_states.append(input_states)
        all_raw_values.append([None] * seq_length)  # Kein raw value für Input

        # Für jede Hidden/Output Schicht
        for layer_idx in range(len(self.weights)):
            layer_size = self.layer_sizes[layer_idx + 1]
            is_output = (layer_idx == len(self.weights) - 1)
            has_recurrence = not is_output

            layer_states = [[0.0] * layer_size]  # Initialer State (t=0)
            layer_raw = []

            # Durch die Zeit
            for t in range(seq_length):
                prev_layer_state = all_states[layer_idx][t]
                prev_time_state = layer_states[-1]

                new_state = []
                new_raw = []

                for neuron_idx in range(layer_size):
                    # Beitrag von vorheriger Schicht
                    value = self.biases[layer_idx][neuron_idx]

                    for prev_idx in range(len(prev_layer_state)):
                        value += prev_layer_state[prev_idx] * \
                                self.weights[layer_idx][neuron_idx][prev_idx]

                    # Rekurrenter Beitrag (nur für Hidden Layers)
                    if has_recurrence:
                        for prev_h_idx in range(layer_size):
                            value += prev_time_state[prev_h_idx] * \
                                    self.recurrent_weights[layer_idx][neuron_idx][prev_h_idx]

                    new_raw.append(value)

                    # Aktivierungsfunktion
                    if is_output:
                        new_state.append(self.sigmoid(value))
                    else:
                        new_state.append(self.tanh(value))

                layer_states.append(new_state)
                layer_raw.append(new_raw)

            all_states.append(layer_states)
            all_raw_values.append(layer_raw)

        # Output ist die letzte Schicht (ohne t=0)
        outputs = all_states[-1][1:]

        return {
            'outputs': outputs,
            'all_states': all_states,
            'all_raw_values': all_raw_values
        }

    def train(self, input_sequence, target_sequence, learning_rate=0.1):
        """
        Training mit Backpropagation Through Time für alle Schichten.
        """
        # Forward Pass
        forward_result = self.forward(input_sequence)
        outputs = forward_result['outputs']
        all_states = forward_result['all_states']
        all_raw_values = forward_result['all_raw_values']

        seq_length = len(input_sequence)

        # Fehler berechnen
        total_error = 0
        for t in range(seq_length):
            for o_idx in range(self.layer_sizes[-1]):
                error = (target_sequence[t][o_idx] - outputs[t][o_idx]) ** 2
                total_error += error
        avg_error = total_error / (seq_length * self.layer_sizes[-1])

        # Backpropagation Through Time
        # Deltas[layer][time][neuron]
        all_deltas = []

        for _ in range(len(self.layer_sizes)):
            all_deltas.append([[0.0] * size for size in [self.layer_sizes[_]] * seq_length])

        # Output Layer Deltas
        for t in range(seq_length):
            for o_idx in range(self.layer_sizes[-1]):
                error = target_sequence[t][o_idx] - outputs[t][o_idx]
                delta = error * self.sigmoid_derivative(outputs[t][o_idx])
                all_deltas[-1][t][o_idx] = delta

        # Hidden Layers Deltas (rückwärts durch Schichten UND Zeit)
        for layer_idx in range(len(self.weights) - 2, -1, -1):
            layer_size = self.layer_sizes[layer_idx + 1]
            next_layer_size = self.layer_sizes[layer_idx + 2]
            has_recurrence = True

            for t in range(seq_length - 1, -1, -1):
                for h_idx in range(layer_size):
                    # Fehler von nächster Schicht (spatial)
                    delta_from_next = 0.0
                    for next_idx in range(next_layer_size):
                        delta_from_next += all_deltas[layer_idx + 2][t][next_idx] * \
                                          self.weights[layer_idx + 1][next_idx][h_idx]

                    # Fehler von nächstem Zeitschritt (temporal)
                    delta_from_future = 0.0
                    if t < seq_length - 1:
                        for next_h_idx in range(layer_size):
                            delta_from_future += all_deltas[layer_idx + 1][t + 1][next_h_idx] * \
                                                self.recurrent_weights[layer_idx][next_h_idx][h_idx]

                    # Gesamter Delta
                    total_delta = (delta_from_next + delta_from_future) * \
                                 self.tanh_derivative(all_states[layer_idx + 1][t + 1][h_idx])

                    all_deltas[layer_idx + 1][t][h_idx] = total_delta

        # Gewichte updaten
        for layer_idx in range(len(self.weights)):
            curr_size = self.layer_sizes[layer_idx + 1]
            prev_size = self.layer_sizes[layer_idx]
            is_output = (layer_idx == len(self.weights) - 1)

            # Standard Gewichte
            for curr_idx in range(curr_size):
                for prev_idx in range(prev_size):
                    gradient = 0.0
                    for t in range(seq_length):
                        gradient += all_deltas[layer_idx + 1][t][curr_idx] * \
                                   all_states[layer_idx][t][prev_idx]
                    self.weights[layer_idx][curr_idx][prev_idx] += learning_rate * gradient

            # Rekurrente Gewichte (nur für Hidden Layers)
            if not is_output:
                for curr_idx in range(curr_size):
                    for prev_h_idx in range(curr_size):
                        gradient = 0.0
                        for t in range(seq_length):
                            gradient += all_deltas[layer_idx + 1][t][curr_idx] * \
                                       all_states[layer_idx + 1][t][prev_h_idx]
                        self.recurrent_weights[layer_idx][curr_idx][prev_h_idx] += learning_rate * gradient

            # Biases
            for curr_idx in range(curr_size):
                gradient = sum(all_deltas[layer_idx + 1][t][curr_idx] for t in range(seq_length))
                self.biases[layer_idx][curr_idx] += learning_rate * gradient

        return avg_error

    def predict(self, input_sequence):
        """Vorhersage für eine Sequenz"""
        result = self.forward(input_sequence)
        return result['outputs']


def compare_architectures():
    """Vergleicht verschiedene RNN-Architekturen"""
    print("=" * 80)
    print("VERGLEICH: VERSCHIEDENE RNN-ARCHITEKTUREN")
    print("=" * 80)

    architectures = [
        [1, 4, 1],          # 1 Hidden Layer
        [1, 4, 4, 1],       # 2 Hidden Layers
        [1, 6, 4, 2, 1],    # 3 Hidden Layers
    ]

    # Einfache Aufgabe: Echo mit Verzögerung
    training_data = [
        ([[1], [0], [1], [0]], [[0], [1], [0], [1]]),
        ([[0], [1], [0], [1]], [[0], [0], [1], [0]]),
        ([[1], [1], [0], [0]], [[0], [1], [1], [0]]),
    ]

    for arch in architectures:
        print(f"\n{'─' * 80}")
        rnn = MultiLayerRNN(arch)

        # Training
        epochs = 500
        learning_rate = 0.1

        print(f"\nTraining für {epochs} Epochen...")
        for epoch in range(epochs):
            total_error = 0
            for inputs, targets in training_data:
                error = rnn.train(inputs, targets, learning_rate)
                total_error += error

            if epoch % 100 == 0:
                avg_error = total_error / len(training_data)
                print(f"  Epoche {epoch:3d}: Fehler = {avg_error:.6f}")

        # Test
        print("\nTest auf [1, 0, 1, 0] (Erwartet: [0, 1, 0, 1]):")
        test_input = [[1], [0], [1], [0]]
        outputs = rnn.predict(test_input)

        for t, out in enumerate(outputs):
            print(f"  Schritt {t}: Output = {out[0]:.4f}")


def example_deep_rnn():
    """Beispiel mit tiefem RNN für komplexere Aufgabe"""
    print("\n\n")
    print("=" * 80)
    print("BEISPIEL: TIEFES RNN FÜR MUSTER-ERKENNUNG")
    print("=" * 80)

    print("""
Aufgabe: Erkenne komplexes Muster "10110"
         Gib 1 aus wenn das Muster erscheint, sonst 0

Beispiel:
    Input:  [1, 0, 1, 1, 0, 0, 1, 1]
    Target: [0, 0, 0, 0, 1, 0, 0, 0]  (Muster bei Position 4 komplett)
    """)

    # Tieferes Netzwerk: 3 Hidden Layers
    rnn = MultiLayerRNN([1, 8, 6, 4, 1])

    # Trainingsdaten generieren
    pattern = [1, 0, 1, 1, 0]

    def generate_training_data(num_samples=20):
        data = []
        for _ in range(num_samples):
            # Zufällige Sequenz
            length = random.randint(8, 12)
            seq = [random.randint(0, 1) for _ in range(length)]

            # Target: 1 wenn Muster komplett ist
            targets = []
            for i in range(length):
                if i >= 4:  # Genug History für Muster
                    matches = all(seq[i-4+j] == pattern[j] for j in range(5))
                    targets.append([1 if matches else 0])
                else:
                    targets.append([0])

            inputs = [[x] for x in seq]
            data.append((inputs, targets))

        return data

    # Training
    print(f"\nTraining...")
    epochs = 300
    learning_rate = 0.15

    for epoch in range(epochs):
        training_data = generate_training_data(30)
        total_error = 0

        for inputs, targets in training_data:
            error = rnn.train(inputs, targets, learning_rate)
            total_error += error

        if epoch % 50 == 0:
            avg_error = total_error / len(training_data)
            print(f"  Epoche {epoch:3d}: Fehler = {avg_error:.6f}")

    # Test
    print("\nTest:")
    test_cases = [
        [1, 0, 1, 1, 0, 0, 0],  # Muster an Position 0-4
        [0, 1, 0, 1, 1, 0, 1],  # Muster an Position 2-6
        [0, 0, 0, 0, 0, 0, 0],  # Kein Muster
    ]

    for seq in test_cases:
        inputs = [[x] for x in seq]
        outputs = rnn.predict(inputs)

        print(f"\n  Sequenz: {seq}")
        print(f"  Outputs: {[f'{o[0]:.2f}' for o in outputs]}")

        # Zeige wo das Muster erkannt wurde
        pattern_found = [i for i, o in enumerate(outputs) if o[0] > 0.5]
        if pattern_found:
            print(f"  Muster erkannt bei: Position {pattern_found}")
        else:
            print(f"  Kein Muster erkannt")


def visualize_depth_advantage():
    """Zeigt den Vorteil von Tiefe"""
    print("\n\n")
    print("=" * 80)
    print("WARUM MEHRERE SCHICHTEN?")
    print("=" * 80)

    print("""
Mehrere RNN-Schichten können hierarchische Features lernen:

Schicht 1 (untere):
    ↓ Lernt einfache Muster (einzelne Bits, kurze Sequenzen)

Schicht 2 (mittlere):
    ↓ Lernt Kombinationen (wiederkehrende Muster)

Schicht 3 (obere):
    ↓ Lernt abstrakte Konzepte (Struktur, Bedeutung)

Ähnlich wie bei Bildverarbeitung:
    - Layer 1: Kanten
    - Layer 2: Formen
    - Layer 3: Objekte

Bei RNNs:
    - Layer 1: Token/Zeichen
    - Layer 2: Wörter/Phrasen
    - Layer 3: Sätze/Bedeutung

Moderne LLMs wie GPT haben oft 96+ Schichten!
    """)


if __name__ == "__main__":
    # Zeige Vergleich
    compare_architectures()

    # Zeige tiefes RNN
    example_deep_rnn()

    # Erkläre Vorteile
    visualize_depth_advantage()

    print("\n" + "=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print("""

Architektur-Beispiele:
    MultiLayerRNN([2, 4, 1])        → 1 Hidden Layer
    MultiLayerRNN([2, 8, 4, 1])     → 2 Hidden Layers
    MultiLayerRNN([3, 16, 12, 8, 2]) → 3 Hidden Layers

Was passiert:
    - Jede Hidden Layer hat rekurrente Verbindungen
    - Output Layer hat KEINE Rekurrenz (nur vorwärts)
    - Backpropagation geht durch Schichten UND Zeit

Analog zur NeuralNetwork-Klasse:
    NeuralNetwork([2, 4, 1])      ← Feed-Forward
    MultiLayerRNN([2, 4, 1])      ← RNN mit gleicher Struktur!

Der Unterschied:
    + Rekurrente Gewichte in jeder Hidden Layer
    + Verarbeitung über Zeit
    + BPTT statt normalem Backprop
    """)
