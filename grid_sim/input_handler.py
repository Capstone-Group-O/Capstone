import pygame

from .phases import PHASE_FINISHED, PHASE_PLANNING


class InputHandler:
    def __init__(self, simulation):
        self.simulation = simulation

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.simulation.stop()
                continue

            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_left_click(event.pos)

    def _handle_keydown(self, key):
        if key == pygame.K_SPACE:
            self.simulation.toggle_pause()
            return

        if key == pygame.K_r:
            self.simulation.reset()
            return

        if key == pygame.K_RETURN:
            if self.simulation.phase in (PHASE_PLANNING, PHASE_FINISHED):
                self.simulation.start()
            return

        if self.simulation.phase != PHASE_PLANNING or self.simulation.paused:
            return

        if key == pygame.K_BACKSPACE:
            self.simulation.undo_selected_plan_step()
            return

        if key == pygame.K_c:
            self.simulation.clear_selected_plan()
            return

        movement = {
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
        }.get(key)

        if movement is not None:
            dx, dy = movement
            self.simulation.plan_selected_step(dx, dy)

    def _handle_left_click(self, mouse_pos):
        if self.simulation.phase == PHASE_PLANNING and not self.simulation.paused:
            self.simulation.handle_click(mouse_pos)
            