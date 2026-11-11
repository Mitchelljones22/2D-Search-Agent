"""Runs a test-script protocol and returns plain, JSON-ready results.

For every map and movement mode:
  1. reference values (not timed): the optimal path cost from uniform cost search (A* with
     h = 0) and the fewest moves from BFS
  2. every method variant (method, plus heuristic for Best-First and A*) is measured with
     evaluation.runner.measure
  3. the optimality score of each variant is filled in once all variants on that map are done

Score = 100 * (C* / C) * (N_min / N)
  C* optimal path cost on this map, C the variant's path cost,
  N_min the fewest nodes expanded by any variant on this map, N the variant's nodes expanded.
  100 means the variant found an optimal path with the least work of any method.
"""
import datetime
import os
import platform
import subprocess
import sys
import time

from environment.graph import Graph
from evaluation.protocol import MOVEMENTS, build_maps
from evaluation.runner import RunResult, measure, reference_values
from search.algorithms import INFORMED, SEARCHES
from search.heuristics import is_admissible
from search.metrics import effective_branching_factor

HISTORY_POINTS = 400   #frontier histories are thinned to about this many points


def variants(protocol):  #(method name, heuristic or None, label)
    for method in protocol["methods"]:
        if SEARCHES[method] in INFORMED:
            for heuristic in protocol["heuristics"]:
                yield method, heuristic, f"{method} ({heuristic})"
        else:
            yield method, None, method


def native_heuristic(protocol, diagonal):  #the exact obstacle-free heuristic for the movement mode
    preferred = "Octile" if diagonal else "Manhattan"
    if preferred in protocol["heuristics"]:
        return preferred
    return protocol["heuristics"][0] if protocol["heuristics"] else None


def environment():
    commit = None
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        pass
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "os": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "git_commit": commit,
        "timer": "time.perf_counter_ns",
        "memory": "tracemalloc peak above baseline",
    }


def _thin(history):  #[[expansion number, frontier size, explored size], ...]
    if not history:
        return []
    count = len(history)
    if count <= HISTORY_POINTS:
        indexes = range(count)
    else:
        stride = count / HISTORY_POINTS
        indexes = sorted({int(i * stride) for i in range(HISTORY_POINTS)} | {count - 1})
    return [[i + 1, history[i][0], history[i][1]] for i in indexes]


