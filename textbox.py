import pygame

import clipboard

DIGITS = "0123456789"
PADDING = 8
SELECT_COLOR = (150, 190, 255)


class TextBox:
    def __init__(self, rect, font, max_length, min_value=None, max_value=None):  
        self.rect = pygame.Rect(rect)
        self.font = font
        self.max_length = max_length
        self.min_value = min_value  
        self.max_value = max_value  
        self.text = ""
        self.active = False
        self.selected = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            was_active = self.active  
            self.active = self.rect.collidepoint(event.pos)
            self.selected = self.active
            if was_active and not self.active:  
                self._finish()  
        elif event.type == pygame.KEYDOWN and self.active:
            ctrl_held = event.mod & pygame.KMOD_CTRL
            if ctrl_held and event.key == pygame.K_a:
                self.selected = True
            elif ctrl_held and event.key == pygame.K_c:
                clipboard.put_text(self.text)
            elif ctrl_held and event.key == pygame.K_x:
                clipboard.put_text(self.text)
                self.text = ""
                self.selected = False
            elif ctrl_held and event.key == pygame.K_v:
                self._paste()
            elif event.key == pygame.K_DELETE:
                self.text = ""
                self.selected = False
            elif event.key == pygame.K_BACKSPACE:
                if self.selected:
                    self.text = ""
                    self.selected = False
                else:
                    self.text = self.text[:-1]
            elif len(event.unicode) == 1 and event.unicode in DIGITS:
                if self.selected:
                    self.text = ""
                    self.selected = False
                if len(self.text) < self.max_length:
                    self.text += event.unicode
                    self._clamp()  

    def _clamp(self):  
        if self.max_value is None or self.text == "":  
            return  
        value = int(self.text)  
        if value > self.max_value:  
            value = self.max_value  
        self.text = str(value)  

    def _finish(self):   #empty ranged box falls back to its minimum
        if self.min_value is not None and self.text == "":  
            self.text = str(self.min_value)  

    def _paste(self):
        digits = ""
        for character in clipboard.get_text():
            if character in DIGITS:
                digits += character
        self.text = digits[: self.max_length]
        self.selected = False
        self._clamp()  

    def get_value(self):
        if self.text == "":
            if self.min_value is not None:  
                return self.min_value  
            return None
        return int(self.text)

    def set_value(self, value):
        self.text = str(value)
        self.selected = False

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), self.rect)

        display = self.text
        while display and self.font.size(display)[0] > self.rect.width - 2 * PADDING:
            display = display[1:]
        text = self.font.render(display, True, (0, 0, 0))
        text_rect = text.get_rect(midleft=(self.rect.x + PADDING, self.rect.centery))

        if self.selected and display:
            pygame.draw.rect(surface, SELECT_COLOR, text_rect.inflate(4, 4))
        surface.blit(text, text_rect)

        if self.active:
            pygame.draw.rect(surface, (255, 215, 0), self.rect, 3)
        else:
            pygame.draw.rect(surface, (110, 110, 110), self.rect, 2)