"""
grid_sim/terrain.py


Each terrain type is a non-blocking Entity subclass that modifies movement
cost and behavior when an entity steps onto or plans through it.

Terrain types:
    Water   - slows movement, high fuel cost multiplier, blocks fire spread
    Barrier - fully blocks movement (visually distinct from Wall)
    Forest  - partial concealment, moderate fuel cost increase

These plug into metrics.cell_movement_cost(terrain_modifier=...) via
grid.get_terrain_cost(x, y). The grid stores terrain separately from
walls so pathfinding and planning can query cost before committing.

Future-facing notes:
    - A* integration should read terrain cost from grid.get_terrain_cost(x, y)
    - Operators planning paths will see color-coded cells during PLANNING phase
    - Terrain can be procedurally generated or hand-placed per scenario

    Side note from Kiara
"""

import random
import pygame
from .config import CELL_SIZE, GRID_WIDTH, GRID_HEIGHT
from .entities import Entity


# ──────────────────────────────────────────────
# TERRAIN COST CONSTANTS
# ──────────────────────────────────────────────

WATER_COST_MULTIPLIER = 2.5
FOREST_COST_MULTIPLIER = 1.6
BARRIER_COST_MULTIPLIER = float("inf")


# ──────────────────────────────────────────────
# WATER
# ──────────────────────────────────────────────

class Water(Entity):
    """
    Water terrain. Passable but costly.

    Movement through water burns extra fuel (2.5x multiplier).
    Fire cannot spread onto water tiles.
    """
    COST_MULTIPLIER = WATER_COST_MULTIPLIER

    def __init__(self, x_pos, y_pos):
        blue = random.randint(140, 180)
        green = random.randint(80, 120)
        water_color = (30, green, blue)
        super().__init__(water_color, x_pos, y_pos, blocking=False)
        self.terrain_type = "water"

    def draw(self, window):
        rect = pygame.Rect(
            self.x_pos * CELL_SIZE,
            self.y_pos * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        pygame.draw.rect(window, self.color, rect)

        wave_y = rect.y + CELL_SIZE // 2
        wave_color = (
            min(self.color[0] + 40, 255),
            min(self.color[1] + 30, 255),
            min(self.color[2] + 30, 255),
        )
        pygame.draw.line(
            window, wave_color,
            (rect.x + 3, wave_y),
            (rect.x + CELL_SIZE - 3, wave_y),
            1,
        )


# ──────────────────────────────────────────────
# BARRIER
# ──────────────────────────────────────────────

class Barrier(Entity):
    """
    Impassable barrier. Blocks all movement and pathfinding.

    Represents deliberate obstructions (fences, rubble, debris)
    rather than structural walls.
    """
    COST_MULTIPLIER = BARRIER_COST_MULTIPLIER

    def __init__(self, x_pos, y_pos):
        barrier_color = (140, 50, 50)
        super().__init__(barrier_color, x_pos, y_pos, blocking=True)
        self.terrain_type = "barrier"

    def draw(self, window):
        rect = pygame.Rect(
            self.x_pos * CELL_SIZE,
            self.y_pos * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        pygame.draw.rect(window, self.color, rect)

        accent = (180, 70, 70)
        pygame.draw.line(window, accent, rect.topleft, rect.bottomright, 1)
        pygame.draw.line(window, accent, rect.topright, rect.bottomleft, 1)


# ──────────────────────────────────────────────
# FOREST
# ──────────────────────────────────────────────

class Forest(Entity):
    """
    Forest terrain. Passable with moderate cost increase.

    Provides concealment: entities inside forest have a reduced
    proximity detection radius (handled at the metrics layer).
    Movement costs 1.6x normal fuel.
    """
    COST_MULTIPLIER = FOREST_COST_MULTIPLIER
    CONCEALMENT_FACTOR = 0.5

    def __init__(self, x_pos, y_pos):
        green = random.randint(60, 100)
        red = random.randint(20, 45)
        forest_color = (red, green, 20)
        super().__init__(forest_color, x_pos, y_pos, blocking=False)
        self.terrain_type = "forest"

    def draw(self, window):
        rect = pygame.Rect(
            self.x_pos * CELL_SIZE,
            self.y_pos * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        pygame.draw.rect(window, self.color, rect)

        cx = rect.centerx
        cy = rect.centery
        tree_color = (
            min(self.color[0] + 30, 255),
            min(self.color[1] + 50, 255),
            min(self.color[2] + 10, 255),
        )
        size = CELL_SIZE // 3
        points = [
            (cx, cy - size),
            (cx - size, cy + size),
            (cx + size, cy + size),
        ]
        pygame.draw.polygon(window, tree_color, points)


# ──────────────────────────────────────────────
# GENERATION HELPERS
# ──────────────────────────────────────────────

def generate_water_body(grid, center_x, center_y, size=6, movables=None, min_entity_dist=5):
    """
    Generate a roughly organic water body around a center point.
    Uses a random walk / flood approach for natural shapes.
    """
    placed = set()
    candidates = [(center_x, center_y)]

    while len(placed) < size and candidates:
        cx, cy = candidates.pop(random.randint(0, len(candidates) - 1))

        if not (0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT):
            continue
        if (cx, cy) in placed:
            continue
        if grid.is_blocked(cx, cy):
            continue
        if (cx, cy) in grid.entities:
            continue

        if movables:
            too_close = False
            for m in movables:
                dist = abs(cx - m.x_pos) + abs(cy - m.y_pos)
                if dist < min_entity_dist:
                    too_close = True
                    break
            if too_close:
                continue

        water = Water(cx, cy)
        grid.add_terrain(water)
        placed.add((cx, cy))

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) not in placed and random.random() < 0.65:
                candidates.append((nx, ny))

    return placed


def generate_forest_cluster(grid, center_x, center_y, size=8, movables=None, min_entity_dist=4):
    """Generate a cluster of forest tiles."""
    placed = set()

    for _ in range(size * 3):
        if len(placed) >= size:
            break

        ox = center_x + random.randint(-2, 2)
        oy = center_y + random.randint(-2, 2)

        if not (0 <= ox < GRID_WIDTH and 0 <= oy < GRID_HEIGHT):
            continue
        if (ox, oy) in placed:
            continue
        if grid.is_blocked(ox, oy):
            continue
        if (ox, oy) in grid.entities:
            continue
        if grid.is_fire(ox, oy):
            continue

        if movables:
            too_close = False
            for m in movables:
                dist = abs(ox - m.x_pos) + abs(oy - m.y_pos)
                if dist < min_entity_dist:
                    too_close = True
                    break
            if too_close:
                continue

        forest = Forest(ox, oy)
        grid.add_terrain(forest)
        placed.add((ox, oy))

    return placed


def generate_barrier_line(grid, start_x, start_y, direction, length):
    """Generate a line of barrier tiles (fences, rubble)."""
    dx, dy = direction
    placed = set()

    for i in range(length):
        bx = start_x + dx * i
        by = start_y + dy * i

        if not (0 <= bx < GRID_WIDTH and 0 <= by < GRID_HEIGHT):
            break
        if grid.is_blocked(bx, by):
            continue
        if (bx, by) in grid.entities:
            continue

        barrier = Barrier(bx, by)
        grid.add_entity(barrier)
        placed.add((bx, by))

    return placed
