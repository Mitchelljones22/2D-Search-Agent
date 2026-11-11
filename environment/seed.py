"""Seeds: a whole map, board size included, packed into one whole number.

Layout, from the lowest bits up:
    bits 0-4    rows    (5 bits, up to 31)
    bits 5-9    columns (5 bits, up to 31)
    bits 10+    tiles, 2 bits each, top-left tile in the highest bits
The size sits in the low bits so it can be read first; it then says how many tiles follow.
"""
import random

from environment.tile_type import TileType

BITS_PER_TILE = 2  
SIZE_BITS = 5   #enough for sizes up to 31 per side
SIZE_MASK = (1 << SIZE_BITS) - 1
HEADER_BITS = 2 * SIZE_BITS   #columns + rows
_TILE_TYPES = {tile_type.value: tile_type for tile_type in TileType}  


def random_seed():
    return random.randint(0, 9999999)


def max_seed_digits(cols, rows):  
    cells = cols * rows  
    return len(str((1 << (BITS_PER_TILE * cells + HEADER_BITS)) - 1))


def encode(tile_map):  
    value = 0  
    for grid_row in tile_map.grid:  
        for tile in grid_row:  
            value = (value << BITS_PER_TILE) | tile.tile_type.value  
    value = (value << SIZE_BITS) | tile_map.x
    value = (value << SIZE_BITS) | tile_map.y
    return value  


def decode(seed, min_size, max_size):   #returns (cols, rows, list of TileTypes), or None if invalid
    if seed is None or seed < 0:
        return None
    rows = seed & SIZE_MASK
    cols = (seed >> SIZE_BITS) & SIZE_MASK
    if not (min_size <= cols <= max_size and min_size <= rows <= max_size):
        return None

    tiles = seed >> HEADER_BITS
    cells = cols * rows  
    if tiles >= 1 << (BITS_PER_TILE * cells):   #more tiles than the board holds
        return None

    tile_types = []  
    for index in range(cells):  
        shift = BITS_PER_TILE * (cells - 1 - index)  
        tile_types.append(_TILE_TYPES[(tiles >> shift) & 0b11])  

    if tile_types.count(TileType.START) > 1:  
        return None  
    if tile_types.count(TileType.GOAL) > 1:  
        return None  
    return cols, rows, tile_types
