import pygame

from .config import (
    APP_WINDOW_WIDTH,
    BACK_BUTTON_RECT,
    BG_COLOR,
    BUTTON_BG_COLOR,
    BUTTON_TEXT_COLOR,
    CELL_SIZE,
    HUD_PANEL_WIDTH,
    PANEL_ACCENT_COLOR,
    PANEL_BG_COLOR,
    PANEL_DIVIDER_COLOR,
    PANEL_MUTED_TEXT_COLOR,
    PANEL_TEXT_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .phases import PHASE_FINISHED, PHASE_MOVING, PHASE_PLANNING


class SimulationRenderer:
    def __init__(self, window):
        self.window = window
        self.font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 22)

    def render(self, simulation):
        self.window.fill(PANEL_BG_COLOR)
        play_surface = self.window.subsurface(pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        play_surface.fill(BG_COLOR)

        self._draw_zones(simulation, play_surface)
        self._draw_objective_cells(simulation, play_surface)
        simulation.grid.draw(play_surface)

        if simulation.phase == PHASE_MOVING:
            self._draw_proximity_overlays(simulation, play_surface)

        if simulation.phase == PHASE_FINISHED:
            simulation.stats.draw(play_surface, self.font)

        self._draw_sidebar_background()
        self._draw_hud(simulation)
        self._draw_back_button()

        if simulation.paused and simulation.phase != PHASE_FINISHED:
            self._render_lines(["PAUSED"], x=WINDOW_WIDTH + 12, y=180, color=(255, 80, 80))

    def _draw_sidebar_background(self):
        panel_x = WINDOW_WIDTH
        pygame.draw.rect(self.window, PANEL_BG_COLOR, (panel_x, 0, HUD_PANEL_WIDTH, WINDOW_HEIGHT))
        pygame.draw.line(self.window, PANEL_DIVIDER_COLOR, (panel_x, 0), (panel_x, WINDOW_HEIGHT), 2)
        pygame.draw.rect(self.window, (18, 22, 28), (panel_x, 0, HUD_PANEL_WIDTH, 42))
        title = self.font.render("SIM INFO", True, PANEL_ACCENT_COLOR)
        self.window.blit(title, (panel_x + 12, 10))

    def _draw_back_button(self):
        rect = pygame.Rect(BACK_BUTTON_RECT)
        pygame.draw.rect(self.window, BUTTON_BG_COLOR, rect, border_radius=8)
        pygame.draw.rect(self.window, PANEL_DIVIDER_COLOR, rect, 1, border_radius=8)
        text = self.small_font.render("Back to launcher", True, BUTTON_TEXT_COLOR)
        self.window.blit(text, text.get_rect(center=rect.center))

    def _draw_zones(self, simulation, surface):
        for zone in (simulation.start_zone, simulation.dest_zone):
            zone.draw(surface)

        start_label = self.font.render(simulation.start_zone.name, True, (200, 200, 220))
        surface.blit(
            start_label,
            (simulation.start_zone.x * CELL_SIZE + 2, simulation.start_zone.y * CELL_SIZE - 18),
        )

    def _draw_objective_cells(self, simulation, surface):
        for ox, oy in simulation.objective_cells:
            block_rect = pygame.Rect(ox * CELL_SIZE, oy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            inset_rect = block_rect.inflate(-6, -6)
            pygame.draw.rect(surface, (210, 210, 80), inset_rect, border_radius=3)
            pygame.draw.rect(surface, (240, 240, 240), inset_rect, 2, border_radius=3)

    def _draw_proximity_overlays(self, simulation, surface):
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
            surface.blit(prox_surface, (px - radius_px, py - radius_px))

    def _draw_hud(self, simulation):
        if simulation.phase == PHASE_PLANNING:
            self._draw_planning_hud(simulation)
        elif simulation.phase == PHASE_MOVING:
            self._draw_movement_hud(simulation)
        elif simulation.phase == PHASE_FINISHED:
            self._draw_finished_hud(simulation)

    def _draw_planning_hud(self, simulation):
        lines = [
            "PHASE: PLANNING",
            "Click a blue square to select it.",
            "Arrow keys: plan path",
            "Backspace: undo   C: clear",
            "Enter: start   Space: pause",
            "R: reset   G: regenerate map",
            "Use the Back button below to return.",
        ]

        for movable in simulation.movables:
            metrics = getattr(movable, "metrics", None)
            if movable.selected and metrics is not None:
                lines.append("")
                lines.append(f"Speed: {metrics.speed_tier.upper()}")
                lines.append(f"Fuel: {metrics.fuel:.0f}/{metrics.max_fuel:.0f}")
                lines.append(f"Proximity: {metrics.proximity_radius} cells")
                planned_len = len(movable.planned_cells)
                tier = metrics.get_speed_tier()
                est_cost = tier.fuel_per_step * planned_len
                lines.append(f"Planned steps: {planned_len}")
                lines.append(f"Est. fuel cost: {est_cost:.1f}")
                if metrics.objective_cell is not None:
                    ox, oy = metrics.objective_cell
                    lines.append(f"Assigned objective: ({ox}, {oy})")

        self._render_lines(lines, x=WINDOW_WIDTH + 12, y=54)

    def _draw_movement_hud(self, simulation):
        lines = [
            "PHASE: MOVEMENT",
            f"Sim tick: {simulation.timing.simulation_tick_fps} Hz",
            f"Fire tick: {simulation.timing.fire_tick_ms} ms",
            "Space: pause   R: reset",
            "Use the Back button below to return.",
        ]

        for index, movable in enumerate(simulation.movables, start=1):
            metrics = getattr(movable, "metrics", None)
            if metrics is None:
                continue

            objective_status = "reached" if metrics.reached_destination else "en route"
            lines.append("")
            lines.append(f"Entity {index}")
            lines.append(f"Fuel: {metrics.fuel:.0f}/{metrics.max_fuel:.0f}")
            lines.append(f"Move cost: {metrics.total_movement_cost:.1f}")
            lines.append(f"Objective: {objective_status}")
            lines.append(f"Health: {movable.health:.1f}")
            lines.append(f"Fire damage: {movable.fire_damage_taken:.1f}")
            lines.append(f"Time in fire: {movable.time_in_fire}")

        self._render_lines(lines, x=WINDOW_WIDTH + 12, y=54)

    def _draw_finished_hud(self, simulation):
        lines = [
            "PHASE: FINISHED",
            "Summary is shown on the grid.",
            "R: reset   Enter: run again",
            "Use the Back button below to return.",
        ]
        self._render_lines(lines, x=WINDOW_WIDTH + 12, y=54)

    def _render_lines(self, lines, x=10, y=10, color=PANEL_TEXT_COLOR, line_gap=4):
        yy = y
        max_width = APP_WINDOW_WIDTH - x - 14
        for line in lines:
            if line == "":
                yy += self.small_font.get_height()
                continue
            for wrapped in self._wrap_text(line, self.small_font, max_width):
                surf = self.small_font.render(wrapped, True, color)
                self.window.blit(surf, (x, yy))
                yy += surf.get_height() + line_gap

    def _wrap_text(self, text, font, max_width):
        words = text.split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines
