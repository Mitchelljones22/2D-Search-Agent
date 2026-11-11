import math

from environment.tile_type import TileType

# North, South, East, West as (col offset, row offset)
DIRECTIONS = [(0, -1), (0, 1), (1, 0), (-1, 0)]  
# North-East, South-East, South-West, North-West, only used when diagonal movement is on
DIAGONALS = [(1, -1), (1, 1), (-1, 1), (-1, -1)]
STRAIGHT_COST = 1
DIAGONAL_COST = math.sqrt(2)   #a diagonal step covers sqrt(1^2 + 1^2) of distance


class Graph:  
    def __init__(self, diagonal=False):  
        self.adjacency = {}  
        self.diagonal = diagonal   #True allows the 4 diagonal moves as well as N, S, E, W

    def build(self, tile_map):  
        self.adjacency = {}  
        for grid_row in tile_map.grid:  
            for tile in grid_row:  
                if tile.tile_type != TileType.OBSTACLE:  
                    self.adjacency[tile] = []  

        for tile in self.adjacency:  
            for d_col, d_row in DIRECTIONS:  
                neighbor = tile_map.get_tile(tile.col + d_col, tile.row + d_row)  
                if neighbor is not None and neighbor in self.adjacency:  
                    self.adjacency[tile].append(neighbor)  
            if not self.diagonal:
                continue
            for d_col, d_row in DIAGONALS:
                neighbor = tile_map.get_tile(tile.col + d_col, tile.row + d_row)
                if neighbor is None or neighbor not in self.adjacency:
                    continue
                side_a = tile_map.get_tile(tile.col + d_col, tile.row)
                side_b = tile_map.get_tile(tile.col, tile.row + d_row)
                if side_a in self.adjacency and side_b in self.adjacency:   #no cutting across an obstacle's corner
                    self.adjacency[tile].append(neighbor)

    def neighbors(self, tile):  
        return self.adjacency.get(tile, [])  

    @staticmethod
    def cost(a, b):  #step cost between two adjacent tiles
        if a.col != b.col and a.row != b.row:
            return DIAGONAL_COST
        return STRAIGHT_COST

    def node_count(self):  
        return len(self.adjacency)  

    def edge_count(self):  
        total = 0  
        for neighbors in self.adjacency.values():  
            total += len(neighbors)  
        return total // 2  
