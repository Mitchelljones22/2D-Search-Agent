"""Human readable results for a SearchStep, shared by the grid header and the tree view."""
import pygame

from environment.graph import Graph
from search.algorithms import SearchStatus

HEADER_HEIGHT = 70   #space reserved above the grid for the result text
FOUND_COLOR = (60, 200, 90)
NO_PATH_COLOR = (230, 80, 80)
STATS_COLOR = (220, 220, 220)
STATS_FONT_SIZES = (24, 22, 20, 18, 16)   #the stats line shrinks to fit narrow windows

STATUS_TEXT = {
    SearchStatus.RUNNING: "Searching",
    SearchStatus.FOUND: "Goal Found!",
    SearchStatus.NO_PATH: "No Path Found",
}


def number(value):  #1 -> "1", 1.41421 -> "1.41"
    return f"{value:.2f}".rstrip("0").rstrip(".")


def path_cost(path):  #1 per straight move, sqrt(2) per diagonal move
    return sum(Graph.cost(a, b) for a, b in zip(path, path[1:]))


def path_text(step):  #path length in moves, the path list also holds the Start tile
    if step.status != SearchStatus.FOUND:
        return "-"
    moves = len(step.path) - 1
    text = "1 move" if moves == 1 else f"{moves} moves"
    cost = path_cost(step.path)
    if cost != moves:   #only differs when the path uses diagonal moves
        text += f", cost {number(cost)}"
    return text


def cost_text(step):  #the numbers an informed search ranks tiles by
    if step.heuristic_value is None:
        return None
    if step.g_value is None:
        return f"h = {number(step.heuristic_value)}"
    f = step.g_value + step.heuristic_value
    return f"f = {number(f)} (g {number(step.g_value)} + h {number(step.heuristic_value)})"


def measurement_lines(measurement):  #measured metrics of a finished single run, for the tree window
    if not measurement:
        return []
    t_mean, t_std, t_min, t_max = measurement["time_ms"]
    lines = [
        f"-- Measured (headless, {measurement['repeats']} runs) --",
        f"Runtime: {t_mean:.3f} ms +/- {t_std:.3f}",
        f"  best {t_min:.3f}, worst {t_max:.3f} ms",
        f"Memory peak: {measurement['memory_kib']:.1f} KiB",
        f"Footprint: {measurement['peak_footprint']} "
        f"(frontier {measurement['peak_frontier']} + explored {measurement['peak_explored']})",
        f"Expanded: {measurement['expanded']}  Generated: {measurement['generated']}",
        f"Branching b: avg {measurement['branching_avg']:.2f}, max {measurement['branching_max']}",
    ]
    if measurement["ebf"] is not None:
        lines.append(f"Effective b*: {measurement['ebf']:.3f}")
    if measurement["found"]:
        lines.append(f"Depth: {measurement['moves']}  Cost: {number(measurement['cost'])}")
    if measurement["optimality_ratio"] is not None:
        lines.append(f"Optimality C*/C: {measurement['optimality_ratio']:.3f} (C* = {number(measurement['optimal_cost'])})")
    return lines


def stats_line(step, search_name, measurement=None):  #one line summary shown above the grid
    parts = [search_name]
    if step.status == SearchStatus.FOUND:
        parts.append(f"Path: {path_text(step)}")
    parts.append(f"States searched: {step.expanded}")
    if measurement and step.status != SearchStatus.RUNNING:
        parts.append(f"Time: {measurement['time_ms'][0]:.3f} ms")
    if step.depth_limit is not None:
        parts.append(f"Depth limit: {step.depth_limit}")
    if step.status == SearchStatus.RUNNING:
        costs = cost_text(step)
        if costs:
            parts.append(costs)
        parts.append(f"Frontier: {len(step.frontier)}")
    return "  |  ".join(parts)


def stats_list(step, search_name, measurement=None):  #one fact per line, shown in the tree window
    lines = [
        f"Search: {search_name}",
        f"Status: {STATUS_TEXT[step.status]}",
        f"States searched: {step.expanded}",
        f"Frontier: {len(step.frontier)}",
        f"Tree nodes: {step.tree_size}",
        f"Path length: {path_text(step)}",
    ]
    extras = []   #inserted after Status
    if step.depth_limit is not None:
        extras.append(f"Depth limit: {step.depth_limit}")
    if step.g_value is not None:
        extras.append(f"f = g + h: {number(step.g_value + step.heuristic_value)}")
        extras.append(f"g (cost so far): {number(step.g_value)}")
    if step.heuristic_value is not None:
        extras.append(f"h (estimate to goal): {number(step.heuristic_value)}")
    lines[2:2] = extras
    return lines + measurement_lines(measurement)


class ResultHeader:  #result message and stats centered above the grid
    def __init__(self):
        self.message_font = pygame.font.Font(None, 40)
        self.stats_fonts = [pygame.font.Font(None, size) for size in STATS_FONT_SIZES]

    def _render_stats(self, text, max_width):  #largest font that fits, the smallest one otherwise
        for font in self.stats_fonts:
            stats = font.render(text, True, STATS_COLOR)
            if stats.get_width() <= max_width:
                break
        return stats

    def draw(self, surface, step, search_name, grid_rect, max_width=None, measurement=None, measuring=False):
        if step is None:
            return
        center_x = grid_rect.centerx
        text = stats_line(step, search_name, measurement)
        if measuring:
            text += "  |  Measuring..."
        stats = self._render_stats(text, max_width or grid_rect.width)
        surface.blit(stats, stats.get_rect(center=(center_x, grid_rect.top - 14)))

        if step.status == SearchStatus.FOUND:
            message = self.message_font.render(STATUS_TEXT[step.status], True, FOUND_COLOR)
        elif step.status == SearchStatus.NO_PATH:
            message = self.message_font.render(STATUS_TEXT[step.status], True, NO_PATH_COLOR)
        else:
            return   #no headline while still searching
        surface.blit(message, message.get_rect(center=(center_x, grid_rect.top - 44)))
