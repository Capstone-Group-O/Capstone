import pygame
import math
from .config import CELL_SIZE


class SimStats:
    """
    Tracks per-entity statistics during a simulation run
    and renders a summary screen when the simulation finishes.

    Usage in game.py:
        1. Create:    stats = SimStats()
        2. On reset:  stats.reset()
        3. Each step: stats.record_step(entity, moved)
        4. On finish: stats.finalize()
        5. Draw:      stats.draw(window, font)
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._data = {}

    def _ensure(self, entity):
        eid = id(entity)
        if eid not in self._data:
            self._data[eid] = {
                "entity": entity,
                "steps_taken": 0,
                "steps_planned": len(entity.planned_cells),
                "start": (entity.start_x, entity.start_y),
                "positions": [(entity.x_pos, entity.y_pos)],
                "collisions": 0,
                "finished": False,
            }
        return self._data[eid]

    def record_step(self, entity, moved: bool):
        """Call every time advance_one_step is called for an entity."""
        d = self._ensure(entity)
        if moved:
            d["steps_taken"] += 1
            d["positions"].append((entity.x_pos, entity.y_pos))
        else:
            d["collisions"] += 1

    def finalize(self):
        """Call once when all entities finish. Computes final metrics."""
        for d in self._data.values():
            entity = d["entity"]
            d["finished"] = entity.is_done()
            d["end"] = (entity.x_pos, entity.y_pos)

            sx, sy = d["start"]
            ex, ey = d["end"]
            d["direct_dist"] = math.sqrt((ex - sx) ** 2 + (ey - sy) ** 2)

            if d["steps_taken"] > 0:
                d["efficiency"] = d["direct_dist"] / d["steps_taken"]
            else:
                d["efficiency"] = 0.0

    def draw(self, window, font):
        """Renders the summary screen overlay."""
        if not self._data:
            return

        win_w, win_h = window.get_size()

        overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        overlay.fill((20, 20, 28, 220))
        window.blit(overlay, (0, 0))

        # Title
        title_font = pygame.font.SysFont(None, 36)
        title = title_font.render("SIMULATION SUMMARY", True, (90, 220, 140))
        title_rect = title.get_rect(centerx=win_w // 2, y=20)
        window.blit(title, title_rect)

        pygame.draw.line(window, (60, 60, 80), (40, 55), (win_w - 40, 55), 2)

        # Draw a card for each entity
        card_y = 70
        card_margin = 20
        card_width = win_w - card_margin * 2
        card_height = 220

        stat_font = pygame.font.SysFont(None, 22)

        for i, d in enumerate(self._data.values()):
            entity = d["entity"]
            cx = card_margin
            cy = card_y + i * (card_height + 10)

            # Card background
            card_rect = pygame.Rect(cx, cy, card_width, card_height)
            pygame.draw.rect(window, (30, 30, 42), card_rect, border_radius=8)
            pygame.draw.rect(window, (60, 60, 80), card_rect, 1, border_radius=8)

            # Color bar
            bar_rect = pygame.Rect(cx, cy, 6, card_height)
            pygame.draw.rect(window, entity.color, bar_rect, border_radius=3)

            # Entity label
            label = font.render(f"Entity {i + 1}", True, entity.color)
            window.blit(label, (cx + 16, cy + 8))

            # Status badge
            if d["finished"]:
                badge_text = "COMPLETE"
                badge_color = (90, 220, 140)
            else:
                badge_text = "INCOMPLETE"
                badge_color = (240, 120, 120)
            badge = font.render(badge_text, True, badge_color)
            window.blit(badge, (cx + card_width - badge.get_width() - 16, cy + 8))

            # Stats layout: 3 columns
            col1_x = cx + 16
            col2_x = cx + card_width // 3
            col3_x = cx + (card_width * 2) // 3
            row_y = cy + 36
            row_h = 20

            # Column 1: Movement
            self._draw_stat(window, stat_font, "Steps Planned", str(d["steps_planned"]), col1_x, row_y)
            self._draw_stat(window, stat_font, "Steps Taken", str(d["steps_taken"]), col1_x, row_y + row_h)
            self._draw_stat(window, stat_font, "Blocked Moves", str(d["collisions"]), col1_x, row_y + row_h * 2)
            self._draw_stat(window, stat_font, "Efficiency", f"{d['efficiency']:.0%}", col1_x, row_y + row_h * 3)

            # Column 2: Position
            self._draw_stat(window, stat_font, "Start", f"({d['start'][0]}, {d['start'][1]})", col2_x, row_y)
            self._draw_stat(window, stat_font, "End", f"({d['end'][0]}, {d['end'][1]})", col2_x, row_y + row_h)
            self._draw_stat(window, stat_font, "Direct Dist", f"{d['direct_dist']:.1f}", col2_x, row_y + row_h * 2)
            self._draw_stat(window, stat_font, "Health Left", f"{entity.health:.1f}", col2_x, row_y + row_h * 3)
            self._draw_stat(window, stat_font, "Time in Fire", str(entity.time_in_fire), col2_x, row_y + row_h * 4)
            self._draw_stat(window, stat_font, "Fire Damage", f"{entity.fire_damage_taken:.1f}", col2_x, row_y + row_h * 5)

            # Column 3: Metrics (from EntityMetrics if available)
            has_metrics = hasattr(entity, "metrics") and entity.metrics is not None
            if has_metrics:
                m = entity.metrics
                self._draw_stat(window, stat_font, "Speed", m.speed_tier.upper(), col3_x, row_y)
                self._draw_stat(window, stat_font, "Fuel Left", f"{m.fuel:.1f}/{m.max_fuel:.1f}", col3_x, row_y + row_h)
                self._draw_stat(window, stat_font, "Fuel Burned", f"{m.total_fuel_burned:.1f}", col3_x, row_y + row_h * 2)
                self._draw_stat(window, stat_font, "Move Cost", f"{m.total_movement_cost:.1f}", col3_x, row_y + row_h * 3)
                self._draw_stat(window, stat_font, "Proximity", f"{m.proximity_radius} cells", col3_x, row_y + row_h * 4)

                # Destination zone status
                if m.destination_zone:
                    zone_status = "REACHED" if m.reached_destination else "MISSED"
                    zone_color = (90, 220, 140) if m.reached_destination else (240, 120, 120)
                    zone_label = f"Zone: {m.destination_zone.name} [{zone_status}]"
                    zone_surf = stat_font.render(zone_label, True, zone_color)
                    window.blit(zone_surf, (col3_x, row_y + row_h * 5))

                # Fuel bar
                bar_x = col3_x
                bar_y = row_y + row_h * 6 + 4
                bar_w = card_width // 3 - 30
                bar_h = 6
                pygame.draw.rect(window, (50, 50, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
                fill_w = int(bar_w * (m.fuel_pct / 100.0))
                fuel_color = (90, 220, 140) if m.fuel_pct > 50 else (255, 220, 120) if m.fuel_pct > 25 else (240, 120, 120)
                pygame.draw.rect(window, fuel_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3)
            else:
                self._draw_stat(window, stat_font, "Metrics", "N/A", col3_x, row_y)

        # Footer
        hint = font.render("R = reset  |  Enter = run again", True, (100, 100, 130))
        hint_rect = hint.get_rect(centerx=win_w // 2, y=win_h - 28)
        window.blit(hint, hint_rect)

    def _draw_stat(self, window, font, name, value, x, y):
        name_surf = font.render(f"{name}:", True, (140, 140, 170))
        val_surf = font.render(value, True, (220, 220, 240))
        window.blit(name_surf, (x, y))
        window.blit(val_surf, (x + name_surf.get_width() + 6, y))
