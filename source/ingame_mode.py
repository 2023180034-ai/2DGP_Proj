from pathlib import Path
import time

import pico2d

from boss import Boss, DIRECTION_DOWN
from camera import Camera
import game_framework
from hp_bar import BOSS1_MAX_HP, PLAYER_MAX_HP, BossHpBar, PlayerHpBar
from map_select_mode import MapSelectMode
from player import DIRECTION_UP, Player


CAMERA_ZOOM = 1.15
BOSS1_WALL_BOTTOM_RATIO = 0.20
BOSS1_BOSS_POSITION_RATIO = 0.72

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
        ) * CAMERA_ZOOM
        world_width = background.w * self.background_scale
        world_height = background.h * self.background_scale
        spawn_x = world_width / 2
        spawn_y = world_height / 2
        spawn_direction = 0
        north_boundary = None
        boss = None
        if map_id == "boss1":
            spawn_y = world_height * 0.15
            spawn_direction = DIRECTION_UP
            north_boundary = world_height * (1 - BOSS1_WALL_BOTTOM_RATIO)
            boss = Boss(
                world_width / 2,
                world_height * BOSS1_BOSS_POSITION_RATIO,
                direction=DIRECTION_DOWN,
                world_scale=CAMERA_ZOOM,
            )

        self.player = Player(
            world_width,
            world_height,
            spawn_x=spawn_x,
            spawn_y=spawn_y,
            direction=spawn_direction,
            world_scale=CAMERA_ZOOM,
            north_boundary=north_boundary,
        )
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
        self.boss = boss
        self.player_hp_bar = PlayerHpBar(PLAYER_MAX_HP)
        self.boss_hp_bar = (
            BossHpBar(BOSS1_MAX_HP, name="보스 1")
            if boss is not None
            else None
        )

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
        now = time.perf_counter()
        delta_time = min(now - self.last_camera_update, 0.1)
        self.last_camera_update = now
        previous_player_x = self.player.x
        previous_player_y = self.player.y
        self.player.update()
        self.player_hp_bar.update(delta_time)
        if self.boss is not None:
            self.boss.update(self.player)
            self.boss.resolve_player_collision(
                self.player,
                previous_player_x,
                previous_player_y,
            )
            self.boss_hp_bar.update(delta_time)
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
        if self.boss is not None:
            self.boss.draw(self.camera.x, self.camera.y)
        self.player.draw(self.camera.x, self.camera.y)
        self.player_hp_bar.draw()
        if self.boss_hp_bar is not None:
            self.boss_hp_bar.draw()
