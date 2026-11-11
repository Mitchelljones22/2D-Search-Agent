import warnings

import pygame

from environment.tile_map import TileMap
from ui.sidebar import Sidebar
from ui.settings_dialog import SettingsDialog
from environment.obstacle_generator import ObstacleGenerator
from environment.seed import random_seed, encode, decode, max_seed_digits
from environment.graph import Graph
from visualization.tree_view import TreeView
from ui.control_bar import ControlBar, PlayState, BAR_HEIGHT
from search.agent import SearchAgent
from search.algorithms import SEARCHES
from visualization.search_report import HEADER_HEIGHT, ResultHeader
from visualization.results_window import ResultsWindow, draw_progress
from evaluation.batch_job import BatchJob

DEFAULT_COLS = 15   #15x15 is the assignment's default test case
DEFAULT_ROWS = 15
DEFAULT_DENSITY_PERCENT = 25  
STEP_MS = 350   #time between agent steps while playing at 1x speed


def show_seed(tile_map, sidebar):
    sidebar.set_seed(encode(tile_map))


def show_idle_tree(tile_map, tree_view):  #tree window message while no search is running
    if tile_map.start_tile is None or tile_map.goal_tile is None:
        tree_view.render(None, message="Place a Start and a Goal tile")
    else:
        tree_view.render(None, message="Press Play to start the search")


def rebuild_graph(tile_map, graph, tree_view):
    graph.build(tile_map)
    show_idle_tree(tile_map, tree_view)


def randomize(tile_map, sidebar, graph, tree_view):
    cols, rows = sidebar.get_grid_size()  
    tile_map.resize(cols, rows)  
    ObstacleGenerator(sidebar.get_density(), random_seed()).generate(tile_map)  
    show_seed(tile_map, sidebar)
    rebuild_graph(tile_map, graph, tree_view)


def load_seed(tile_map, sidebar, graph, tree_view):  #the seed holds the board size, the size boxes follow it
    decoded = decode(sidebar.get_seed(), Sidebar.MIN_GRID_SIZE, Sidebar.MAX_GRID_SIZE)
    if decoded is None:
        return
    cols, rows, tile_types = decoded
    sidebar.set_grid_size(cols, rows)
    tile_map.resize(cols, rows)  
    tile_map.apply_types(tile_types)
    show_seed(tile_map, sidebar)
    rebuild_graph(tile_map, graph, tree_view)


def layout(size, sidebar, tile_map, control_bar, settings_dialog):  #places every panel for the current window size
    width, height = size
    settings_dialog.set_area(pygame.Rect(0, 0, width, height))
    main_width = width - sidebar.width
    grid_height = height - BAR_HEIGHT
    sidebar.resize(height)
    tile_map.set_area(pygame.Rect(sidebar.width, HEADER_HEIGHT, main_width, grid_height - HEADER_HEIGHT))
    control_bar.set_area(pygame.Rect(sidebar.width, grid_height, main_width, BAR_HEIGHT))


def start_batch(tile_map, graph, sidebar):  #returns (BatchJob, None) or (None, error message)
    source = sidebar.get_batch_source()
    if source == Sidebar.CURRENT_MAP:   #every method and heuristic on the map on screen, current movement mode
        if tile_map.start_tile is None or tile_map.goal_tile is None:
            return None, "Place a Start and a Goal tile to batch the current map"
        movement = "8-dir" if graph.diagonal else "4-dir"
        return BatchJob("current_map", map_seed=encode(tile_map), movements=[movement]), None
    return BatchJob(source.stem, script=source), None


def draw_message(surface, text, area):  #one line of red text above the grid
    font = pygame.font.Font(None, 24)
    image = font.render(text, True, (235, 90, 90))
    surface.blit(image, image.get_rect(center=(area.centerx, area.top - 14)))


def apply_control(action, state, tile_map, graph, agent, sidebar, settings_dialog):  #returns the next PlayState
    if action == ControlBar.ACTION_PLAY:
        if state == PlayState.IDLE:
            if tile_map.start_tile is None or tile_map.goal_tile is None:
                return state   #a search needs both a Start and a Goal
            agent.start(graph, tile_map.start_tile, tile_map.goal_tile, SEARCHES[sidebar.get_search()],
                        settings_dialog.heuristic)
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

WINDOW_SIZE = (800, Sidebar.MIN_HEIGHT)
MIN_WINDOW_SIZE = (680, Sidebar.MIN_HEIGHT)   #wide enough for the speed buttons left of the playback controls
screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
with warnings.catch_warnings():   #the warning is about drawing through this Window, we only set its minimum size
    warnings.simplefilter("ignore", DeprecationWarning)
    pygame.Window.from_display_module().minimum_size = MIN_WINDOW_SIZE

pygame.display.set_caption("2D Search Agent")

clock = pygame.time.Clock()
running = True

