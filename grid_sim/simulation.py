import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

from .entities import Movable
from .generation import generate_walls
from .grid import Grid
from .metrics import Zone, random_entity_metrics
from .phases import PHASE_FINISHED, PHASE_MOVING, PHASE_PLANNING
from .stats import SimStats
from .config import GRID_WIDTH, GRID_HEIGHT


@dataclass(frozen=True)
class SimulationTiming:
    # Simulation updates are decoupled from rendering, so movement speed
    # is controlled here rather than by the display framerate
    simulation_tick_fps: int = 7
    fire_tick_ms: int = 400

    @property
    def simulation_step_ms(self) -> float:
        return 1000.0 / self.simulation_tick_fps


class SimulationManager:
    def __init__(self):
        self.grid = Grid()
        self.stats = SimStats()
        self.timing = SimulationTiming()

        self.phase = PHASE_PLANNING
        self.paused = False
        self.running = True

        self._randomize_zones()

        self.movables: List[Movable] = []
        self.objective_cells: List[Tuple[int, int]] = []
        self.initial_fire_positions: List[Tuple[int, int]] = []

        # Tracks elapsed real time so fixed simulation steps can run independently
        # of however often the render loop happens to execute.
        self._simulation_accumulator_ms = 0.0
        self._last_frame_time_ms = pygame.time.get_ticks()
        self._last_fire_spread_time_ms = 0

        self._build_world()

    def _build_world(self):
        self._spawn_movables()

        entity_positions = [(m.x_pos, m.y_pos) for m in self.movables]
        generate_walls(self.grid, self.start_zone, self.dest_zone, entity_positions)

        self.grid.rand_gen_water()
        self.grid.rand_gen_barriers()
        self.grid.rand_gen_forest()

        self.objective_cells = self._build_objective_cells()
        self._assign_objectives_and_metrics(randomize_metrics=False)

        self.grid.rand_gen_fire(
            self.movables,
            cluster_count=2,
            min_cluster_distance=8,
            min_entity_distance=7,
        )
        # Save the initial fire pattern so reset/start can restore the same scenario.
        self.initial_fire_positions = list(self.grid.fire_tiles)

    def _spawn_movables(self, count: int = 2):
        occupied = set()
        
        for _ in range(count):
            while True:
                sx, sy = self.start_zone.random_point()

                if (sx, sy) in occupied:
                    continue
                if self.grid.is_blocked(sx, sy):
                    continue
                if self.grid.is_fire(sx, sy):
                    continue
                if self.grid.is_adjacent_to_fire(sx, sy):
                    continue

                break

            movable = Movable((0, 0, 255), sx, sy)
            self.movables.append(movable)
            self.grid.add_entity(movable)
            occupied.add((sx, sy))

    def _build_objective_cells(self) -> List[Tuple[int, int]]:
        preferred_cells = [
            (self.dest_zone.x + 1, self.dest_zone.y + 1),
            (self.dest_zone.x + self.dest_zone.width - 2, self.dest_zone.y + self.dest_zone.height - 2),
            (self.dest_zone.x + 1, self.dest_zone.y + self.dest_zone.height - 2),
            (self.dest_zone.x + self.dest_zone.width - 2, self.dest_zone.y + 1),
        ]
        open_cells: List[Tuple[int, int]] = []

        for cell in preferred_cells:
            if self.dest_zone.contains(*cell) and not self.grid.is_blocked(*cell):
                open_cells.append(cell)

        if len(open_cells) < len(self.movables):
            for cell in self.dest_zone.all_cells():
                if cell not in open_cells and not self.grid.is_blocked(*cell):
                    open_cells.append(cell)
                if len(open_cells) >= len(self.movables):
                    break

        if len(open_cells) < len(self.movables):
            raise RuntimeError("Not enough open cells inside the objective zone for all entities.")

        return open_cells[: len(self.movables)]

    def _assign_objectives_and_metrics(self, randomize_metrics: bool):
        available = list(self.objective_cells)
        random.shuffle(available)

        for movable in self.movables:
            if randomize_metrics or not hasattr(movable, "metrics") or movable.metrics is None:
                movable.metrics = random_entity_metrics()

            # Each entity gets one assigned objective cell inside the destination zone
            movable.metrics.destination_zone = self.dest_zone
            movable.metrics.objective_cell = available.pop() if available else None
            movable.metrics.reached_destination = False
            movable.metrics.detected_entities.clear()

    def restore_initial_fire(self):
        self.grid.fire_tiles.clear()
        for x, y in self.initial_fire_positions:
            self.grid.add_fire(x, y)

    def reset(self):
        self.phase = PHASE_PLANNING
        self.paused = False
        self.stats.reset()
        self._simulation_accumulator_ms = 0.0
        self._last_fire_spread_time_ms = 0

        # Clear everything
        self.grid = Grid()
        self.movables.clear()
        self.objective_cells.clear()
        self.initial_fire_positions.clear()

        # Rebuild world with new random zones
        self._randomize_zones()
        self._build_world()

    def start(self):
        self.phase = PHASE_MOVING
        self.paused = False
        self.stats.reset()
        self._simulation_accumulator_ms = 0.0
        now = pygame.time.get_ticks()
        self._last_frame_time_ms = now
        self._last_fire_spread_time_ms = now

        self.restore_initial_fire()
        for movable in self.movables:
            movable.start_movement()

    def stop(self):
        self.running = False

    def toggle_pause(self):
        self.paused = not self.paused

    def update(self, now_ms: int):
        delta_ms = now_ms - self._last_frame_time_ms
        self._last_frame_time_ms = now_ms

        if self.phase != PHASE_MOVING or self.paused:
            return

        self._simulation_accumulator_ms += max(delta_ms, 0)

        # Run fixed size simulation steps so the sim stays consistent even if
        # rendering speeds up or slows down
        while self._simulation_accumulator_ms >= self.timing.simulation_step_ms:
            self._step_simulation()
            self._simulation_accumulator_ms -= self.timing.simulation_step_ms

        if now_ms - self._last_fire_spread_time_ms >= self.timing.fire_tick_ms:
            self.grid.spread_fire()
            self._last_fire_spread_time_ms = now_ms

    def _step_simulation(self):
        for movable in self.movables:
            if hasattr(movable, "metrics") and movable.metrics is not None and movable.metrics.is_out_of_fuel:
                self.stats.record_step(movable, False)
                movable.apply_fire_damage(self.grid)
                continue

            moved = movable.advance_one_step(self.grid)
            movable.apply_fire_damage(self.grid)
            self.stats.record_step(movable, moved)

            if moved and hasattr(movable, "metrics") and movable.metrics is not None:
                movable.metrics.burn_fuel_for_step()
                movable.metrics.check_in_zone(movable.x_pos, movable.y_pos)
                self._update_proximity(movable)

        if all(self._entity_finished(m) for m in self.movables):
            self.stats.finalize()
            self.phase = PHASE_FINISHED
            self.paused = True

    def _update_proximity(self, movable: Movable):
        for other in self.movables:
            if other is movable:
                continue
            if movable.metrics.check_proximity(movable.x_pos, movable.y_pos, other.x_pos, other.y_pos):
                if id(other) not in [id(entity) for entity in movable.metrics.detected_entities]:
                    movable.metrics.detected_entities.append(other)

    def _entity_finished(self, movable: Movable) -> bool:
        metrics = getattr(movable, "metrics", None)
        return movable.is_done() or (metrics is not None and metrics.is_out_of_fuel)

    def selected_movables(self) -> List[Movable]:
        return [m for m in self.movables if m.selected]

    def handle_click(self, mouse_pos):
        for movable in self.movables:
            movable.handle_click(mouse_pos)

    def undo_selected_plan_step(self):
        for movable in self.selected_movables():
            movable.undo_last_step()

    def clear_selected_plan(self):
        for movable in self.selected_movables():
            movable.clear_plan()

    def plan_selected_step(self, dx: int, dy: int):
        for movable in self.selected_movables():
            movable.plan_step(dx, dy, self.grid)

    def _randomize_zones(self, zone_size=4, max_attempts=200):
        min_distance = (GRID_WIDTH + GRID_HEIGHT) // 2

        for _ in range(max_attempts):
            sx = random.randint(0, GRID_WIDTH - zone_size)
            sy = random.randint(0, GRID_HEIGHT - zone_size)

            dx = random.randint(0, GRID_WIDTH - zone_size)
            dy = random.randint(0, GRID_HEIGHT - zone_size)

            start_center = (sx + zone_size // 2, sy + zone_size // 2)
            dest_center = (dx + zone_size // 2, dy + zone_size // 2)

            dist = abs(start_center[0] - dest_center[0]) + abs(start_center[1] - dest_center[1])

            if dist < min_distance:
                continue

            self.start_zone = Zone("Start", sx, sy, zone_size, zone_size, (40, 80, 120))
            self.dest_zone = Zone("Objective", dx, dy, zone_size, zone_size, (80, 120, 40))
            return

        raise RuntimeError("Failed to generate valid zones")
    
    