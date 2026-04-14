import pygame

from .config import BG_COLOR, CELL_SIZE
from .phases import PHASE_FINISHED, PHASE_MOVING, PHASE_PLANNING


class SimulationRenderer:
    def __init__(self, window):
        self.window = window
        self.font = pygame.font.Font(None, 26)

    def render(self, simulation):
        self.window.fill(BG_COLOR)

        self._draw_zones(simulation)
        self._draw_objective_cells(simulation)
        simulation.grid.draw(self.window)

        if simulation.phase == PHASE_MOVING:
            self._draw_proximity_overlays(simulation)

        self._draw_hud(simulation)

        if simulation.paused and simulation.phase != PHASE_FINISHED:
            self._render_lines(["PAUSED"], x=10, y=110, color=(255, 80, 80))

    def _draw_zones(self, simulation):
        for zone in (simulation.start_zone, simulation.dest_zone):
            zone.draw(self.window)

        start_label = self.font.render(simulation.start_zone.name, True, (200, 200, 220))
        self.window.blit(
            start_label,
            (simulation.start_zone.x * CELL_SIZE + 2, simulation.start_zone.y * CELL_SIZE - 18),
        )

    def _draw_objective_cells(self, simulation):
        for ox, oy in simulation.objective_cells:
            block_rect = pygame.Rect(ox * CELL_SIZE, oy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            inset_rect = block_rect.inflate(-6, -6)
            pygame.draw.rect(self.window, (210, 210, 80), inset_rect, border_radius=3)
            pygame.draw.rect(self.window, (240, 240, 240), inset_rect, 2, border_radius=3)

    def _draw_proximity_overlays(self, simulation):
        for movable in simulation.movables:
            metrics = getattr(movable, "metrics", None)
            if metrics is None:
                continue

            px = movable.x_pos * CELL_SIZE + CELL_SIZE // 2
            py = movable.y_pos * CELL_SIZE + CELL_SIZE // 2
            radius_px = metrics.proximity_radius * CELL_SIZE
            prox_surface = pygame.Surface((radius_px * 2, radius_px * 2), pygame.SRCALPHA)
            pygame.draw.circle(prox_surface, (100, 180, 255, 30), (radius_px, radius_px), radius_px)
            pygame.draw.circle(prox_surface, (100, 180, 255, 80), (radius_px, radius_px), radius_px, 1)
            self.window.blit(prox_surface, (px - radius_px, py - radius_px))

    def _draw_hud(self, simulation):
        if simulation.phase == PHASE_PLANNING:
            self._draw_planning_hud(simulation)
        elif simulation.phase == PHASE_MOVING:
            self._draw_movement_hud(simulation)
        elif simulation.phase == PHASE_FINISHED:
            simulation.stats.draw(self.window, self.font)

    def _draw_planning_hud(self, simulation):
        lines = [
            "PHASE: PLANNING",
            "Click a blue square to select it.",
            "Arrow keys: plan path   Backspace: undo   C: clear",
            "G: regenerate map   Enter: start   Space: pause   R: reset",
        ]

        for movable in simulation.movables:
            metrics = getattr(movable, "metrics", None)
            if movable.selected and metrics is not None:
                lines.append("")
                lines.append(
                    f"Speed: {metrics.speed_tier.upper()}  |  Fuel: {metrics.fuel:.0f}/{metrics.max_fuel:.0f}  |  Proximity: {metrics.proximity_radius} cells"
                )
                planned_len = len(movable.planned_cells)
                tier = metrics.get_speed_tier()
                est_cost = tier.fuel_per_step * planned_len
                lines.append(f"Planned steps: {planned_len}  |  Est. fuel cost: {est_cost:.1f}")
                if metrics.objective_cell is not None:
                    ox, oy = metrics.objective_cell
                    lines.append(f"Assigned objective: ({ox}, {oy})")

        self._render_lines(lines, x=10, y=10)

    def _draw_movement_hud(self, simulation):
        lines = [
            "PHASE: MOVEMENT",
            f"Sim tick: {simulation.timing.simulation_tick_fps} Hz   |   Fire tick: {simulation.timing.fire_tick_ms} ms",
            "Space: pause   R: reset",
        ]

        for index, movable in enumerate(simulation.movables, start=1):
            metrics = getattr(movable, "metrics", None)
            if metrics is None:
                continue

            objective_status = "reached" if metrics.reached_destination else "en route"
            lines.append(
                f"Entity {index}: fuel {metrics.fuel:.0f}/{metrics.max_fuel:.0f} | cost {metrics.total_movement_cost:.1f} | objective {objective_status}"
            )
            lines.append(
                f"health {movable.health:.1f} | fire dmg {movable.fire_damage_taken:.1f} | in fire {movable.time_in_fire}"
            )

        self._render_lines(lines, x=10, y=10)

    def _render_lines(self, lines, x=10, y=10, color=(255, 255, 255), line_gap=2):
        yy = y
        for line in lines:
            surf = self.font.render(line, True, color)
            self.window.blit(surf, (x, yy))
            yy += surf.get_height() + line_gap