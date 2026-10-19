from tile_type import TileType, TILE_COLORS  


class Tile:
    def __init__(self, col, row, tile_type=TileType.TRAVERSABLE):  
        self.col = col
        self.row = row
        self.tile_type = tile_type  

    @property  
    def color(self):  
        return TILE_COLORS[self.tile_type]  