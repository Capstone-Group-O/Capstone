import pygame
from .config import *
import random
from .entities import Wall

class Grid:
    def __init__(self):
        self.entities = {}  #{(x, y): entity}

        #self.entities = []
        #self.occupied = set()

    def add_entity(self, entity):
        self.entities[(entity.x_pos, entity.y_pos)] = entity

    def is_blocked(self, x, y):
        entity = self.entities.get((x, y))
        return entity is not None and entity.blocking
    
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
