import pygame
from .config import *
import random
from .entities import Wall

class Grid:
    def __init__(self):
        self.entities = {}  #{(x, y): entity}
        self.fire_tiles = set() # Mark entity as destroyed when health is depleted

    def add_entity(self, entity):
        self.entities[(entity.x_pos, entity.y_pos)] = entity

    def is_blocked(self, x, y):
        entity = self.entities.get((x, y))
        return entity is not None and entity.blocking
    
    def add_fire(self, x, y):
        # Fire is stored separately from entities so it behaves like a hazard layer
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            self.fire_tiles.add((x, y))

    def is_fire(self, x, y):
        # Returns True if this grid cell currently contains fire
        return (x, y) in self.fire_tiles

    def is_adjacent_to_fire(self, x, y):
        # Checks the four neighboring cells to see if the entity is near fire

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for dx, dy in directions:
            nx = x + dx
            ny = y + dy

            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                if self.is_fire(nx, ny):
                    return True

        return False

    def move_entity(self, entity, new_x, new_y, ignore_blocking=False):
        if not (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT):
            return False

        # Allowing for moving into own cell and enforcing blocking if not ignored
        if (
                not ignore_blocking
                and self.is_blocked(new_x, new_y)
                and (new_x, new_y) != (entity.x_pos, entity.y_pos)
        ):
            return False

        old_key = (entity.x_pos, entity.y_pos)
        if old_key in self.entities:
            del self.entities[old_key]

        entity.x_pos = new_x
        entity.y_pos = new_y
        self.entities[(new_x, new_y)] = entity
        return True

    def rand_gen_walls(self, count):
        placed = 0

        while placed < count:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)

            if (x,y) not in self.entities:
                self.add_entity(Wall(x,y))
                placed += 1

    def rand_gen_fire(self, movables, cluster_count=2, min_cluster_distance=6, min_entity_distance=6):
        # Generates clustered fire tiles while keeping them away from starting entities
        centers = []

        for _ in range(cluster_count):
            while True:
                cx = random.randint(0, GRID_WIDTH - 1)
                cy = random.randint(0, GRID_HEIGHT - 1)
                valid = True

                # Check distance from other fire clusters
                for ox, oy in centers:
                    dist = abs(cx - ox) + abs(cy - oy)
                    if dist < min_cluster_distance:
                        valid = False
                        break
                if not valid:
                    continue

                # Check distance from movable entities
                for m in movables:
                    dist = abs(cx - m.x_pos) + abs(cy - m.y_pos)
                    if dist < min_entity_distance:
                        valid = False
                        break
                if valid:
                    centers.append((cx, cy))
                    break

            # Generate cluster around center
            cluster_size = random.randint(2, 4)
            for _ in range(cluster_size):
                dx = random.randint(-1, 1)
                dy = random.randint(-1, 1)

                x = cx + dx
                y = cy + dy

                if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
                    continue
                if (x, y) not in self.entities:
                    self.add_fire(x, y)
    
    def spread_fire(self):
        # Fire spreads from existing fire tiles into neighboring cells over time
        new_fire_tiles = set(self.fire_tiles)
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for fx, fy in list(self.fire_tiles):
             if random.random() > 0.35:
                 continue
             dx, dy = random.choice(directions)
             nx, ny = fx + dx, fy + dy
             # Prevent fire from spreading outside the map
             if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                continue
             # Fire should not spread into blocked terrain such as walls
             if not self.is_blocked(nx, ny):
                new_fire_tiles.add((nx, ny))
                
        self.fire_tiles = new_fire_tiles
        

    def draw(self, window):

        # Draw the grid
        w = GRID_WIDTH * CELL_SIZE
        h = GRID_HEIGHT * CELL_SIZE
        for x in range(0, w + 1, CELL_SIZE):
            pygame.draw.line(window, GRID_COLOR, (x, 0), (x, h))
        for y in range(0, h + 1, CELL_SIZE):
            pygame.draw.line(window, GRID_COLOR, (0, y), (w, y))

        # Draw fire tiles
        for fx, fy in self.fire_tiles:
            rect = pygame.Rect(
                fx * CELL_SIZE,
                fy * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(window, (255, 100, 0), rect)

        # Draw entities
        for entity in self.entities.values():
            entity.draw(window)