def run(protocol, progress=None, should_cancel=None):
    """progress(done, total, text) is called before each measurement; should_cancel() stops early."""
    started = time.time()
    maps, skipped = build_maps(protocol)
    variant_list = list(variants(protocol))
    total = len(maps) * len(protocol["movements"]) * len(variant_list)
    done = 0
    cancelled = False
    runs = []

    for spec in maps:
        if cancelled:
            break
        tile_map = spec.tile_map
        for movement in protocol["movements"]:
            if cancelled:
                break
            diagonal = MOVEMENTS[movement]
            graph = Graph(diagonal)
            graph.build(tile_map)
            optimal_cost, shortest_moves = reference_values(graph, tile_map.start_tile, tile_map.goal_tile)
            map_runs = []
            for method, heuristic, label in variant_list:
                if should_cancel and should_cancel():
                    cancelled = True
                    break
                if progress:
                    progress(done, total, f"{spec.label}, {movement}: {label}")
                result = measure(SEARCHES[method], graph, tile_map.start_tile, tile_map.goal_tile, heuristic,
                                 protocol["repeats"])
                done += 1
                t_mean, t_std, t_min, t_max = RunResult.spread(result.times_ms)
                m_mean, m_std, m_min, m_max = RunResult.spread(result.memory_kib)
                ebf = effective_branching_factor(result.expanded, shortest_moves)
                map_runs.append({
                    "map_id": spec.map_id, "cols": spec.size[0], "rows": spec.size[1],
                    "density": spec.density, "obstacle_percent": round(spec.obstacle_percent, 2),
                    "placement": spec.placement, "movement": movement,
                    "method": method, "heuristic": heuristic or "", "variant": label,
                    "admissible": (is_admissible(heuristic, diagonal) if heuristic else None),
                    "found": result.found,
                    "path_moves": result.path_moves, "path_cost": round(result.path_cost, 4),
                    "shortest_moves": shortest_moves, "optimal_cost": round(optimal_cost, 4),
                    "expanded": result.expanded, "generated": result.generated, "enqueued": result.enqueued,
                    "branching_avg": round(result.branching_avg, 4), "branching_max": result.branching_max,
                    "ebf": round(ebf, 4) if ebf is not None else None,
                    "peak_frontier": result.peak_frontier, "peak_explored": result.peak_explored,
                    "peak_footprint": result.peak_footprint,
                    "time_ms_mean": t_mean, "time_ms_std": t_std, "time_ms_min": t_min, "time_ms_max": t_max,
                    "mem_kib_mean": m_mean, "mem_kib_std": m_std, "mem_kib_min": m_min, "mem_kib_max": m_max,
                    "times_ms": result.times_ms, "memory_kib": result.memory_kib,
                })
            _score(map_runs)
            runs.extend(map_runs)

    frontier = {} if cancelled else _frontier_histories(protocol, maps)
    finished = time.time()
    return {
        "protocol": protocol,
        "environment": environment(),
        "started": datetime.datetime.fromtimestamp(started).isoformat(timespec="seconds"),
        "finished": datetime.datetime.fromtimestamp(finished).isoformat(timespec="seconds"),
        "elapsed_s": round(finished - started, 2),
        "cancelled": cancelled,
        "measurements_done": done,
        "measurements_total": total,
        "maps": [{
            "map_id": spec.map_id, "label": spec.label, "cols": spec.size[0], "rows": spec.size[1],
            "density": spec.density, "obstacle_percent": round(spec.obstacle_percent, 2),
            "placement": spec.placement, "generator_seed": spec.generator_seed, "map_seed": str(spec.map_seed),
            "start": [spec.tile_map.start_tile.col, spec.tile_map.start_tile.row],
            "goal": [spec.tile_map.goal_tile.col, spec.tile_map.goal_tile.row],
        } for spec in maps],
        "skipped": skipped,
        "runs": runs,
        "frontier": frontier,
    }


def _score(map_runs):
    found = [run for run in map_runs if run["found"]]
    if not found:
        return
    fewest = min(run["expanded"] for run in found)
    for run in map_runs:
        if not run["found"]:
            run["optimality_ratio"] = None
            run["score"] = None
            continue
        ratio = run["optimal_cost"] / run["path_cost"] if run["path_cost"] else 1.0
        run["optimality_ratio"] = round(ratio, 4)
        run["score"] = round(100 * ratio * fewest / run["expanded"], 2)


def _frontier_histories(protocol, maps):
    """Frontier and explored size after every expansion, for one representative map per movement:
    the largest corners map (longest guaranteed solution), else the largest map."""
    if not maps:
        return {}
    corners = [spec for spec in maps if spec.placement == "corners"] or maps
    spec = max(corners, key=lambda s: (s.size[0] * s.size[1], s.density or 0))
    histories = {}
    for movement in protocol["movements"]:
        diagonal = MOVEMENTS[movement]
        graph = Graph(diagonal)
        graph.build(spec.tile_map)
        native = native_heuristic(protocol, diagonal)
        series = {}
        for method, heuristic, label in variants(protocol):
            if heuristic not in (None, native, "None"):
                continue   #one informed heuristic plus h = 0 keeps the chart readable
            result = measure(SEARCHES[method], graph, spec.tile_map.start_tile, spec.tile_map.goal_tile, heuristic,
                             repeats=0, history=True)
            series[label] = _thin(result.history)
        histories[movement] = {"map_id": spec.map_id, "label": spec.label, "series": series}
    return histories
