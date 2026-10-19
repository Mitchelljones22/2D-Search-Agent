"""Uninformed (blind) search over a Graph, one expansion at a time.

The agent only perceives its current node and graph.neighbors(current), its 4-cardinal
neighbors. Obstacles are never in the graph, so every move the search makes is admissible.

Each search is a generator that yields a SearchStep after every expansion, letting the
caller animate, pause, or record the steps for stepping backwards.
"""
from collections import deque
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

    @property
    def expanded(self):  #number of states searched so far
        return len(self.visited)


def _snapshot(current, frontier, visited, tree, status, goal=None):
    path = ()
    if status == SearchStatus.FOUND:
        path = tuple(tree.path_to(goal))
    frontier = tuple(frontier)
    return SearchStep(
        current, frontier, frozenset(visited), tree, len(tree.parent), status, path,
        frozenset(frontier), frozenset(path),
    )


def bfs(graph, start, goal):
    """Breadth-First Search: FIFO queue, explores outward in rings from the start.

    Every edge costs the same, so the first time the goal is expanded it was reached by
    the fewest moves -- BFS always returns a shortest path when one exists.
    Neighbors are added to the tree as soon as they are discovered, so the tree shows the
    frontier of candidate "next" nodes.
    """
    tree = SearchTree(start)
    queue = deque([start])
    discovered = {start}   #in the tree already (expanded or waiting in the queue)
    visited = set()
    current = start

    while queue:
        current = queue.popleft()
        visited.add(current)
        if current is goal:
            yield _snapshot(current, queue, visited, tree, SearchStatus.FOUND, goal)
            return

        for neighbor in graph.neighbors(current):
            if neighbor not in discovered:
                discovered.add(neighbor)
                tree.add_child(current, neighbor)
                queue.append(neighbor)

        yield _snapshot(current, queue, visited, tree, SearchStatus.RUNNING)

    yield _snapshot(current, queue, visited, tree, SearchStatus.NO_PATH)


def dfs(graph, start, goal):
    """Depth-First Search: LIFO stack, follows one branch as deep as it can before backtracking.

    DFS finds *a* path but not necessarily the shortest, since it commits to the first
    branch it tries. A node joins the tree only when the agent actually moves into it,
    because a cell can be pushed several times from different parents before it is visited.
    """
    tree = SearchTree(start)
    stack = [(start, None)]   #(node, parent that pushed it)
    visited = set()
    current = start

    while stack:
        node, parent = stack.pop()
        if node in visited:
            continue   #stale entry, reached through another branch first

        current = node
        visited.add(current)
        if parent is not None:
            tree.add_child(parent, current)
        if current is goal:
            yield _snapshot(current, _stack_frontier(stack, visited), visited, tree, SearchStatus.FOUND, goal)
            return

        for neighbor in reversed(graph.neighbors(current)):   #reversed so North is popped first
            if neighbor not in visited:
                stack.append((neighbor, current))

        yield _snapshot(current, _stack_frontier(stack, visited), visited, tree, SearchStatus.RUNNING)

    yield _snapshot(current, (), visited, tree, SearchStatus.NO_PATH)


def _stack_frontier(stack, visited):  #unvisited stack nodes, top of stack first, no duplicates
    frontier = []
    seen = set()
    for node, _ in reversed(stack):
        if node not in visited and node not in seen:
            seen.add(node)
            frontier.append(node)
    return frontier


SEARCHES = {"BFS": bfs, "DFS": dfs}
