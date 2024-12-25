import numpy as np

class SimpleNeuralNetwork:
    # Sigmoid Aktivierungsfunktion
    def sigmoid(self,x):
        return 1 / (1 + np.exp(-x))

    # Ableitung der Sigmoid Funktion
    def sigmoid_derivative(self,x):
        return x * (1 - x)

    def __init__(self, input_size, hidden_size, output_size):
        # Initialisierung der Gewichte
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Gewichtsmatrizen
        self.W1 = np.random.rand(self.input_size, self.hidden_size)
        self.b1 = np.zeros((1, self.hidden_size))
        self.W2 = np.random.rand(self.hidden_size, self.output_size)
        self.b2 = np.zeros((1, self.output_size))

    def forward(self, X):
        # Vorwärtsdurchlauf (Feedforward)
        self.hidden_layer_input = np.dot(X, self.W1) + self.b1
        self.hidden_layer_output = self.sigmoid(self.hidden_layer_input)
        
        self.output_layer_input = np.dot(self.hidden_layer_output, self.W2) + self.b2
        self.output_layer_output = self.sigmoid(self.output_layer_input)
        
        return self.output_layer_output

    def backward(self, X, y, learning_rate=0.1):
        # Rückpropagation
        output_error = y - self.output_layer_output
        output_delta = output_error * self.sigmoid_derivative(self.output_layer_output)
        
        hidden_error = output_delta.dot(self.W2.T)
        hidden_delta = hidden_error * self.sigmoid_derivative(self.hidden_layer_output)
        
        # Gewichtsanpassung
        self.W2 += self.hidden_layer_output.T.dot(output_delta) * learning_rate
        self.b2 += np.sum(output_delta, axis=0, keepdims=True) * learning_rate
        
        self.W1 += X.T.dot(hidden_delta) * learning_rate
        self.b1 += np.sum(hidden_delta, axis=0, keepdims=True) * learning_rate

    def train(self, X, y, epochs=10000, learning_rate=0.1):
        for epoch in range(epochs):
            self.forward(X)
            self.backward(X, y, learning_rate)
            if epoch % 1000 == 0:
                loss = np.mean(np.square(y - self.output_layer_output))
                print(f'Epoch {epoch}, Loss: {loss}')

    def predict(self, X):
        return self.forward(X)

# XOR Eingabedaten
X = np.array([[0, 0],
              [0, 1],
              [1, 0],
              [1, 1]])

# XOR Ausgabedaten
y = np.array([[0], [1], [1], [0]])

# Erstellen des neuronalen Netzes (2 Eingaben, 4 Neuronen in der versteckten Schicht, 1 Ausgang)
nn = SimpleNeuralNetwork(input_size=2, hidden_size=4, output_size=1)

# Trainiere das Netzwerk
nn.train(X, y, epochs=10000, learning_rate=0.1)

# Vorhersagen für die Eingabedaten
predictions = nn.predict(X)

# Ergebnisse anzeigen
print("\nVorhersagen nach dem Training:")
for i in range(len(X)):
    print(f"Input: {X[i]} - Predicted: {predictions[i][0]:.4f} - Actual: {y[i][0]}")