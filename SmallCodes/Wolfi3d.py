"""
3D Raycasting Engine in Python
Basierend auf der Java Engine3D Implementation
Steuerung: Pfeiltasten (↑↓←→)
"""

import pygame
import math
import sys

# =============================================================================
# TEXTUREN - Eingebettet als Pixel-Arrays
# =============================================================================

def create_wood_texture():
    """Holz-Textur (64x64)"""
    pixels = []
    for y in range(64):
        for x in range(64):
            # Vertikale Holzmaserung
            base = 139 + int(20 * math.sin(x * 0.3))
            variation = int(10 * math.sin(y * 0.1))
            r = max(0, min(255, base + variation))
            g = max(0, min(255, int(r * 0.6)))
            b = max(0, min(255, int(r * 0.3)))
            pixels.append((r, g, b))
    return pixels

def create_brick_texture():
    """Rote Ziegel-Textur (64x64)"""
    pixels = []
    for y in range(64):
        for x in range(64):
            # Ziegel-Muster
            brick_x = (x % 32) < 30
            brick_y = (y % 16) < 14
            # Versatz jede zweite Reihe
            if (y // 16) % 2 == 1:
                brick_x = ((x + 16) % 32) < 30
            
            if brick_x and brick_y:
                # Ziegel
                r = 150 + (x % 8) * 5
                g = 50 + (y % 4) * 3
                b = 40
            else:
                # Mörtel
                r, g, b = 180, 180, 180
            pixels.append((r, g, b))
    return pixels

def create_bluestone_texture():
    """Blaue Stein-Textur (64x64)"""
    pixels = []
    for y in range(64):
        for x in range(64):
            # Stein-Muster
            noise = int(20 * math.sin(x * 0.5) * math.cos(y * 0.5))
            r = max(0, min(255, 100 + noise))
            g = max(0, min(255, 100 + noise))
            b = max(0, min(255, 180 + noise))
            pixels.append((r, g, b))
    return pixels

def create_greystone_texture():
    """Graue Stein-Textur (64x64)"""
    pixels = []
    for y in range(64):
        for x in range(64):
            # Unregelmäßiges Stein-Muster
            base = 120
            noise = int(30 * math.sin(x * 0.3 + y * 0.4))
            gray = max(60, min(200, base + noise))
            pixels.append((gray, gray, gray))
    return pixels

# =============================================================================
# VEKTOR-KLASSE
# =============================================================================

class Vector:
    """Einfache 2D/3D Vektor-Klasse"""
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def rotate(self, angle):
        """Rotation um Z-Achse"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        new_x = self.x * cos_a - self.y * sin_a
        new_y = self.x * sin_a + self.y * cos_a
        return Vector(new_x, new_y, self.z)

# =============================================================================
# KAMERA/SPIELER
# =============================================================================

class Camera:
    """Spieler-Kamera mit Position und Blickrichtung"""
    def __init__(self, x, y, dir_x, dir_y, plane_x, plane_y):
        self.pos = Vector(x, y, 0)
        self.dir = Vector(dir_x, dir_y, 0)
        self.plane = Vector(plane_x, plane_y, 0)
        
        self.move_forward = False
        self.move_backward = False
        self.rotate_left = False
        self.rotate_right = False
        
        self.move_speed = 0.08
        self.rotation_speed = 0.045
    
    def update(self, world_map):
        """Update Kamera-Position und Rotation"""
        # Vorwärts/Rückwärts Bewegung
        if self.move_forward:
            next_x = self.pos.x + self.dir.x * self.move_speed
            next_y = self.pos.y + self.dir.y * self.move_speed
            
            # Kollisionsprüfung
            if world_map[int(next_x)][int(self.pos.y)] == 0:
                self.pos.x = next_x
            if world_map[int(self.pos.x)][int(next_y)] == 0:
                self.pos.y = next_y
        
        if self.move_backward:
            next_x = self.pos.x - self.dir.x * self.move_speed
            next_y = self.pos.y - self.dir.y * self.move_speed
            
            if world_map[int(next_x)][int(self.pos.y)] == 0:
                self.pos.x = next_x
            if world_map[int(self.pos.x)][int(next_y)] == 0:
                self.pos.y = next_y
        
        # Rotation
        if self.rotate_right:
            self.dir = self.dir.rotate(-self.rotation_speed)
            self.plane = self.plane.rotate(-self.rotation_speed)
        
        if self.rotate_left:
            self.dir = self.dir.rotate(self.rotation_speed)
            self.plane = self.plane.rotate(self.rotation_speed)

# =============================================================================
# RAYCASTING RENDERER
# =============================================================================

class RaycasterEngine:
    """3D Raycasting Engine"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Spielwelt (0 = frei, 1-4 = Wände mit verschiedenen Texturen)
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
        
        # Kamera initialisieren
        self.camera = Camera(4.5, 4.5, 1, 0, 0, -0.66)
        
        # Texturen laden
        self.textures = [
            create_wood_texture(),      # Index 0 (Wall-Type 1)
            create_brick_texture(),     # Index 1 (Wall-Type 2)
            create_bluestone_texture(), # Index 2 (Wall-Type 3)
            create_greystone_texture()  # Index 3 (Wall-Type 4)
        ]
        self.tex_size = 64
        
        # Pygame initialisieren
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("3D Raycaster Engine")
        self.clock = pygame.time.Clock()
        
        # Pixel-Array für direkten Zugriff
        self.pixel_array = pygame.surfarray.pixels3d(self.screen)
    
    def cast_ray(self, x):
        """Wirft einen Strahl für Bildschirm-Spalte x"""
        # Berechne Strahl-Richtung
        camera_x = 2 * x / self.width - 1
        ray_dir = Vector(
            self.camera.dir.x + self.camera.plane.x * camera_x,
            self.camera.dir.y + self.camera.plane.y * camera_x,
            0
        )
        
        # Aktuelle Map-Position
        map_x = int(self.camera.pos.x)
        map_y = int(self.camera.pos.y)
        
        # Länge des Strahls von einer Gitter-Seite zur nächsten
        delta_dist_x = abs(1 / ray_dir.x) if ray_dir.x != 0 else 1e30
        delta_dist_y = abs(1 / ray_dir.y) if ray_dir.y != 0 else 1e30
        
        # Richtung und initiale Distanz
        if ray_dir.x < 0:
            step_x = -1
            side_dist_x = (self.camera.pos.x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - self.camera.pos.x) * delta_dist_x
        
        if ray_dir.y < 0:
            step_y = -1
            side_dist_y = (self.camera.pos.y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - self.camera.pos.y) * delta_dist_y
        
        # DDA-Algorithmus: Verfolge Strahl bis zur Wand
        hit = False
        side = 0  # 0 = x-Seite, 1 = y-Seite
        
        while not hit:
            # Springe zum nächsten Grid-Quadrat
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
            
            # Prüfe ob Wand getroffen wurde
            if map_x < 0 or map_x >= len(self.world_map) or \
               map_y < 0 or map_y >= len(self.world_map[0]):
                hit = True
                wall_type = 1
            elif self.world_map[map_x][map_y] > 0:
                hit = True
                wall_type = self.world_map[map_x][map_y]
        
        # Berechne Distanz zur Wand (perpendikular zur Kamera, nicht direkt)
        if side == 0:
            perp_wall_dist = (map_x - self.camera.pos.x + (1 - step_x) / 2) / ray_dir.x
        else:
            perp_wall_dist = (map_y - self.camera.pos.y + (1 - step_y) / 2) / ray_dir.y
        
        # Verhindere Division durch 0
        if perp_wall_dist < 0.01:
            perp_wall_dist = 0.01
        
        # Berechne Höhe der Linie zum Zeichnen
        line_height = int(self.height / perp_wall_dist)
        
        # Berechne Start und Ende der vertikalen Linie
        draw_start = -line_height // 2 + self.height // 2
        if draw_start < 0:
            draw_start = 0
        draw_end = line_height // 2 + self.height // 2
        if draw_end >= self.height:
            draw_end = self.height - 1
        
        # Textur-Berechnung
        # Exakte Position wo die Wand getroffen wurde
        if side == 0:
            wall_x = self.camera.pos.y + perp_wall_dist * ray_dir.y
        else:
            wall_x = self.camera.pos.x + perp_wall_dist * ray_dir.x
        wall_x -= math.floor(wall_x)
        
        # X-Koordinate auf der Textur
        tex_x = int(wall_x * self.tex_size)
        if side == 0 and ray_dir.x > 0:
            tex_x = self.tex_size - tex_x - 1
        if side == 1 and ray_dir.y < 0:
            tex_x = self.tex_size - tex_x - 1
        
        return {
            'draw_start': draw_start,
            'draw_end': draw_end,
            'line_height': line_height,
            'tex_x': tex_x,
            'wall_type': wall_type,
            'side': side
        }
    
    def render(self):
        """Rendert die 3D-Szene"""
        # Hintergrund zeichnen
        # Obere Hälfte: Dunkelgrau (Himmel)
        self.pixel_array[:, :self.height//2] = (64, 64, 64)
        # Untere Hälfte: Hellgrau (Boden)
        self.pixel_array[:, self.height//2:] = (128, 128, 128)
        
        # Raycasting für jede Bildschirm-Spalte
        for x in range(self.width):
            ray_result = self.cast_ray(x)
            
            # Hole Textur (wall_type - 1, da Array 0-basiert ist)
            texture = self.textures[ray_result['wall_type'] - 1]
            
            # Zeichne vertikale texturierte Linie
            for y in range(ray_result['draw_start'], ray_result['draw_end']):
                # Y-Koordinate auf der Textur berechnen
                d = y * 2 - self.height + ray_result['line_height']
                tex_y = ((d * self.tex_size) // ray_result['line_height']) // 2
                
                # Begrenze tex_y auf gültige Werte
                tex_y = max(0, min(self.tex_size - 1, tex_y))
                
                # Hole Farbe aus Textur
                color = texture[ray_result['tex_x'] + tex_y * self.tex_size]
                
                # Mache y-Seiten dunkler für besseren 3D-Effekt
                if ray_result['side'] == 1:
                    color = (color[0] // 2, color[1] // 2, color[2] // 2)
                
                # Setze Pixel
                self.pixel_array[x, y] = color
    
    def handle_events(self):
        """Behandelt Eingaben"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Tastatur-Events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.camera.move_forward = True
                elif event.key == pygame.K_DOWN:
                    self.camera.move_backward = True
                elif event.key == pygame.K_LEFT:
                    self.camera.rotate_left = True
                elif event.key == pygame.K_RIGHT:
                    self.camera.rotate_right = True
                elif event.key == pygame.K_ESCAPE:
                    return False
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    self.camera.move_forward = False
                elif event.key == pygame.K_DOWN:
                    self.camera.move_backward = False
                elif event.key == pygame.K_LEFT:
                    self.camera.rotate_left = False
                elif event.key == pygame.K_RIGHT:
                    self.camera.rotate_right = False
        
        return True
    
    def run(self):
        """Haupt-Game-Loop"""
        running = True
        
        while running:
            # Events behandeln
            running = self.handle_events()
            
            # Kamera aktualisieren
            self.camera.update(self.world_map)
            
            # Szene rendern
            self.render()
            
            # Display aktualisieren
            pygame.display.flip()
            
            # FPS begrenzen
            self.clock.tick(60)
            
            # FPS anzeigen
            fps = int(self.clock.get_fps())
            pygame.display.set_caption(f"3D Raycaster Engine - FPS: {fps}")
        
        pygame.quit()
        sys.exit()

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Engine starten
    engine = RaycasterEngine(640, 480)
    engine.run()
