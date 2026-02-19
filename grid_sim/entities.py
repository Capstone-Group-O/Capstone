import pygame
from .config import CELL_SIZE, GRID_WIDTH, GRID_HEIGHT


class Entity():
    def __init__(self, color, x_pos, y_pos, blocking=False):
        self.x_pos = x_pos
        self.y_pos = y_pos

        self.color = color

        #blocking=true means other entities can't occupy the same space
        self.blocking=blocking


    def draw(self, window):
        rect = pygame.Rect(
            self.x_pos * CELL_SIZE,
            self.y_pos * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )

        pygame.draw.rect(window, self.color, rect)



#Some entity examples:


#Walls can inhibit movement
class Wall(Entity):
    def __init__(self, x_pos, y_pos):
        wall_color = (128,128,128) #gray
        super().__init__(wall_color,x_pos, y_pos, blocking=True)


#Movable entity
class Movable(Entity):
    def __init__(self, color, x_pos, y_pos):
        super().__init__(color, x_pos, y_pos, blocking=True)
        self.selected = False



    def handle_click(self, mouse_pos):

        #Gets the position on the grid from mouse_pos (which is in pixels)
        grid_x = mouse_pos[0] // CELL_SIZE
        grid_y = mouse_pos[1] // CELL_SIZE
        self.selected = (grid_x == self.x_pos and grid_y == self.y_pos)

    def move(self, dx, dy, grid):
        new_x = self.x_pos + dx
        new_y = self.y_pos + dy
        
        if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
            if not grid.is_blocked(new_x, new_y):
                del grid.entities[(self.x_pos, self.y_pos)]
                self.x_pos = new_x
                self.y_pos = new_y
                grid.entities[(self.x_pos, self.y_pos)] = self

    def draw(self, window):
        super().draw(window)
        if self.selected:
            rect = pygame.Rect(
                self.x_pos * CELL_SIZE,
                self.y_pos * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(window, (255, 255, 255), rect, 3)









