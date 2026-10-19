import pygame

from tile_map import TileMap
from sidebar import Sidebar
from obstacle_generator import ObstacleGenerator
from seed import random_seed, encode, decode, max_seed_digits
from graph import Graph
from tree import build_preview_tree
from tree_view import TreeView
from control_bar import ControlBar, PlayState, BAR_HEIGHT
from agent import SearchAgent
from search import SEARCHES
from search_report import HEADER_HEIGHT, ResultHeader

DEFAULT_COLS = 15   #15x15 is the assignment's default test case
DEFAULT_ROWS = 15
DEFAULT_DENSITY_PERCENT = 25  
STEP_MS = 350   #time between agent steps while playing


def show_seed(tile_map, sidebar):
    sidebar.set_seed(encode(tile_map))


def rebuild_graph(tile_map, graph, tree_view):
    graph.build(tile_map)
    if tile_map.start_tile is None:
        tree_view.render(None)
    else:
        tree_view.render(build_preview_tree(graph, tile_map.start_tile))


def randomize(tile_map, sidebar, graph, tree_view):
    cols, rows = sidebar.get_grid_size()  
    tile_map.resize(cols, rows)  
    ObstacleGenerator(sidebar.get_density(), random_seed()).generate(tile_map)  
    show_seed(tile_map, sidebar)
    rebuild_graph(tile_map, graph, tree_view)


def load_seed(tile_map, sidebar, graph, tree_view):
    cols, rows = sidebar.get_grid_size()  
    tile_types = decode(sidebar.get_seed(), cols, rows)  
    if tile_types is None:
        return
    tile_map.resize(cols, rows)  
    tile_map.apply_types(tile_types)
    show_seed(tile_map, sidebar)
    rebuild_graph(tile_map, graph, tree_view)


def apply_control(action, state, tile_map, graph, agent, sidebar):  #returns the next PlayState
    if action == ControlBar.ACTION_PLAY:
        if state == PlayState.IDLE:
            if tile_map.start_tile is None or tile_map.goal_tile is None:
                return state   #a search needs both a Start and a Goal
            agent.start(graph, tile_map.start_tile, tile_map.goal_tile, SEARCHES[sidebar.get_search()])
        return PlayState.PLAYING
    if action == ControlBar.ACTION_PAUSE:
        return PlayState.PAUSED
    if action == ControlBar.ACTION_STOP:
        agent.reset()
        return PlayState.IDLE
    if action == ControlBar.ACTION_STEP_FORWARD:
        agent.step_forward()
    elif action == ControlBar.ACTION_STEP_BACK:
        agent.step_back()
    return state


pygame.init()

screen = pygame.display.set_mode((800, 600))

pygame.display.set_caption("2D Search Agent")

clock = pygame.time.Clock()
running = True

tile_map = TileMap(DEFAULT_COLS, DEFAULT_ROWS)  
graph = Graph()
tree_view = TreeView(700, 500)
max_digits = max_seed_digits(Sidebar.MAX_GRID_SIZE, Sidebar.MAX_GRID_SIZE)  
sidebar = Sidebar(200, screen.get_height(), max_digits, DEFAULT_COLS, DEFAULT_ROWS, DEFAULT_DENSITY_PERCENT)  
main_width = screen.get_width() - sidebar.width
grid_height = screen.get_height() - BAR_HEIGHT
tile_map.set_area(pygame.Rect(sidebar.width, HEADER_HEIGHT, main_width, grid_height - HEADER_HEIGHT))
result_header = ResultHeader()
control_bar = ControlBar(pygame.Rect(sidebar.width, grid_height, main_width, BAR_HEIGHT))
play_state = PlayState.IDLE
agent = SearchAgent()
step_timer = 0
tree_shown = None   #agent step index the tree window is showing, None for the preview
randomize(tile_map, sidebar, graph, tree_view)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if getattr(event, "window", None) is tree_view.window:
            continue

        if play_state == PlayState.IDLE:   #sidebar and tiles are locked while a search runs
            action = sidebar.handle_event(event)
            if action == Sidebar.ACTION_NEW_SEED:
                randomize(tile_map, sidebar, graph, tree_view)
            elif action == Sidebar.ACTION_GENERATE:
                load_seed(tile_map, sidebar, graph, tree_view)

            tile_edited = tile_map.handle_event(event, screen, sidebar.selected_button)
            if tile_edited:
                show_seed(tile_map, sidebar)
                rebuild_graph(tile_map, graph, tree_view)

        control_action = control_bar.handle_event(event, play_state)
        play_state = apply_control(control_action, play_state, tile_map, graph, agent, sidebar)

    elapsed = clock.tick(60)
    if play_state == PlayState.PLAYING:
        step_timer += elapsed
        if step_timer >= STEP_MS:
            step_timer = 0
            agent.step_forward()
        if agent.at_end:   #search is over, pause so the user can step back through it
            play_state = PlayState.PAUSED
    else:
        step_timer = 0

    shown = agent.index if agent.active else None
    if shown != tree_shown:   #redraw the tree only when the step changes, rendering it is slow
        tree_shown = shown
        if agent.active:
            tree_view.render(agent.current_step.tree, agent.current_step, agent.search_name)
        else:
            rebuild_graph(tile_map, graph, tree_view)

    screen.fill((30, 30, 30))
    tile_map.draw(screen, agent.current_step)
    result_header.draw(screen, agent.current_step, agent.search_name, tile_map.get_rect(screen))
    sidebar.draw(screen, play_state != PlayState.IDLE)
    control_bar.draw(screen, play_state)
    pygame.display.flip()
    tree_view.draw()

pygame.quit()