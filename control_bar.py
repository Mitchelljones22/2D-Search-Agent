from enum import Enum

import pygame

BAR_HEIGHT = 70
BUTTON_SIZE = 44
BUTTON_GAP = 12
STOP_GAP = 32   #extra space so Stop sits apart from the playback buttons

ENABLED_FILL = (70, 70, 70)
DISABLED_FILL = (45, 45, 45)
BORDER = (110, 110, 110)
ICON = (255, 255, 255)
STOP_ICON = (220, 70, 70)
DISABLED_ICON = (100, 100, 100)


class PlayState(Enum):
    IDLE = 0      #editing allowed, no search running
    PLAYING = 1
    PAUSED = 2


# Icon outlines in units of the button size, centered on (0, 0)
_RIGHT_ARROW = [
    (-0.28, -0.06), (0.04, -0.06), (0.04, -0.2),
    (0.28, 0.0),
    (0.04, 0.2), (0.04, 0.06), (-0.28, 0.06),
]
_LEFT_ARROW = [(-x, y) for x, y in _RIGHT_ARROW]
_PLAY = [(-0.18, -0.25), (0.25, 0.0), (-0.18, 0.25)]
_PAUSE_BARS = [(-0.17, -0.25, 0.12, 0.5), (0.05, -0.25, 0.12, 0.5)]
_STOP = (-0.2, -0.2, 0.4, 0.4)


class IconButton:
    def __init__(self, icon, rect):
        self.icon = icon
        self.rect = pygame.Rect(rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface, enabled, icon=None):
        if enabled:
            pygame.draw.rect(surface, ENABLED_FILL, self.rect)
        else:
            pygame.draw.rect(surface, DISABLED_FILL, self.rect)
        pygame.draw.rect(surface, BORDER, self.rect, 2)

        if icon is None:
            icon = self.icon
        color = DISABLED_ICON
        if enabled:
            color = STOP_ICON if icon == "stop" else ICON
        self._draw_icon(surface, icon, color)

    def _point(self, x, y):  #converts icon units to screen pixels
        return (self.rect.centerx + x * self.rect.width, self.rect.centery + y * self.rect.height)

    def _box(self, x, y, w, h):
        left, top = self._point(x, y)
        return pygame.Rect(left, top, w * self.rect.width, h * self.rect.height)

    def _draw_icon(self, surface, icon, color):
        if icon == "left":
            pygame.draw.polygon(surface, color, [self._point(x, y) for x, y in _LEFT_ARROW])
        elif icon == "right":
            pygame.draw.polygon(surface, color, [self._point(x, y) for x, y in _RIGHT_ARROW])
        elif icon == "play":
            pygame.draw.polygon(surface, color, [self._point(x, y) for x, y in _PLAY])
        elif icon == "pause":
            for bar in _PAUSE_BARS:
                pygame.draw.rect(surface, color, self._box(*bar))
        elif icon == "stop":
            pygame.draw.rect(surface, color, self._box(*_STOP))


class ControlBar:  #playback controls centered under the grid
    ACTION_PLAY = "play"
    ACTION_PAUSE = "pause"
    ACTION_STEP_BACK = "step_back"
    ACTION_STEP_FORWARD = "step_forward"
    ACTION_STOP = "stop"

    def __init__(self, area):
        self.area = pygame.Rect(area)
        trio_width = 3 * BUTTON_SIZE + 2 * BUTTON_GAP
        left = self.area.centerx - trio_width // 2
        top = self.area.centery - BUTTON_SIZE // 2

        def slot(x):
            return (x, top, BUTTON_SIZE, BUTTON_SIZE)

        self.back_button = IconButton("left", slot(left))
        self.play_button = IconButton("play", slot(left + BUTTON_SIZE + BUTTON_GAP))
        self.forward_button = IconButton("right", slot(left + 2 * (BUTTON_SIZE + BUTTON_GAP)))
        self.stop_button = IconButton("stop", slot(left + trio_width + STOP_GAP))

    @staticmethod
    def _steps_enabled(state):  #stepping only makes sense while paused
        return state == PlayState.PAUSED

    @staticmethod
    def _stop_enabled(state):
        return state != PlayState.IDLE

    def handle_event(self, event, state):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None
        if self.play_button.is_clicked(event.pos):
            if state == PlayState.PLAYING:
                return self.ACTION_PAUSE
            return self.ACTION_PLAY
        if self._steps_enabled(state):
            if self.back_button.is_clicked(event.pos):
                return self.ACTION_STEP_BACK
            if self.forward_button.is_clicked(event.pos):
                return self.ACTION_STEP_FORWARD
        if self._stop_enabled(state) and self.stop_button.is_clicked(event.pos):
            return self.ACTION_STOP
        return None

    def draw(self, surface, state):
        steps_enabled = self._steps_enabled(state)
        self.back_button.draw(surface, steps_enabled)
        if state == PlayState.PLAYING:
            self.play_button.draw(surface, True, "pause")
        else:
            self.play_button.draw(surface, True, "play")
        self.forward_button.draw(surface, steps_enabled)
        self.stop_button.draw(surface, self._stop_enabled(state))
