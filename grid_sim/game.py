import pygame
from .config import *
from .grid import Grid
from .entities import Movable


def game():
    pygame.init()
    
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Test Sim")

    clock = pygame.time.Clock()
    running = True

    #Create grid
    #randomly generate 20 wall entities
    grid = Grid()
    grid.rand_gen_walls(100)

    #Font
    font = pygame.font.Font(None, 26)
    paused=False

    #Two movable entities
    movables = [
        Movable((0, 0, 255), 15, 15),  # Red
        Movable((0, 0, 255), 10, 10),  # Blue
    ]
    for m in movables:
        grid.add_entity(m)


    #Movement constraints
    move_delay = 50  #milliseconds between moves
    last_move_time = 0

    while running:

        
        #Event handling
        #
        for event in pygame.event.get():

            #If user presses x on window, quit
            if event.type == pygame.QUIT:
                running = False

            #Pause the simulation
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused

            #select the movable you want to move
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    #Deselect all, then select the clicked one
                    if not paused:
                        for m in movables:
                            m.handle_click(event.pos)

            
            


        if not paused:

            #Temporary movement using arrow keys
            #This could be deleted once charting a path is implemented
            curr_time = pygame.time.get_ticks()
            if curr_time - last_move_time > move_delay:
                keys = pygame.key.get_pressed()
                for m in movables:
                    if m.selected:
                        dx = 0
                        dy = 0
                        if keys[pygame.K_UP]:
                            dy -= 1
                        if keys[pygame.K_DOWN]:
                            dy += 1
                        if keys[pygame.K_LEFT]:
                            dx -= 1
                        if keys[pygame.K_RIGHT]:
                            dx += 1
                        
                        if dx != 0 or dy != 0:
                            m.move(dx, dy, grid)
                            last_move_time = curr_time

             


             

        window.fill(BG_COLOR) 
        grid.draw(window)
        
        if paused:
            text = font.render("paused (press Space to unpause)", True, (255,0,0))
            window.blit(text, (10,10))

        #pygame.draw draws to a back buffer, and pygame.display.flip() renders 
        #drawings on screen
        pygame.display.flip()
        
        #60 FPS (in config)
        #For every second, at most 60 frames should pass
        #Note: 1 loop = 1 frame
        clock.tick(FPS)
    
    



