import heapq
from itertools import count

from search.algorithms.search_step import SearchStatus, snapshot
from search.heuristics import manhattan
from search.metrics import SearchMetrics
from search.tree import SearchTree


def best_first(graph, start, goal, heuristic=manhattan, metrics=None, trace=True):
    """Greedy Best-First Search: always expands the open tile estimated closest to the goal.

    The open list holds the frontier ordered by h(n), the heuristic estimate of the cost
    left to the goal (Manhattan distance by default, chosen in the settings dialog). The closed list holds tiles already
    expanded. Unlike hill climbing it keeps every open tile, so when the closest-looking tile
    runs into a dead end it falls back to the next most promising one anywhere on the frontier.

    It is greedy: f(n) = h(n) only, the cost already paid (g) is ignored when choosing, so
    the path found is not guaranteed to be the shortest.

    Ties on h are broken by the order tiles were added to the open list (oldest first), and
    neighbors are added North, South, East, West (then the diagonals), so runs are repeatable.

    A tile is kept in the open list only once. If it is reached again by a shorter route
    while still open, its parent is switched to the shorter route (its h, and so its place
    in the open list, does not change).

    metrics collects search effort; trace=False yields only the final step.
    """
    metrics = metrics if metrics is not None else SearchMetrics()
    order = count()   #tie breaker: insertion order
    tree = SearchTree(start)
    open_heap = [(heuristic(start, goal), next(order), start)]
    g_cost = {start: 0}   #moves from Start along the best route found so far
    closed = set()
    current = start

    def step(status):
        frontier = [node for _, _, node in sorted(open_heap)]   #most promising first
        return snapshot(current, frontier, closed, tree, status, goal, heuristic_value=heuristic(current, goal))

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        closed.add(current)
        if current is goal:
            metrics.visit_leaf(len(open_heap), len(closed))
            yield step(SearchStatus.FOUND)
            return

        neighbors = graph.neighbors(current)
        added = 0
        for neighbor in neighbors:   #N, S, E, W, then the diagonals if allowed
            if neighbor in closed:
                continue
            g = g_cost[current] + graph.cost(current, neighbor)
            if neighbor not in g_cost:   #new tile, goes on the open list
                g_cost[neighbor] = g
                tree.add_child(current, neighbor)
                heapq.heappush(open_heap, (heuristic(neighbor, goal), next(order), neighbor))
                added += 1
            elif g < g_cost[neighbor]:   #already open, keep only the lower cost route
                g_cost[neighbor] = g
                tree.add_child(current, neighbor)
        metrics.expand(len(neighbors), added, len(open_heap), len(closed))

        if trace:
            yield step(SearchStatus.RUNNING)

    yield step(SearchStatus.NO_PATH)
