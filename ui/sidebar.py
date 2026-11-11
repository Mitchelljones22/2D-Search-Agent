from pathlib import Path

import pygame

from ui.action_button import ActionButton
from ui.button import Button
from ui.dropdown import Dropdown
from ui.textbox import TextBox
from environment.tile_type import TileType
from search.algorithms import SEARCHES

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent / "experiments"   #test scripts listed in Batch mode

class Sidebar:
    ACTION_NEW_SEED = "new_seed"
    ACTION_GENERATE = "generate"
    ACTION_SETTINGS = "settings"
    MODE_SINGLE = "Single"   #one method on the current map, animated, then measured
    MODE_BATCH = "Batch"     #every method, measured in a background process, results window
    CURRENT_MAP = "Current map"   #batch source: the map on screen instead of a test script
    MIN_GRID_SIZE = 2   #smallest grid that fits both a Start and a Goal
    MAX_GRID_SIZE = 1000   #seeds store up to 1023 per side
    MAX_DENSITY_PERCENT = 100
    MIN_HEIGHT = 680   #seed row is pinned to the bottom, this keeps it below the Search Settings button

    def __init__(self, width, height, seed_max_length, cols, rows, density_percent):  
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 28)
        self.seed_font = pygame.font.Font(None, 22)
        self.selected_button = None
        self.buttons = [
            Button(TileType.START, (20, 20, width - 40, 40)),
            Button(TileType.GOAL, (20, 80, width - 40, 40)),
            Button(TileType.OBSTACLE, (20, 140, width - 40, 40)),
            Button(TileType.TRAVERSABLE, (20, 200, width - 40, 40), (0, 0, 0)),
        ]

        content_width = width - 40
        box_width = 80
        gap = 5

        half_width = (content_width - gap) // 2  
        self.size_label_pos = (20, 258)  
        self.density_label_pos = (20, 338)  
        self.cols_box = TextBox((20, 280, half_width, 40), self.seed_font, len(str(self.MAX_GRID_SIZE)), self.MIN_GRID_SIZE, self.MAX_GRID_SIZE)
        self.rows_box = TextBox((20 + half_width + gap, 280, half_width, 40), self.seed_font, len(str(self.MAX_GRID_SIZE)), self.MIN_GRID_SIZE, self.MAX_GRID_SIZE)
        self.density_box = TextBox((20, 360, content_width, 40), self.seed_font, 3, 0, self.MAX_DENSITY_PERCENT)  
        self.cols_box.set_value(cols)  
        self.rows_box.set_value(rows)  
        self.density_box.set_value(density_percent)  

        self.search_label_pos = (20, 410)
        self.mode = self.MODE_SINGLE
        self.mode_buttons = [
            ActionButton(self.MODE_SINGLE, (20, 428, half_width, 30)),
            ActionButton(self.MODE_BATCH, (20 + half_width + gap, 428, half_width, 30)),
        ]
        self.dropdown_rect = (20, 464, content_width, 36)
        self.search_dropdown = Dropdown(SEARCHES.keys(), self.dropdown_rect)
        self.batch_dropdown = Dropdown(self._batch_sources(), self.dropdown_rect)
        self.settings_button = ActionButton("Search Settings", (20, 508, content_width, 36))

        self.seed_box = TextBox((20, 0, box_width, 40), self.seed_font, seed_max_length)
        self.generate_button = ActionButton("Generate", (20 + box_width + gap, 0, content_width - box_width - gap, 40))
        self.new_seed_button = ActionButton("New Seed", (20, 0, content_width, 40))
        self.resize(height)

    def resize(self, height):  #keeps the seed row and New Seed pinned to the bottom of the window
        self.height = max(height, self.MIN_HEIGHT)
        self.seed_box.rect.y = self.height - 120
        self.generate_button.rect.y = self.height - 120
        self.new_seed_button.rect.y = self.height - 60
        self.search_dropdown.max_bottom = self.height
        self.batch_dropdown.max_bottom = self.height
        self.lock_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.lock_overlay.fill((30, 30, 30, 170))

    def set_seed(self, seed):
        self.seed_box.set_value(seed)

    def get_seed(self):
        return self.seed_box.get_value()

    def get_grid_size(self):  
        return self.cols_box.get_value(), self.rows_box.get_value()  

    def set_grid_size(self, cols, rows):
        self.cols_box.set_value(cols)
        self.rows_box.set_value(rows)

    def get_density(self): #returns 0.0 to 1.0
        return self.density_box.get_value() / 100  

    def get_search(self):  #a key of SEARCHES, e.g. "BFS"
        return self.search_dropdown.selected

    def get_batch_source(self):  #CURRENT_MAP, or the path of a test script
        if self.batch_dropdown.selected == self.CURRENT_MAP:
            return self.CURRENT_MAP
        return EXPERIMENTS_DIR / f"{self.batch_dropdown.selected}.json"

    @classmethod
    def _batch_sources(cls):
        return [cls.CURRENT_MAP] + sorted(path.stem for path in EXPERIMENTS_DIR.glob("*.json"))

    def _set_mode(self, mode):
        self.mode = mode
        if mode == self.MODE_BATCH:   #pick up scripts added since the app started, keep the choice
            previous = self.batch_dropdown.selected
            sources = self._batch_sources()
            self.batch_dropdown = Dropdown(sources, self.dropdown_rect, previous if previous in sources else None)
            self.batch_dropdown.max_bottom = self.height

    @property
    def _active_dropdown(self):
        return self.batch_dropdown if self.mode == self.MODE_BATCH else self.search_dropdown

    def handle_event(self, event):
        if self._active_dropdown.handle_event(event):   #open list overlaps the widgets below, so it gets the click first
            return None
        self.cols_box.handle_event(event)  
        self.rows_box.handle_event(event)  
        self.density_box.handle_event(event)  
        self.seed_box.handle_event(event)
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None
        if self.new_seed_button.is_clicked(event.pos):
            return self.ACTION_NEW_SEED
        if self.generate_button.is_clicked(event.pos):
            return self.ACTION_GENERATE
        if self.settings_button.is_clicked(event.pos):
            return self.ACTION_SETTINGS
        for button in self.mode_buttons:
            if button.is_clicked(event.pos) and button.label != self.mode:
                self._set_mode(button.label)
        for button in self.buttons:
            if button.is_clicked(event.pos):
                if self.selected_button == button.tile_type:
                    self.selected_button = None
                else:
                    self.selected_button = button.tile_type
        return None

    def _draw_label(self, surface, text, pos):  
        label = self.seed_font.render(text, True, (200, 200, 200))  
        surface.blit(label, pos)  

    def draw(self, surface, locked=False):   #locked greys out the sidebar during a search
        dropdown = self._active_dropdown
        if locked:
            dropdown.open = False
        pygame.draw.rect(surface, (50, 50, 50), (0, 0, self.width, self.height))
        for button in self.buttons:
            if button.tile_type == self.selected_button:
                button.draw(surface, self.font, True)
            else:
                button.draw(surface, self.font, False)
        self._draw_label(surface, "Grid Size (X, Y)", self.size_label_pos)  
        self.cols_box.draw(surface)  
        self.rows_box.draw(surface)  
        self._draw_label(surface, "Obstacle Density (%)", self.density_label_pos)  
        self.density_box.draw(surface)  
        self._draw_label(surface, "Evaluation Mode", self.search_label_pos)
        for button in self.mode_buttons:
            button.draw(surface, self.seed_font, button.label == self.mode)
        dropdown.draw(surface, self.font)
        self.settings_button.draw(surface, self.seed_font)
        self.seed_box.draw(surface)
        self.generate_button.draw(surface, self.seed_font)
        self.new_seed_button.draw(surface, self.font)
        dropdown.draw_list(surface, self.font)   #last so the open list covers the seed row
        if locked:
            surface.blit(self.lock_overlay, (0, 0))
