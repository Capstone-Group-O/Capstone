import pygame

from .config import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from .input_handler import InputHandler
from .renderer import SimulationRenderer
from .simulation import SimulationManager


def game(simulation=None):
    pygame.init()

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Test Sim")

    clock = pygame.time.Clock()
    if simulation is None:
        simulation = SimulationManager()
    input_handler = InputHandler(simulation)
    renderer = SimulationRenderer(window)

    while simulation.running:
        input_handler.handle_events(pygame.event.get())
        simulation.update(pygame.time.get_ticks())
        renderer.render(simulation)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
