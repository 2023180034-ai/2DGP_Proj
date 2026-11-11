import pico2d

import game_framework
from player import Player


class IngameMode(game_framework.Mode):
    def enter(self):
        self.player = Player()

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            game_framework.quit()
        else:
            self.player.handle_event(event)

    def update(self):
        self.player.update()

    def draw(self):
        self.player.draw()
