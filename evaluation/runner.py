"""Measures one search configuration on one graph.

Each measurement is split into separate passes so they do not distort each other:
  effort pass   one traced-off run that records the search effort counters
  timed passes  wall-clock time with time.perf_counter_ns, garbage collector paused,
                tracemalloc off (tracing allocations slows Python down several times)
  memory passes tracemalloc on, peak bytes allocated by the search above what existed
                before it started (the graph and map are built beforehand, so they are excluded)
Search effort is deterministic, so every timed pass is checked against the effort pass.
"""
import gc
import statistics
import time
import tracemalloc
from dataclasses import dataclass, field

from search.algorithms import INFORMED, SearchStatus, a_star, bfs
from search.heuristics import HEURISTICS
from search.metrics import SearchMetrics
from visualization.search_report import path_cost


@dataclass
class RunResult:
    found: bool
    path_moves: int          #path length in moves (= solution depth)
    path_cost: float         #1 per straight move, sqrt(2) per diagonal
    expanded: int
    generated: int
    enqueued: int
    branching_avg: float
    branching_max: int
    peak_frontier: int
    peak_explored: int
    peak_footprint: int
    times_ms: list = field(default_factory=list)
    memory_kib: list = field(default_factory=list)
    history: list = None     #(frontier size, explored size) per expansion, when requested

    @staticmethod
    def spread(values):  #mean, std, best (min), worst (max)
        if not values:
            return None, None, None, None
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        return statistics.mean(values), std, min(values), max(values)


def _search(method, graph, start, goal, heuristic, metrics):
    if method in INFORMED:
        return method(graph, start, goal, HEURISTICS[heuristic], metrics=metrics, trace=False)
    return method(graph, start, goal, metrics=metrics, trace=False)


def _final_step(method, graph, start, goal, heuristic, metrics):
    step = None
    for step in _search(method, graph, start, goal, heuristic, metrics):
        pass
    return step


def reference_values(graph, start, goal):
    """(optimal path cost from uniform cost search, fewest moves from BFS), or (None, None) if unsolvable."""
    for step in a_star(graph, start, goal, HEURISTICS["None"], trace=False):
        pass
    if step.status != SearchStatus.FOUND:
        return None, None
    optimal = path_cost(step.path)
    for step in bfs(graph, start, goal, trace=False):
        pass
    return optimal, len(step.path) - 1


def measure(method, graph, start, goal, heuristic=None, repeats=5, history=False, memory_repeats=None):
    """Runs one method on one graph: 1 effort pass, `repeats` timed passes, `memory_repeats`
    (default `repeats`) memory passes."""
    if memory_repeats is None:
        memory_repeats = repeats
    metrics = SearchMetrics(history=history)
    step = _final_step(method, graph, start, goal, heuristic, metrics)   #also warms up caches
    found = step.status == SearchStatus.FOUND
    result = RunResult(
        found=found,
        path_moves=len(step.path) - 1 if found else 0,
        path_cost=path_cost(step.path) if found else 0.0,
        expanded=metrics.expanded,
        generated=metrics.generated,
        enqueued=metrics.enqueued,
        branching_avg=metrics.branching_avg,
        branching_max=metrics.branch_max,
        peak_frontier=metrics.peak_frontier,
        peak_explored=metrics.peak_explored,
        peak_footprint=metrics.peak_footprint,
        history=metrics.history,
    )
    effort = (metrics.expanded, metrics.generated, metrics.peak_footprint)

    for _ in range(repeats):
        check = SearchMetrics()
        gc_was_enabled = gc.isenabled()
        gc.disable()
        begin = time.perf_counter_ns()
        _final_step(method, graph, start, goal, heuristic, check)
        elapsed = time.perf_counter_ns() - begin
        if gc_was_enabled:
            gc.enable()
        if (check.expanded, check.generated, check.peak_footprint) != effort:
            raise RuntimeError(f"{method.__name__} is not deterministic: {effort} vs {vars(check)}")
        result.times_ms.append(elapsed / 1_000_000)

    for _ in range(memory_repeats):
        gc.collect()
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]
        _final_step(method, graph, start, goal, heuristic, SearchMetrics())
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        result.memory_kib.append((peak - baseline) / 1024)

    return result
