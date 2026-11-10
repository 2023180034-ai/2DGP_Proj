import pico2d

import game_framework


class IngameMode(game_framework.Mode):
    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            game_framework.quit()

    def update(self):
        pass

    def draw(self):
        pass
