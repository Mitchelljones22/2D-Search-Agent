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


def stats_line(step, search_name):  #one line summary shown above the grid
    parts = [search_name]
    if step.status == SearchStatus.FOUND:
        parts.append(f"Path: {path_text(step)}")
    parts.append(f"States searched: {step.expanded}")
    if step.depth_limit is not None:
        parts.append(f"Depth limit: {step.depth_limit}")
    if step.status == SearchStatus.RUNNING:
        costs = cost_text(step)
        if costs:
            parts.append(costs)
        parts.append(f"Frontier: {len(step.frontier)}")
    return "  |  ".join(parts)


def stats_list(step, search_name):  #one fact per line, shown in the tree window
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
    return lines


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

    def draw(self, surface, step, search_name, grid_rect, max_width=None):
        if step is None:
            return
        center_x = grid_rect.centerx
        stats = self._render_stats(stats_line(step, search_name), max_width or grid_rect.width)
        surface.blit(stats, stats.get_rect(center=(center_x, grid_rect.top - 14)))

        if step.status == SearchStatus.FOUND:
            message = self.message_font.render(STATUS_TEXT[step.status], True, FOUND_COLOR)
        elif step.status == SearchStatus.NO_PATH:
            message = self.message_font.render(STATUS_TEXT[step.status], True, NO_PATH_COLOR)
        else:
            return   #no headline while still searching
        surface.blit(message, message.get_rect(center=(center_x, grid_rect.top - 44)))
