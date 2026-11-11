from search.algorithms.search_step import SearchStatus, snapshot
from search.metrics import SearchMetrics
from search.tree import SearchTree


def dfs(graph, start, goal, metrics=None, trace=True):
    """Depth-First Search: LIFO stack, follows one branch as deep as it can before backtracking.

    DFS finds *a* path but not necessarily the shortest, since it commits to the first
    branch it tries. A node joins the tree only when the agent actually moves into it,
    because a cell can be pushed several times from different parents before it is visited.

    metrics collects search effort; trace=False yields only the final step.
    """
    metrics = metrics if metrics is not None else SearchMetrics()
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
            metrics.visit_leaf(len(stack), len(visited))
            yield snapshot(current, _stack_frontier(stack, visited), visited, tree, SearchStatus.FOUND, goal)
            return

        neighbors = graph.neighbors(current)
        added = 0
        for neighbor in reversed(neighbors):   #reversed so North is popped first
            if neighbor not in visited:
                stack.append((neighbor, current))
                added += 1
        metrics.expand(len(neighbors), added, len(stack), len(visited))

        if trace:
            yield snapshot(current, _stack_frontier(stack, visited), visited, tree, SearchStatus.RUNNING)

    yield snapshot(current, (), visited, tree, SearchStatus.NO_PATH)


def _stack_frontier(stack, visited):  #unvisited stack nodes, top of stack first, no duplicates
    frontier = []
    seen = set()
    for node, _ in reversed(stack):
        if node not in visited and node not in seen:
            seen.add(node)
            frontier.append(node)
    return frontier
