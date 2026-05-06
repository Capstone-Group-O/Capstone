import pygame
from typing import Optional

from .config import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from .map_data import MapData
from .map_storage import delete_custom_mission, list_custom_missions, load_custom_mission
from .renderer import SimulationRenderer
from .simulation import SimulationManager

TAB_H = 34
PANEL_W = 320
TOTAL_W = PANEL_W + WINDOW_WIDTH
TOTAL_H = TAB_H + WINDOW_HEIGHT

BG = (10, 14, 20)
PANEL = (13, 19, 27)
ACCENT = (34, 197, 94)
DIM = (65, 90, 78)
DIVIDER = (26, 40, 32)
TEXT = (180, 210, 195)
BUTTON = (40, 48, 58)
BUTTON_HOVER = (58, 68, 82)
CARD = (20, 26, 34)
CARD_HOVER = (28, 34, 44)
ICON_BG = (30, 38, 48)
ICON_HOVER = (48, 58, 72)
DELETE_ACCENT = (170, 70, 70)

TABS = [
    ("RANDOMIZED SIM", "simulation"),
    ("CUSTOM MISSIONS", "missions"),
    ("MAP EDITOR", "editor"),
    ("QUIT", "quit"),
]


class LauncherState:
    def __init__(self):
        self.selected = 0
        self.scroll_y = 0
        self.mission_buttons = []
        self.mission_edit_buttons = []
        self.mission_delete_buttons = []
        self.action_button = None
        self.selected_mission_path = None
        self.preview_cache = {}
        self.preview_sim = _make_preview_surface(SimulationManager())
        self.preview_editor = None
        self.preview_mission = None


def _make_preview_surface(simulation):
    surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    SimulationRenderer(surf).render(simulation)
    return surf


def _get_preview_for_map(state: LauncherState, map_data: MapData, cache_key: str):
    if cache_key not in state.preview_cache:
        try:
            sim = SimulationManager(map_data)
            state.preview_cache[cache_key] = _make_preview_surface(sim)
        except Exception:
            return None
    return state.preview_cache[cache_key]


