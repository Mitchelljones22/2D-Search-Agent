"""Heuristics: estimates h(n) of the cost left from tile n to the goal.

Each one comes from relaxing the movement rules (ignoring obstacles) so the remaining
cost can be worked out without any search. Whether an estimate is admissible (never
overestimates) depends on which moves are allowed, see ADMISSIBLE below.

With dx = |column difference| and dy = |row difference|:
  Manhattan  dx + dy                      exact on an empty 4-direction grid
  Euclidean  sqrt(dx^2 + dy^2)            straight line, as if the agent could move in any direction
  Octile     max + (sqrt(2) - 1) * min    exact on an empty 8-direction grid with sqrt(2) diagonals
  Chebyshev  max(dx, dy)                  exact if a diagonal step cost the same as a straight one
  None       0                            no estimate, A* becomes uniform cost search
"""
import math

_DIAGONAL_EXTRA = math.sqrt(2) - 1


def _deltas(tile, goal):
    return abs(tile.col - goal.col), abs(tile.row - goal.row)


def manhattan(tile, goal):
    dx, dy = _deltas(tile, goal)
    return dx + dy


def euclidean(tile, goal):
    dx, dy = _deltas(tile, goal)
    return math.hypot(dx, dy)


def octile(tile, goal):
    dx, dy = _deltas(tile, goal)
    return max(dx, dy) + _DIAGONAL_EXTRA * min(dx, dy)


def chebyshev(tile, goal):
    dx, dy = _deltas(tile, goal)
    return max(dx, dy)


def zero(tile, goal):
    return 0


HEURISTICS = {   #display name -> function, in the order the settings dialog lists them
    "Manhattan": manhattan,
    "Euclidean": euclidean,
    "Octile": octile,
    "Chebyshev": chebyshev,
    "None": zero,
}

FORMULAS = {
    "Manhattan": "|dx| + |dy|",
    "Euclidean": "\u221a(dx\u00b2 + dy\u00b2)",
    "Octile": "max + 0.41 \u00b7 min",
    "Chebyshev": "max(|dx|, |dy|)",
    "None": "h = 0",
}


def is_admissible(name, diagonal):
    """True when the heuristic never overestimates the real remaining cost.

    4-direction: every estimate here is <= Manhattan, which is the exact cost with no
    obstacles, so all are admissible (Manhattan is the most informed).
    8-direction: the exact obstacle-free cost is Octile. Manhattan counts a diagonal step
    as 2 when it really costs sqrt(2), so it overestimates; the rest stay <= Octile.
    """
    return not (diagonal and name == "Manhattan")
