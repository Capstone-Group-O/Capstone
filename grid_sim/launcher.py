# launcher.py
import pygame

from .config import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from .map_storage import list_custom_missions, load_custom_mission
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
SUBTEXT = (120, 145, 132)
BUTTON = (40, 48, 58)
BUTTON_HOVER = (58, 68, 82)
CARD = (20, 26, 34)
CARD_HOVER = (28, 34, 44)

TABS = [
    ("START SIM", "simulation"),
    ("CUSTOM MISSIONS", "missions"),
    ("MAP EDITOR", "editor"),
    ("ABOUT", "about"),
    ("QUIT", "quit"),
]


class LauncherState:
    def __init__(self):
        self.selected = 0
        self.scroll_y = 0
        self.mission_buttons = []
        self.action_button = None


def _make_preview(simulation):
    surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    SimulationRenderer(surf).render(simulation)
    return surf


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


def _render_multiline(window, font, lines, x, y, color=TEXT, line_gap=6):
    yy = y
    for line in lines:
        surf = font.render(line, True, color)
        window.blit(surf, (x, yy))
        yy += surf.get_height() + line_gap
    return yy


def _draw_button(window, font, rect, label):
    hover = rect.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(window, BUTTON_HOVER if hover else BUTTON, rect, border_radius=8)
    pygame.draw.rect(window, DIVIDER, rect, 1, border_radius=8)
    surf = font.render(label, True, TEXT)
    window.blit(surf, surf.get_rect(center=rect.center))


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


def _draw_mission_list(window, body_font, small_font, state: LauncherState):
    missions = list_custom_missions()
    viewport = pygame.Rect(16, TAB_H + 74, PANEL_W - 32, TOTAL_H - TAB_H - 94)
    clip = window.get_clip()
    window.set_clip(viewport)

    state.mission_buttons = []
    content_y = viewport.y - state.scroll_y
    content_bottom = content_y

    if not missions:
        lines = [
            "No custom missions saved yet.",
            "Create one in the map editor, then",
            "save it with a title and description.",
        ]
        _render_multiline(window, body_font, lines, viewport.x, content_y)
        content_bottom = content_y + 80
    else:
        for mission in missions:
            desc_lines = _wrap_text(
                small_font,
                mission.get("description") or "No description.",
                viewport.width - 24,
            )
            card_h = 72 + len(desc_lines) * 16
            card = pygame.Rect(viewport.x, content_y, viewport.width, card_h)
            hover = card.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(window, CARD_HOVER if hover else CARD, card, border_radius=10)
            pygame.draw.rect(window, DIVIDER, card, 1, border_radius=10)

            title_surf = body_font.render(mission.get("title", "Untitled Mission"), True, ACCENT)
            window.blit(title_surf, (card.x + 12, card.y + 10))

            yy = card.y + 34
            for line in desc_lines:
                surf = small_font.render(line, True, TEXT)
                window.blit(surf, (card.x + 12, yy))
                yy += surf.get_height() + 2

            button_rect = pygame.Rect(card.x + 12, card.bottom - 38, card.width - 24, 28)
            _draw_button(window, small_font, button_rect, "Select Mission")
            state.mission_buttons.append((button_rect, mission["path"]))

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

    if action == "simulation":
        lines = [
            "Launch the randomized simulation.",
            "",
            "Use this for quick sandbox runs",
            "without selecting a saved mission.",
        ]
        _render_multiline(window, body_font, lines, 16, TAB_H + 68)
        state.action_button = (pygame.Rect(16, TOTAL_H - 54, PANEL_W - 32, 34), "simulation")
        _draw_button(window, body_font, state.action_button[0], "Start randomized sim")
    elif action == "missions":
        _draw_mission_list(window, body_font, small_font, state)
    elif action == "editor":
        lines = [
            "Open the custom map editor.",
            "",
            "Create, edit, test, and save",
            "missions for the Custom Missions tab.",
        ]
        _render_multiline(window, body_font, lines, 16, TAB_H + 68)
        state.action_button = (pygame.Rect(16, TOTAL_H - 54, PANEL_W - 32, 34), "editor")
        _draw_button(window, body_font, state.action_button[0], "Open map editor")
    elif action == "about":
        lines = [
            "SWORD launcher",
            "",
            "Use START SIM for random runs,",
            "CUSTOM MISSIONS for saved maps,",
            "and MAP EDITOR to author new missions.",
        ]
        _render_multiline(window, body_font, lines, 16, TAB_H + 68)
    else:
        lines = [
            "Exit the application.",
        ]
        _render_multiline(window, body_font, lines, 16, TAB_H + 68)
        state.action_button = (pygame.Rect(16, TOTAL_H - 54, PANEL_W - 32, 34), "quit")
        _draw_button(window, body_font, state.action_button[0], "Quit application")


def launch():
    pygame.init()
    window = pygame.display.set_mode((TOTAL_W, TOTAL_H))
    pygame.display.set_caption("SWORD")

    simulation = SimulationManager()
    preview = _make_preview(simulation)

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
    tab_w = TOTAL_W // len(TABS)
    clock = pygame.time.Clock()

    while True:
        mx, my = pygame.mouse.get_pos()
        hovered = min(mx // tab_w, len(TABS) - 1) if my < TAB_H else -1

        window.fill(BG)
        window.blit(preview, (PANEL_W, TAB_H))
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
                        return {"action": "editor", "map_data": None}
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
                                return {"action": "editor", "map_data": None}
                            if action == "quit":
                                return {"action": "quit"}
                        else:
                            state.selected = clicked
                            state.scroll_y = 0
                    else:
                        if TABS[state.selected][1] == "missions":
                            for rect, path in state.mission_buttons:
                                if rect.collidepoint(event.pos):
                                    pygame.quit()
                                    return {
                                        "action": "simulation",
                                        "simulation": SimulationManager(load_custom_mission(path)),
                                        "return_action": "launcher",
                                    }
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
                                return {"action": "editor", "map_data": None}
                            if action == "quit":
                                return {"action": "quit"}

        pygame.display.flip()
        clock.tick(FPS)