"""Test scripts (JSON) and the maps they describe.

A script either generates maps from parameter ranges, or lists exact maps by seed:

  generated  "sizes": [10, 15, ...], "densities": [8, 16, ...] (percent), "maps_per_config": 1,
             "placements": ["corners", "random"], "base_seed": 1000
  explicit   "maps": [{"seed": <map seed copied from the app>, "label": "..."}]

Shared keys: "name", "description", "movements" (["4-dir", "8-dir"]), "methods" (dropdown
names), "heuristics" (HEURISTICS names, used by Best-First and A*), "repeats" (>= 1).

Generated maps are reproducible: the obstacle generator seed for config i, attempt a is
base_seed + 100 * i + a. A seed is only used if the map is solvable with Start/Goal in the
corners AND in their random positions, so both placements share the same obstacles. Seeds that
give unsolvable maps are skipped and logged.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

from environment.graph import Graph
from environment.obstacle_generator import ObstacleGenerator
from environment.seed import decode, encode
from environment.tile_map import TileMap
from environment.tile_type import TileType
from search.algorithms import SEARCHES, SearchStatus, bfs
from search.heuristics import HEURISTICS

MIN_SIZE = 2
MAX_SIZE = 30
MOVEMENTS = {"4-dir": False, "8-dir": True}
PLACEMENTS = ("corners", "random")
MAX_ATTEMPTS = 100

DEFAULTS = {
    "name": "experiment",
    "description": "",
    "base_seed": 1000,
    "sizes": [15],
    "densities": [20],
    "maps_per_config": 1,
    "placements": ["random"],
    "movements": ["4-dir", "8-dir"],
    "methods": list(SEARCHES),
    "heuristics": list(HEURISTICS),
    "repeats": 5,
}


@dataclass
class MapSpec:
    map_id: str
    label: str
    size: tuple          #(cols, rows)
    density: float       #requested obstacle percent, None for explicit maps
    placement: str       #"corners", "random" or "given"
    generator_seed: int  #None for explicit maps
    tile_map: TileMap = field(repr=False)

    @property
    def map_seed(self):  #paste into the app's seed box and press Generate to see this map
        return encode(self.tile_map)

    @property
    def obstacle_percent(self):
        tiles = self.tile_map.x * self.tile_map.y
        obstacles = sum(tile.tile_type == TileType.OBSTACLE for row in self.tile_map.grid for tile in row)
        return 100 * obstacles / tiles


class ProtocolError(ValueError):
    pass


def load(path):
    with open(path, encoding="utf-8") as file:
        script = json.load(file)
    return validate(script, Path(path).stem)


def validate(script, fallback_name="experiment"):
    protocol = dict(DEFAULTS)
    protocol["name"] = fallback_name
    protocol.update(script)
    for movement in protocol["movements"]:
        if movement not in MOVEMENTS:
            raise ProtocolError(f"unknown movement {movement!r}, use {list(MOVEMENTS)}")
    for method in protocol["methods"]:
        if method not in SEARCHES:
            raise ProtocolError(f"unknown method {method!r}, use {list(SEARCHES)}")
    for heuristic in protocol["heuristics"]:
        if heuristic not in HEURISTICS:
            raise ProtocolError(f"unknown heuristic {heuristic!r}, use {list(HEURISTICS)}")
    for placement in protocol["placements"]:
        if placement not in PLACEMENTS:
            raise ProtocolError(f"unknown placement {placement!r}, use {list(PLACEMENTS)}")
    for size in protocol["sizes"]:
        if not MIN_SIZE <= size <= MAX_SIZE:
            raise ProtocolError(f"size {size} outside {MIN_SIZE}-{MAX_SIZE}")
    for density in protocol["densities"]:
        if not 0 <= density <= 100:
            raise ProtocolError(f"density {density} outside 0-100")
    if int(protocol["repeats"]) < 1:
        raise ProtocolError("repeats must be at least 1")
    return protocol


def _solvable(tile_map):
    if tile_map.start_tile is None or tile_map.goal_tile is None:
        return False
    graph = Graph(False)   #diagonals cannot cut corners, so 8-dir connects exactly what 4-dir connects
    graph.build(tile_map)
    for step in bfs(graph, tile_map.start_tile, tile_map.goal_tile, trace=False):
        pass
    return step.status == SearchStatus.FOUND


def _generate(size, density, seed):
    tile_map = TileMap(size, size)
    ObstacleGenerator(density / 100, seed).generate(tile_map)
    return tile_map


def _to_corners(tile_map):  #Start top-left, Goal bottom-right; overwrites whatever was there
    tile_map.set_tile_type(0, 0, TileType.START)
    tile_map.set_tile_type(tile_map.x - 1, tile_map.y - 1, TileType.GOAL)
    return tile_map


def build_maps(protocol):
    """Returns (list of MapSpec, list of skip notes)."""
    if "maps" in protocol:
        return _explicit_maps(protocol), []

    maps = []
    skipped = []
    config = 0
    for size in protocol["sizes"]:
        for density in protocol["densities"]:
            for copy in range(protocol["maps_per_config"]):
                chosen = None
                for attempt in range(MAX_ATTEMPTS):
                    seed = protocol["base_seed"] + 100 * config + attempt
                    candidates = {
                        "random": _generate(size, density, seed),
                        "corners": _to_corners(_generate(size, density, seed)),
                    }
                    if all(_solvable(candidates[p]) for p in protocol["placements"]):
                        chosen = (seed, candidates)
                        break
                    skipped.append(f"{size}x{size} {density}% seed {seed}: unsolvable, tried next seed")
                if chosen is None:
                    skipped.append(f"{size}x{size} {density}%: no solvable map in {MAX_ATTEMPTS} seeds, config dropped")
                else:
                    seed, candidates = chosen
                    for placement in protocol["placements"]:
                        maps.append(MapSpec(
                            map_id=f"{size}x{size}-d{density}-m{copy}-{placement}",
                            label=f"{size}x{size}, {density}% obstacles, {placement}",
                            size=(size, size), density=density, placement=placement,
                            generator_seed=seed, tile_map=candidates[placement],
                        ))
                config += 1
    return maps, skipped


def _explicit_maps(protocol):
    maps = []
    for index, entry in enumerate(protocol["maps"]):
        decoded = decode(int(entry["seed"]), MIN_SIZE, MAX_SIZE)
        if decoded is None:
            raise ProtocolError(f"map {index}: invalid seed")
        cols, rows, tile_types = decoded
        tile_map = TileMap(cols, rows)
        tile_map.apply_types(tile_types)
        if not _solvable(tile_map):
            raise ProtocolError(f"map {index}: needs a Start and a Goal with a path between them")
        maps.append(MapSpec(
            map_id=f"map{index}", label=entry.get("label", f"{cols}x{rows} map"),
            size=(cols, rows), density=None, placement="given", generator_seed=None, tile_map=tile_map,
        ))
    return maps
