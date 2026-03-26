"""
Samples a 2D fractal noise field over the grid using perlin-numpy.
Cells whose noise value falls above a threshold become walls;
everything else is open. A flood-fill check guarantees connectivity
between each entity spawn and the objective. If disconnected, a
minimal path is carved to restore it.

Link: https://github.com/pvigier/perlin-numpy
"""

import numpy as np
from perlin_numpy import generate_fractal_noise_2d

from .config import GRID_WIDTH, GRID_HEIGHT
from .entities import Wall

# Base resolution — lower = larger blobs, higher = finer
NOISE_RES = (4, 4) 

# Layers of detail — more = rougher edges
OCTAVES = 3  

# Amplitude falloff per octave (0–1)
PERSISTENCE = 0.5

# Noise above this becomes a wall (raise = more walls)
WALL_THRESHOLD = 0.1     



# Parameters:
# open_set - set of non-wall cells
# start - starting coordinate of an entity
#
# Returns:
# The set of every cell reachable from the start
def _flood_fill(open_set, start):
    """Return all cells in open_set reachable from start."""
    if start not in open_set:
        return set()

    visited = set()
    stack = [start]

    while stack:
        cell = stack.pop()
        if cell in visited or cell not in open_set:
            continue
        visited.add(cell)
        x, y = cell
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            stack.append((x + dx, y + dy))

    return visited


# Parameters:
# walls - set of wall coordinates to modify
# zone - a Zone object whose area should be cleared
#
# Returns:
# Nothing — modifies walls in place
def _carve_zone(walls, zone):
    """Ensure every cell inside a zone is open."""
    for zx, zy in zone.all_cells():
        walls.discard((zx, zy))


# Parameters:
# start_zone - the spawn zone to keep clear
# dest_zone - the objective zone to keep clear
# entity_positions - list of (x, y) spawn coordinates
#
# Returns:
# A set of wall coordinates, or None if any entity is cut off from the objective
def _generate_noise_walls(start_zone, dest_zone, entity_positions):
    
    factor = NOISE_RES[0] * (2 ** (OCTAVES - 1))
    gen_h = ((GRID_HEIGHT + factor - 1) // factor) * factor
    gen_w = ((GRID_WIDTH + factor - 1) // factor) * factor

    # generate_fractal_noise_2d() generates a 32x32 array of floats (each)
    # value from [-1,1]. This is the pattern.
    noise = generate_fractal_noise_2d(
        shape=(gen_h, gen_w),
        res=NOISE_RES,
        octaves=OCTAVES,
        persistence=PERSISTENCE,
    )
    # Note: Two or more arrays/patterns can be layered over each other, if desired.

    # Noise is cropped to grid size (imported from .config)
    noise = noise[:GRID_HEIGHT, :GRID_WIDTH]

    # The noise pattern is converted to walls. Everything above WALL_THRESHOLD
    # (default: 0.1) is converted into walls, while everything below is not.
    walls = set()
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):

            if noise[y, x] > WALL_THRESHOLD:
                walls.add((x, y))

            # Note: More conditions may be added above for different types of 
            # entities (TREE_THRESHOLD, WATER_THRESHOLD, etc.). It will be 
            # integrated into the existing perlin pattern.

    # Remove walls that landed inside start zone, objective zone, or entity spawn
    _carve_zone(walls, start_zone)
    _carve_zone(walls, dest_zone)
    for ex, ey in entity_positions:
        walls.discard((ex, ey))

    # Collect open cells. Later, there will be a check to ensure that every 
    # entity can reach the destination.
    open_cells = set()
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            if (x, y) not in walls:
                open_cells.add((x, y))

    # The target cell that entities need to be able to reach (inside objective)
    dest_cx = dest_zone.x + dest_zone.width // 2
    dest_cy = dest_zone.y + dest_zone.height // 2

    #_flood_fill() returns the set of reachable cells from an entity.
    # If the set does not include the target cell, it is unreachable,
    # and generatee_walls() calls _generate_noise_cells() again until
    # all entities can reach the objective.
    for ex, ey in entity_positions:
        reachable = _flood_fill(open_cells, (ex, ey))
        if (dest_cx, dest_cy) not in reachable:
            return None

    return walls


# Parameters:
# grid - the simulation grid to populate with Wall entities
# start_zone - the spawn zone to keep clear
# dest_zone - the objective zone to keep clear
# entity_positions - list of (x, y) spawn coordinates
#
# Returns:
# Nothing — places Wall entities directly on the grid
def generate_walls(grid, start_zone, dest_zone, entity_positions):
    walls = None
    while walls is None:
        walls = _generate_noise_walls(start_zone, dest_zone, entity_positions)

    for wx, wy in walls:
        if (wx, wy) not in grid.entities:
            grid.add_entity(Wall(wx, wy))
