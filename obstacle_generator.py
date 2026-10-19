import random

from tile_type import TileType  

#Seeds allow for reproducibility
class ObstacleGenerator:  #No Reachability cheack (Some mazes will be unsolvable)
    def __init__(self, density, seed=None):  #Seeds allow for reproducibility
        if density < 0 or density > 1:  
            raise ValueError("density must be between 0 and 1")  
        self.density = density  
        self._rng = random.Random(seed)  

    def generate(self, tile_map):
        tiles = []
        for grid_row in tile_map.grid:
            for tile in grid_row:
                tiles.append(tile)

        for tile in tiles:   #reset every tile, including old start/goal
            tile_map.set_tile_type(tile.col, tile.row, TileType.TRAVERSABLE)

        if len(tiles) < 2:  #not enough tiles for a Start and a Goal
            return  

        start_tile, goal_tile = self._rng.sample(tiles, 2)  
        tile_map.set_tile_type(start_tile.col, start_tile.row, TileType.START)  
        tile_map.set_tile_type(goal_tile.col, goal_tile.row, TileType.GOAL)  

        candidates = []  
        for tile in tiles:  
            if tile.tile_type == TileType.TRAVERSABLE:  
                candidates.append(tile)  

        count = int(len(candidates) * self.density)
        for tile in self._rng.sample(candidates, count):
            tile_map.set_tile_type(tile.col, tile.row, TileType.OBSTACLE)