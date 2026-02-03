#!/usr/bin/env python3
"""
3D ASCII Raycaster Engine - Verbesserte Version
Mit funktionierendem Input!
Steuerung: w/a/s/d (dann ENTER), q zum Beenden
"""

import math
import sys
import time
import os

# =============================================================================
# VEKTOR-KLASSE
# =============================================================================

class Vector:
    def __init__(self, x=0.0, y=0.0):
        self.x, self.y = float(x), float(y)
    
    def __add__(self, o): return Vector(self.x + o.x, self.y + o.y)
    def __sub__(self, o): return Vector(self.x - o.x, self.y - o.y)
    def __mul__(self, s): return Vector(self.x * s, self.y * s)
    
    def rotate(self, angle):
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        return Vector(self.x * cos_a - self.y * sin_a,
                     self.x * sin_a + self.y * cos_a)

# =============================================================================
# KAMERA
# =============================================================================

class Camera:
    def __init__(self, x, y, dx, dy, px, py):
        self.pos = Vector(x, y)
        self.dir = Vector(dx, dy)
        self.plane = Vector(px, py)
        self.move_speed = 0.3
        self.rot_speed = 0.15
    
    def move_forward(self, world):
        next_pos = self.pos + self.dir * self.move_speed
        if world[int(next_pos.x)][int(self.pos.y)] == 0:
            self.pos.x = next_pos.x
        if world[int(self.pos.x)][int(next_pos.y)] == 0:
            self.pos.y = next_pos.y
    
    def move_backward(self, world):
        next_pos = self.pos - self.dir * self.move_speed
        if world[int(next_pos.x)][int(self.pos.y)] == 0:
            self.pos.x = next_pos.x
        if world[int(self.pos.x)][int(next_pos.y)] == 0:
            self.pos.y = next_pos.y
    
    def rotate_left(self):
        self.dir = self.dir.rotate(self.rot_speed)
        self.plane = self.plane.rotate(self.rot_speed)
    
    def rotate_right(self):
        self.dir = self.dir.rotate(-self.rot_speed)
        self.plane = self.plane.rotate(-self.rot_speed)

# =============================================================================
# ASCII RAYCASTER
# =============================================================================

