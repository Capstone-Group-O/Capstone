import pygame
import math
from .config import WINDOW_WIDTH, WINDOW_HEIGHT, CELL_SIZE


class SimStats:
    """
    Tracks per-entity statistics during a simulation run
    and renders a summary screen when the simulation finishes.

    Usage in game.py:
        1. Create:    stats = SimStats()
        2. On reset:  stats.reset()
        3. Each step: stats.record_step(entity, grid)
        4. On finish: stats.finalize()
        5. Draw:      stats.draw(window, font)
    """

    def __init__(self):
        self.reset()

    def reset(self):
        # Keyed by id(entity) so each movable gets its own bucket
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

            # Straight-line distance from start to end (in cells)
            sx, sy = d["start"]
            ex, ey = d["end"]
            d["direct_dist"] = math.sqrt((ex - sx) ** 2 + (ey - sy) ** 2)

            # Efficiency: direct distance vs steps taken (1.0 = perfect straight line)
            if d["steps_taken"] > 0:
                d["efficiency"] = d["direct_dist"] / d["steps_taken"]
            else:
                d["efficiency"] = 0.0

    def draw(self, window, font):
        """Renders the summary screen overlay."""
        if not self._data:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 20, 28, 220))
        window.blit(overlay, (0, 0))

        # Title
        title_font = pygame.font.SysFont(None, 36)
        title = title_font.render("SIMULATION SUMMARY", True, (90, 220, 140))
        title_rect = title.get_rect(centerx=WINDOW_WIDTH // 2, y=30)
        window.blit(title, title_rect)

        # Divider line under title
        pygame.draw.line(
            window, (60, 60, 80),
            (40, 70), (WINDOW_WIDTH - 40, 70), 2
        )

        # Draw a card for each entity
        card_y = 90
        card_margin = 20
        card_width = WINDOW_WIDTH - card_margin * 2
        card_height = 160

        for i, d in enumerate(self._data.values()):
            entity = d["entity"]
            cx = card_margin
            cy = card_y + i * (card_height + 12)

            # Card background
            card_rect = pygame.Rect(cx, cy, card_width, card_height)
            pygame.draw.rect(window, (30, 30, 42), card_rect, border_radius=8)
            pygame.draw.rect(window, (60, 60, 80), card_rect, 1, border_radius=8)

            # Color indicator bar on the left
            bar_rect = pygame.Rect(cx, cy, 6, card_height)
            pygame.draw.rect(window, entity.color, bar_rect, border_radius=3)

            # Entity label
            label_color = entity.color
            label = font.render(f"Entity {i + 1}", True, label_color)
            window.blit(label, (cx + 16, cy + 10))

            # Status badge
            if d["finished"]:
                badge_text = "COMPLETE"
                badge_color = (90, 220, 140)
            else:
                badge_text = "INCOMPLETE"
                badge_color = (240, 120, 120)

            badge = font.render(badge_text, True, badge_color)
            window.blit(badge, (cx + card_width - badge.get_width() - 16, cy + 10))

            # Stats in two columns
            stat_font = pygame.font.SysFont(None, 22)
            col1_x = cx + 16
            col2_x = cx + card_width // 2
            row_y = cy + 40
            row_h = 22

            stats_left = [
                ("Steps Planned", str(d["steps_planned"])),
                ("Steps Taken", str(d["steps_taken"])),
                ("Blocked Moves", str(d["collisions"])),
            ]

            stats_right = [
                ("Start", f"({d['start'][0]}, {d['start'][1]})"),
                ("End", f"({d['end'][0]}, {d['end'][1]})"),
                ("Direct Dist", f"{d['direct_dist']:.1f} cells"),
                ("Efficiency", f"{d['efficiency']:.0%}"),
            ]

            for j, (name, val) in enumerate(stats_left):
                name_surf = stat_font.render(f"{name}:", True, (140, 140, 170))
                val_surf = stat_font.render(val, True, (220, 220, 240))
                window.blit(name_surf, (col1_x, row_y + j * row_h))
                window.blit(val_surf, (col1_x + name_surf.get_width() + 8, row_y + j * row_h))

            for j, (name, val) in enumerate(stats_right):
                name_surf = stat_font.render(f"{name}:", True, (140, 140, 170))
                val_surf = stat_font.render(val, True, (220, 220, 240))
                window.blit(name_surf, (col2_x, row_y + j * row_h))
                window.blit(val_surf, (col2_x + name_surf.get_width() + 8, row_y + j * row_h))

        # Footer hint
        hint = font.render("Press R to reset  |  Press Enter to run again", True, (100, 100, 130))
        hint_rect = hint.get_rect(centerx=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT - 30)
        window.blit(hint, hint_rect)
