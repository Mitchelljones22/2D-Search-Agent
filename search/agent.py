"""Search agent: drives a search generator one step at a time and remembers every step.

The history lets the user step backwards and forwards through a search that has
already happened, while new steps are only pulled from the search when needed.
"""
from search.algorithms import INFORMED, SEARCHES, SearchStatus, bfs
from search.heuristics import HEURISTICS
from search.metrics import effective_branching_factor

MEASURE_REPEATS = 5   #timed reruns of a finished single-run search


class SearchAgent:
    def __init__(self):
        self.reset()

    def reset(self):  #forget the current search, agent is no longer on the map
        self._search = None
        self.history = []
        self.index = -1
        self.search_name = ""
        self.measurement = None   #measured metrics of the finished search, see measure()
        self._run = None          #(method, graph, start, goal, heuristic name) to rerun headless

    @property
    def active(self):
        return self._search is not None

    @property
    def current_step(self):  #SearchStep being shown, or None before the first step
        if self.index < 0:
            return None
        return self.history[self.index]

    @property
    def finished(self):  #the search has produced its final step (found or no path)
        return bool(self.history) and self.history[-1].status != SearchStatus.RUNNING

    @property
    def at_end(self):  #showing the newest step, and the search has nothing more to give
        return self.finished and self.index == len(self.history) - 1

    def start(self, graph, start_tile, goal_tile, search=bfs, heuristic="Manhattan"):  #heuristic is a HEURISTICS name
        self.reset()
        self._run = (search, graph, start_tile, goal_tile, heuristic if search in INFORMED else None)
        details = []   #shown after the search name so runs with different settings can be told apart
        if search in INFORMED:
            self._search = search(graph, start_tile, goal_tile, HEURISTICS[heuristic])
            details.append(heuristic)
        else:
            self._search = search(graph, start_tile, goal_tile)
        if graph.diagonal:
            details.append("8-dir")
        self.search_name = next((name for name, fn in SEARCHES.items() if fn is search), search.__name__)   #dropdown label
        if details:
            self.search_name += f" ({', '.join(details)})"
        self.step_forward()   #first expansion puts the agent on the Start tile

    def step_forward(self):
        if self._search is None:
            return
        if self.index < len(self.history) - 1:   #replaying a step we already have
            self.index += 1
        elif not self.finished:
            self.history.append(next(self._search))
            self.index += 1

    def measure(self):
        """Reruns the finished search headless (no animation snapshots) to measure it:
        5 timed runs, 1 tracemalloc run, plus the map's optimal cost for the optimality ratio."""
        from evaluation.runner import RunResult, measure, reference_values   #only needed once a search is done
        if not self.finished or self._run is None:
            return
        method, graph, start, goal, heuristic = self._run
        result = measure(method, graph, start, goal, heuristic, MEASURE_REPEATS, memory_repeats=1)
        optimal, shortest = reference_values(graph, start, goal)
        t_mean, t_std, t_min, t_max = RunResult.spread(result.times_ms)
        ratio = None
        if result.found and optimal is not None:
            ratio = optimal / result.path_cost if result.path_cost else 1.0
        self.measurement = {
            "found": result.found, "moves": result.path_moves, "cost": result.path_cost,
            "optimal_cost": optimal, "optimality_ratio": ratio,
            "expanded": result.expanded, "generated": result.generated,
            "branching_avg": result.branching_avg, "branching_max": result.branching_max,
            "ebf": effective_branching_factor(result.expanded, shortest) if shortest else None,
            "peak_frontier": result.peak_frontier, "peak_explored": result.peak_explored,
            "peak_footprint": result.peak_footprint,
            "time_ms": (t_mean, t_std, t_min, t_max), "memory_kib": result.memory_kib[0],
            "repeats": MEASURE_REPEATS,
        }

    def step_back(self):
        if self.index > 0:
            self.index -= 1