tile_map = TileMap(DEFAULT_COLS, DEFAULT_ROWS)  
graph = Graph()
settings_dialog = SettingsDialog(graph.diagonal)
tree_view = TreeView(700, 500)
max_digits = max_seed_digits(Sidebar.MAX_GRID_SIZE, Sidebar.MAX_GRID_SIZE)  
sidebar = Sidebar(200, screen.get_height(), max_digits, DEFAULT_COLS, DEFAULT_ROWS, DEFAULT_DENSITY_PERCENT)  
result_header = ResultHeader()
control_bar = ControlBar(pygame.Rect(0, 0, 0, 0))
layout_size = None   #window size the layout was last built for
play_state = PlayState.IDLE
agent = SearchAgent()
step_timer = 0
tree_shown = None   #agent step index the tree window is showing, None when idle
measure_pending = False   #a finished search is shown with "Measuring..." for one frame, then measured
batch_job = None          #running batch comparison (separate process), None otherwise
batch_message = None      #why the last batch could not start or failed
results_window = None     #window showing the last batch's results
randomize(tile_map, sidebar, graph, tree_view)

while running:
    screen = pygame.display.get_surface()   #replaced by pygame when the window is resized
    if screen.get_size() != layout_size:
        layout_size = screen.get_size()
        layout(layout_size, sidebar, tile_map, control_bar, settings_dialog)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if getattr(event, "window", None) is tree_view.window:
            continue
        if results_window is not None and getattr(event, "window", None) is results_window.window:
            results_window.handle_event(event)
            continue

        if settings_dialog.open:   #modal, nothing else reacts until it closes
            if settings_dialog.handle_event(event) and settings_dialog.diagonal != graph.diagonal:
                graph.diagonal = settings_dialog.diagonal
                rebuild_graph(tile_map, graph, tree_view)
            continue

        if play_state == PlayState.IDLE:   #sidebar and tiles are locked while a search runs
            action = sidebar.handle_event(event)
            if action == Sidebar.ACTION_NEW_SEED:
                randomize(tile_map, sidebar, graph, tree_view)
            elif action == Sidebar.ACTION_GENERATE:
                load_seed(tile_map, sidebar, graph, tree_view)
            elif action == Sidebar.ACTION_SETTINGS:
                settings_dialog.open = True
                continue   #the click that opened the dialog is not a tile click

            tile_edited = tile_map.handle_event(event, screen, sidebar.selected_button)
            if tile_edited:
                show_seed(tile_map, sidebar)
                rebuild_graph(tile_map, graph, tree_view)

        control_action = control_bar.handle_event(event, play_state)
        if batch_job is not None:   #a batch is running, only Stop (cancel) does anything
            if control_action == ControlBar.ACTION_STOP:
                batch_job.cancel()
            continue
        if control_action == ControlBar.ACTION_PLAY and play_state == PlayState.IDLE and sidebar.mode == Sidebar.MODE_BATCH:
            batch_job, batch_message = start_batch(tile_map, graph, sidebar)
            if batch_job is not None:
                play_state = PlayState.PLAYING
            continue
        if control_action == ControlBar.ACTION_PLAY:
            batch_message = None
        play_state = apply_control(control_action, play_state, tile_map, graph, agent, sidebar, settings_dialog)

    if batch_job is not None and not batch_job.running:   #batch finished, cancelled, or failed
        results, batch_message = batch_job.outcome()
        if results is not None:
            if results_window is not None:
                results_window.destroy()
            results_window = ResultsWindow(results, batch_job.result_dir)
        batch_job = None
        play_state = PlayState.IDLE
    if results_window is not None and results_window.closed:
        results_window.destroy()
        results_window = None

    elapsed = clock.tick(60)
    if play_state == PlayState.PLAYING:
        step_timer += elapsed
        step_interval = STEP_MS / control_bar.speed
        if step_timer >= step_interval:
            step_timer = min(step_timer - step_interval, step_interval)   #keep leftover time so steps stay evenly paced
            agent.step_forward()
        if agent.at_end:   #search is over, pause so the user can step back through it
            play_state = PlayState.PAUSED
    else:
        step_timer = 0

    if agent.finished and agent.measurement is None:   #rerun the finished search headless to measure it
        if measure_pending:   #"Measuring..." has been drawn, now do the blocking work
            agent.measure()
            measure_pending = False
            tree_shown = None   #redraw the tree window stats with the measured metrics
        else:
            measure_pending = True
    else:
        measure_pending = False

    shown = agent.index if agent.active else None
    if shown != tree_shown:   #redraw the tree only when the step changes, rendering it is slow
        tree_shown = shown
        if agent.active:
            tree_view.render(agent.current_step.tree, agent.current_step, agent.search_name,
                             history=agent.history, index=agent.index, measurement=agent.measurement)
        else:
            show_idle_tree(tile_map, tree_view)

    screen.fill((30, 30, 30))
    tile_map.draw(screen, agent.current_step)
    result_header.draw(screen, agent.current_step, agent.search_name, tile_map.get_rect(screen),
                       screen.get_width() - sidebar.width - 20, agent.measurement, measure_pending)
    if batch_message and agent.current_step is None:
        draw_message(screen, batch_message, tile_map.get_rect(screen))
    sidebar.draw(screen, play_state != PlayState.IDLE)
    control_bar.draw(screen, play_state)
    if batch_job is not None:
        draw_progress(screen, tile_map.get_rect(screen), batch_job)
    settings_dialog.draw(screen)
    pygame.display.flip()
    tree_view.draw()
    if results_window is not None:
        results_window.draw()

if batch_job is not None:   #closing the app stops a running batch
    batch_job.kill()
pygame.quit()