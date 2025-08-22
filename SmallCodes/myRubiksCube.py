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

def copy_cube_state(state):
    return {face: [row[:] for row in state[face]] for face in state}

def rotate_face(face, counterclockwise=False, double=False):
    if double:
        return rotate_face(rotate_face(face))
    if counterclockwise:
        return [list(row) for row in zip(*face[::-1])]
    return [list(row) for row in zip(*face)][::-1]

def rotate_cube(outer_state, moves):
    if isinstance(moves, str):
        moves = [moves]
    
    state = copy_cube_state(outer_state)

    for move in moves:
        counterclockwise = "'" in move
        double = "2" in move
        move = move.replace("'", "").replace("2", "")
        
        if move in ['U', 'D', 'F', 'B', 'L', 'R']:
            state[move] = rotate_face(state[move], counterclockwise, double)
        
        for _ in range(2 if double else 1):
            
            if move == 'U': #up
                state['F'][0], state['R'][0], state['B'][0], state['L'][0] = state['R'][0], state['B'][0], state['L'][0], state['F'][0]
            elif move == 'D': #down
                state['F'][2], state['L'][2], state['B'][2], state['R'][2] = state['L'][2], state['B'][2], state['R'][2], state['F'][2]
            elif move == 'F':  # Front
                temp = state['U'][2].copy()
                for i in range(3):
                    state['U'][2][i]     = state['L'][2 - i][2]
                    state['L'][2 - i][2] = state['D'][0][2 - i]
                    state['D'][0][2 - i] = state['R'][i][0]
                    state['R'][i][0]     = temp[i]
            elif move == 'B': #back
                for i in range(3):
                    state['U'][0][i], state['L'][2 - i][0], state['D'][2][2 - i], state['R'][i][2] = state['R'][i][2], state['U'][0][i], state['L'][2 - i][0], state['D'][2][2 - i]
            elif move == 'L': #left
                for i in range(3):
                    state['U'][i][0], state['B'][2 - i][2], state['D'][i][0], state['F'][i][0] = state['F'][i][0], state['U'][i][0], state['B'][2 - i][2], state['D'][i][0]
            elif move == 'R': #right
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
            if state[face][pos[0]][pos[1]] == color:
                color_corners.append((face, pos))
    
    return color_corners

def find_center_color(state, color):
    color_corners = []
    corner_positions = {
        'U': [(1, 1)],
        'D': [(1, 1)],
        'F': [(1, 1)],
        'B': [(1, 1)],
        'L': [(1, 1)],
        'R': [(1, 1)]
    }
    
    for face, positions in corner_positions.items():
        for pos in positions:
            if state[face][pos[0]][pos[1]] == color:
                color_corners.append((face, pos))
    
    return color_corners

def print_rubiks_cube(state):
    for face in ['U', 'L', 'F', 'R', 'B', 'D']:
        print(face + ':')
        for row in state[face]:
            print(' '.join(row))
        print()

def print_rubiks_cube_2D(state):
    net = [[' ']*12 for _ in range(9)]
    
    positions = {
        'U': (0, 3), 'L': (3, 0), 'F': (3, 3), 'R': (3, 6), 'B': (3, 9), 'D': (6, 3)
    }
    
    for face, (x_offset, y_offset) in positions.items():
        for i in range(3):
            for j in range(3):
                net[x_offset + i][y_offset + j] = state[face][i][j]
    
    for row in net:
        print(' '.join(row))

def generate_initial_state():
    # Initialer Zustand des Rubik's Cubes
    initial_state = {
        'U': [['W', 'W', 'W'], ['W', 'W', 'W'], ['W', 'W', 'W']], 
        'L': [['O', 'O', 'O'], ['O', 'O', 'O'], ['O', 'O', 'O']], 
        'F': [['G', 'G', 'G'], ['G', 'G', 'G'], ['G', 'G', 'G']],
        'R': [['R', 'R', 'R'], ['R', 'R', 'R'], ['R', 'R', 'R']],
        'B': [['B', 'B', 'B'], ['B', 'B', 'B'], ['B', 'B', 'B']],
        'D': [['Y', 'Y', 'Y'], ['Y', 'Y', 'Y'], ['Y', 'Y', 'Y']]
    }
    return initial_state

