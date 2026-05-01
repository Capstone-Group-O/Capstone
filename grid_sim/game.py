# game.py
import pygame

from .config import APP_WINDOW_HEIGHT, APP_WINDOW_WIDTH, FPS
from .input_handler import InputHandler
from .renderer import SimulationRenderer
from .simulation import SimulationManager


def game(simulation=None, return_action="launcher"):
    pygame.init()

    window = pygame.display.set_mode((APP_WINDOW_WIDTH, APP_WINDOW_HEIGHT))
    pygame.display.set_caption("Test Sim")

    clock = pygame.time.Clock()
    if simulation is None:
        simulation = SimulationManager()
    simulation.back_target = return_action
    input_handler = InputHandler(simulation)
    renderer = SimulationRenderer(window)

    result = {"action": return_action}

    while simulation.running:
        input_handler.handle_events(pygame.event.get())
        simulation.update(pygame.time.get_ticks())
        renderer.render(simulation)
        pygame.display.flip()
        clock.tick(FPS)

    if simulation.requested_action is not None:
        if simulation.requested_action == "editor":
            result = {
                "action": "editor",
                "map_data": getattr(simulation, "editor_map_data", None),
            }
        else:
            result = {"action": simulation.requested_action}

    pygame.quit()
    return result