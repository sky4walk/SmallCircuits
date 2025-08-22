import pygame
from pygame.math import Vector3
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import numpy as np

# Game Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WORLD_SIZE = 32
CHUNK_SIZE = 16

class Block:
    def __init__(self, position, block_type):
        self.position = position
        self.type = block_type

    @staticmethod
    def get_block_color(block_type):
        colors = {
            'grass': (0.2, 0.8, 0.2, 1.0),     # Green
            'dirt':  (0.5, 0.35, 0.05, 1.0),   # Brown
            'stone': (0.5, 0.5, 0.5, 1.0),     # Gray
            'water': (0.0, 0.4, 0.8, 0.7),     # Transparent Blue
            'sand':  (0.9, 0.9, 0.6, 1.0),     # Light Yellow
            'wood':  (0.6, 0.4, 0.2, 1.0)      # Brown
        }
        return colors.get(block_type, (1.0, 1.0, 1.0, 1.0))

class World:
    def __init__(self):
        self.blocks = {}
        self.generate_terrain()

    def generate_terrain(self):
        # Noise generation for more natural terrain
        noise = np.random.rand(WORLD_SIZE, WORLD_SIZE)
        
        for x in range(WORLD_SIZE):
            for z in range(WORLD_SIZE):
                # Base terrain height
                height = int(noise[x, z] * 5) + 5
                
                for y in range(height):
                    if y == height - 1:
                        block_type = 'grass'
                    elif y > height - 4:
                        block_type = 'dirt'
                    else:
                        block_type = 'stone'
                    
                    self.blocks[(x, y, z)] = Block((x, y, z), block_type)
                
                # Add some water
                if height < 4:
                    for y in range(height, 4):
                        self.blocks[(x, y, z)] = Block((x, y, z), 'water')
                
                # Random features
                if random.random() < 0.05:
                    tree_height = random.randint(3, 6)
                    for ty in range(height, height + tree_height):
                        self.blocks[(x, ty, z)] = Block((x, ty, z), 'wood')

    def get_block(self, position):
        return self.blocks.get(position)

    def remove_block(self, position):
        if position in self.blocks:
            del self.blocks[position]

    def render(self):
        for block in self.blocks.values():
            self.render_block(block)

    def render_block(self, block):
        x, y, z = block.position
        color = Block.get_block_color(block.type)
        
        glColor4f(*color)
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Cube rendering
        vertices = [
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
            (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)
        ]
        
        faces = [
            (0, 1, 2, 3),  # Front
            (4, 5, 6, 7),  # Back
            (0, 4, 7, 3),  # Left
            (1, 5, 6, 2),  # Right
            (3, 2, 6, 7),  # Top
            (0, 1, 5, 4)   # Bottom
        ]
        
        # Render each face
        for face in faces:
            glBegin(GL_QUADS)
            for vertex in face:
                glVertex3fv(vertices[vertex])
            glEnd()
        
        glPopMatrix()

class Player:
    def __init__(self, position=None):
        self.position = position or Vector3(WORLD_SIZE // 2, 10, WORLD_SIZE // 2)
        self.rotation = Vector3(0, 0, 0)
        self.velocity = Vector3(0, 0, 0)
        self.flying = False
        self.inventory = {}

    def move(self, dx, dy, dz):
        # Simple movement with flying mode
        if self.flying:
            self.position += Vector3(dx, dy, dz)
        else:
            # Ground movement with basic gravity
            self.velocity.x = dx
            self.velocity.z = dz
            self.position.x += self.velocity.x
            self.position.z += self.velocity.z

    def mine_block(self, world):
        # Mine block in front of player
        look_dir = Vector3(
            -np.sin(np.radians(self.rotation.y)),
            -np.sin(np.radians(self.rotation.x)),
            -np.cos(np.radians(self.rotation.y))
        )
        target = (
            int(self.position.x + look_dir.x),
            int(self.position.y + look_dir.y),
            int(self.position.z + look_dir.z)
        )
        
        block = world.get_block(target)
        if block:
            block_type = block.type
            # Add to inventory
            self.inventory[block_type] = self.inventory.get(block_type, 0) + 1
            # Remove from world
            world.remove_block(target)

def main():
    pygame.init()
    display = (SCREEN_WIDTH, SCREEN_HEIGHT)
    pygame.display.set_mode(display, pygame.OPENGL | pygame.DOUBLEBUF)
    
    # OpenGL setup
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Projection setup
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    world = World()
    player = Player()
    
    clock = pygame.time.Clock()
    
    # Camera and movement variables
    mouse_sensitivity = 0.1
    last_mouse_pos = pygame.mouse.get_pos()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Mining blocks
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.mine_block(world)
                # Toggle flying mode
                if event.key == pygame.K_f:
                    player.flying = not player.flying

        # Mouse look
        mouse_pos = pygame.mouse.get_pos()
        mouse_dx = mouse_pos[0] - last_mouse_pos[0]
        mouse_dy = mouse_pos[1] - last_mouse_pos[1]
        
        # Update player rotation
        player.rotation.y += mouse_dx * mouse_sensitivity
        player.rotation.x -= mouse_dy * mouse_sensitivity
        
        # Clamp rotation
        player.rotation.x = max(min(player.rotation.x, 90), -90)
        
        last_mouse_pos = mouse_pos
        
        # Keyboard movement
        keys = pygame.key.get_pressed()
        move_speed = 0.1
        
        # Calculate movement based on player rotation
        forward = Vector3(
            -np.sin(np.radians(player.rotation.y)),
            0,
            -np.cos(np.radians(player.rotation.y))
        ).normalize()
        
        right = Vector3(
            np.cos(np.radians(player.rotation.y)),
            0,
            -np.sin(np.radians(player.rotation.y))
        ).normalize()
        
        if keys[pygame.K_w]:
            player.move(forward.x * move_speed, 0, forward.z * move_speed)
        if keys[pygame.K_s]:
            player.move(-forward.x * move_speed, 0, -forward.z * move_speed)
        if keys[pygame.K_a]:
            player.move(-right.x * move_speed, 0, -right.z * move_speed)
        if keys[pygame.K_d]:
            player.move(right.x * move_speed, 0, right.z * move_speed)
        if keys[pygame.K_SPACE] and player.flying:
            player.move(0, move_speed, 0)
        if keys[pygame.K_LSHIFT] and player.flying:
            player.move(0, -move_speed, 0)

        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Reset ModelView Matrix
        glLoadIdentity()
        
        # Apply camera transformations
        glRotatef(player.rotation.x, 1, 0, 0)
        glRotatef(player.rotation.y, 0, 1, 0)
        glTranslatef(-player.position.x, -player.position.y, -player.position.z)
        
        # Render world
        world.render()
        
        # Update display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)
    
    pygame.quit()

if __name__ == '__main__':
    main()