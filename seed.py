import random

from tile_type import TileType

BITS_PER_TILE = 2  
_TILE_TYPES = {tile_type.value: tile_type for tile_type in TileType}  


def random_seed():
    return random.randint(0, 9999999)


def max_seed_digits(cols, rows):  
    cells = cols * rows  
    return len(str((1 << (BITS_PER_TILE * cells)) - 1))


def encode(tile_map):  
    value = 0  
    for grid_row in tile_map.grid:  
        for tile in grid_row:  
            value = (value << BITS_PER_TILE) | tile.tile_type.value  
    return value  


def decode(seed, cols, rows):   #returns a list of TileTypes, or None if invalid
    cells = cols * rows  
    if seed is None or seed < 0 or seed >= 1 << (BITS_PER_TILE * cells):
        return None

    tile_types = []  
    for index in range(cells):  
        shift = BITS_PER_TILE * (cells - 1 - index)  
        tile_types.append(_TILE_TYPES[(seed >> shift) & 0b11])  

    if tile_types.count(TileType.START) > 1:  
        return None  
    if tile_types.count(TileType.GOAL) > 1:  
        return None  
    return tile_types  