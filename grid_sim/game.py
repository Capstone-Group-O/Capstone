import pygame
from .config import *
from .grid import Grid
from .entities import Movable, Fire

# Constants to make life slightly easier
PHASE_PLANNING = "PLANNING"
PHASE_MOVING = "MOVING"
PHASE_FINISHED = "FINISHED"

def _render_lines(window, font, lines, x=10, y=10, color=(255, 255, 255), line_gap=2):
    yy = y
    for line in lines:
        surf = font.render(line, True, color)
        window.blit(surf, (x, yy))
        yy += surf.get_height() + line_gap
def game():
    pygame.init()
    
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Test Sim")

    clock = pygame.time.Clock()
    running = True
    movables = [
        Movable((0, 0, 255), 15, 15),  # Red
        Movable((0, 0, 255), 10, 10),  # Blue
    ]
    
    #Create grid
    #randomly generate 20 wall entities
    grid = Grid()
    grid.rand_gen_walls(100)
    grid.rand_gen_fire(movables, cluster_count=2,
        min_cluster_distance=8,
        min_entity_distance=7
    )
    initial_fire_positions = [
        (x, y) for (x, y), entity in grid.entities.items()
        if isinstance(entity, Fire)
    ]

    #Font
    font = pygame.font.Font(None, 26)

    paused = False
    phase = PHASE_PLANNING

    #Two movable entities
    
    for m in movables:
        grid.add_entity(m)


    #Movement constraints
    move_delay = 150  #milliseconds between moves
    last_move_time = 0
    fire_delay = 400
    last_fire_time = 0

    def reset_everything():
        nonlocal paused, phase, last_move_time
        paused = False
        phase = PHASE_PLANNING
        last_move_time = 0
        for m in movables:
            m.reset_to_start(grid)

        # Remove all fire tiles
        for pos, entity in list(grid.entities.items()):
            if isinstance(entity, Fire):
                del grid.entities[pos]
        # Restore original fire cluster
        for x, y in initial_fire_positions:
            grid.add_entity(Fire(x, y))

    def start_simulation():
        nonlocal paused, phase, last_move_time
        paused = False
        phase = PHASE_MOVING
        last_move_time = pygame.time.get_ticks()
        # Reset fire to original cluster
        for pos, entity in list(grid.entities.items()):
            if isinstance(entity, Fire):
                del grid.entities[pos]
        for x, y in initial_fire_positions:
            grid.add_entity(Fire(x, y))
        for m in movables:
            m.start_movement()

    while running:

        
        # Event handling
        for event in pygame.event.get():

            # Close window (X button)
            if event.type == pygame.QUIT:
                running = False
                continue

            # Simulation keyboard controls
            if event.type == pygame.KEYDOWN:
                # Pause and unpause (works in any phase)
                if event.key == pygame.K_SPACE:
                    paused = not paused

                # Reset (also works in any phase)
                if event.key == pygame.K_r:
                    reset_everything()

                # Start movement (only works from planning and finished)
                if event.key == pygame.K_RETURN:
                    if phase in (PHASE_PLANNING, PHASE_FINISHED):
                        start_simulation()

                # Planning controls
                if phase == PHASE_PLANNING and not paused:
                    if event.key == pygame.K_BACKSPACE:
                        for m in movables:
                            if m.selected:
                                m.undo_last_step()

                    if event.key == pygame.K_c:
                        for m in movables:
                            if m.selected:
                                m.clear_plan()

                    dx = 0
                    dy = 0
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

            # Select a movable in planning phase (point and click)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if phase == PHASE_PLANNING and not paused:
                    for m in movables:
                        m.handle_click(event.pos)

        if phase == PHASE_MOVING and not paused:
            curr_time = pygame.time.get_ticks()
            if curr_time - last_move_time >= move_delay:
                for m in movables:
                    m.advance_one_step(grid)

                last_move_time = curr_time

                # Stop when all entities have reached their endpoints
                if all(m.is_done() for m in movables):
                    phase = PHASE_FINISHED
                    paused = True

            if curr_time - last_fire_time >= fire_delay:
                for entity in list(grid.entities.values()):
                    if isinstance(entity, Fire):
                        entity.spread(grid)

                last_fire_time = curr_time

            #Temporary movement using arrow keys
            #This could be deleted once charting a path is implemented
            # Keeping this in case we need this for any reason
            # curr_time = pygame.time.get_ticks()
            # if curr_time - last_move_time > move_delay:
            #     keys = pygame.key.get_pressed()
            #     for m in movables:
            #         if m.selected:
            #             dx = 0
            #             dy = 0
            #             if keys[pygame.K_UP]:
            #                 dy -= 1
            #             if keys[pygame.K_DOWN]:
            #                 dy += 1
            #             if keys[pygame.K_LEFT]:
            #                 dx -= 1
            #             if keys[pygame.K_RIGHT]:
            #                 dx += 1
            #
            #             if dx != 0 or dy != 0:
            #                 m.move(dx, dy, grid)
            #                 last_move_time = curr_time

        window.fill(BG_COLOR) 
        grid.draw(window)
        
        # if paused:
        #     text = font.render("paused (press Space to unpause)", True, (255,0,0))
        #     window.blit(text, (10,10))

        # UI / instructions
        if phase == PHASE_PLANNING:
            lines = [
                "PHASE: PLANNING",
                "Click a blue square to select it (white outline).",
                "Arrow keys: add steps to its planned path (yellow dots).",
                "Backspace: undo last step   C: clear plan",
                "Enter: start simulation   Space: pause/unpause   R: reset",
            ]
            _render_lines(window, font, lines, x=10, y=10)

        elif phase == PHASE_MOVING:
            lines = [
                "PHASE: MOVEMENT",
                "Entities are following their planned paths.",
                "Space: pause/unpause   R: reset",
            ]
            _render_lines(window, font, lines, x=10, y=10)

        elif phase == PHASE_FINISHED:
            lines = [
                "PHASE: FINISHED",
                "All entities reached their endpoints.",
                "Enter: run again   R: reset (and re-plan)",
            ]
            _render_lines(window, font, lines, x=10, y=10)

        if paused and phase != PHASE_FINISHED:
            _render_lines(window, font, ["PAUSED"], x=10, y=110, color=(255, 80, 80))

        #pygame.draw draws to a back buffer, and pygame.display.flip() renders 
        #drawings on screen
        pygame.display.flip()
        
        #60 FPS (in config)
        #For every second, at most 60 frames should pass
        #Note: 1 loop = 1 frame
        clock.tick(FPS)
    
    



