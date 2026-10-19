import pygame

from tile_type import TILE_COLORS, TILE_LABELS  


class Button:
    def __init__(self, tile_type, rect, text_color=(255, 255, 255)):  
        self.tile_type = tile_type  
        self.label = TILE_LABELS[tile_type]  
        self.color = TILE_COLORS[tile_type]  
        self.text_color = text_color  
        self.rect = pygame.Rect(rect)

    def draw(self, surface, font, selected):
        pygame.draw.rect(surface, self.color, self.rect)
        if selected:
            pygame.draw.rect(surface, (255, 215, 0), self.rect, 4)  
        else:
            pygame.draw.rect(surface, (110, 110, 110), self.rect, 2)
        text = font.render(self.label, True, self.text_color)  
        surface.blit(text, text.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)