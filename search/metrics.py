"""Search effort counters, filled in by the algorithms while they run.

Definitions (also written into batch logs):
  expanded    nodes taken off the frontier and goal-tested (IDDFS counts repeats across rounds)
  generated   successors produced by expanding nodes, plus 1 for Start; includes neighbors that
              were already seen, since producing them is real work
  enqueued    nodes actually added to the frontier (generated minus duplicates that were dropped)
  branching   successors generated per expanded non-goal node: avg and max
  footprint   len(frontier container) + len(explored container), peak over the run; uses the real
              container sizes, so stale heap entries and duplicate stack entries count
"""


class SearchMetrics:
    def __init__(self, history=False):
        self.expanded = 0
        self.generated = 1   #Start
        self.enqueued = 1
        self.branch_nodes = 0   #expansions that produced successors (leaves do not)
        self.branch_max = 0
        self.peak_frontier = 0
        self.peak_explored = 0
        self.peak_footprint = 0
        self.history = [] if history else None   #(frontier size, explored size) after each expansion

    def expand(self, successors, enqueued, frontier_size, explored_size):  #one non-goal expansion
        self.expanded += 1
        self.generated += successors
        self.enqueued += enqueued
        self.branch_nodes += 1
        if successors > self.branch_max:
            self.branch_max = successors
        self._observe(frontier_size, explored_size)

    def visit_leaf(self, frontier_size, explored_size):  #goal-tested but no successors generated (the goal, or IDDFS at its depth limit)
        self.expanded += 1
        self._observe(frontier_size, explored_size)

    def _observe(self, frontier_size, explored_size):
        if frontier_size > self.peak_frontier:
            self.peak_frontier = frontier_size
        if explored_size > self.peak_explored:
            self.peak_explored = explored_size
        footprint = frontier_size + explored_size
        if footprint > self.peak_footprint:
            self.peak_footprint = footprint
        if self.history is not None:
            self.history.append((frontier_size, explored_size))

    @property
    def branching_avg(self):
        if self.branch_nodes == 0:
            return 0.0
        return (self.generated - 1) / self.branch_nodes


def effective_branching_factor(expanded, depth):
    """b* such that a uniform tree of depth d holds expanded + 1 nodes: N + 1 = 1 + b + b^2 + ... + b^d.

    1.0 means the search went straight to the goal; larger means more wasted expansions.
    Uses nodes expanded as N. Returns None when the depth is 0 (Start is the Goal).
    """
    if depth <= 0:
        return None
    target = expanded + 1

    def tree_size(b):
        return sum(b ** level for level in range(depth + 1))

    if tree_size(1.0) >= target:
        return 1.0
    low, high = 1.0, float(max(expanded, 2))
    for _ in range(100):   #bisection, tree_size grows with b
        mid = (low + high) / 2
        if tree_size(mid) < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2
