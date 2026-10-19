import networkx as nx
import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from tile_type import TILE_COLORS

DPI = 100


class TreeView:  
    def __init__(self, width, height):  
        self.width = width  
        self.height = height  
        self.window = pygame.Window("Search Tree", (width, height))  
        self.surface = self.window.get_surface()  
        self.image = None  

    def render(self, tree):  #Call only when the tree changes
        figure = Figure(figsize=(self.width / DPI, self.height / DPI), dpi=DPI)  
        canvas = FigureCanvasAgg(figure)  
        axes = figure.add_axes([0, 0, 1, 1])  
        axes.axis("off")  

        if tree is None:  
            axes.text(0.5, 0.5, "Place a Start tile", ha="center", va="center")  
        else:  
            self._draw_tree(axes, tree)  

        canvas.draw()  
        size = canvas.get_width_height()  
        self.image = pygame.image.frombuffer(bytes(canvas.buffer_rgba()), size, "RGBA")  

    def _draw_tree(self, axes, tree):  
        rows = {}  
        for node in tree.nodes():  
            rows.setdefault(tree.depth[node], []).append(node)  
        max_depth = max(rows)  

        positions = {}  
        widest = 1  
        for depth, row in rows.items():  
            widest = max(widest, len(row))  
            for index, node in enumerate(row):  
                positions[node] = ((index + 1) / (len(row) + 1), -depth)   #Root on top

        nx_graph = nx.DiGraph()  
        nx_graph.add_nodes_from(tree.nodes())  
        nx_graph.add_edges_from(tree.edges())  

        colors = []  
        for node in nx_graph.nodes:  
            r, g, b = TILE_COLORS[node.tile_type]  
            colors.append((r / 255, g / 255, b / 255))  

        across = self.width / (widest + 1)  
        down = self.height / (max_depth + 2)  
        diameter = min(across, down) * 0.6  
        if diameter > 24:  
            diameter = 24  
        node_size = (diameter * 72 / DPI) ** 2  

        nx.draw_networkx_edges(nx_graph, positions, ax=axes, arrows=False)  
        nx.draw_networkx_nodes(  
            nx_graph, positions, ax=axes, node_color=colors,  
            node_size=node_size, edgecolors="black",  
        )  
        axes.set_xlim(0, 1)  
        axes.set_ylim(-max_depth - 0.5, 0.5)  

    def draw(self):  
        self.surface.fill((255, 255, 255))  
        if self.image is not None:  
            self.surface.blit(self.image, (0, 0))  
        self.window.flip()  