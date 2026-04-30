from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import pygame

from .config import (
    APP_WINDOW_HEIGHT,
    APP_WINDOW_WIDTH,
    BACK_BUTTON_RECT,
    BG_COLOR,
    BUTTON_BG_COLOR,
    BUTTON_HOVER_COLOR,
    BUTTON_TEXT_COLOR,
    CELL_SIZE,
    FPS,
    GRID_HEIGHT,
    GRID_WIDTH,
    HUD_PANEL_WIDTH,
    PANEL_ACCENT_COLOR,
    PANEL_BG_COLOR,
    PANEL_DIVIDER_COLOR,
    PANEL_MUTED_TEXT_COLOR,
    PANEL_TEXT_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .entities import Movable, Wall
from .map_data import MapData, MovableSpawnData, ZoneData, blank_map
from .map_runtime import build_runtime_world
from .map_storage import DEFAULT_MAP_PATH, load_or_create_default_map, save_map_data
from .metrics import Zone
from .terrain import Barrier, Forest, Water

TOOL_WALL = "wall"
TOOL_WATER = "water"
TOOL_FOREST = "forest"
TOOL_BARRIER = "barrier"
TOOL_FIRE = "fire"
TOOL_MOVABLE = "movable"
TOOL_OBJECTIVE = "objective"
TOOL_START_ZONE = "start_zone"
TOOL_DEST_ZONE = "dest_zone"
TOOL_ERASE = "erase"

TOOLS = [
    (pygame.K_1, TOOL_WALL, "Wall"),
    (pygame.K_2, TOOL_WATER, "Water"),
    (pygame.K_3, TOOL_FOREST, "Forest"),
    (pygame.K_4, TOOL_BARRIER, "Barrier"),
    (pygame.K_5, TOOL_FIRE, "Fire"),
    (pygame.K_6, TOOL_MOVABLE, "Movable"),
    (pygame.K_7, TOOL_OBJECTIVE, "Objective"),
    (pygame.K_8, TOOL_START_ZONE, "Start zone"),
    (pygame.K_9, TOOL_DEST_ZONE, "Dest zone"),
    (pygame.K_0, TOOL_ERASE, "Erase"),
]
TOOL_KEYS = {key: tool for key, tool, _ in TOOLS}
TOOL_LABELS = {tool: label for _, tool, label in TOOLS}
TOOL_SHORTCUTS = {tool: str((index + 1) % 10) for index, (_, tool, _) in enumerate(TOOLS)}

TOOL_BG = (31, 37, 45)
TOOL_ACTIVE = (72, 94, 120)
TOOL_PREVIEW_BG = (17, 20, 25)
STATUS_BG = (19, 23, 28)

TOOL_BUTTON_SIZE = 54
TOOL_BUTTON_GAP_X = 8
TOOL_BUTTON_GAP_Y = 16
TOOL_GRID_COLS = 5

ACTION_BUTTON_H = 32
ACTION_BUTTON_GAP = 8
STATUS_BOX_H = 118


@dataclass
class MapEditorResult:
    action: str
    map_data: Optional[MapData] = None


class MapEditor:
    def __init__(self, map_data: Optional[MapData] = None):
        self.map_data = map_data or load_or_create_default_map()
        self.current_tool = TOOL_WALL
        self.zone_anchor: Optional[Tuple[int, int]] = None
        self.status = "Editor ready. Save, test, or use Back to return."
        self.font = None
        self.small_font = None
        self.tiny_font = None
        self.tool_buttons: list[tuple[pygame.Rect, str]] = []
        self.action_buttons: dict[str, pygame.Rect] = {}
        self._tool_palette_bottom = 0
        self._action_buttons_bottom = 0

    def run(self) -> MapEditorResult:
        pygame.init()
        window = pygame.display.set_mode((APP_WINDOW_WIDTH, APP_WINDOW_HEIGHT))
        pygame.display.set_caption("SWORD Map Editor")
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.tiny_font = pygame.font.Font(None, 16)
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return MapEditorResult("cancel", self.map_data)
                if event.type == pygame.KEYDOWN:
                    result = self._handle_keydown(event.key)
                    if result is not None:
                        pygame.quit()
                        return result
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        action_result = self._handle_panel_click(event.pos)
                        if action_result is not None:
                            pygame.quit()
                            return action_result
                    grid_cell = self._mouse_to_grid(event.pos)
                    if grid_cell is None:
                        continue
                    if event.button == 1:
                        self._apply_tool(grid_cell)
                    elif event.button == 3:
                        self._erase_at(grid_cell)
                if event.type == pygame.MOUSEMOTION and event.buttons[0]:
                    grid_cell = self._mouse_to_grid(event.pos)
                    if grid_cell is not None and self.current_tool not in (TOOL_START_ZONE, TOOL_DEST_ZONE):
                        self._apply_tool(grid_cell)

            self._render(window)
            pygame.display.flip()
            clock.tick(FPS)

    def _handle_keydown(self, key: int) -> Optional[MapEditorResult]:
        if key in TOOL_KEYS:
            self.current_tool = TOOL_KEYS[key]
            self.zone_anchor = None
            self.status = f"Selected tool: {TOOL_LABELS[self.current_tool]}"
            return None

        if key == pygame.K_s:
            self._save_current_map()
            return None

        if key == pygame.K_l:
            self.map_data = load_or_create_default_map()
            self.zone_anchor = None
            self.status = f"Loaded {DEFAULT_MAP_PATH.name}"
            return None

        if key == pygame.K_n:
            self.map_data = blank_map()
            self.zone_anchor = None
            self.status = "Started a blank map."
            return None

        if key == pygame.K_t:
            return MapEditorResult("test", self.map_data)

        if key in (pygame.K_ESCAPE, pygame.K_b):
            return MapEditorResult("cancel", self.map_data)

        return None

    def _handle_panel_click(self, mouse_pos: Tuple[int, int]) -> Optional[MapEditorResult]:
        back = pygame.Rect(BACK_BUTTON_RECT)
        if back.collidepoint(mouse_pos):
            return MapEditorResult("cancel", self.map_data)

        for rect, tool in self.tool_buttons:
            if rect.collidepoint(mouse_pos):
                self.current_tool = tool
                self.zone_anchor = None
                self.status = f"Selected tool: {TOOL_LABELS[tool]}"
                return None

        for action, rect in self.action_buttons.items():
            if rect.collidepoint(mouse_pos):
                if action == "save":
                    self._save_current_map()
                    return None
                if action == "load":
                    self.map_data = load_or_create_default_map()
                    self.zone_anchor = None
                    self.status = f"Loaded {DEFAULT_MAP_PATH.name}"
                    return None
                if action == "blank":
                    self.map_data = blank_map()
                    self.zone_anchor = None
                    self.status = "Started a blank map."
                    return None
                if action == "test":
                    return MapEditorResult("test", self.map_data)
        return None

    def _save_current_map(self):
        path = save_map_data(self.map_data, DEFAULT_MAP_PATH)
        self.status = f"Saved map to {path.name}"

    def _mouse_to_grid(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        if mouse_pos[0] >= WINDOW_WIDTH:
            return None
        x = mouse_pos[0] // CELL_SIZE
        y = mouse_pos[1] // CELL_SIZE
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            return (x, y)
        return None

    def _apply_tool(self, cell: Tuple[int, int]):
        if self.current_tool == TOOL_ERASE:
            self._erase_at(cell)
            return

        if self.current_tool in (TOOL_START_ZONE, TOOL_DEST_ZONE):
            self._apply_zone_tool(cell)
            return

        self._remove_from_static_layers(cell)

        if self.current_tool == TOOL_WALL:
            self.map_data.walls.append(cell)
        elif self.current_tool == TOOL_WATER:
            self.map_data.water.append(cell)
        elif self.current_tool == TOOL_FOREST:
            self.map_data.forest.append(cell)
        elif self.current_tool == TOOL_BARRIER:
            self.map_data.barriers.append(cell)
        elif self.current_tool == TOOL_FIRE:
            if cell not in self.map_data.fire:
                self.map_data.fire.append(cell)
        elif self.current_tool == TOOL_OBJECTIVE:
            if cell not in self.map_data.objective_cells:
                self.map_data.objective_cells.append(cell)
        elif self.current_tool == TOOL_MOVABLE:
            self.map_data.movables = [m for m in self.map_data.movables if (m.x, m.y) != cell]
            self.map_data.movables.append(MovableSpawnData(cell[0], cell[1]))

        self._dedupe_layers()

    def _apply_zone_tool(self, cell: Tuple[int, int]):
        if self.zone_anchor is None:
            self.zone_anchor = cell
            self.status = f"Zone anchor set at {cell}. Click a second corner to finish."
            return

        x1, y1 = self.zone_anchor
        x2, y2 = cell
        zx = min(x1, x2)
        zy = min(y1, y2)
        width = abs(x2 - x1) + 1
        height = abs(y2 - y1) + 1
        zone = ZoneData(
            "Start" if self.current_tool == TOOL_START_ZONE else "Objective",
            zx,
            zy,
            width,
            height,
            (40, 80, 120) if self.current_tool == TOOL_START_ZONE else (80, 120, 40),
        )
        if self.current_tool == TOOL_START_ZONE:
            self.map_data.start_zone = zone
        else:
            self.map_data.dest_zone = zone
        self.zone_anchor = None
        self.status = f"Placed {TOOL_LABELS[self.current_tool]}."

    def _erase_at(self, cell: Tuple[int, int]):
        self._remove_from_static_layers(cell)
        self.map_data.fire = [pos for pos in self.map_data.fire if pos != cell]
        self.map_data.objective_cells = [pos for pos in self.map_data.objective_cells if pos != cell]
        self.map_data.movables = [m for m in self.map_data.movables if (m.x, m.y) != cell]
        self.status = f"Erased {cell}."

    def _remove_from_static_layers(self, cell: Tuple[int, int]):
        for attr in ("walls", "water", "forest", "barriers"):
            current = getattr(self.map_data, attr)
            setattr(self.map_data, attr, [pos for pos in current if pos != cell])

    def _dedupe_layers(self):
        for attr in ("walls", "water", "forest", "barriers", "fire", "objective_cells"):
            seen = []
            for cell in getattr(self.map_data, attr):
                if cell not in seen:
                    seen.append(cell)
            setattr(self.map_data, attr, seen)

    def _build_preview_world(self):
        return build_runtime_world(self.map_data)

    def _render(self, window):
        window.fill(PANEL_BG_COLOR)
        play_surface = window.subsurface(pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        play_surface.fill(BG_COLOR)
        runtime = self._build_preview_world()
        self._draw_zones(play_surface, runtime.start_zone, runtime.dest_zone)
        self._draw_objective_cells(play_surface, runtime.objective_cells)
        runtime.grid.draw(play_surface)
        self._draw_sidebar(window)

    def _draw_zones(self, surface, start_zone: Zone, dest_zone: Zone):
        start_zone.draw(surface)
        dest_zone.draw(surface)

    def _draw_objective_cells(self, surface, objective_cells):
        for ox, oy in objective_cells:
            block_rect = pygame.Rect(ox * CELL_SIZE, oy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            inset_rect = block_rect.inflate(-6, -6)
            pygame.draw.rect(surface, (210, 210, 80), inset_rect, border_radius=3)
            pygame.draw.rect(surface, (240, 240, 240), inset_rect, 2, border_radius=3)

    def _draw_sidebar(self, window):
        panel_x = WINDOW_WIDTH
        pygame.draw.rect(window, PANEL_BG_COLOR, (panel_x, 0, HUD_PANEL_WIDTH, WINDOW_HEIGHT))
        pygame.draw.line(window, PANEL_DIVIDER_COLOR, (panel_x, 0), (panel_x, WINDOW_HEIGHT), 2)
        pygame.draw.rect(window, (18, 22, 28), (panel_x, 0, HUD_PANEL_WIDTH, 42))
        title = self.font.render("MAP EDITOR", True, PANEL_ACCENT_COLOR)
        window.blit(title, (panel_x + 12, 10))

        self.tool_buttons = []
        self.action_buttons = {}
        self._draw_tool_palette(window, panel_x + 12, 52)
        self._draw_action_buttons(window, panel_x + 12, self._tool_palette_bottom + 14)
        self._draw_status_box(window, panel_x + 12, self._action_buttons_bottom + 14)

        rect = pygame.Rect(BACK_BUTTON_RECT)
        hover = rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(window, BUTTON_HOVER_COLOR if hover else BUTTON_BG_COLOR, rect, border_radius=8)
        pygame.draw.rect(window, PANEL_DIVIDER_COLOR, rect, 1, border_radius=8)
        text = self.small_font.render("Back to launcher", True, BUTTON_TEXT_COLOR)
        window.blit(text, text.get_rect(center=rect.center))

    def _draw_tool_palette(self, window, x0: int, y0: int):
        label = self.small_font.render("TOOLS (click or use 1-0)", True, PANEL_TEXT_COLOR)
        window.blit(label, (x0, y0))
        start_y = y0 + 24

        for index, (_, tool, _tool_label) in enumerate(TOOLS):
            col = index % TOOL_GRID_COLS
            row = index // TOOL_GRID_COLS
            x = x0 + col * (TOOL_BUTTON_SIZE + TOOL_BUTTON_GAP_X)
            y_btn = start_y + row * (TOOL_BUTTON_SIZE + TOOL_BUTTON_GAP_Y)
            rect = pygame.Rect(x, y_btn, TOOL_BUTTON_SIZE, TOOL_BUTTON_SIZE)
            self.tool_buttons.append((rect, tool))

            active = tool == self.current_tool
            hover = rect.collidepoint(pygame.mouse.get_pos())
            fill = TOOL_ACTIVE if active else (BUTTON_HOVER_COLOR if hover else TOOL_BG)
            pygame.draw.rect(window, fill, rect, border_radius=8)
            border_color = PANEL_ACCENT_COLOR if active else PANEL_DIVIDER_COLOR
            border_width = 3 if active else 1
            pygame.draw.rect(window, border_color, rect, border_width, border_radius=8)

            badge = pygame.Rect(rect.x + 4, rect.y + 4, 14, 14)
            pygame.draw.rect(window, (15, 18, 22), badge, border_radius=4)
            key_label = self.tiny_font.render(TOOL_SHORTCUTS[tool], True, BUTTON_TEXT_COLOR)
            window.blit(key_label, key_label.get_rect(center=badge.center))

            preview_rect = pygame.Rect(rect.x + 10, rect.y + 12, rect.w - 20, rect.h - 18)
            self._draw_tool_preview(window, tool, preview_rect)

        rows = (len(TOOLS) + TOOL_GRID_COLS - 1) // TOOL_GRID_COLS
        self._tool_palette_bottom = start_y + rows * TOOL_BUTTON_SIZE + (rows - 1) * TOOL_BUTTON_GAP_Y

    def _draw_action_buttons(self, window, x0: int, y0: int):
        label = self.small_font.render("ACTIONS", True, PANEL_TEXT_COLOR)
        window.blit(label, (x0, y0))
        y = y0 + 22
        button_w = (HUD_PANEL_WIDTH - 36 - ACTION_BUTTON_GAP) // 2
        actions = [
            ("save", "Save"),
            ("load", "Load"),
            ("blank", "Blank"),
            ("test", "Test"),
        ]
        for index, (action, label_text) in enumerate(actions):
            col = index % 2
            row = index // 2
            rect = pygame.Rect(
                x0 + col * (button_w + ACTION_BUTTON_GAP),
                y + row * (ACTION_BUTTON_H + ACTION_BUTTON_GAP),
                button_w,
                ACTION_BUTTON_H,
            )
            self.action_buttons[action] = rect
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(window, BUTTON_HOVER_COLOR if hover else BUTTON_BG_COLOR, rect, border_radius=8)
            pygame.draw.rect(window, PANEL_DIVIDER_COLOR, rect, 1, border_radius=8)
            text = self.small_font.render(label_text, True, BUTTON_TEXT_COLOR)
            window.blit(text, text.get_rect(center=rect.center))

        rows = (len(actions) + 1) // 2
        self._action_buttons_bottom = y + rows * ACTION_BUTTON_H + (rows - 1) * ACTION_BUTTON_GAP

    def _draw_status_box(self, window, x0: int, y0: int):
        rect = pygame.Rect(x0, y0, HUD_PANEL_WIDTH - 24, STATUS_BOX_H)
        pygame.draw.rect(window, STATUS_BG, rect, border_radius=10)
        pygame.draw.rect(window, PANEL_DIVIDER_COLOR, rect, 1, border_radius=10)
        title = self.small_font.render(f"ACTIVE: {TOOL_LABELS[self.current_tool]} ({TOOL_SHORTCUTS[self.current_tool]})", True, PANEL_ACCENT_COLOR)
        window.blit(title, (rect.x + 10, rect.y + 10))

        lines = [
            "Left click paints. Right click erases.",
            "Start/Dest zone: click two corners.",
            self.status,
        ]
        yy = rect.y + 34
        for line in lines:
            wrapped_lines = self._wrap_text(line, rect.width - 20)
            line_color = PANEL_TEXT_COLOR if line == self.status else PANEL_MUTED_TEXT_COLOR
            for wrapped in wrapped_lines:
                surf = self.tiny_font.render(wrapped, True, line_color)
                window.blit(surf, (rect.x + 10, yy))
                yy += surf.get_height() + 3

    def _draw_tool_preview(self, window, tool: str, rect: pygame.Rect):
        preview_box = rect.copy()
        pygame.draw.rect(window, TOOL_PREVIEW_BG, preview_box, border_radius=6)

        tile_size = min(preview_box.w, preview_box.h)
        tile_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        tile_surface.fill((0, 0, 0, 0))
        self._draw_tool_tile_surface(tile_surface, tool)
        scaled = pygame.transform.smoothscale(tile_surface, (tile_size, tile_size))
        tile_rect = scaled.get_rect(center=preview_box.center)
        window.blit(scaled, tile_rect)

    def _draw_tool_tile_surface(self, surface: pygame.Surface, tool: str):
        surface.fill((0, 0, 0, 0))
        if tool == TOOL_WALL:
            Wall(0, 0).draw(surface)
        elif tool == TOOL_WATER:
            Water(0, 0).draw(surface)
        elif tool == TOOL_FOREST:
            Forest(0, 0).draw(surface)
        elif tool == TOOL_BARRIER:
            Barrier(0, 0).draw(surface)
        elif tool == TOOL_MOVABLE:
            Movable((0, 0, 255), 0, 0).draw(surface)
        elif tool == TOOL_FIRE:
            pygame.draw.rect(surface, (255, 100, 0), (0, 0, CELL_SIZE, CELL_SIZE))
        elif tool == TOOL_OBJECTIVE:
            inset_rect = pygame.Rect(0, 0, CELL_SIZE, CELL_SIZE).inflate(-6, -6)
            pygame.draw.rect(surface, (210, 210, 80), inset_rect, border_radius=3)
            pygame.draw.rect(surface, (240, 240, 240), inset_rect, 2, border_radius=3)
        elif tool == TOOL_START_ZONE:
            zone_rect = pygame.Rect(0, 0, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, (40, 80, 120), zone_rect)
            pygame.draw.rect(surface, (180, 220, 255), zone_rect, 2)
        elif tool == TOOL_DEST_ZONE:
            zone_rect = pygame.Rect(0, 0, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, (80, 120, 40), zone_rect)
            pygame.draw.rect(surface, (220, 255, 180), zone_rect, 2)
        elif tool == TOOL_ERASE:
            pygame.draw.rect(surface, (180, 120, 140), (0, 0, CELL_SIZE, CELL_SIZE))
            pygame.draw.line(surface, (245, 245, 245), (3, 3), (CELL_SIZE - 3, CELL_SIZE - 3), 3)
            pygame.draw.line(surface, (245, 245, 245), (CELL_SIZE - 3, 3), (3, CELL_SIZE - 3), 3)

    def _wrap_text(self, text: str, max_width: int):
        words = text.split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if self.tiny_font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines


def run_map_editor(initial_map: Optional[MapData] = None) -> MapEditorResult:
    editor = MapEditor(initial_map)
    return editor.run()
