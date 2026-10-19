"""Colors for drawing a search in progress, shared by the grid and the tree view."""
from search.algorithms import SearchStatus
from environment.tile_type import TileType

AGENT_COLOR = (255, 220, 0)      #tile the search agent is currently on
FRONTIER_COLOR = (150, 205, 255)  #discovered, waiting to be expanded
PATH_COLOR = (220, 40, 40)        #final route from Start to Goal
SEARCHED_GREY = (128, 128, 128)
SEARCHED_BLEND = 0.5   #how far searched tiles are pulled toward grey

_KEEP_COLOR = (TileType.START, TileType.GOAL)   #endpoints stay recognizable on the frontier and path


def grey_out(color):
    return tuple(int(c + (g - c) * SEARCHED_BLEND) for c, g in zip(color, SEARCHED_GREY))


def tile_color(tile, step):  #step is a SearchStep, or None when no search is running
    if step is None:
        return tile.color
    if step.status == SearchStatus.FOUND and tile in step.path_set:
        if tile.tile_type in _KEEP_COLOR:
            return tile.color
        return PATH_COLOR
    if tile is step.current:
        return AGENT_COLOR
    if tile in step.visited:
        return grey_out(tile.color)
    if tile in step.frontier_set and tile.tile_type not in _KEEP_COLOR:
        return FRONTIER_COLOR
    return tile.color
