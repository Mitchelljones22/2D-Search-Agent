"""Shared types for the search algorithms: the step status, the per-step snapshot, and the
helper that builds a snapshot from a search's internal state.
"""
from dataclasses import dataclass
from enum import Enum

from search.tree import SearchTree


class SearchStatus(Enum):
    RUNNING = 0
    FOUND = 1
    NO_PATH = 2   #frontier emptied without reaching the goal (unsolvable maze)


@dataclass(frozen=True)
class SearchStep:  #snapshot of the search after one expansion
    current: object      #tile the agent is on (the node just expanded)
    frontier: tuple      #tiles waiting to be expanded, next one first
    visited: frozenset   #tiles already expanded
    tree: SearchTree     #shared tree, only grows
    tree_size: int       #how many tree nodes existed at this step (insertion order)
    status: SearchStatus
    path: tuple = ()     #start to goal, filled in once found
    frontier_set: frozenset = frozenset()   #fast membership tests for drawing
    path_set: frozenset = frozenset()
    expansions: int = None   #total expansions including repeats, set by searches that re-expand (IDDFS)
    depth_limit: int = None  #current depth limit, only for depth-limited searches
    heuristic_value: int = None   #h(current), only for informed searches

    @property
    def expanded(self):  #number of states searched so far
        if self.expansions is not None:
            return self.expansions
        return len(self.visited)


def snapshot(current, frontier, visited, tree, status, goal=None, expansions=None, depth_limit=None, heuristic_value=None):
    path = ()
    if status == SearchStatus.FOUND:
        path = tuple(tree.path_to(goal))
    frontier = tuple(frontier)
    return SearchStep(
        current, frontier, frozenset(visited), tree, len(tree.parent), status, path,
        frozenset(frontier), frozenset(path), expansions, depth_limit, heuristic_value,
    )
