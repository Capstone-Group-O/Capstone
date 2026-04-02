"""
grid_sim/game.py — updated with metrics integration

This is your existing game.py with the metrics system wired in.
Key changes are marked with # NEW comments.
"""

import pygame
from .config import *
from .config import WORLD_WIDTH, WORLD_HEIGHT
from .grid import Grid
from .entities import Movable
from .stats import SimStats
from .metrics import EntityMetrics, Zone, random_entity_metrics, SPEED_TIERS  # NEW
from .generation import generate_walls

PHASE_PLANNING = "PLANNING"
PHASE_MOVING = "MOVING"
PHASE_FINISHED = "FINISHED"

def _render_lines(surface, font, lines, x=10, y=10, color=(255, 255, 255), line_gap=2):
    yy = y
    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (x, yy))
        yy += surf.get_height() + line_gap

def game():
    pygame.init()

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Test Sim")

    # Off-screen surface that the grid world is drawn to at native resolution
    world_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

    # Camera state
    cam_zoom = 1.0
    cam_x = 0.0
    cam_y = 0.0
    panning = False
    pan_start = (0, 0)
    cam_start = (0.0, 0.0)

    ZOOM_MIN = 0.3
    ZOOM_MAX = 4.0
    ZOOM_STEP = 0.1

    def screen_to_world(sx, sy):
        """Convert screen (mouse) coordinates to world pixel coordinates."""
        wx = (sx - cam_x) / cam_zoom
        wy = (sy - cam_y) / cam_zoom
        return wx, wy

    clock = pygame.time.Clock()
    running = True
    movables = []  # Populated after zone setup below

    grid = Grid()

    font = pygame.font.Font(None, 26)

    paused = False
    phase = PHASE_PLANNING

    stats = SimStats()

    # NEW — Define start and destination zones
    start_zone = Zone("Start", x=1, y=1, width=4, height=4, color=(40, 80, 120))
    dest_zone = Zone("Objective", x=24, y=24, width=4, height=4, color=(80, 120, 40))

    def build_objective_cells():
        """Choose two distinct objective cells inside the destination zone."""
        preferred_cells = [
            (dest_zone.x + 1, dest_zone.y + 1),
            (dest_zone.x + dest_zone.width - 2, dest_zone.y + dest_zone.height - 2),
            (dest_zone.x + 1, dest_zone.y + dest_zone.height - 2),
            (dest_zone.x + dest_zone.width - 2, dest_zone.y + 1),
        ]
        open_cells = []

        for cell in preferred_cells:
            if dest_zone.contains(*cell) and not grid.is_blocked(*cell):
                open_cells.append(cell)

        if len(open_cells) < 2:
            for cell in dest_zone.all_cells():
                if cell not in open_cells and not grid.is_blocked(*cell):
                    open_cells.append(cell)
                if len(open_cells) >= 2:
                    break

        if len(open_cells) < 2:
            raise RuntimeError("Not enough open cells inside the objective zone for both entities.")

        return open_cells[:2]

    objective_cells = build_objective_cells()

    # NEW — Create entities with randomized metrics
    for i in range(2):
        # Spawn inside the start zone
        sx, sy = start_zone.random_point()

        # Make sure we don't spawn on a wall
        while grid.is_blocked(sx, sy):
            sx, sy = start_zone.random_point()

        m = Movable((0, 0, 255), sx, sy)

        # Attach randomized metrics to the entity
        m.metrics = random_entity_metrics()
        m.metrics.destination_zone = dest_zone
        m.metrics.objective_cells = objective_cells

        movables.append(m)
        grid.add_entity(m)

    # Procedurally generate walls using Perlin noise
    entity_positions = [(m.x_pos, m.y_pos) for m in movables]
    generate_walls(grid, start_zone, dest_zone, entity_positions)

    # Add advanced terrain on top of the perlin wall layout
    grid.rand_gen_water()
    grid.rand_gen_barriers()
    grid.rand_gen_forest()

    # Generate fire after movables are placed so fire can spawn away from entities
    grid.rand_gen_fire(
        movables,
        cluster_count=2,
        min_cluster_distance=8,
        min_entity_distance=7
    )
    initial_fire_positions = list(grid.fire_tiles)

    move_delay = 150
    last_move_time = 0
    fire_delay = 400
    last_fire_time = 0

    def reset_everything():
        nonlocal paused, phase, last_move_time, last_fire_time
        paused = False
        phase = PHASE_PLANNING
        last_move_time = 0
        last_fire_time = 0
        stats.reset()

        for m in movables:
            m.reset_to_start(grid)
            # NEW — Re-randomize metrics on reset
            m.metrics = random_entity_metrics()
            m.metrics.destination_zone = dest_zone
            m.metrics.objective_cells = objective_cells

        # Reset fire to the original fire layout
        grid.fire_tiles.clear()
        for x, y in initial_fire_positions:
            grid.add_fire(x, y)

    def start_simulation():
        nonlocal paused, phase, last_move_time, last_fire_time
        paused = False
        phase = PHASE_MOVING
        last_move_time = pygame.time.get_ticks()
        last_fire_time = pygame.time.get_ticks()
        stats.reset()

        # Restore initial fire before starting the run
        grid.fire_tiles.clear()
        for x, y in initial_fire_positions:
            grid.add_fire(x, y)

        for m in movables:
            m.start_movement()

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            # Zoom with scroll wheel
            if event.type == pygame.MOUSEWHEEL:
                old_zoom = cam_zoom
                cam_zoom += event.y * ZOOM_STEP
                cam_zoom = max(ZOOM_MIN, min(ZOOM_MAX, cam_zoom))
                # Zoom toward mouse pointer
                mx, my = pygame.mouse.get_pos()
                cam_x = mx - (mx - cam_x) * (cam_zoom / old_zoom)
                cam_y = my - (my - cam_y) * (cam_zoom / old_zoom)

            # Pan with right mouse button
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                panning = True
                pan_start = event.pos
                cam_start = (cam_x, cam_y)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                panning = False
            if event.type == pygame.MOUSEMOTION and panning:
                dx_px = event.pos[0] - pan_start[0]
                dy_px = event.pos[1] - pan_start[1]
                cam_x = cam_start[0] + dx_px
                cam_y = cam_start[1] + dy_px

            # Handle window resize
            if event.type == pygame.VIDEORESIZE:
                window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_r:
                    reset_everything()
                if event.key == pygame.K_RETURN:
                    if phase in (PHASE_PLANNING, PHASE_FINISHED):
                        start_simulation()

                if phase == PHASE_PLANNING and not paused:
                    if event.key == pygame.K_BACKSPACE:
                        for m in movables:
                            if m.selected:
                                m.undo_last_step()
                    if event.key == pygame.K_c:
                        for m in movables:
                            if m.selected:
                                m.clear_plan()

                    dx, dy = 0, 0
                    if event.key == pygame.K_UP:
                        dy = -1
                    elif event.key == pygame.K_DOWN:
                        dy = 1
                    elif event.key == pygame.K_LEFT:
                        dx = -1
                    elif event.key == pygame.K_RIGHT:
                        dx = 1

                    if dx != 0 or dy != 0:
                        for m in movables:
                            if m.selected:
                                m.plan_step(dx, dy, grid)

            # Left click — transform screen coords to world coords
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if phase == PHASE_PLANNING and not paused:
                    wx, wy = screen_to_world(*event.pos)
                    world_pos = (int(wx), int(wy))
                    for m in movables:
                        m.handle_click(world_pos)

        # Movement phase with fuel tracking
        if phase == PHASE_MOVING and not paused:
            curr_time = pygame.time.get_ticks()

            if curr_time - last_move_time >= move_delay:
                for m in movables:
                    # NEW — Check fuel before moving
                    if hasattr(m, "metrics") and m.metrics is not None:
                        if m.metrics.is_out_of_fuel:
                            stats.record_step(m, False)
                            m.apply_fire_damage(grid)
                            continue

                    # Apply thermal damage after movement so fire affects entity survival
                    moved = m.advance_one_step(grid)
                    m.apply_fire_damage(grid)
                    stats.record_step(m, moved)

                    # NEW — Burn fuel and track metrics
                    if moved and hasattr(m, "metrics") and m.metrics is not None:
                        m.metrics.burn_fuel_for_step()
                        m.metrics.check_in_zone(m.x_pos, m.y_pos)

                        # NEW — Check proximity to other entities
                        for other in movables:
                            if other is not m:
                                if m.metrics.check_proximity(m.x_pos, m.y_pos, other.x_pos, other.y_pos):
                                    if id(other) not in [id(e) for e in m.metrics.detected_entities]:
                                        m.metrics.detected_entities.append(other)

                last_move_time = curr_time

                if all(m.is_done() or (hasattr(m, "metrics") and m.metrics.is_out_of_fuel) for m in movables):
                    stats.finalize()
                    phase = PHASE_FINISHED
                    paused = True

            # Spread fire at a slower interval than movement
            if curr_time - last_fire_time >= fire_delay:
                grid.spread_fire()
                last_fire_time = curr_time

        # ── Rendering ──

        # 1) Draw the world onto the off-screen surface
        world_surface.fill(BG_COLOR)

        for zone in (start_zone, dest_zone):
            zone.draw(world_surface)

        label = font.render(start_zone.name, True, (200, 200, 220))
        world_surface.blit(label, (start_zone.x * CELL_SIZE + 2, start_zone.y * CELL_SIZE - 18))

        for (ox, oy) in objective_cells:
            block_rect = pygame.Rect(ox * CELL_SIZE, oy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            inset_rect = block_rect.inflate(-6, -6)
            pygame.draw.rect(world_surface, (210, 210, 80), inset_rect, border_radius=3)
            pygame.draw.rect(world_surface, (240, 240, 240), inset_rect, 2, border_radius=3)

        grid.draw(world_surface)

        if phase == PHASE_MOVING:
            for m in movables:
                if hasattr(m, "metrics") and m.metrics is not None:
                    px = m.x_pos * CELL_SIZE + CELL_SIZE // 2
                    py = m.y_pos * CELL_SIZE + CELL_SIZE // 2
                    radius_px = m.metrics.proximity_radius * CELL_SIZE
                    prox_surf = pygame.Surface((radius_px * 2, radius_px * 2), pygame.SRCALPHA)
                    pygame.draw.circle(prox_surf, (100, 180, 255, 30), (radius_px, radius_px), radius_px)
                    pygame.draw.circle(prox_surf, (100, 180, 255, 80), (radius_px, radius_px), radius_px, 1)
                    world_surface.blit(prox_surf, (px - radius_px, py - radius_px))

        # 2) Scale the world surface and blit onto the window
        win_w, win_h = window.get_size()
        window.fill((30, 30, 30))

        scaled_w = int(WORLD_WIDTH * cam_zoom)
        scaled_h = int(WORLD_HEIGHT * cam_zoom)
        scaled_surface = pygame.transform.smoothscale(world_surface, (scaled_w, scaled_h))
        window.blit(scaled_surface, (int(cam_x), int(cam_y)))

        # 3) HUD — drawn directly on the window (not affected by zoom/pan)
        if phase == PHASE_PLANNING:
            lines = [
                "PHASE: PLANNING",
                "Click a blue square to select it.",
                "Arrow keys: plan path   Backspace: undo   C: clear",
                "Enter: start   Space: pause   R: reset",
                "Scroll: zoom   Right click: pan",
            ]

            for m in movables:
                if m.selected and hasattr(m, "metrics") and m.metrics is not None:
                    mt = m.metrics
                    lines.append("")
                    lines.append(
                        f"Speed: {mt.speed_tier.upper()}  |  Fuel: {mt.fuel:.0f}/{mt.max_fuel:.0f}  |  Proximity: {mt.proximity_radius} cells"
                    )
                    planned_len = len(m.planned_cells)
                    tier = mt.get_speed_tier()
                    est_cost = tier.fuel_per_step * planned_len
                    lines.append(f"Planned steps: {planned_len}  |  Est. fuel cost: {est_cost:.1f}")

            _render_lines(window, font, lines, x=10, y=10)

        elif phase == PHASE_MOVING:
            lines = [
                "PHASE: MOVEMENT",
                "Space: pause   R: reset",
            ]

            for i, m in enumerate(movables):
                if hasattr(m, "metrics") and m.metrics is not None:
                    mt = m.metrics
                    objective_status = "reached" if mt.reached_destination else "en route"
                    lines.append(
                        f"Entity {i+1}: fuel {mt.fuel:.0f}/{mt.max_fuel:.0f} | cost {mt.total_movement_cost:.1f} | objective {objective_status}"
                    )
                    lines.append(f"health {m.health:.1f} | fire dmg {m.fire_damage_taken:.1f} | in fire {m.time_in_fire}")

            _render_lines(window, font, lines, x=10, y=10)

        elif phase == PHASE_FINISHED:
            stats.draw(window, font)

        if paused and phase != PHASE_FINISHED:
            _render_lines(window, font, ["PAUSED"], x=10, y=110, color=(255, 80, 80))

        pygame.display.flip()
        clock.tick(FPS)
