import pygame


class Dropdown:  #collapsed box showing the selected option, click to open a list of the rest below it
    def __init__(self, options, rect, selected=None, color=(70, 70, 70), text_color=(255, 255, 255)):
        self.options = list(options)
        self.rect = pygame.Rect(rect)
        self.selected = selected if selected is not None else self.options[0]
        self.color = color
        self.text_color = text_color
        self.open = False

    def _option_rect(self, index):  #list rows sit directly under the collapsed box
        return pygame.Rect(self.rect.x, self.rect.bottom + index * self.rect.height, self.rect.width, self.rect.height)

    def handle_event(self, event):  #returns True when the dropdown used the click, so nothing under it reacts
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.open:
            self.open = False
            return True
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if self.rect.collidepoint(event.pos):
            self.open = not self.open
            return True
        if not self.open:
            return False
        self.open = False   #any click while open closes the list
        for index, option in enumerate(self.options):
            if self._option_rect(index).collidepoint(event.pos):
                self.selected = option
                return True
        return False

    def _draw_arrow(self, surface):
        cx = self.rect.right - 16
        cy = self.rect.centery
        if self.open:
            points = [(cx - 6, cy + 3), (cx + 6, cy + 3), (cx, cy - 4)]
        else:
            points = [(cx - 6, cy - 3), (cx + 6, cy - 3), (cx, cy + 4)]
        pygame.draw.polygon(surface, self.text_color, points)

    def draw(self, surface, font):  #draws the collapsed box only, call draw_list last so it is on top
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, (255, 215, 0) if self.open else (110, 110, 110), self.rect, 2)
        text = font.render(self.selected, True, self.text_color)
        surface.blit(text, text.get_rect(midleft=(self.rect.x + 12, self.rect.centery)))
        self._draw_arrow(surface)

    def draw_list(self, surface, font):
        if not self.open:
            return
        mouse = pygame.mouse.get_pos()
        for index, option in enumerate(self.options):
            row = self._option_rect(index)
            hovered = row.collidepoint(mouse)
            pygame.draw.rect(surface, (95, 95, 95) if hovered else (60, 60, 60), row)
            pygame.draw.rect(surface, (110, 110, 110), row, 1)
            if option == self.selected:
                pygame.draw.rect(surface, (255, 215, 0), row.inflate(-4, -4), 2)
            text = font.render(option, True, self.text_color)
            surface.blit(text, text.get_rect(midleft=(row.x + 12, row.centery)))
