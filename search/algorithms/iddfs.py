"""Iterative Deepening DFS: a recursive Depth-Limited Search (DLS) run again with a
larger depth limit each time, until the goal is reached.

Adapted from the classic recursive version (DLS + IDDFS over an adjacency list) to work
with this program:
  - DLS and IDDFS are generators, so the UI gets a SearchStep after every node the
    search enters and can animate, pause, and step back through it.
  - Each DLS call records the node in the search tree so the path can be traced back.
  - The grid is undirected, so the original would walk back and forth between two tiles
    forever. A tile is skipped when this round already explored it with as much depth
    left (or more), which removes the repeats without losing the shortest path.
  - maxDepth is the number of open tiles (no path can be longer), and the loop stops
    early once a round never hits its depth limit, since a deeper round would only
    repeat it.
"""
import sys

from search.algorithms.search_step import SearchStatus, snapshot
from search.tree import SearchTree


class _IterativeDeepening:
    def __init__(self, graph, src, target):
        self.graph = graph
        self.src = src
        self.target = target
        self.expansions = 0   #every DLS call that enters a node, across all rounds

    def _snapshot(self, current, status):
        return snapshot(current, self._frontier(), self.visited, self.tree, status, self.target,
                        expansions=self.expansions, depth_limit=self.limit)

    def _frontier(self):  #neighbors still waiting at each level of the recursion, deepest level first
        frontier = []
        seen = set()
        for level in reversed(self.pending):
            for node in level:
                if node not in seen:
                    seen.add(node)
                    frontier.append(node)
        return frontier

    def DLS(self, src, parent, maxDepth):  #Depth-Limited Search from src, returns True if the target was reached
        if self.depth_left.get(src, -1) >= maxDepth:
            return False   #already explored from this tile with at least this much depth left
        self.depth_left[src] = maxDepth
        self.visited.add(src)
        self.expansions += 1
        if parent is not None:
            self.tree.add_child(parent, src)   #moves the tile if it was reached by a longer route earlier

        if src is self.target:
            yield self._snapshot(src, SearchStatus.FOUND)
            return True

        # If reached the maximum depth, stop recursing.
        if maxDepth <= 0:
            if self.graph.neighbors(src):
                self.cutoff = True   #there is more to see past the limit
            yield self._snapshot(src, SearchStatus.RUNNING)
            return False

        # Recur for all the tiles adjacent to this tile
        level = list(self.graph.neighbors(src))   #North, South, East, West
        self.pending.append(level)
        yield self._snapshot(src, SearchStatus.RUNNING)
        while level:
            i = level.pop(0)
            if (yield from self.DLS(i, src, maxDepth - 1)):
                return True
        self.pending.pop()
        return False

    def IDDFS(self, maxDepth):  #repeatedly depth-limit search till the maximum depth
        sys.setrecursionlimit(max(sys.getrecursionlimit(), maxDepth + 500))   #one Python frame per tile on the branch
        for i in range(maxDepth):
            self.limit = i
            self.tree = SearchTree(self.src)   #every round starts over from Start
            self.depth_left = {}
            self.visited = set()
            self.pending = []
            self.cutoff = False
            if (yield from self.DLS(self.src, None, i)):
                return True
            if not self.cutoff:
                break   #the whole reachable area fit inside the limit, the target is unreachable
        yield self._snapshot(self.src, SearchStatus.NO_PATH)
        return False


def iddfs(graph, start, goal):
    """Iterative Deepening DFS: depth-limited DFS with limit 0, 1, 2, ... until the goal is found.

    Keeps DFS's small memory (one branch at a time) but finds the shortest path like BFS,
    at the cost of redoing the shallower levels every round.
    """
    search = _IterativeDeepening(graph, start, goal)
    yield from search.IDDFS(max(graph.node_count(), 1))
