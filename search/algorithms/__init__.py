"""Uninformed (blind) search over a Graph, one expansion at a time.

The agent only perceives its current node and graph.neighbors(current), its 4-cardinal
neighbors. Obstacles are never in the graph, so every move the search makes is admissible.

Each search is a generator that yields a SearchStep after every expansion, letting the
caller animate, pause, or record the steps for stepping backwards.

Each algorithm lives in its own module; this package re-exports them along with the
shared step types so callers can keep importing from search.algorithms.
"""
from search.algorithms.search_step import SearchStatus, SearchStep
from search.algorithms.bfs import bfs
from search.algorithms.dfs import dfs
from search.algorithms.iddfs import iddfs
from search.algorithms.best_first import best_first
from search.algorithms.a_star import a_star

SEARCHES = {"BFS": bfs, "DFS": dfs, "IDDFS": iddfs, "Best-First": best_first, "A*": a_star}   #display name -> search generator, in dropdown order
INFORMED = {best_first, a_star}   #searches that take a heuristic
