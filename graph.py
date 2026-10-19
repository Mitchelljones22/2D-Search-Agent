from tile_type import TileType

# North, South, East, West as (col offset, row offset)
DIRECTIONS = [(0, -1), (0, 1), (1, 0), (-1, 0)]  


class Graph:  
    def __init__(self):  
        self.adjacency = {}  

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

    def neighbors(self, tile):  
        return self.adjacency.get(tile, [])  

    def node_count(self):  
        return len(self.adjacency)  

    def edge_count(self):  
        total = 0  
        for neighbors in self.adjacency.values():  
            total += len(neighbors)  
        return total // 2  