class ASCIIRaycaster:
    def __init__(self, width=80, height=24):
        self.width = width
        self.height = height
        
        # Spielwelt
        self.world_map = [
            [1,1,1,1,1,1,1,1,2,2,2,2,2,2,2],
            [1,0,0,0,0,0,0,0,2,0,0,0,0,0,2],
            [1,0,3,3,3,3,3,0,0,0,0,0,0,0,2],
            [1,0,3,0,0,0,3,0,2,0,0,0,0,0,2],
            [1,0,3,0,0,0,3,0,2,2,2,0,2,2,2],
            [1,0,3,0,0,0,3,0,2,0,0,0,0,0,2],
            [1,0,3,3,0,3,3,0,2,0,0,0,0,0,2],
            [1,0,0,0,0,0,0,0,2,0,0,0,0,0,2],
            [1,1,1,1,1,1,1,1,4,4,4,0,4,4,4],
            [1,0,0,0,0,0,1,4,0,0,0,0,0,0,4],
            [1,0,0,0,0,0,1,4,0,0,0,0,0,0,4],
            [1,0,0,0,0,0,1,4,0,3,3,3,3,0,4],
            [1,0,0,0,0,0,1,4,0,3,3,3,3,0,4],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,4],
            [1,1,1,1,1,1,1,4,4,4,4,4,4,4,4]
        ]
        
        self.camera = Camera(4.5, 4.5, 1, 0, 0, -0.66)
        
        # ASCII Zeichen für verschiedene Wände (dunkel -> hell)
        self.wall_chars = {
            1: " .:-=+*#%@",      # Holz
            2: " .:;+=xX$&#",     # Ziegel  
            3: " .'`^\"~<>i!",    # Blauer Stein
            4: " .,;:!/>?[]{}",   # Grauer Stein
        }
    
    def cast_ray(self, x):
        """Wirft einen Strahl"""
        camera_x = 2 * x / self.width - 1
        ray_dir = Vector(
            self.camera.dir.x + self.camera.plane.x * camera_x,
            self.camera.dir.y + self.camera.plane.y * camera_x
        )
        
        map_x, map_y = int(self.camera.pos.x), int(self.camera.pos.y)
        
        ddx = abs(1 / ray_dir.x) if ray_dir.x != 0 else 1e30
        ddy = abs(1 / ray_dir.y) if ray_dir.y != 0 else 1e30
        
        if ray_dir.x < 0:
            step_x, sdx = -1, (self.camera.pos.x - map_x) * ddx
        else:
            step_x, sdx = 1, (map_x + 1.0 - self.camera.pos.x) * ddx
        
        if ray_dir.y < 0:
            step_y, sdy = -1, (self.camera.pos.y - map_y) * ddy
        else:
            step_y, sdy = 1, (map_y + 1.0 - self.camera.pos.y) * ddy
        
        # DDA
        hit, side = False, 0
        while not hit:
            if sdx < sdy:
                sdx += ddx
                map_x += step_x
                side = 0
            else:
                sdy += ddy
                map_y += step_y
                side = 1
            
            if map_x < 0 or map_x >= len(self.world_map) or \
               map_y < 0 or map_y >= len(self.world_map[0]):
                hit, wall_type = True, 1
            elif self.world_map[map_x][map_y] > 0:
                hit, wall_type = True, self.world_map[map_x][map_y]
        
        if side == 0:
            dist = (map_x - self.camera.pos.x + (1 - step_x) / 2) / ray_dir.x
        else:
            dist = (map_y - self.camera.pos.y + (1 - step_y) / 2) / ray_dir.y
        
        return max(0.1, dist), wall_type, side
    
    def clear_screen(self):
        """Löscht den Bildschirm"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def render(self):
        """Rendert die ASCII-Szene"""
        buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Boden (untere Hälfte)
        for y in range(self.height // 2, self.height):
            for x in range(self.width):
                buffer[y][x] = '.'
        
        # Raycasting für jede Spalte
        for x in range(self.width):
            dist, wall_type, side = self.cast_ray(x)
            
            line_height = int(self.height / dist) if dist > 0 else self.height
            draw_start = max(0, -line_height // 2 + self.height // 2)
            draw_end = min(self.height - 1, line_height // 2 + self.height // 2)
            
            # Wähle Zeichen basierend auf Wand-Typ
            char_set = self.wall_chars[wall_type]
            brightness = int((1.0 - min(dist / 8.0, 1.0)) * (len(char_set) - 1))
            
            # Seiten dunkler
            if side == 1:
                brightness = max(0, brightness - 3)
            
            char = char_set[min(brightness, len(char_set) - 1)]
            
            # Zeichne vertikale Linie
            for y in range(draw_start, draw_end + 1):
                buffer[y][x] = char
        
        # Ausgabe
        self.clear_screen()
        for row in buffer:
            print(''.join(row))
        
        print(f"\nPos: ({self.camera.pos.x:.1f}, {self.camera.pos.y:.1f}) | " +
              f"Blick: ({self.camera.dir.x:.2f}, {self.camera.dir.y:.2f})")
        print("\nSteuerung: W=Vor, S=Zurück, A=Links, D=Rechts, Q=Beenden")
        print("Eingabe (dann ENTER): ", end='', flush=True)
    
    def run(self):
        """Game Loop"""
        self.clear_screen()
        print("="*60)
        print("3D ASCII RAYCASTER")
        print("="*60)
        print("\nSteuerung:")
        print("  W - Vorwärts")
        print("  S - Rückwärts")
        print("  A - Links drehen")
        print("  D - Rechts drehen")
        print("  Q - Beenden")
        print("\nDrücke ENTER zum Starten...")
        input()
        
        running = True
        
        # Initiales Rendering
        self.render()
        
        while running:
            # Warte auf Input
            try:
                cmd = input().strip().lower()
                
                if not cmd:
                    # Bei leerem Input nur neu rendern
                    self.render()
                    continue
                
                # Verarbeite alle Zeichen im Input
                for ch in cmd:
                    if ch == 'w':
                        self.camera.move_forward(self.world_map)
                    elif ch == 's':
                        self.camera.move_backward(self.world_map)
                    elif ch == 'a':
                        self.camera.rotate_left()
                    elif ch == 'd':
                        self.camera.rotate_right()
                    elif ch == 'q':
                        running = False
                        break
                
                # Neu rendern nach Bewegung
                if running:
                    self.render()
                    
            except KeyboardInterrupt:
                running = False
            except EOFError:
                running = False
        
        self.clear_screen()
        print("\nGame beendet. Tschüss!")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    try:
        # Terminal-Größe anpassen (optional)
        raycaster = ASCIIRaycaster(width=80, height=24)
        raycaster.run()
    except Exception as e:
        print(f"\nFehler: {e}")
        import traceback
        traceback.print_exc()
