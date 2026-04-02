import pygame
from .config import *
import random
from .entities import Wall
from .terrain import Water, Barrier, Forest

class Grid:
    def __init__(self):
        self.entities = {}  #{(x, y): entity}
        self.fire_tiles = set() # Mark entity as destroyed when health is depleted

    def add_entity(self, entity):
        self.entities[(entity.x_pos, entity.y_pos)] = entity

    def is_blocked(self, x, y):
        entity = self.entities.get((x, y))
        return entity is not None and entity.blocking
    
    def get_terrain_modifier(self, x, y):
        """
        Returns the movement cost modifier for a cell.
        Forest = 2.0, everything else = 1.0.
        
        Hook this into metrics.cell_movement_cost for fuel-aware pathing.
        """
        entity = self.entities.get((x, y))
        if isinstance(entity, Forest):
            return Forest.COST_MULTIPLIER
        return 1.0

    def is_forest(self, x, y):
        """Check if a cell contains a forest tile."""
        entity = self.entities.get((x, y))
        return isinstance(entity, Forest)

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

    def rand_gen_water(self, body_count=3, min_body_size=4, max_body_size=10):
        """
        Generate natural-looking water bodies using a flood-fill approach.
        Each body starts at a random seed and grows outward, producing
        organic pond/river shapes rather than uniform rectangles.

        Args:
            body_count: number of distinct water bodies to generate
            min_body_size: minimum tiles per body
            max_body_size: maximum tiles per body
        """
        for _ in range(body_count):
            # Pick a seed cell that is not already occupied
            attempts = 0
            while attempts < 100:
                sx = random.randint(2, GRID_WIDTH - 3)
                sy = random.randint(2, GRID_HEIGHT - 3)
                if (sx, sy) not in self.entities:
                    break
                attempts += 1
            else:
                continue

            size = random.randint(min_body_size, max_body_size)
            frontier = [(sx, sy)]
            placed = set()

            while frontier and len(placed) < size:
                random.shuffle(frontier)
                cx, cy = frontier.pop()

                if (cx, cy) in placed or (cx, cy) in self.entities:
                    continue
                if not (0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT):
                    continue

                self.add_entity(Water(cx, cy))
                placed.add((cx, cy))

                # Expand to neighbors with some randomness for organic shape
                for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) not in placed and random.random() < 0.7:
                        frontier.append((nx, ny))

    def rand_gen_barriers(self, count=15):
        """
        Generate barrier clusters (rubble, collapsed structures).
        Barriers form small tight groups of 2-4 tiles.
        """
        clusters = max(1, count // 3)

        for _ in range(clusters):
            attempts = 0
            while attempts < 100:
                cx = random.randint(1, GRID_WIDTH - 2)
                cy = random.randint(1, GRID_HEIGHT - 2)
                if (cx, cy) not in self.entities:
                    break
                attempts += 1
            else:
                continue

            cluster_size = random.randint(2, 4)
            self.add_entity(Barrier(cx, cy))

            for _ in range(cluster_size - 1):
                dx = random.randint(-1, 1)
                dy = random.randint(-1, 1)
                bx, by = cx + dx, cy + dy
                if (0 <= bx < GRID_WIDTH and 0 <= by < GRID_HEIGHT
                        and (bx, by) not in self.entities):
                    self.add_entity(Barrier(bx, by))

    def rand_gen_forest(self, patch_count=4, min_patch_size=6, max_patch_size=14):
        """
        Generate forest patches using organic growth similar to water bodies.
        Forest is passable but costs extra fuel, so patches should be large
        enough that routing through vs around is a meaningful decision.
        """
        for _ in range(patch_count):
            attempts = 0
            while attempts < 100:
                sx = random.randint(2, GRID_WIDTH - 3)
                sy = random.randint(2, GRID_HEIGHT - 3)
                if (sx, sy) not in self.entities:
                    break
                attempts += 1
            else:
                continue

            size = random.randint(min_patch_size, max_patch_size)
            frontier = [(sx, sy)]
            placed = set()

            while frontier and len(placed) < size:
                random.shuffle(frontier)
                cx, cy = frontier.pop()

                if (cx, cy) in placed or (cx, cy) in self.entities:
                    continue
                if not (0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT):
                    continue

                self.add_entity(Forest(cx, cy))
                placed.add((cx, cy))

                for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) not in placed and random.random() < 0.65:
                        frontier.append((nx, ny))

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
        """
        Fire spreads from existing fire tiles into neighboring cells.
        Forest tiles increase spread chance (fire catches on trees).
        Water and barrier tiles block fire spread.
        """
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
             # Fire should not spread into blocked terrain (walls, water, barriers)
             if self.is_blocked(nx, ny):
                continue
             # Forest tiles have higher ignition chance
             if self.is_forest(nx, ny):
                 if random.random() < 0.8:  # 80% chance to catch forest on fire
                     new_fire_tiles.add((nx, ny))
             else:
                 new_fire_tiles.add((nx, ny))
                
        self.fire_tiles = new_fire_tiles
        

    def draw(self, window):

        # Draw the grid
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(window, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(window, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))

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
