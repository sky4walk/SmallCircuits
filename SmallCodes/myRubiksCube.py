import matplotlib.pyplot as plt
import numpy as np
import random

def draw_rubiks_cube(state):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.set_frame_on(False)
    
    # Positionen für die 6 Flächen
    face_positions = {
        'U': (3, 6), 'L': (0, 3), 'F': (3, 3), 'R': (6, 3), 'B': (9, 3), 'D': (3, 0)
    }
    
    # Farben für die Flächen (Weiß, Rot, Blau, Orange, Grün, Gelb)
    face_colors = {'W': 'white', 'R': 'red', 'B': 'blue', 'O': 'orange', 'G': 'green', 'Y': 'yellow'}
    
    for face, (x_offset, y_offset) in face_positions.items():
        for i in range(3):
            for j in range(3):
                color = face_colors[state[face][i][j]]
                rect = plt.Rectangle((x_offset + j, y_offset + (2 - i)), 1, 1, edgecolor='black', facecolor=color)
                ax.add_patch(rect)
                
    plt.show()

def rotate_face(face, counterclockwise=False, double=False):
    if double:
        return rotate_face(rotate_face(face))
    if counterclockwise:
        return [list(row) for row in zip(*face)][::-1]
    return [list(row) for row in zip(*face[::-1])]

def rotate_cube(state, moves):
    if isinstance(moves, str):
        moves = [moves]
    
    for move in moves:
        counterclockwise = "'" in move
        double = "2" in move
        move = move.replace("'", "").replace("2", "")
        
        if move in ['U', 'D', 'F', 'B', 'L', 'R']:
            state[move] = rotate_face(state[move], counterclockwise, double)
        
        for _ in range(2 if double else 1):
            if move == 'U':
                state['F'][0], state['R'][0], state['B'][0], state['L'][0] = state['R'][0], state['B'][0], state['L'][0], state['F'][0]
            elif move == 'D':
                state['F'][2], state['L'][2], state['B'][2], state['R'][2] = state['L'][2], state['B'][2], state['R'][2], state['F'][2]
            elif move == 'F':
                for i in range(3):
                    state['U'][2][i], state['R'][i][0], state['D'][0][2 - i], state['L'][2 - i][2] = state['L'][2 - i][2], state['U'][2][i], state['R'][i][0], state['D'][0][2 - i]
            elif move == 'B':
                for i in range(3):
                    state['U'][0][i], state['L'][2 - i][0], state['D'][2][2 - i], state['R'][i][2] = state['R'][i][2], state['U'][0][i], state['L'][2 - i][0], state['D'][2][2 - i]
            elif move == 'L':
                for i in range(3):
                    state['U'][i][0], state['B'][2 - i][2], state['D'][i][0], state['F'][i][0] = state['F'][i][0], state['U'][i][0], state['B'][2 - i][2], state['D'][i][0]
            elif move == 'R':
                for i in range(3):
                    state['U'][i][2], state['F'][i][2], state['D'][i][2], state['B'][2 - i][0] = state['B'][2 - i][0], state['U'][i][2], state['F'][i][2], state['D'][i][2]
    
    return state


def generate_random_moves(num_moves=20):
    possible_moves = ['U', 'D', 'F', 'B', 'L', 'R']
    modifiers = ['', "'", '2']
    return [random.choice(possible_moves) + random.choice(modifiers) for _ in range(num_moves)]

def find_edges_color(state, color):
    color_edges = []
    edge_positions = {
        'U': [(0, 1), (1, 0), (1, 2), (2, 1)],
        'D': [(0, 1), (1, 0), (1, 2), (2, 1)],
        'F': [(0, 1), (1, 0), (1, 2), (2, 1)],
        'B': [(0, 1), (1, 0), (1, 2), (2, 1)],
        'L': [(0, 1), (1, 0), (1, 2), (2, 1)],
        'R': [(0, 1), (1, 0), (1, 2), (2, 1)]
    }
    
    for face, positions in edge_positions.items():
        for pos in positions:
            if state[face][pos[0]][pos[1]] == color:
                color_edges.append((face, pos))
    
    return color_edges

def find_corners_color(state, color):
    color_corners = []
    corner_positions = {
        'U': [(0, 0), (0, 2), (2, 0), (2, 2)],
        'D': [(0, 0), (0, 2), (2, 0), (2, 2)],
        'F': [(0, 0), (0, 2), (2, 0), (2, 2)],
        'B': [(0, 0), (0, 2), (2, 0), (2, 2)],
        'L': [(0, 0), (0, 2), (2, 0), (2, 2)],
        'R': [(0, 0), (0, 2), (2, 0), (2, 2)]
    }
    
    for face, positions in corner_positions.items():
        for pos in positions:
            if state[face][pos[0]][pos[1]] == 'W':
                color_corners.append((face, pos))
    
    return color_corners

# Initialer Zustand des Rubik's Cubes
initial_state = {
    'U': [['W', 'W', 'W'], ['W', 'W', 'W'], ['W', 'W', 'W']],
    'L': [['O', 'O', 'O'], ['O', 'O', 'O'], ['O', 'O', 'O']],
    'F': [['G', 'G', 'G'], ['G', 'G', 'G'], ['G', 'G', 'G']],
    'R': [['R', 'R', 'R'], ['R', 'R', 'R'], ['R', 'R', 'R']],
    'B': [['B', 'B', 'B'], ['B', 'B', 'B'], ['B', 'B', 'B']],
    'D': [['Y', 'Y', 'Y'], ['Y', 'Y', 'Y'], ['Y', 'Y', 'Y']]
}

random_moves = generate_random_moves()
print("Random Moves:", random_moves)

positions = find_edges_color(initial_state,'W')
print("positions w:",positions)
cornercolors = find_corners_color(initial_state,'W')
print("positions corners w:",positions)

draw_rubiks_cube(initial_state)

# Beispiel: Lösungsalgorithmus ausführen
initial_state = rotate_cube(initial_state,random_moves)
draw_rubiks_cube(initial_state)

