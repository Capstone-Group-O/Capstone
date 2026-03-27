import pygame
from .config import CELL_SIZE, GRID_WIDTH, GRID_HEIGHT
import random

class Entity():
    def __init__(self, color, x_pos, y_pos, blocking=False):
        self.x_pos = x_pos
        self.y_pos = y_pos

        self.color = color

        #blocking=true means other entities can't occupy the same space
        self.blocking=blocking


    def draw(self, window):
        rect = pygame.Rect(
            self.x_pos * CELL_SIZE,
            self.y_pos * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )

        pygame.draw.rect(window, self.color, rect)

# Walls inhibit movement
class Wall(Entity):
    def __init__(self, x_pos, y_pos):
        wall_color = (128,128,128) #gray
        super().__init__(wall_color,x_pos, y_pos, blocking=True)


# ──────────────────────────────────────────────
# NEW TERRAIN TYPES
# ──────────────────────────────────────────────

class Water(Entity):
    """
    Water tiles block movement entirely (impassable terrain).
    
    Future integration points:
        - Could become passable at reduced speed for amphibious entities
        - Could interact with the metrics system via a terrain_modifier > 1.0
          (see cell_movement_cost in metrics.py)
        - Pathing algorithms (A*) should treat water as blocked unless the
          entity has a water-traversal capability
    """
    def __init__(self, x_pos, y_pos):
        # Slight color variation per tile for a natural look
        blue = random.randint(140, 180)
        green = random.randint(80, 120)
        water_color = (30, green, blue)
        super().__init__(water_color, x_pos, y_pos, blocking=True)

    def draw(self, window):
        rect = pygame.Rect(
            self.x_pos * CELL_SIZE,
            self.y_pos * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.rect(window, self.color, rect)

        # Wave accent line for visual distinction from walls
        wave_y = self.y_pos * CELL_SIZE + CELL_SIZE // 2
        wave_x1 = self.x_pos * CELL_SIZE + 3
        wave_x2 = self.x_pos * CELL_SIZE + CELL_SIZE - 3
        pygame.draw.line(
            window,
            (80, 160, 220),
            (wave_x1, wave_y),
            (wave_x2, wave_y),
            1
        )


class Barrier(Entity):
    """
    Barriers are hard obstacles (concrete, rubble, collapsed structures).
    They block all movement and cannot be destroyed by fire.

    Future integration points:
        - Could have a durability value that degrades over time or under force
        - Pathing algorithms should treat these as permanently blocked
        - Could be placed dynamically during the sim to model collapsing terrain
    """
    def __init__(self, x_pos, y_pos):
        # Dark reddish-brown tones to distinguish from gray walls
        r = random.randint(100, 130)
        g = random.randint(50, 70)
        b = random.randint(40, 60)
        barrier_color = (r, g, b)
        super().__init__(barrier_color, x_pos, y_pos, blocking=True)

    def draw(self, window):
        rect = pygame.Rect(
            self.x_pos * CELL_SIZE,
            self.y_pos * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.rect(window, self.color, rect)

        # Cross-hatch accent to visually separate from walls and water
        x0 = self.x_pos * CELL_SIZE
        y0 = self.y_pos * CELL_SIZE
        accent = (70, 40, 35)
        pygame.draw.line(window, accent, (x0 + 2, y0 + 2), (x0 + CELL_SIZE - 3, y0 + CELL_SIZE - 3), 1)
        pygame.draw.line(window, accent, (x0 + CELL_SIZE - 3, y0 + 2), (x0 + 2, y0 + CELL_SIZE - 3), 1)


class Forest(Entity):
    """
    Forest tiles are passable but slow movement (movement cost modifier).

    Entities CAN move through forest, but it costs more fuel. Fire can
    spread into and through forest tiles, and forest tiles increase fire
    spread chance when adjacent.

    Future integration points:
        - terrain_modifier for metrics.cell_movement_cost (suggested: 2.0)
        - A* heuristic should weight forest cells higher than open ground
        - Fire spread probability could increase when a fire tile neighbors forest
        - Could reduce entity visibility / proximity radius while inside
    """
    TERRAIN_MODIFIER = 2.0  # Double fuel cost to move through forest

    def __init__(self, x_pos, y_pos):
        # Green tones darker than the BG_COLOR to read as dense terrain
        g = random.randint(100, 150)
        r = random.randint(20, 50)
        b = random.randint(15, 40)
        forest_color = (r, g, b)
        super().__init__(forest_color, x_pos, y_pos, blocking=False)

    def draw(self, window):
        rect = pygame.Rect(
            self.x_pos * CELL_SIZE,
            self.y_pos * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.rect(window, self.color, rect)

        # Small tree-like triangle accent
        cx = self.x_pos * CELL_SIZE + CELL_SIZE // 2
        top_y = self.y_pos * CELL_SIZE + 3
        bot_y = self.y_pos * CELL_SIZE + CELL_SIZE - 3
        left_x = self.x_pos * CELL_SIZE + 4
        right_x = self.x_pos * CELL_SIZE + CELL_SIZE - 4
        accent = (10, min(self.color[1] + 40, 255), 20)
        pygame.draw.polygon(window, accent, [(cx, top_y), (left_x, bot_y), (right_x, bot_y)], 1)


class Fire(Entity):
    SPREAD_CHANCE = 0.35

    def __init__(self, x_pos, y_pos):
        fire_color = (
            random.randint(220,255),
            random.randint(80,140),
            random.randint(0,40)
        )
        super().__init__(fire_color, x_pos, y_pos, blocking=False)

    def spread(self, grid):
        # choose ONE direction randomly
        directions = [
            (1,0), (-1,0),
            (0,1), (0,-1)
        ]

        dx, dy = random.choice(directions)

        if random.random() > self.SPREAD_CHANCE:
            return

        x = self.x_pos + dx
        y = self.y_pos + dy

        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
            return

        if (x, y) not in grid.entities:
            grid.add_entity(Fire(x, y))


#Movable entity
class Movable(Entity):
    PATH_DOT_COLOR = (255, 255, 0)  # yellow
    PATH_DOT_INSET = 6  # pixels inset for the dot

    def __init__(self, color, x_pos, y_pos):
        super().__init__(color, x_pos, y_pos, blocking=True)
        self.selected = False

        # for reset()
        self.start_x = x_pos
        self.start_y = y_pos

        # planning / movement state
        self._reset_planning_state()
        # thermal damage / metrics 
        self.max_health = 100
        self.health = 100
        self.fire_damage_taken = 0
        self.time_in_fire = 0
        self.time_near_fire = 0
        self.exposure_ticks = 0
        self.destroyed = False

    def _reset_planning_state(self):
        # Cursor is where the plan currently ends (entity does not move yet)
        self.plan_cursor_x = self.x_pos
        self.plan_cursor_y = self.y_pos

        # List of x,y cells to move through. Gets one entry per step
        self.planned_cells = []

        # Playback pointer for the movement phase
        self._next_step_idx = 0

    def reset_to_start(self, grid):
        grid.move_entity(self, self.start_x, self.start_y, ignore_blocking=True)
        self.selected = False
        self._reset_planning_state()
        # Reset fire/health metrics when restarting the simulation
        self.health = self.max_health
        self.fire_damage_taken = 0
        self.time_in_fire = 0
        self.time_near_fire = 0
        self.exposure_ticks = 0
        self.destroyed = False

    def handle_click(self, mouse_pos):
        # Gets the position on the grid from mouse_pos (which is in pixels)
        grid_x = mouse_pos[0] // CELL_SIZE
        grid_y = mouse_pos[1] // CELL_SIZE
        self.selected = (grid_x == self.x_pos and grid_y == self.y_pos)

    # -------- Planning --------
    def plan_step(self, dx, dy, grid):
        new_x = self.plan_cursor_x + dx
        new_y = self.plan_cursor_y + dy

        if not (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT):
            return False
        if grid.is_blocked(new_x, new_y):
            return False

        self.plan_cursor_x = new_x
        self.plan_cursor_y = new_y
        self.planned_cells.append((new_x, new_y))
        return True

    def undo_last_step(self):
        if not self.planned_cells:
            return False

        self.planned_cells.pop()
        if self.planned_cells:
            self.plan_cursor_x, self.plan_cursor_y = self.planned_cells[-1]
        else:
            self.plan_cursor_x, self.plan_cursor_y = self.x_pos, self.y_pos
        return True

    def clear_plan(self):
        self._reset_planning_state()

    # -------- Movement --------
    def start_movement(self):
        self._next_step_idx = 0

    def is_done(self):
        # Entity is considered done if it finished its path or was destroyed by fire
        return self.destroyed or self._next_step_idx >= len(self.planned_cells)

    def advance_one_step(self, grid):
        
        if self.destroyed:
            return False
        if self.is_done():
            return False

        target_x, target_y = self.planned_cells[self._next_step_idx]

        # Should already be valid from plannin but doing this to be safe
        if grid.is_blocked(target_x, target_y):
            return False

        grid.move_entity(self, target_x, target_y)
        self._next_step_idx += 1
        return True
    
    def apply_fire_damage(self, grid):
        # Apply thermal damage based on whether the entity is in fire
        # or one tile away from fire
        if self.destroyed:
            return

        on_fire = grid.is_fire(self.x_pos, self.y_pos)
        near_fire = grid.is_adjacent_to_fire(self.x_pos, self.y_pos)

        damage = 0

        if on_fire:
            # Direct fire contact causes high damage
            self.time_in_fire += 1
            self.exposure_ticks += 1
            multiplier = min(1 + 0.25 * (self.exposure_ticks - 1), 2.0)
            damage = 10 * multiplier

        elif near_fire:
            # Direct fire contact causes high damage
            self.time_near_fire += 1
            self.exposure_ticks += 1
            multiplier = min(1 + 0.25 * (self.exposure_ticks - 1), 2.0)
            damage = 3 * multiplier

        else:
            # Exposure resets when the entity reaches a safe tile
            self.exposure_ticks = 0

        if damage > 0:
            self.health -= damage
            self.fire_damage_taken += damage

        # Mark entity as destroyed when health is depleted
        if self.health <= 0:
            self.health = 0
            self.destroyed = True
            self.selected = False

    def draw(self, window):
        # Draw planned path dots first so entity draws on top
        for (x, y) in self.planned_cells:
            dot = pygame.Rect(
                x * CELL_SIZE + self.PATH_DOT_INSET,
                y * CELL_SIZE + self.PATH_DOT_INSET,
                CELL_SIZE - 2 * self.PATH_DOT_INSET,
                CELL_SIZE - 2 * self.PATH_DOT_INSET,
            )
            pygame.draw.rect(window, self.PATH_DOT_COLOR, dot)

        super().draw(window)
        if self.selected:
            rect = pygame.Rect(
                self.x_pos * CELL_SIZE,
                self.y_pos * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(window, (255, 255, 255), rect, 3)
