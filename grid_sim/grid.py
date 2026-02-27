import pygame
from .config import *
import random
from .entities import Wall

class Grid:
    def __init__(self):
        self.entities = {}  #{(x, y): entity}

    def add_entity(self, entity):
        self.entities[(entity.x_pos, entity.y_pos)] = entity

    def is_blocked(self, x, y):
        entity = self.entities.get((x, y))
        return entity is not None and entity.blocking

    def move_entity(self, entity, new_x, new_y, ignore_blocking=False):
        if not (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT):
            return False

        # Allowing for moving into own cell and enforcing blocking if not ignored
        if (
                not ignore_blocking
                and self.is_blocked(new_x, new_y)
                and (new_x, new_y) != (entity.x_pos, entity.y_pos)
        ):
            return False

        old_key = (entity.x_pos, entity.y_pos)
        if old_key in self.entities:
            del self.entities[old_key]

        entity.x_pos = new_x
        entity.y_pos = new_y
        self.entities[(new_x, new_y)] = entity
        return True

    def rand_gen_walls(self, count):
        placed = 0

        while placed < count:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)

            if (x,y) not in self.entities:
                self.add_entity(Wall(x,y))
                placed += 1


    def draw(self, window):

        #Draw the grid
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(window, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(window, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))

        #Draw entities
        for entity in self.entities.values():
            entity.draw(window)
