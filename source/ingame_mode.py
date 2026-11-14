from pathlib import Path
import time

import pico2d

from camera import Camera
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
        canvas_width = pico2d.get_canvas_width()
        canvas_height = pico2d.get_canvas_height()
        self.background_scale = max(
            canvas_width / background.w,
            canvas_height / background.h,
        )
        world_width = background.w * self.background_scale
        world_height = background.h * self.background_scale
        self.player = Player(world_width, world_height)
        self.camera = Camera(
            world_width,
            world_height,
            canvas_width,
            canvas_height,
        )
        self.camera.reset(self.player.x, self.player.y)
        self.last_camera_update = time.perf_counter()
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
        now = time.perf_counter()
        delta_time = min(now - self.last_camera_update, 0.1)
        self.last_camera_update = now
        self.camera.follow(self.player.x, self.player.y, delta_time)

    def draw(self):
        canvas_width = pico2d.get_canvas_width()
        canvas_height = pico2d.get_canvas_height()
        self.background.draw(
            self.background.w * self.background_scale / 2 - self.camera.x,
            self.background.h * self.background_scale / 2 - self.camera.y,
            self.background.w * self.background_scale,
            self.background.h * self.background_scale,
        )
        self.player.draw(self.camera.x, self.camera.y)
