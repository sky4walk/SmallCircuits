import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class RubiksCube:
    def __init__(self):
        # Define colors for each face: Front, Back, Left, Right, Up, Down
        self.colors = {
            'F': 'red',      # Front
            'B': 'orange',   # Back
            'L': 'green',    # Left
            'R': 'blue',     # Right
            'U': 'white',    # Up
            'D': 'yellow'    # Down
        }

        # Initialize cube state (3x3x3 array of colors)
        self.state = self.initialize_cube()

    def initialize_cube(self):
        """Initialize a solved cube"""
        cube = np.empty((3, 3, 3), dtype=object)

        # Each small cube has 6 faces, we'll store which face colors are visible
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    cube[x, y, z] = {
                        'front': 'red' if z == 2 else 'black',
                        'back': 'orange' if z == 0 else 'black',
                        'left': 'green' if x == 0 else 'black',
                        'right': 'blue' if x == 2 else 'black',
                        'up': 'white' if y == 2 else 'black',
                        'down': 'yellow' if y == 0 else 'black'
                    }

        return cube

    def draw_cube(self, ax):
        """Draw the Rubik's Cube"""
        ax.clear()

        size = 1
        gap = 0.05

        for x in range(3):
            for y in range(3):
                for z in range(3):
                    center = np.array([x * (size + gap), y * (size + gap), z * (size + gap)])
                    colors = self.state[x, y, z]
                    self.draw_cubie(ax, center, size, colors)

        ax.set_xlim([-0.5, 3])
        ax.set_ylim([-0.5, 3])
        ax.set_zlim([-0.5, 3])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('Rubik\'s Cube - Buttons zum Drehen verwenden')

    def draw_cubie(self, ax, center, size, colors):
        """Draw a single cubie (small cube)"""
        s = size / 2

        # Define the 6 faces of the cube
        faces = [
            # Front face (z+)
            [center + np.array([-s, -s, s]), center + np.array([s, -s, s]),
             center + np.array([s, s, s]), center + np.array([-s, s, s])],
            # Back face (z-)
            [center + np.array([-s, -s, -s]), center + np.array([-s, s, -s]),
             center + np.array([s, s, -s]), center + np.array([s, -s, -s])],
            # Left face (x-)
            [center + np.array([-s, -s, -s]), center + np.array([-s, -s, s]),
             center + np.array([-s, s, s]), center + np.array([-s, s, -s])],
            # Right face (x+)
            [center + np.array([s, -s, -s]), center + np.array([s, s, -s]),
             center + np.array([s, s, s]), center + np.array([s, -s, s])],
            # Up face (y+)
            [center + np.array([-s, s, -s]), center + np.array([-s, s, s]),
             center + np.array([s, s, s]), center + np.array([s, s, -s])],
            # Down face (y-)
            [center + np.array([-s, -s, -s]), center + np.array([s, -s, -s]),
             center + np.array([s, -s, s]), center + np.array([-s, -s, s])]
        ]

        face_colors = [colors['front'], colors['back'], colors['left'],
                      colors['right'], colors['up'], colors['down']]

        for face, color in zip(faces, face_colors):
            poly = Poly3DCollection([face], alpha=0.9, facecolor=color,
                                   edgecolor='black', linewidth=1.5)
            ax.add_collection3d(poly)

    def rotate_face(self, face, clockwise=True):
        """Rotate a face of the cube"""
        if face == 'F':  # Front face (z=2)
            self.rotate_front(clockwise)
        elif face == 'B':  # Back face (z=0)
            self.rotate_back(clockwise)
        elif face == 'R':  # Right face (x=2)
            self.rotate_right(clockwise)
        elif face == 'L':  # Left face (x=0)
            self.rotate_left(clockwise)
        elif face == 'U':  # Up face (y=2)
            self.rotate_up(clockwise)
        elif face == 'D':  # Down face (y=0)
            self.rotate_down(clockwise)

    def rotate_front(self, clockwise=True):
        """Rotate front face (z=2)"""
        # Extract the layer
        old_layer = [[self.state[x, y, 2].copy() for y in range(3)] for x in range(3)]

        # Rotate positions clockwise: (0,0)->(2,0)->(2,2)->(0,2)->(0,0)
        if clockwise:
            # New positions after clockwise rotation
            positions = [
                ((0, 0), (0, 2)),
                ((1, 0), (0, 1)),
                ((2, 0), (0, 0)),
                ((0, 1), (1, 2)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 0)),
                ((0, 2), (2, 2)),
                ((1, 2), (2, 1)),
                ((2, 2), (2, 0))
            ]
        else:
            # Counter-clockwise
            positions = [
                ((0, 0), (2, 0)),
                ((1, 0), (2, 1)),
                ((2, 0), (2, 2)),
                ((0, 1), (1, 0)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 2)),
                ((0, 2), (0, 0)),
                ((1, 2), (0, 1)),
                ((2, 2), (0, 2))
            ]

        # Apply rotation
        for (old_x, old_y), (new_x, new_y) in positions:
            old_colors = old_layer[old_x][old_y]
            new_colors = old_colors.copy()

            # Rotate the stickers on the front face
            if clockwise:
                new_colors['up'] = old_colors['left']
                new_colors['right'] = old_colors['up']
                new_colors['down'] = old_colors['right']
                new_colors['left'] = old_colors['down']
            else:
                new_colors['up'] = old_colors['right']
                new_colors['right'] = old_colors['down']
                new_colors['down'] = old_colors['left']
                new_colors['left'] = old_colors['up']

            self.state[new_x, new_y, 2] = new_colors

    def rotate_right(self, clockwise=True):
        """Rotate right face (x=2)"""
        old_layer = [[self.state[2, y, z].copy() for z in range(3)] for y in range(3)]

        if clockwise:
            positions = [
                ((0, 0), (0, 2)),
                ((1, 0), (0, 1)),
                ((2, 0), (0, 0)),
                ((0, 1), (1, 2)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 0)),
                ((0, 2), (2, 2)),
                ((1, 2), (2, 1)),
                ((2, 2), (2, 0))
            ]
        else:
            positions = [
                ((0, 0), (2, 0)),
                ((1, 0), (2, 1)),
                ((2, 0), (2, 2)),
                ((0, 1), (1, 0)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 2)),
                ((0, 2), (0, 0)),
                ((1, 2), (0, 1)),
                ((2, 2), (0, 2))
            ]

        for (old_y, old_z), (new_y, new_z) in positions:
            old_colors = old_layer[old_y][old_z]
            new_colors = old_colors.copy()

            if clockwise:
                new_colors['front'] = old_colors['down']
                new_colors['up'] = old_colors['front']
                new_colors['back'] = old_colors['up']
                new_colors['down'] = old_colors['back']
            else:
                new_colors['front'] = old_colors['up']
                new_colors['up'] = old_colors['back']
                new_colors['back'] = old_colors['down']
                new_colors['down'] = old_colors['front']

            self.state[2, new_y, new_z] = new_colors

    def rotate_up(self, clockwise=True):
        """Rotate up face (y=2)"""
        old_layer = [[self.state[x, 2, z].copy() for z in range(3)] for x in range(3)]

        if clockwise:
            # Clockwise rotation when viewed from above (looking down at y=2)
            # In x-z plane: (x,z) -> (z, 2-x)
            positions = [
                ((0, 0), (0, 2)),
                ((1, 0), (0, 1)),
                ((2, 0), (0, 0)),
                ((0, 1), (1, 2)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 0)),
                ((0, 2), (2, 2)),
                ((1, 2), (2, 1)),
                ((2, 2), (2, 0))
            ]
        else:
            # Counter-clockwise rotation
            # In x-z plane: (x,z) -> (2-z, x)
            positions = [
                ((0, 0), (2, 0)),
                ((1, 0), (2, 1)),
                ((2, 0), (2, 2)),
                ((0, 1), (1, 0)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 2)),
                ((0, 2), (0, 0)),
                ((1, 2), (0, 1)),
                ((2, 2), (0, 2))
            ]

        for (old_x, old_z), (new_x, new_z) in positions:
            old_colors = old_layer[old_x][old_z]
            new_colors = {}

            # Copy all colors first
            for key in old_colors:
                new_colors[key] = old_colors[key]

            if clockwise:
                # When rotating clockwise around y-axis (viewed from above):
                # front -> right, right -> back, back -> left, left -> front
                new_colors['front'] = old_colors['left']
                new_colors['right'] = old_colors['front']
                new_colors['back'] = old_colors['right']
                new_colors['left'] = old_colors['back']
            else:
                # Counter-clockwise rotation
                # front -> left, left -> back, back -> right, right -> front
                new_colors['front'] = old_colors['right']
                new_colors['left'] = old_colors['front']
                new_colors['back'] = old_colors['left']
                new_colors['right'] = old_colors['back']

            self.state[new_x, 2, new_z] = new_colors

    def rotate_back(self, clockwise=True):
        """Rotate back face (z=0)"""
        old_layer = [[self.state[x, y, 0].copy() for y in range(3)] for x in range(3)]

        # For back face, viewing from front means we see it mirrored
        # So clockwise from the back perspective is counter-clockwise from front
        if clockwise:
            positions = [
                ((0, 0), (2, 0)),
                ((1, 0), (2, 1)),
                ((2, 0), (2, 2)),
                ((0, 1), (1, 0)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 2)),
                ((0, 2), (0, 0)),
                ((1, 2), (0, 1)),
                ((2, 2), (0, 2))
            ]
            # Rotate stickers: when viewing from back, clockwise means
            # up -> left, left -> down, down -> right, right -> up
            sticker_rotation = lambda old: {
                'front': old['front'],
                'back': old['back'],
                'left': old['up'],
                'right': old['down'],
                'up': old['right'],
                'down': old['left']
            }
        else:
            positions = [
                ((0, 0), (0, 2)),
                ((1, 0), (0, 1)),
                ((2, 0), (0, 0)),
                ((0, 1), (1, 2)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 0)),
                ((0, 2), (2, 2)),
                ((1, 2), (2, 1)),
                ((2, 2), (2, 0))
            ]
            sticker_rotation = lambda old: {
                'front': old['front'],
                'back': old['back'],
                'left': old['down'],
                'right': old['up'],
                'up': old['left'],
                'down': old['right']
            }

        for (old_x, old_y), (new_x, new_y) in positions:
            old_colors = old_layer[old_x][old_y]
            new_colors = sticker_rotation(old_colors)
            self.state[new_x, new_y, 0] = new_colors

    def rotate_left(self, clockwise=True):
        """Rotate left face (x=0)"""
        old_layer = [[self.state[0, y, z].copy() for z in range(3)] for y in range(3)]

        if clockwise:
            # Clockwise when viewed from the left
            positions = [
                ((0, 0), (0, 2)),
                ((1, 0), (0, 1)),
                ((2, 0), (0, 0)),
                ((0, 1), (1, 2)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 0)),
                ((0, 2), (2, 2)),
                ((1, 2), (2, 1)),
                ((2, 2), (2, 0))
            ]
        else:
            # Counter-clockwise
            positions = [
                ((0, 0), (2, 0)),
                ((1, 0), (2, 1)),
                ((2, 0), (2, 2)),
                ((0, 1), (1, 0)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 2)),
                ((0, 2), (0, 0)),
                ((1, 2), (0, 1)),
                ((2, 2), (0, 2))
            ]

        for (old_y, old_z), (new_y, new_z) in positions:
            old_colors = old_layer[old_y][old_z]
            new_colors = {}

            for key in old_colors:
                new_colors[key] = old_colors[key]

            if clockwise:
                # When rotating left face clockwise (viewed from left):
                # front -> up, up -> back, back -> down, down -> front
                new_colors['up'] = old_colors['front']
                new_colors['back'] = old_colors['up']
                new_colors['down'] = old_colors['back']
                new_colors['front'] = old_colors['down']
            else:
                # Counter-clockwise
                new_colors['front'] = old_colors['up']
                new_colors['up'] = old_colors['back']
                new_colors['back'] = old_colors['down']
                new_colors['down'] = old_colors['front']

            self.state[0, new_y, new_z] = new_colors

    def rotate_down(self, clockwise=True):
        """Rotate down face (y=0)"""
        old_layer = [[self.state[x, 0, z].copy() for z in range(3)] for x in range(3)]

        # For down face, when viewed from below, rotation is opposite
        if clockwise:
            positions = [
                ((0, 0), (2, 0)),
                ((1, 0), (2, 1)),
                ((2, 0), (2, 2)),
                ((0, 1), (1, 0)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 2)),
                ((0, 2), (0, 0)),
                ((1, 2), (0, 1)),
                ((2, 2), (0, 2))
            ]
            # When rotating down face clockwise (viewed from below):
            # right -> front, front -> left, left -> back, back -> right
            sticker_rotation = lambda old: {
                'front': old['right'],
                'back': old['left'],
                'left': old['front'],
                'right': old['back'],
                'up': old['up'],
                'down': old['down']
            }
        else:
            positions = [
                ((0, 0), (0, 2)),
                ((1, 0), (0, 1)),
                ((2, 0), (0, 0)),
                ((0, 1), (1, 2)),
                ((1, 1), (1, 1)),
                ((2, 1), (1, 0)),
                ((0, 2), (2, 2)),
                ((1, 2), (2, 1)),
                ((2, 2), (2, 0))
            ]
            sticker_rotation = lambda old: {
                'front': old['left'],
                'back': old['right'],
                'left': old['back'],
                'right': old['front'],
                'up': old['up'],
                'down': old['down']
            }

        for (old_x, old_z), (new_x, new_z) in positions:
            old_colors = old_layer[old_x][old_z]
            new_colors = sticker_rotation(old_colors)
            self.state[new_x, 0, new_z] = new_colors

