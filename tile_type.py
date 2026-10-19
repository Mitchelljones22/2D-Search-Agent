from enum import Enum  


class TileType(Enum):  
    TRAVERSABLE = 0
    OBSTACLE = 1
    GOAL = 2
    START = 3


TILE_COLORS = {  
    TileType.TRAVERSABLE: (255, 255, 255),
    TileType.OBSTACLE: (0, 0, 0),
    TileType.GOAL: (0, 160, 0),
    TileType.START: (0, 0, 255),
}

TILE_LABELS = {  
    TileType.TRAVERSABLE: "Traversable",
    TileType.OBSTACLE: "Obstacle",
    TileType.GOAL: "Goal",
    TileType.START: "Start",
}