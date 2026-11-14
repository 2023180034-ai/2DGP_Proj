from pathlib import Path

import pico2d

import game_framework
from map_select_mode import MapSelectMode
from player import Player


MAP_IMAGE_PATHS = {
    "test": Path(__file__).resolve().parent.parent
    / "sprites"
    / "map"
    / "test_map.png",
    "boss1": Path(__file__).resolve().parent.parent
    / "sprites"
    / "map"
    / "boss1_map.png",
}


class IngameMode(game_framework.Mode):
    def enter(self):
        self.reset_map("test")

    def reset_map(self, map_id):
        background = pico2d.load_image(str(MAP_IMAGE_PATHS[map_id]))
        self.player = Player()
        self.current_map_id = map_id
        self.background = background

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            game_framework.quit()
        elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_m:
            game_framework.push_mode(MapSelectMode(self))
        else:
            self.player.handle_event(event)

    def pause(self):
        self.player.clear_input()

    def update(self):
        self.player.update()

    def draw(self):
        canvas_width = pico2d.get_canvas_width()
        canvas_height = pico2d.get_canvas_height()
        scale = max(
            canvas_width / self.background.w,
            canvas_height / self.background.h,
        )
        self.background.draw(
            canvas_width / 2,
            canvas_height / 2,
            self.background.w * scale,
            self.background.h * scale,
        )
        self.player.draw()
