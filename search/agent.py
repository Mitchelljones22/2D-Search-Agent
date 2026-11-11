"""Search agent: drives a search generator one step at a time and remembers every step.

The history lets the user step backwards and forwards through a search that has
already happened, while new steps are only pulled from the search when needed.
"""
from search.algorithms import INFORMED, SEARCHES, SearchStatus, bfs
from search.heuristics import HEURISTICS


class SearchAgent:
    def __init__(self):
        self.reset()

    def reset(self):  #forget the current search, agent is no longer on the map
        self._search = None
        self.history = []
        self.index = -1
        self.search_name = ""

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

    def step_back(self):
        if self.index > 0:
            self.index -= 1
