import networkx as nx
import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from search.algorithms import SearchStatus
from visualization.search_report import measurement_lines, stats_list
from visualization.step_colors import FRONTIER_COLOR, PATH_COLOR, tile_color

DPI = 100
CURRENT_OUTLINE = (170, 120, 0)   #dark gold ring marks the agent's node
MIN_SIZE = (300, 200)
STRIP_HEIGHT = 130   #pixels for the frontier chart under the tree


def _rgb(color):  #pygame 0-255 color to matplotlib 0-1 color
    r, g, b = color
    return (r / 255, g / 255, b / 255)


def _layout(root, children):
    """Tidy tree layout: leaves are spaced evenly left to right, each parent is centered
    over its children, so branches never cross. Returns ({node: (x, depth)}, leaf count)."""
    order = []   #preorder, children visited left to right
    depth = {root: 0}
    stack = [root]
    while stack:   #iterative, DFS trees can be deeper than Python's recursion limit
        node = stack.pop()
        order.append(node)
        for child in reversed(children[node]):
            depth[child] = depth[node] + 1
            stack.append(child)

    x = {}
    leaves = 0
    for node in order:   #preorder meets leaves in left to right order
        if not children[node]:
            x[node] = leaves
            leaves += 1
    for node in reversed(order):   #children are placed before their parent
        kids = children[node]
        if kids:
            x[node] = (x[kids[0]] + x[kids[-1]]) / 2

    positions = {}
    for node in order:
        positions[node] = ((x[node] + 1) / (leaves + 1), -depth[node])   #root on top
    return positions, leaves


class TreeView:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.window = pygame.Window("Search Tree", (width, height), resizable=True)
        self.window.minimum_size = MIN_SIZE
        self.surface = self.window.get_surface()
        self.image = None
        self._last_render = ((None, None, "", ""), {})   #redrawn at the new size when the window is resized

    def render(self, tree, step=None, search_name="", message="", history=None, index=None, measurement=None):
        """Call only when the tree changes; step limits it to that point in the search.
        history (all steps so far) and index add the frontier strip chart; measurement adds the
        measured metrics to the stats box."""
        self._last_render = ((tree, step, search_name, message),
                             {"history": history, "index": index, "measurement": measurement})
        figure = Figure(figsize=(self.width / DPI, self.height / DPI), dpi=DPI)
        canvas = FigureCanvasAgg(figure)
        show_chart = tree is not None and bool(history) and self.height >= 300
        chart_share = STRIP_HEIGHT / self.height if show_chart else 0
        axes = figure.add_axes([0, chart_share, 1, 1 - chart_share])
        axes.axis("off")

        if tree is None:
            axes.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, color="#555555")
        else:
            self._draw_tree(axes, tree, step)
            if step is not None:
                self._draw_stats(axes, step, search_name, measurement)
            if show_chart:
                self._draw_strip(figure, chart_share, history, index)

        canvas.draw()
        size = canvas.get_width_height()
        self.image = pygame.image.frombuffer(bytes(canvas.buffer_rgba()), size, "RGBA")

    def _draw_tree(self, axes, tree, step):
        nodes = tree.nodes()   #insertion order, so a prefix is the tree at an earlier step
        if step is not None:
            nodes = nodes[:step.tree_size]
        included = set(nodes)
        children = {node: [kid for kid in tree.children[node] if kid in included] for node in nodes}

        positions, leaves = _layout(tree.root, children)
        max_depth = -min(y for _, y in positions.values())

        nx_graph = nx.DiGraph()
        nx_graph.add_nodes_from(nodes)
        nx_graph.add_edges_from((tree.parent[node], node) for node in nodes[1:])

        path_edges = []
        if step is not None and step.status == SearchStatus.FOUND:
            path_edges = list(zip(step.path, step.path[1:]))

        colors = []
        outlines = []
        for node in nx_graph.nodes:
            colors.append(_rgb(tile_color(node, step)))
            if step is not None and node is step.current:
                outlines.append(_rgb(CURRENT_OUTLINE))
            else:
                outlines.append("black")

        across = self.width / (leaves + 1)
        down = self.height / (max_depth + 2)
        diameter = min(across, down) * 0.6
        diameter = max(3, min(diameter, 24))
        node_size = (diameter * 72 / DPI) ** 2

        nx.draw_networkx_edges(nx_graph, positions, ax=axes, arrows=False, edge_color="#999999")
        if path_edges:
            nx.draw_networkx_edges(
                nx_graph, positions, ax=axes, edgelist=path_edges, arrows=False,
                edge_color=[_rgb(PATH_COLOR)], width=3,
            )
        nx.draw_networkx_nodes(
            nx_graph, positions, ax=axes, node_color=colors,
            node_size=node_size, edgecolors=outlines, linewidths=[2.5 if o != "black" else 1.2 for o in outlines],
        )
        axes.set_xlim(0, 1)
        axes.set_ylim(-max_depth - 0.5, 0.5)

    def _draw_stats(self, axes, step, search_name, measurement=None):  #stats list in the top left corner
        box = {"facecolor": "white", "alpha": 0.85, "edgecolor": "#bbbbbb"}
        axes.text(   #this step, top left
            0.01, 0.99, "\n".join(stats_list(step, search_name)), transform=axes.transAxes,
            ha="left", va="top", fontsize=9, family="monospace", zorder=10, bbox=box,
        )
        if measurement:   #the whole search, measured headless, top right
            axes.text(
                0.99, 0.99, "\n".join(measurement_lines(measurement)), transform=axes.transAxes,
                ha="right", va="top", fontsize=8, family="monospace", zorder=10,
                bbox={**box, "facecolor": "#f4f8ff"},
            )

    def _draw_strip(self, figure, share, history, index):
        """Frontier and explored size at every step so far, with the shown step marked."""
        margin_x = 60 / self.width
        chart = figure.add_axes([margin_x, 36 / self.height, 1 - 1.4 * margin_x, share - 48 / self.height])
        steps = range(1, len(history) + 1)
        frontier = [len(step.frontier) for step in history]
        explored = [len(step.visited) for step in history]
        chart.fill_between(steps, frontier, color=_rgb(FRONTIER_COLOR), alpha=0.6, linewidth=0)
        chart.plot(steps, frontier, color="#3b7dd8", linewidth=1.2, label="frontier (open list)")
        chart.plot(steps, explored, color="#777777", linewidth=1.2, linestyle="--", label="explored (closed)")
        if index is not None and 0 <= index < len(history):
            chart.axvline(index + 1, color=_rgb(CURRENT_OUTLINE), linewidth=1.5)
            chart.plot([index + 1], [frontier[index]], marker="o", color=_rgb(CURRENT_OUTLINE), markersize=4)
        chart.set_xlim(1, max(len(history), 2))
        chart.set_ylim(bottom=0)
        chart.set_xlabel("step", fontsize=8, labelpad=1)
        chart.tick_params(labelsize=7)
        chart.grid(alpha=0.3)
        chart.legend(fontsize=7, loc="upper left", framealpha=0.8)

    def _fit_window(self):  #matplotlib draws at a fixed pixel size, so re-render after a resize
        width, height = self.window.size
        if (width, height) == (self.width, self.height):
            return
        self.width = width
        self.height = height
        self.surface = self.window.get_surface()   #the old surface is invalid after a resize
        args, options = self._last_render
        self.render(*args, **options)

    def draw(self):
        self._fit_window()
        self.surface.fill((255, 255, 255))
        if self.image is not None:
            self.surface.blit(self.image, (0, 0))
        self.window.flip()
