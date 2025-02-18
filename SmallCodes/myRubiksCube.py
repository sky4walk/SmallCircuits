import numpy as np

class RubiksCube:
    def __init__(self):
        """Initialisiert einen gelösten Würfel mit 6 farbigen Seiten."""
        self.colors = {'U': 'W', 'D': 'Y', 'L': 'O', 'R': 'R', 'F': 'G', 'B': 'B'}
        self.faces = ['U', 'D', 'L', 'R', 'F', 'B']
        
        # Dictionary für den Würfel, jede Seite ist eine 3x3-Matrix mit einer Farbe
        self.cube = {face: np.full((3, 3), self.colors[face]) for face in self.faces}

    def rotate_face(self, face, clockwise=True):
        """Dreht eine Seite des Würfels und verschiebt angrenzende Kanten."""
        self.cube[face] = np.rot90(self.cube[face], -1 if clockwise else 1)

        # Definition der angrenzenden Reihen/Spalten für jede Seite
        adjacent_faces = {
            'U': [('B', 0, 'row'), ('R', 0, 'row'), ('F', 0, 'row'), ('L', 0, 'row')],
            'D': [('F', 2, 'row'), ('R', 2, 'row'), ('B', 2, 'row'), ('L', 2, 'row')],
            'F': [('U', 2, 'row'), ('R', slice(None), 'col'), ('D', 0, 'row'), ('L', slice(None), 'col')],
            'B': [('U', 0, 'row'), ('L', slice(None), 'col'), ('D', 2, 'row'), ('R', slice(None), 'col')],
            'L': [('U', slice(None), 'col'), ('F', slice(None), 'col'), ('D', slice(None), 'col'), ('B', slice(None), 'col')],
            'R': [('U', slice(None), 'col'), ('B', slice(None), 'col'), ('D', slice(None), 'col'), ('F', slice(None), 'col')]
        }

        edges = adjacent_faces[face]

        # Speichert die Werte der letzten Kante
        temp = self.get_edge(*edges[-1])

        # Verschiebt Werte um eine Position weiter
        for i in range(3):
            self.set_edge(*edges[i], self.get_edge(*edges[i + 1]))

        # Setzt die letzte Kante mit den vorher gespeicherten Werten
        self.set_edge(*edges[3], temp)

    def get_edge(self, face, index, mode):
        """Gibt eine Zeile oder Spalte zurück."""
        if mode == 'row':
            return self.cube[face][index, :].copy()
        elif mode == 'col':
            return self.cube[face][:, index].copy()
        else:
            raise ValueError(f"Ungültiger Modus: {mode}")

    def set_edge(self, face, index, values, mode):
        """Setzt eine Zeile oder Spalte auf neue Werte."""
        if mode == 'row':
            self.cube[face][index, :] = values
        elif mode == 'col':
            self.cube[face][:, index] = values
        else:
            raise ValueError(f"Ungültiger Modus: {mode}")

    def display(self):
        """Zeigt den aktuellen Zustand des Würfels in der Konsole."""
        for face in self.faces:
            print(f"{face} Seite:")
            print('\n'.join([' '.join(row) for row in self.cube[face]]))
            print()

# Beispielverwendung
cube = RubiksCube()
cube.display()

cube.rotate_face("U")  # Test: Dreht die obere Seite
print("Nach der Drehung der oberen Seite (U):")
cube.display()