def _draw_tab_bar(window, font, hovered, selected):
    tab_w = TOTAL_W // len(TABS)
    pygame.draw.rect(window, BG, (0, 0, TOTAL_W, TAB_H))
    pygame.draw.line(window, DIVIDER, (0, TAB_H - 1), (TOTAL_W, TAB_H - 1))

    for i, (label, _) in enumerate(TABS):
        x = i * tab_w
        lit = (i == selected) or (i == hovered)
        color = ACCENT if lit else DIM

        if i > 0:
            pygame.draw.line(window, DIVIDER, (x, 6), (x, TAB_H - 7))
        if i == selected:
            pygame.draw.line(window, ACCENT, (x + 2, TAB_H - 2), (x + tab_w - 3, TAB_H - 2), 2)

        ts = font.render(label, True, color)
        window.blit(ts, ts.get_rect(center=(x + tab_w // 2, TAB_H // 2)))


def _wrap_text(font, text, max_width):
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


def _render_multiline(window, font, lines, x, y, color=TEXT, line_gap=6, max_width=None):
    yy = y
    if max_width is None:
        max_width = PANEL_W - x - 16

    for line in lines:
        wrapped = _wrap_text(font, line, max_width) if line else [""]
        for wrapped_line in wrapped:
            if wrapped_line:
                surf = font.render(wrapped_line, True, color)
                window.blit(surf, (x, yy))
                yy += surf.get_height() + line_gap
            else:
                yy += font.get_height() + line_gap
    return yy


def _draw_button(window, font, rect, label):
    hover = rect.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(window, BUTTON_HOVER if hover else BUTTON, rect, border_radius=8)
    pygame.draw.rect(window, DIVIDER, rect, 1, border_radius=8)
    surf = font.render(label, True, TEXT)
    window.blit(surf, surf.get_rect(center=rect.center))


def _draw_icon_button(window, font, rect, label, delete=False):
    hover = rect.collidepoint(pygame.mouse.get_pos())
    fill = ICON_HOVER if hover else ICON_BG
    border = DELETE_ACCENT if delete else DIVIDER
    pygame.draw.rect(window, fill, rect, border_radius=6)
    pygame.draw.rect(window, border, rect, 1, border_radius=6)
    surf = font.render(label, True, TEXT)
    window.blit(surf, surf.get_rect(center=rect.center))


def _update_mission_preview(state: LauncherState, missions):
    if not missions:
        state.preview_mission = None
        state.selected_mission_path = None
        return

    if state.selected_mission_path is None or not any(m["path"] == state.selected_mission_path for m in missions):
        state.selected_mission_path = missions[0]["path"]

    selected = next((m for m in missions if m["path"] == state.selected_mission_path), missions[0])
    map_data = load_custom_mission(selected["path"])
    state.preview_mission = _get_preview_for_map(state, map_data, f"mission:{selected['path']}")


def _draw_mission_list(window, body_font, small_font, state: LauncherState):
    missions = list_custom_missions()
    _update_mission_preview(state, missions)

    viewport = pygame.Rect(16, TAB_H + 74, PANEL_W - 32, TOTAL_H - TAB_H - 94)
    clip = window.get_clip()
    window.set_clip(viewport)

    state.mission_buttons = []
    state.mission_edit_buttons = []
    state.mission_delete_buttons = []
    content_y = viewport.y - state.scroll_y
    content_bottom = content_y

    if not missions:
        lines = [
            "No custom missions saved yet.",
            "Create one in the map editor, then",
            "save it with a title and description.",
        ]
        _render_multiline(window, body_font, lines, viewport.x, content_y, max_width=viewport.width)
        content_bottom = content_y + 80
    else:
        for mission in missions:
            desc_lines = _wrap_text(
                small_font,
                mission.get("description") or "No description.",
                viewport.width - 24,
            )
            card_h = 76 + len(desc_lines) * 16
            card = pygame.Rect(viewport.x, content_y, viewport.width, card_h)
            hover = card.collidepoint(pygame.mouse.get_pos())
            selected = mission["path"] == state.selected_mission_path
            fill = CARD_HOVER if hover or selected else CARD
            pygame.draw.rect(window, fill, card, border_radius=10)
            pygame.draw.rect(window, ACCENT if selected else DIVIDER, card, 2 if selected else 1, border_radius=10)

            title_surf = body_font.render(mission.get("title", "Untitled Mission"), True, ACCENT)
            window.blit(title_surf, (card.x + 12, card.y + 10))

            icon_size = 24
            delete_rect = pygame.Rect(card.right - 12 - icon_size, card.y + 10, icon_size, icon_size)
            edit_rect = pygame.Rect(delete_rect.x - 6 - icon_size, card.y + 10, icon_size, icon_size)
            _draw_icon_button(window, small_font, edit_rect, "E")
            _draw_icon_button(window, small_font, delete_rect, "X", delete=True)
            state.mission_edit_buttons.append((edit_rect, mission["path"]))
            state.mission_delete_buttons.append((delete_rect, mission["path"]))

            yy = card.y + 40
            for line in desc_lines:
                surf = small_font.render(line, True, TEXT)
                window.blit(surf, (card.x + 12, yy))
                yy += surf.get_height() + 2

            button_rect = pygame.Rect(card.x + 12, card.bottom - 38, card.width - 24, 28)
            _draw_button(window, small_font, button_rect, "Select Mission")
            state.mission_buttons.append((button_rect, mission["path"], card))

            content_y += card_h + 10
            content_bottom = content_y

    window.set_clip(clip)
    max_scroll = max(0, content_bottom - viewport.y - viewport.height)
    state.scroll_y = max(0, min(state.scroll_y, max_scroll))


def _draw_panel(window, title_font, body_font, small_font, state: LauncherState):
    r = pygame.Rect(0, TAB_H, PANEL_W, WINDOW_HEIGHT)
    pygame.draw.rect(window, PANEL, r)
    pygame.draw.line(window, DIVIDER, (PANEL_W - 1, TAB_H), (PANEL_W - 1, TOTAL_H))

    label, action = TABS[state.selected]
    title = title_font.render(label, True, ACCENT)
    window.blit(title, (16, TAB_H + 18))
    pygame.draw.line(window, DIVIDER, (16, TAB_H + 52), (PANEL_W - 16, TAB_H + 52))

    state.action_button = None
    panel_text_width = PANEL_W - 32

    if action == "simulation":
        lines = [
            "Launch the randomized simulation.",
            "",
            "This simulator was built to put operators in scenarios where terrain and hazards"
            " are randomized for each run.",
        ]
        _render_multiline(window, body_font, lines, 16, TAB_H + 68, max_width=panel_text_width)
        state.action_button = (pygame.Rect(16, TOTAL_H - 54, PANEL_W - 32, 34), "simulation")
        _draw_button(window, body_font, state.action_button[0], "Start randomized sim")
    elif action == "missions":
        _draw_mission_list(window, body_font, small_font, state)
    elif action == "editor":
        lines = [
            "Open the custom map editor.",
            "",
            "Create, edit, test, and save missions for the Custom Missions tab.",
        ]
        _render_multiline(window, body_font, lines, 16, TAB_H + 68, max_width=panel_text_width)
        state.action_button = (pygame.Rect(16, TOTAL_H - 54, PANEL_W - 32, 34), "editor")
        _draw_button(window, body_font, state.action_button[0], "Open map editor")
    else:
        lines = ["Exit the application."]
        _render_multiline(window, body_font, lines, 16, TAB_H + 68, max_width=panel_text_width)
        state.action_button = (pygame.Rect(16, TOTAL_H - 54, PANEL_W - 32, 34), "quit")
        _draw_button(window, body_font, state.action_button[0], "Quit application")


def _draw_preview_area(window, small_font, state: LauncherState):
    action = TABS[state.selected][1]
    preview_rect = pygame.Rect(PANEL_W, TAB_H, WINDOW_WIDTH, WINDOW_HEIGHT)

    pygame.draw.rect(window, BG, preview_rect)

    surf = None
    if action == "simulation":
        surf = state.preview_sim
    elif action == "missions":
        surf = state.preview_mission
    elif action == "editor":
        surf = state.preview_editor

    if surf is not None:
        window.blit(surf, preview_rect.topleft)
    else:
        empty = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        empty.fill((18, 22, 28))
        window.blit(empty, preview_rect.topleft)
        msg = small_font.render("No preview available", True, TEXT)
        window.blit(msg, msg.get_rect(center=preview_rect.center))


def launch(editor_map: Optional[MapData] = None):
    pygame.init()
    window = pygame.display.set_mode((TOTAL_W, TOTAL_H))
    pygame.display.set_caption("SWORD")

    try:
        tab_font = pygame.font.SysFont("monospace", 13)
        title_font = pygame.font.SysFont("monospace", 24, bold=True)
        body_font = pygame.font.SysFont("monospace", 15)
        small_font = pygame.font.SysFont("monospace", 12)
    except Exception:
        tab_font = pygame.font.Font(None, 18)
        title_font = pygame.font.Font(None, 32)
        body_font = pygame.font.Font(None, 22)
        small_font = pygame.font.Font(None, 16)

    state = LauncherState()
    state.preview_sim = _make_preview_surface(SimulationManager())
    if editor_map is not None:
        state.preview_editor = _get_preview_for_map(state, editor_map, "editor_current")
    else:
        state.preview_editor = None

    tab_w = TOTAL_W // len(TABS)
    clock = pygame.time.Clock()

    while True:
        mx, my = pygame.mouse.get_pos()
        hovered = min(mx // tab_w, len(TABS) - 1) if my < TAB_H else -1

        window.fill(BG)
        _draw_preview_area(window, small_font, state)
        _draw_panel(window, title_font, body_font, small_font, state)
        _draw_tab_bar(window, tab_font, hovered, state.selected)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return {"action": "quit"}

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return {"action": "quit"}
                if event.key == pygame.K_LEFT:
                    state.selected = (state.selected - 1) % len(TABS)
                    state.scroll_y = 0
                elif event.key == pygame.K_RIGHT:
                    state.selected = (state.selected + 1) % len(TABS)
                    state.scroll_y = 0
                elif event.key == pygame.K_UP:
                    state.scroll_y = max(0, state.scroll_y - 40)
                elif event.key == pygame.K_DOWN:
                    state.scroll_y += 40
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    action = TABS[state.selected][1]
                    pygame.quit()
                    if action == "simulation":
                        return {
                            "action": "simulation",
                            "simulation": SimulationManager(),
                            "return_action": "launcher",
                        }
                    if action == "editor":
                        return {"action": "editor", "map_data": editor_map}
                    if action == "quit":
                        return {"action": "quit"}

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    state.scroll_y = max(0, state.scroll_y - 40)
                elif event.button == 5:
                    state.scroll_y += 40
                elif event.button == 1:
                    if my < TAB_H:
                        clicked = min(mx // tab_w, len(TABS) - 1)
                        if clicked == state.selected:
                            action = TABS[state.selected][1]
                            pygame.quit()
                            if action == "simulation":
                                return {
                                    "action": "simulation",
                                    "simulation": SimulationManager(),
                                    "return_action": "launcher",
                                }
                            if action == "editor":
                                return {"action": "editor", "map_data": editor_map}
                            if action == "quit":
                                return {"action": "quit"}
                        else:
                            state.selected = clicked
                            state.scroll_y = 0
                    else:
                        if TABS[state.selected][1] == "missions":
                            for rect, path in state.mission_delete_buttons:
                                if rect.collidepoint(event.pos):
                                    delete_custom_mission(path)
                                    if state.selected_mission_path == path:
                                        state.selected_mission_path = None
                                    state.scroll_y = max(0, state.scroll_y - 1)
                                    break
                            else:
                                for rect, path in state.mission_edit_buttons:
                                    if rect.collidepoint(event.pos):
                                        pygame.quit()
                                        return {"action": "editor", "map_data": load_custom_mission(path)}
                                for rect, path, card in state.mission_buttons:
                                    if rect.collidepoint(event.pos):
                                        pygame.quit()
                                        return {
                                            "action": "simulation",
                                            "simulation": SimulationManager(load_custom_mission(path)),
                                            "return_action": "launcher",
                                        }
                                    if card.collidepoint(event.pos):
                                        state.selected_mission_path = path
                                        break

                        if state.action_button and state.action_button[0].collidepoint(event.pos):
                            action = state.action_button[1]
                            pygame.quit()
                            if action == "simulation":
                                return {
                                    "action": "simulation",
                                    "simulation": SimulationManager(),
                                    "return_action": "launcher",
                                }
                            if action == "editor":
                                return {"action": "editor", "map_data": editor_map}
                            if action == "quit":
                                return {"action": "quit"}

        pygame.display.flip()
        clock.tick(FPS)