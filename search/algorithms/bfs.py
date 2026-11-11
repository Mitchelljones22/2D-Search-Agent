from collections import deque

from search.algorithms.search_step import SearchStatus, snapshot
from search.metrics import SearchMetrics
from search.tree import SearchTree


def bfs(graph, start, goal, metrics=None, trace=True):
    """Breadth-First Search: FIFO queue, explores outward in rings from the start.

    Every edge costs the same, so the first time the goal is expanded it was reached by
    the fewest moves -- BFS always returns a shortest path when one exists.
    Neighbors are added to the tree as soon as they are discovered, so the tree shows the
    frontier of candidate "next" nodes.

    metrics collects search effort; trace=False skips the per-step snapshots and yields only
    the final step (used when timing the search).
    """
    metrics = metrics if metrics is not None else SearchMetrics()
    tree = SearchTree(start)
    queue = deque([start])
    discovered = {start}   #in the tree already (expanded or waiting in the queue)
    visited = set()
    current = start

    while queue:
        current = queue.popleft()
        visited.add(current)
        if current is goal:
            metrics.visit_leaf(len(queue), len(visited))
            yield snapshot(current, queue, visited, tree, SearchStatus.FOUND, goal)
            return

        neighbors = graph.neighbors(current)
        added = 0
        for neighbor in neighbors:
            if neighbor not in discovered:
                discovered.add(neighbor)
                tree.add_child(current, neighbor)
                queue.append(neighbor)
                added += 1
        metrics.expand(len(neighbors), added, len(queue), len(visited))

        if trace:
            yield snapshot(current, queue, visited, tree, SearchStatus.RUNNING)

    yield snapshot(current, queue, visited, tree, SearchStatus.NO_PATH)
