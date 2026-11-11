import math

import numpy as np
import pygame

from environment.tile import Tile
from environment.tile_type import TileType  
from search.algorithms import SearchStatus
from visualization.step_colors import (AGENT_COLOR, FRONTIER_COLOR, PATH_COLOR, SEARCHED_BLEND, SEARCHED_GREY,
                                       tile_color)

PADDING = 20  
MAX_TILE_SIZE = 80   #lets the grid grow when the window is enlarged
MIN_RECT_TILE = 5    #smaller tiles are drawn as an image instead of one rectangle each
MAX_RECT_TILES = 4000   #more tiles than this are drawn as an image too, to keep frames fast


class TileMap:
    def __init__(self, x, y, tile_size=40):
        self.x = x
        self.y = y
        self.tile_size = tile_size
        self.grid = []
        self.start_tile = None  
        self.goal_tile = None  
        self._version = 0   #bumped on every tile change, invalidates the cached image
        self._base = None
        self._base_version = -1
        self._image = None
        self._image_key = None
        self.generate()
        self.area = None  

    def generate(self):
        self._version += 1
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
        self._version += 1
        return True  

    def set_area(self, area):  
        self.area = area  
        self._fit()  

    def resize(self, x, y):  
        self.x = x  
        self.y = y  
        self._fit()  
        self.generate()  

    def _fit(self): #shrinks tiles so the grid fits inside the area; below 1 pixel per tile the size is fractional
        if self.area is None or self.x == 0 or self.y == 0:
            return
        fit_width = (self.area.width - 2 * PADDING) / self.x
        fit_height = (self.area.height - 2 * PADDING) / self.y
        size = min(fit_width, fit_height, MAX_TILE_SIZE)
        if size >= 1:
            size = int(size)   #whole pixels keep tile edges crisp
        self.tile_size = max(size, 0.01)

    def _map_size(self):
        return max(1, int(self.x * self.tile_size)), max(1, int(self.y * self.tile_size))

    def get_rect(self, surface):  #screen rect covered by the grid
        start_x, start_y = self.get_origin(surface)
        return pygame.Rect(start_x, start_y, *self._map_size())

    def get_origin(self, surface):
        area = self.area
        if area is None:
            area = surface.get_rect()
        map_width, map_height = self._map_size()
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
        col = math.floor((event.pos[0] - start_x) / self.tile_size)
        row = math.floor((event.pos[1] - start_y) / self.tile_size)
        return self.set_tile_type(col, row, selected_type)

    def draw(self, surface, step=None):   #step is the agent's current SearchStep, or None when idle
        if self.tile_size < MIN_RECT_TILE or self.x * self.y > MAX_RECT_TILES:
            self._draw_image(surface, step)
            return
        start_x, start_y = self.get_origin(surface)

        for grid_row in self.grid:
            for tile in grid_row:
                rect = pygame.Rect(
                    start_x + tile.col * self.tile_size,
                    start_y + tile.row * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                pygame.draw.rect(surface, tile_color(tile, step), rect)
                pygame.draw.rect(surface, (120, 120, 120), rect, 1)  
                if step is not None and tile is step.current and step.status == SearchStatus.FOUND:
                    pygame.draw.rect(surface, AGENT_COLOR, rect, 3)   #agent standing on the Goal

    # Large boards: one pixel per tile in an image, scaled to fit. Per-tile rectangles would be
    # a million draw calls per frame at 1000 x 1000. Colors follow visualization.step_colors.tile_color.

    def _base_colors(self):  #(x, y, 3) array of tile colors, rebuilt only when tiles change
        if self._base is None or self._base_version != self._version:
            colors = np.empty((self.x, self.y, 3), dtype=np.uint8)
            for grid_row in self.grid:
                for tile in grid_row:
                    colors[tile.col, tile.row] = tile.color
            self._base = colors
            self._base_version = self._version
        return self._base

    def _draw_image(self, surface, step):
        size = self._map_size()
        key = (self._version, id(step), size)
        if self._image_key != key:
            colors = self._base_colors().copy()
            if step is not None:
                base = self._base
                keep = {self.start_tile, self.goal_tile}

                def coords(tiles):
                    tiles = [t for t in tiles]
                    return (np.fromiter((t.col for t in tiles), dtype=np.intp, count=len(tiles)),
                            np.fromiter((t.row for t in tiles), dtype=np.intp, count=len(tiles)))

                cols, rows = coords(t for t in step.frontier_set if t not in keep)
                colors[cols, rows] = FRONTIER_COLOR
                cols, rows = coords(step.visited)
                colors[cols, rows] = (base[cols, rows] * (1 - SEARCHED_BLEND) +
                                      np.array(SEARCHED_GREY) * SEARCHED_BLEND).astype(np.uint8)
                colors[step.current.col, step.current.row] = AGENT_COLOR
                if step.status == SearchStatus.FOUND:
                    cols, rows = coords(t for t in step.path_set if t not in keep)
                    colors[cols, rows] = PATH_COLOR
                    for tile in keep:
                        if tile is not None and tile in step.path_set:
                            colors[tile.col, tile.row] = base[tile.col, tile.row]
            image = pygame.surfarray.make_surface(colors)
            self._image = pygame.transform.scale(image, size)
            self._image_key = key
        start_x, start_y = self.get_origin(surface)
        surface.blit(self._image, (start_x, start_y))
        pygame.draw.rect(surface, (120, 120, 120), (start_x - 1, start_y - 1, size[0] + 2, size[1] + 2), 1)
        if step is not None and step.status == SearchStatus.FOUND:   #ring around the agent on the Goal
            ring = max(6, int(self.tile_size * 2))
            center = (start_x + int((step.current.col + 0.5) * self.tile_size),
                      start_y + int((step.current.row + 0.5) * self.tile_size))
            pygame.draw.rect(surface, AGENT_COLOR, pygame.Rect(0, 0, ring, ring).move(center[0] - ring // 2,
                                                                                    center[1] - ring // 2), 2)

    def apply_types(self, tile_types):
        index = 0  
        for grid_row in self.grid:  
            for tile in grid_row:  
                self.set_tile_type(tile.col, tile.row, tile_types[index])  
                index += 1  