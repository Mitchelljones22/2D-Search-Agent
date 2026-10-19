import pygame


class ActionButton:  
    def __init__(self, label, rect, color=(70, 70, 70), text_color=(255, 255, 255)):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.color = color
        self.text_color = text_color

    def draw(self, surface, font):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, (110, 110, 110), self.rect, 2)
        text = font.render(self.label, True, self.text_color)
        surface.blit(text, text.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)