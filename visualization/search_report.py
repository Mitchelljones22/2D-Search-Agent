"""Human readable results for a SearchStep, shared by the grid header and the tree view."""
import pygame

from search.algorithms import SearchStatus

HEADER_HEIGHT = 70   #space reserved above the grid for the result text
FOUND_COLOR = (60, 200, 90)
NO_PATH_COLOR = (230, 80, 80)
STATS_COLOR = (220, 220, 220)

STATUS_TEXT = {
    SearchStatus.RUNNING: "Searching",
    SearchStatus.FOUND: "Goal Found!",
    SearchStatus.NO_PATH: "No Path Found",
}


def path_text(step):  #path length in moves, the path list also holds the Start tile
    if step.status != SearchStatus.FOUND:
        return "-"
    moves = len(step.path) - 1
    if moves == 1:
        return "1 move"
    return f"{moves} moves"


def stats_line(step, search_name):  #one line summary shown above the grid
    parts = [search_name]
    if step.status == SearchStatus.FOUND:
        parts.append(f"Path: {path_text(step)}")
    parts.append(f"States searched: {step.expanded}")
    if step.status == SearchStatus.RUNNING:
        parts.append(f"Frontier: {len(step.frontier)}")
    return "   |   ".join(parts)


def stats_list(step, search_name):  #one fact per line, shown in the tree window
    return [
        f"Search: {search_name}",
        f"Status: {STATUS_TEXT[step.status]}",
        f"States searched: {step.expanded}",
        f"Frontier: {len(step.frontier)}",
        f"Tree nodes: {step.tree_size}",
        f"Path length: {path_text(step)}",
    ]


class ResultHeader:  #result message and stats centered above the grid
    def __init__(self):
        self.message_font = pygame.font.Font(None, 40)
        self.stats_font = pygame.font.Font(None, 24)

    def draw(self, surface, step, search_name, grid_rect):
        if step is None:
            return
        center_x = grid_rect.centerx
        stats = self.stats_font.render(stats_line(step, search_name), True, STATS_COLOR)
        surface.blit(stats, stats.get_rect(center=(center_x, grid_rect.top - 14)))

        if step.status == SearchStatus.FOUND:
            message = self.message_font.render(STATUS_TEXT[step.status], True, FOUND_COLOR)
        elif step.status == SearchStatus.NO_PATH:
            message = self.message_font.render(STATUS_TEXT[step.status], True, NO_PATH_COLOR)
        else:
            return   #no headline while still searching
        surface.blit(message, message.get_rect(center=(center_x, grid_rect.top - 44)))
