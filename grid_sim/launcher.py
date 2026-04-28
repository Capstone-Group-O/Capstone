import sys

import pygame

from .config import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from .renderer import SimulationRenderer
from .simulation import SimulationManager

# ── Layout ────────────────────────────────────────────────────────────────────
TAB_H   = 30
PANEL_W = 280                          # left sidebar width
TOTAL_W = PANEL_W + WINDOW_WIDTH       # 880
TOTAL_H = TAB_H + WINDOW_HEIGHT        # 630

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = (10,  14,  20)
PANEL   = (13,  19,  27)
ACCENT  = (34,  197, 94)
DIM     = (65,  90,  78)
DIVIDER = (26,  40,  32)
TEXT    = (180, 210, 195)

TABS = ["START SIM", "RUBEN", "RALEIGH", "GRACE", "KIARA", "JASMINE"]


# ── Helpers ───────────────────────────────────────────────────────────────────
def _make_preview(simulation):
    surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    SimulationRenderer(surf).render(simulation)
    return surf


def _draw_tab_bar(window, font, hovered, selected):
    tab_w = TOTAL_W // len(TABS)
    pygame.draw.rect(window, BG, (0, 0, TOTAL_W, TAB_H))
    pygame.draw.line(window, DIVIDER, (0, TAB_H - 1), (TOTAL_W, TAB_H - 1))

    for i, label in enumerate(TABS):
        x = i * tab_w
        lit   = (i == selected) or (i == hovered)
        color = ACCENT if lit else DIM

        if i > 0:
            pygame.draw.line(window, DIVIDER, (x, 6), (x, TAB_H - 7))
        if i == selected:
            pygame.draw.line(window, ACCENT, (x + 2, TAB_H - 2), (x + tab_w - 3, TAB_H - 2), 2)

        ts = font.render(label, True, color)
        window.blit(ts, ts.get_rect(center=(x + tab_w // 2, TAB_H // 2)))


def _draw_panel(window, name_font, small_font, selected):
    """Left sidebar — always dark, shows member name when a tab is active."""
    r = pygame.Rect(0, TAB_H, PANEL_W, WINDOW_HEIGHT)
    pygame.draw.rect(window, PANEL, r)
    pygame.draw.line(window, DIVIDER, (PANEL_W - 1, TAB_H), (PANEL_W - 1, TOTAL_H))

    cy = TAB_H + WINDOW_HEIGHT // 2

    if selected == 0:
        hint = small_font.render("SELECT A MODULE  OR  START SIM", True, DIM)
        window.blit(hint, hint.get_rect(center=(PANEL_W // 2, cy)))
    else:
        ns = name_font.render(TABS[selected], True, ACCENT)
        window.blit(ns, ns.get_rect(center=(PANEL_W // 2, cy)))


# ── Entry point ───────────────────────────────────────────────────────────────
def launch():
    pygame.init()
    window = pygame.display.set_mode((TOTAL_W, TOTAL_H))
    pygame.display.set_caption("SWORD")

    simulation = SimulationManager()
    preview    = _make_preview(simulation)   # frozen 600×600 grid surface

    try:
        font       = pygame.font.SysFont("monospace", 12)
        name_font  = pygame.font.SysFont("monospace", 36, bold=True)
        small_font = pygame.font.SysFont("monospace", 11)
    except Exception:
        font       = pygame.font.Font(None, 16)
        name_font  = pygame.font.Font(None, 44)
        small_font = pygame.font.Font(None, 14)

    tab_w    = TOTAL_W // len(TABS)
    selected = 0
    clock    = pygame.time.Clock()

    while True:
        mx, my = pygame.mouse.get_pos()
        hovered = min(mx // tab_w, len(TABS) - 1) if my < TAB_H else -1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if selected != 0:
                    selected = 0
                else:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and my < TAB_H:
                clicked = min(mx // tab_w, len(TABS) - 1)
                if clicked == 0:
                    pygame.quit()
                    return simulation
                selected = clicked

        window.fill(BG)
        window.blit(preview, (PANEL_W, TAB_H))   # grid always on the right
        _draw_panel(window, name_font, small_font, selected)
        _draw_tab_bar(window, font, hovered, selected)

        pygame.display.flip()
        clock.tick(FPS)
