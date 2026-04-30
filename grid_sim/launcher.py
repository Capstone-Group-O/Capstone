import pygame

from .config import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from .renderer import SimulationRenderer
from .simulation import SimulationManager

TAB_H = 34
PANEL_W = 300
TOTAL_W = PANEL_W + WINDOW_WIDTH
TOTAL_H = TAB_H + WINDOW_HEIGHT

BG = (10, 14, 20)
PANEL = (13, 19, 27)
ACCENT = (34, 197, 94)
DIM = (65, 90, 78)
DIVIDER = (26, 40, 32)
TEXT = (180, 210, 195)
SUBTEXT = (120, 145, 132)

TABS = [
    ("START SIM", "simulation"),
    ("MAP EDITOR", "editor"),
    ("ABOUT", "about"),
    ("QUIT", "quit"),
]


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


def _draw_panel(window, title_font, body_font, small_font, selected):
    r = pygame.Rect(0, TAB_H, PANEL_W, WINDOW_HEIGHT)
    pygame.draw.rect(window, PANEL, r)
    pygame.draw.line(window, DIVIDER, (PANEL_W - 1, TAB_H), (PANEL_W - 1, TOTAL_H))

    label, action = TABS[selected]
    title = title_font.render(label, True, ACCENT)
    window.blit(title, (20, TAB_H + 22))
    pygame.draw.line(window, DIVIDER, (20, TAB_H + 58), (PANEL_W - 20, TAB_H + 58))

    if action == "simulation":
        lines = [
            "Launch the randomized simulation.",
            "",
            "Inside the sim, the right panel",
            "contains status text and a Back",
            "button that returns here.",
            "",
            "Click this tab again, or press",
            "Enter, to launch.",
        ]
    elif action == "editor":
        lines = [
            "Open the custom map editor.",
            "",
            "Inside the editor, the right panel",
            "contains tool/help text and a",
            "Back button that returns here.",
            "",
            "Click this tab again, or press",
            "Enter, to open it.",
        ]
    elif action == "about":
        lines = [
            "SWORD launcher",
            "",
            "This keeps the tabbed launcher",
            "style while using the newer",
            "navigation flow.",
        ]
    else:
        lines = [
            "Exit the application.",
            "",
            "Click this tab again, or press",
            "Enter, to quit.",
        ]

    bottom_y = _render_multiline(window, body_font, lines, 20, TAB_H + 74)
    hint = small_font.render("Left/Right switches tabs.", True, SUBTEXT)
    window.blit(hint, (20, min(bottom_y + 20, TOTAL_H - 32)))


def launch():
    pygame.init()
    window = pygame.display.set_mode((TOTAL_W, TOTAL_H))
    pygame.display.set_caption("SWORD")

    simulation = SimulationManager()
    preview = _make_preview(simulation)

    try:
        tab_font = pygame.font.SysFont("monospace", 13)
        title_font = pygame.font.SysFont("monospace", 26, bold=True)
        body_font = pygame.font.SysFont("monospace", 15)
        small_font = pygame.font.SysFont("monospace", 12)
    except Exception:
        tab_font = pygame.font.Font(None, 18)
        title_font = pygame.font.Font(None, 32)
        body_font = pygame.font.Font(None, 22)
        small_font = pygame.font.Font(None, 16)

    tab_w = TOTAL_W // len(TABS)
    selected = 0
    clock = pygame.time.Clock()

    while True:
        mx, my = pygame.mouse.get_pos()
        hovered = min(mx // tab_w, len(TABS) - 1) if my < TAB_H else -1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return {"action": "quit"}

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return {"action": "quit"}
                if event.key == pygame.K_LEFT:
                    selected = (selected - 1) % len(TABS)
                elif event.key == pygame.K_RIGHT:
                    selected = (selected + 1) % len(TABS)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    _, action = TABS[selected]
                    pygame.quit()
                    if action == "simulation":
                        return {"action": "simulation", "simulation": SimulationManager(), "return_action": "launcher"}
                    if action == "editor":
                        return {"action": "editor", "map_data": None}
                    if action == "quit":
                        return {"action": "quit"}

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and my < TAB_H:
                clicked = min(mx // tab_w, len(TABS) - 1)
                if clicked == selected:
                    _, action = TABS[selected]
                    pygame.quit()
                    if action == "simulation":
                        return {"action": "simulation", "simulation": SimulationManager(), "return_action": "launcher"}
                    if action == "editor":
                        return {"action": "editor", "map_data": None}
                    if action == "quit":
                        return {"action": "quit"}
                else:
                    selected = clicked

        window.fill(BG)
        window.blit(preview, (PANEL_W, TAB_H))
        _draw_panel(window, title_font, body_font, small_font, selected)
        _draw_tab_bar(window, tab_font, hovered, selected)
        pygame.display.flip()
        clock.tick(FPS)
