import pygame

from tile import Tile
from tile_type import TileType  

PADDING = 20  
MAX_TILE_SIZE = 40  


class TileMap:
    def __init__(self, x, y, tile_size=40):
        self.x = x
        self.y = y
        self.tile_size = tile_size
        self.grid = []
        self.start_tile = None  
        self.goal_tile = None  
        self.generate()
        self.area = None  

    def generate(self):
        self.grid = []
        self.start_tile = None  
        self.goal_tile = None  
        for row in range(self.y):
            grid_row = []
            for col in range(self.x):
                grid_row.append(Tile(col, row))  
            self.grid.append(grid_row)

    def get_tile(self, col, row):
        if 0 <= row < self.y and 0 <= col < self.x:
            return self.grid[row][col]
        return None

    def set_tile_type(self, col, row, tile_type):
        tile = self.get_tile(col, row)
        if tile is None:
            return False  

        if tile is self.start_tile:
            self.start_tile = None
        if tile is self.goal_tile:
            self.goal_tile = None

        if tile_type == TileType.START:
            if self.start_tile is not None:
                self.start_tile.tile_type = TileType.TRAVERSABLE
            self.start_tile = tile
        elif tile_type == TileType.GOAL:
            if self.goal_tile is not None:
                self.goal_tile.tile_type = TileType.TRAVERSABLE
            self.goal_tile = tile

        tile.tile_type = tile_type
        return True  

    def set_area(self, area):  
        self.area = area  
        self._fit()  

    def resize(self, x, y):  
        self.x = x  
        self.y = y  
        self._fit()  
        self.generate()  

    def _fit(self): #shrinks tiles so the grid fits inside the area
        if self.area is None or self.x == 0 or self.y == 0:  
            return  
        fit_width = (self.area.width - 2 * PADDING) // self.x  
        fit_height = (self.area.height - 2 * PADDING) // self.y  
        size = min(fit_width, fit_height, MAX_TILE_SIZE)  
        if size < 1:  
            size = 1  
        self.tile_size = size  

    def get_origin(self, surface):
        area = self.area  
        if area is None:  
            area = surface.get_rect()  
        map_width = self.x * self.tile_size
        map_height = self.y * self.tile_size
        start_x = area.x + (area.width - map_width) // 2  
        start_y = area.y + (area.height - map_height) // 2  
        return start_x, start_y

    # Handles clicking on tiles and updates them to the selected type
    def handle_event(self, event, surface, selected_type):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False  
        if selected_type is None:
            return False  
        start_x, start_y = self.get_origin(surface)
        col = (event.pos[0] - start_x) // self.tile_size
        row = (event.pos[1] - start_y) // self.tile_size
        return self.set_tile_type(col, row, selected_type)  

    def draw(self, surface):
        start_x, start_y = self.get_origin(surface)  

        for grid_row in self.grid:
            for tile in grid_row:
                rect = pygame.Rect(
                    start_x + tile.col * self.tile_size,
                    start_y + tile.row * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                pygame.draw.rect(surface, tile.color, rect)
                pygame.draw.rect(surface, (120, 120, 120), rect, 1)  

    def apply_types(self, tile_types):  
        index = 0  
        for grid_row in self.grid:  
            for tile in grid_row:  
                self.set_tile_type(tile.col, tile.row, tile_types[index])  
                index += 1  