# Create interactive visualization
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

cube = RubiksCube()
cube.draw_cube(ax)

# Add rotation buttons
def on_button_click(event, face, clockwise):
    cube.rotate_face(face, clockwise)
    cube.draw_cube(ax)
    plt.draw()

# Create button panel
button_ax = []
buttons = []
button_labels = [
    ('F', True, 'Front CW'),
    ('F', False, 'Front CCW'),
    ('B', True, 'Back CW'),
    ('B', False, 'Back CCW'),
    ('R', True, 'Right CW'),
    ('R', False, 'Right CCW'),
    ('L', True, 'Left CW'),
    ('L', False, 'Left CCW'),
    ('U', True, 'Up CW'),
    ('U', False, 'Up CCW'),
    ('D', True, 'Down CW'),
    ('D', False, 'Down CCW')
]

from matplotlib.widgets import Button

for i, (face, clockwise, label) in enumerate(button_labels):
    row = i // 4
    col = i % 4
    ax_button = plt.axes([0.05 + col * 0.23, 0.08 - row * 0.045, 0.18, 0.035])
    button = Button(ax_button, label)
    button.on_clicked(lambda event, f=face, cw=clockwise: on_button_click(event, f, cw))
    button_ax.append(ax_button)
    buttons.append(button)

plt.show()
