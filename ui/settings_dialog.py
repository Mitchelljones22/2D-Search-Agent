import pygame

from search.heuristics import FORMULAS, HEURISTICS, is_admissible
from ui.action_button import ActionButton

WIDTH = 480
HEIGHT = 430
ROW_HEIGHT = 28
PAD = 20

BACKGROUND = (50, 50, 50)
BORDER = (255, 215, 0)
TEXT = (235, 235, 235)
SECTION = (255, 215, 0)
NOTE = (160, 160, 160)
HOVER = (70, 70, 70)
GOOD = (90, 200, 110)
BAD = (235, 90, 90)

MOVEMENT_OPTIONS = [   #(diagonal, label)
    (False, "4-direction: N, S, E, W  (cost 1 per move)"),
    (True, "8-direction: adds diagonals  (cost √2 per diagonal)"),
]


class SettingsDialog:  #modal popup that picks the movement rules and the heuristic
    def __init__(self, diagonal=False, heuristic="Manhattan"):
        self.diagonal = diagonal
        self.heuristic = heuristic   #a HEURISTICS name
        self.open = False
        self.title_font = pygame.font.Font(None, 32)
        self.section_font = pygame.font.Font(None, 24)
        self.font = pygame.font.Font(None, 22)
        self.note_font = pygame.font.Font(None, 19)
        self.rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        self.done_button = ActionButton("Done", (0, 0, 120, 36))
        self.overlay = None
        self.set_area(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def set_area(self, window_rect):  #centers the dialog, call when the window is resized
        self.rect.center = window_rect.center
        self.done_button.rect.bottomright = (self.rect.right - PAD, self.rect.bottom - 16)
        self.overlay = pygame.Surface(window_rect.size, pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150))

    def _movement_row(self, index):
        return pygame.Rect(self.rect.x + 10, self.rect.y + 82 + index * ROW_HEIGHT, WIDTH - 20, ROW_HEIGHT)

    def _heuristic_row(self, index):
        return pygame.Rect(self.rect.x + 10, self.rect.y + 200 + index * ROW_HEIGHT, WIDTH - 20, ROW_HEIGHT)

    def handle_event(self, event):  #returns True when the dialog closes
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.open = False
            return True
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if self.done_button.is_clicked(event.pos) or not self.rect.collidepoint(event.pos):
            self.open = False
            return True
        for index, (diagonal, _) in enumerate(MOVEMENT_OPTIONS):
            if self._movement_row(index).collidepoint(event.pos):
                self.diagonal = diagonal
        for index, name in enumerate(HEURISTICS):
            if self._heuristic_row(index).collidepoint(event.pos):
                self.heuristic = name
        return False

    def _text(self, surface, text, font, color, pos):
        image = font.render(text, True, color)
        surface.blit(image, pos)
        return image

    def _radio(self, surface, row, selected):  #radio circle at the left of the row, hover highlight behind it
        if row.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(surface, HOVER, row)
        center = (row.x + 14, row.centery)
        pygame.draw.circle(surface, TEXT, center, 7, 2)
        if selected:
            pygame.draw.circle(surface, BORDER, center, 4)

    def draw(self, surface):
        if not self.open:
            return
        surface.blit(self.overlay, (0, 0))
        pygame.draw.rect(surface, BACKGROUND, self.rect)
        pygame.draw.rect(surface, BORDER, self.rect, 2)
        x = self.rect.x + PAD
        y = self.rect.y

        self._text(surface, "Search Settings", self.title_font, TEXT, (x, y + 16))

        self._text(surface, "Movement (all searches)", self.section_font, SECTION, (x, y + 60))
        for index, (diagonal, label) in enumerate(MOVEMENT_OPTIONS):
            row = self._movement_row(index)
            self._radio(surface, row, diagonal == self.diagonal)
            self._text(surface, label, self.font, TEXT, (row.x + 30, row.y + 7))
        self._text(surface, "Diagonal moves may not cut across the corner of an obstacle.",
                   self.note_font, NOTE, (x, y + 142))

        self._text(surface, "Heuristic h(n) (Best-First and A*)", self.section_font, SECTION, (x, y + 176))
        for index, name in enumerate(HEURISTICS):
            row = self._heuristic_row(index)
            self._radio(surface, row, name == self.heuristic)
            self._text(surface, name, self.font, TEXT, (row.x + 30, row.y + 7))
            self._text(surface, FORMULAS[name], self.font, NOTE, (row.x + 140, row.y + 7))
            if is_admissible(name, self.diagonal):
                self._text(surface, "admissible", self.font, GOOD, (row.x + 330, row.y + 7))
            else:
                self._text(surface, "overestimates", self.font, BAD, (row.x + 330, row.y + 7))
        self._text(surface, "Admissible = never overestimates the remaining cost,",
                   self.note_font, NOTE, (x, y + 348))
        self._text(surface, "so A* is guaranteed the cheapest path.",
                   self.note_font, NOTE, (x, y + 366))

        self.done_button.draw(surface, self.font)
