from pathlib import Path

import pico2d

import game_framework


PANEL_IMAGE_PATH = (
    Path(__file__).resolve().parent.parent
    / "sprites"
    / "ui"
    / "map_select_panel.png"
)
BASE_SCREEN_HEIGHT = 600


class MapSelectMode(game_framework.Mode):
    def __init__(self, ingame_mode):
        self.ingame_mode = ingame_mode
        self.open_key_held = True

    def enter(self):
        self.panel = pico2d.load_image(str(PANEL_IMAGE_PATH))

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYUP and event.key == pico2d.SDLK_m:
            self.open_key_held = False
            return

        if event.type != pico2d.SDL_KEYDOWN:
            return

        if event.key == pico2d.SDLK_m:
            if not self.open_key_held:
                game_framework.pop_mode()
        elif event.key == pico2d.SDLK_ESCAPE:
            game_framework.pop_mode()
        else:
            return

    def update(self):
        pass

    def draw(self):
        self.ingame_mode.draw()

        scale = pico2d.get_canvas_height() / BASE_SCREEN_HEIGHT
        self.panel.draw(
            pico2d.get_canvas_width() / 2,
            pico2d.get_canvas_height() / 2,
            self.panel.w * scale,
            self.panel.h * scale,
        )
