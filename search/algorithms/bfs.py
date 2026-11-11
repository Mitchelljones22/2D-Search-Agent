from collections import deque

from search.algorithms.search_step import SearchStatus, snapshot
from search.tree import SearchTree


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
            yield snapshot(current, queue, visited, tree, SearchStatus.FOUND, goal)
            return

        for neighbor in graph.neighbors(current):
            if neighbor not in discovered:
                discovered.add(neighbor)
                tree.add_child(current, neighbor)
                queue.append(neighbor)

        yield snapshot(current, queue, visited, tree, SearchStatus.RUNNING)

    yield snapshot(current, queue, visited, tree, SearchStatus.NO_PATH)
