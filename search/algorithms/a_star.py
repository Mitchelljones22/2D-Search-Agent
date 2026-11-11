import heapq
from itertools import count

from search.algorithms.search_step import SearchStatus, snapshot
from search.heuristics import manhattan
from search.metrics import SearchMetrics
from search.tree import SearchTree


def a_star(graph, start, goal, heuristic=manhattan, metrics=None, trace=True):
    """A* Search: always expands the open tile with the lowest f(n) = g(n) + h(n).

    g(n) is the actual cost from Start to n along the best route found so far (1 per straight
    move, sqrt(2) per diagonal), and h(n) is the heuristic estimate of the cost left to the
    goal. f(n) is the estimated cost of the cheapest full path that goes through n.

    It is branch and bound (always looks back at the cost so far) plus an estimate of the
    distance to the goal. With an admissible heuristic it is complete and optimal: the goal
    is only taken off the open list once no other open tile could lead to a cheaper path.
    With h = 0 it is uniform cost search.

    Open list: tiles that may be explored, ordered by f, ties go to the lower h (the tile
    closer to the goal), then to the oldest entry.
    Closed list: tiles already expanded.

    Principle of optimality: if a cheaper route to a tile is found, the costlier one is
    dropped. The tile gets the new parent and lower g and goes back on the open list, even
    if it was already closed (this only happens with a heuristic that is not consistent,
    such as Manhattan when diagonal moves are allowed).

    metrics collects search effort; trace=False yields only the final step.
    """
    metrics = metrics if metrics is not None else SearchMetrics()
    order = count()   #tie breaker: insertion order
    tree = SearchTree(start)
    h_start = heuristic(start, goal)
    open_heap = [(h_start, h_start, next(order), 0, start)]   #(f, h, order, g, tile)
    g_cost = {start: 0}
    closed = set()
    expansions = 0
    current = start

    def live_open():  #heap entries that still hold a tile's best g, most promising first
        return [node for _, _, _, g, node in sorted(open_heap) if node not in closed and g == g_cost[node]]

    def step(status):
        return snapshot(current, live_open(), closed, tree, status, goal, expansions=expansions,
                        heuristic_value=heuristic(current, goal), g_value=g_cost[current])

    while open_heap:
        _, _, _, g, node = heapq.heappop(open_heap)
        if node in closed or g != g_cost[node]:
            continue   #stale entry, a cheaper route to this tile was found after it was added

        current = node
        closed.add(current)
        expansions += 1
        if current is goal:
            metrics.visit_leaf(len(open_heap), len(closed))
            yield step(SearchStatus.FOUND)
            return

        neighbors = graph.neighbors(current)
        added = 0
        for neighbor in neighbors:   #N, S, E, W, then the diagonals if allowed
            new_g = g + graph.cost(current, neighbor)
            if new_g >= g_cost.get(neighbor, float("inf")):
                continue   #already reached at least as cheaply
            g_cost[neighbor] = new_g
            closed.discard(neighbor)   #reopen if it was expanded through a costlier route
            tree.add_child(current, neighbor)   #moves the tile if it was in the tree under a costlier parent
            h = heuristic(neighbor, goal)
            heapq.heappush(open_heap, (new_g + h, h, next(order), new_g, neighbor))
            added += 1
        metrics.expand(len(neighbors), added, len(open_heap), len(closed))

        if trace:
            yield step(SearchStatus.RUNNING)

    yield step(SearchStatus.NO_PATH)
