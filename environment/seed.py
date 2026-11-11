"""Seeds: a whole map, board size included, packed into one whole number.

Layout, from the lowest bits up:
    bits 0-9    rows    (10 bits, up to 1023)
    bits 10-19  columns (10 bits, up to 1023)
    bits 20+    tiles, 2 bits each, top-left tile in the highest bits
The size sits in the low bits so it can be read first; it then says how many tiles follow.

The tiles are packed 4 per byte and converted with int.from_bytes / int.to_bytes, which is
linear in the board size. (Shifting a growing integer once per tile is quadratic: a
1000 x 1000 board took about 18 seconds that way.)
"""
import math
import random
import sys

from environment.tile_type import TileType

BITS_PER_TILE = 2
TILES_PER_BYTE = 8 // BITS_PER_TILE
SIZE_BITS = 10   #enough for sizes up to 1023 per side
SIZE_MASK = (1 << SIZE_BITS) - 1
HEADER_BITS = 2 * SIZE_BITS   #columns + rows
_TILE_TYPES = {tile_type.value: tile_type for tile_type in TileType}
_BY_VALUE = [_TILE_TYPES[value] for value in range(4)]

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)   #a 1000 x 1000 seed has about 600,000 digits; Python refuses over 4,300 by default


def random_seed():
    return random.randint(0, 9999999)


def max_seed_digits(cols, rows):  #digits in the largest possible seed, worked out without building it
    bits = BITS_PER_TILE * cols * rows + HEADER_BITS
    return math.floor(bits * math.log10(2)) + 1


def encode(tile_map):
    cells = tile_map.x * tile_map.y
    pad = (-cells) % TILES_PER_BYTE   #leading zero tiles so the last byte ends on the last tile
    packed = bytearray((cells + pad) // TILES_PER_BYTE)
    index = pad
    for grid_row in tile_map.grid:
        for tile in grid_row:
            packed[index // TILES_PER_BYTE] |= tile.tile_type.value << (6 - BITS_PER_TILE * (index % TILES_PER_BYTE))
            index += 1
    tiles = int.from_bytes(packed, "big")
    return (((tiles << SIZE_BITS) | tile_map.x) << SIZE_BITS) | tile_map.y


def decode(seed, min_size, max_size):   #returns (cols, rows, list of TileTypes), or None if invalid
    if seed is None or seed < 0:
        return None
    rows = seed & SIZE_MASK
    cols = (seed >> SIZE_BITS) & SIZE_MASK
    if not (min_size <= cols <= max_size and min_size <= rows <= max_size):
        return None

    tiles = seed >> HEADER_BITS
    cells = cols * rows
    if tiles.bit_length() > BITS_PER_TILE * cells:   #more tiles than the board holds
        return None

    pad = (-cells) % TILES_PER_BYTE
    packed = tiles.to_bytes((cells + pad) // TILES_PER_BYTE, "big")
    tile_types = []
    for index in range(pad, cells + pad):
        value = (packed[index // TILES_PER_BYTE] >> (6 - BITS_PER_TILE * (index % TILES_PER_BYTE))) & 0b11
        tile_types.append(_BY_VALUE[value])

    if tile_types.count(TileType.START) > 1:
        return None
    if tile_types.count(TileType.GOAL) > 1:
        return None
    return cols, rows, tile_types
