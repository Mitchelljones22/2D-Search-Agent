import pygame

from action_button import ActionButton
from button import Button
from textbox import TextBox
from tile_type import TileType


class Sidebar:
    ACTION_NEW_SEED = "new_seed"
    ACTION_GENERATE = "generate"
    MAX_GRID_SIZE = 30  
    MAX_DENSITY_PERCENT = 100  

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
        self.cols_box = TextBox((20, 280, half_width, 40), self.seed_font, 2, 0, self.MAX_GRID_SIZE)  
        self.rows_box = TextBox((20 + half_width + gap, 280, half_width, 40), self.seed_font, 2, 0, self.MAX_GRID_SIZE)  
        self.density_box = TextBox((20, 360, content_width, 40), self.seed_font, 3, 0, self.MAX_DENSITY_PERCENT)  
        self.cols_box.set_value(cols)  
        self.rows_box.set_value(rows)  
        self.density_box.set_value(density_percent)  

        seed_row_y = height - 120
        self.seed_box = TextBox((20, seed_row_y, box_width, 40), self.seed_font, seed_max_length)
        self.generate_button = ActionButton(
            "Generate",
            (20 + box_width + gap, seed_row_y, content_width - box_width - gap, 40),
        )
        self.new_seed_button = ActionButton("New Seed", (20, height - 60, content_width, 40))

        self.lock_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self.lock_overlay.fill((30, 30, 30, 170))

    def set_seed(self, seed):
        self.seed_box.set_value(seed)

    def get_seed(self):
        return self.seed_box.get_value()

    def get_grid_size(self):  
        return self.cols_box.get_value(), self.rows_box.get_value()  

    def get_density(self): #returns 0.0 to 1.0
        return self.density_box.get_value() / 100  

    def handle_event(self, event):
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
        self.seed_box.draw(surface)
        self.generate_button.draw(surface, self.seed_font)
        self.new_seed_button.draw(surface, self.font)
        if locked:
            surface.blit(self.lock_overlay, (0, 0))