def get_corresponding_corner_positions(face, pos):
    corner_map = {
        'U': {(0, 0): [('L', (0, 0)), ('B', (0, 2))],
              (0, 2): [('B', (0, 0)), ('R', (0, 2))],
              (2, 0): [('L', (0, 2)), ('F', (0, 0))],
              (2, 2): [('F', (0, 2)), ('R', (0, 0))]},
        
        'D': {(0, 0): [('L', (2, 0)), ('F', (2, 0))],
              (0, 2): [('F', (2, 2)), ('R', (2, 0))],
              (2, 0): [('L', (2, 2)), ('B', (2, 2))],
              (2, 2): [('B', (2, 0)), ('R', (2, 2))]},
        
        'F': {(0, 0): [('U', (2, 0)), ('L', (0, 2))],
              (0, 2): [('U', (2, 2)), ('R', (0, 0))],
              (2, 0): [('D', (0, 0)), ('L', (2, 2))],
              (2, 2): [('D', (0, 2)), ('R', (2, 0))]},
        
        'B': {(0, 0): [('U', (0, 2)), ('R', (0, 2))],
              (0, 2): [('U', (0, 0)), ('L', (0, 0))],
              (2, 0): [('D', (2, 2)), ('R', (2, 2))],
              (2, 2): [('D', (2, 0)), ('L', (2, 0))]},
        
        'L': {(0, 0): [('U', (0, 0)), ('B', (0, 2))],
              (0, 2): [('U', (2, 0)), ('F', (0, 0))],
              (2, 0): [('D', (2, 0)), ('B', (2, 2))],
              (2, 2): [('D', (0, 0)), ('F', (2, 0))]},
        
        'R': {(0, 0): [('U', (2, 2)), ('F', (0, 2))],
              (0, 2): [('U', (0, 2)), ('B', (0, 0))],
              (2, 0): [('D', (0, 2)), ('F', (2, 2))],
              (2, 2): [('D', (2, 2)), ('B', (2, 0))]}
    }
    
    return corner_map.get(face, {}).get(pos, [])
    
def get_corresponding_edge_positions(face, pos):
    edge_map = {
        'U': {(0, 1): ('B', (0, 1)), (1, 0): ('L', (0, 1)), (1, 2): ('R', (0, 1)), (2, 1): ('F', (0, 1))},
        'D': {(0, 1): ('F', (2, 1)), (1, 0): ('L', (2, 1)), (1, 2): ('R', (2, 1)), (2, 1): ('B', (2, 1))},
        'F': {(0, 1): ('U', (2, 1)), (1, 0): ('L', (1, 2)), (1, 2): ('R', (1, 0)), (2, 1): ('D', (0, 1))},
        'B': {(0, 1): ('U', (0, 1)), (1, 0): ('R', (1, 2)), (1, 2): ('L', (1, 0)), (2, 1): ('D', (2, 1))},
        'L': {(0, 1): ('U', (1, 0)), (1, 0): ('B', (1, 2)), (1, 2): ('F', (1, 0)), (2, 1): ('D', (1, 0))},
        'R': {(0, 1): ('U', (1, 2)), (1, 0): ('F', (1, 2)), (1, 2): ('B', (1, 0)), (2, 1): ('D', (1, 2))}
    }
    
    return edge_map.get(face, {}).get(pos, None)

def get_color_of_position(state, face, pos):
    """Gibt die Farbe einer bestimmten Position auf dem Rubik's Cube zurück."""
    if face in state and 0 <= pos[0] < 3 and 0 <= pos[1] < 3:
        return state[face][pos[0]][pos[1]]
    return None  # Falls eine ungültige Eingabe gemacht wurde

initial_state = generate_initial_state()

state1 = rotate_cube(initial_state,"U")
draw_rubiks_cube(state1)

state2 = rotate_cube(state1,"R")
draw_rubiks_cube(state2)

state3 = rotate_cube(state2,"U")
draw_rubiks_cube(state3)


random_moves = generate_random_moves()
print("Random Moves:", random_moves)

positions = find_edges_color(initial_state,'W')
print("positions w:",positions)
cornercolors = find_corners_color(initial_state,'W')
print("corners w:",cornercolors)

retState = get_color_of_position(initial_state,'U',(0,2))
print("farbe ",retState)

cntrpos = find_center_color(initial_state,'R')
print("center r:",cntrpos)

corresponding_corners = get_corresponding_corner_positions('U', (2,2))
print(f"Die angrenzenden Ecken sind: {corresponding_corners}")

corresponding_edge = get_corresponding_edge_positions('U', (2,1))
print(f"Die angrenzende Kante von ist: {corresponding_edge}")