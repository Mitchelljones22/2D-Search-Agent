"""Heuristics: estimates h(n) of the number of moves left from tile n to the goal.

Manhattan distance comes from relaxing the movement rule. The real rule is "move to an
adjacent tile that is not an obstacle"; dropping "not an obstacle" leaves a problem that
can be solved without any search: |d_col| + |d_row| moves on an empty 4-direction grid.
Because it solves an easier version of the problem it never overestimates (admissible),
and one move changes it by exactly 1 (monotonic / consistent).
"""


def manhattan(tile, goal):
    return abs(tile.col - goal.col) + abs(tile.row - goal.row)
