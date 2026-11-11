from search.algorithms.search_step import SearchStatus, snapshot
from search.tree import SearchTree


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
            yield snapshot(current, _stack_frontier(stack, visited), visited, tree, SearchStatus.FOUND, goal)
            return

        for neighbor in reversed(graph.neighbors(current)):   #reversed so North is popped first
            if neighbor not in visited:
                stack.append((neighbor, current))

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
