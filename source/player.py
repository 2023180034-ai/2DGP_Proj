import math
from pathlib import Path
import time

import pico2d


FRAME_WIDTH = 128
FRAME_HEIGHT = 128
FRAME_COUNT = 12
RUN_FRAME_COUNT = 8
ANIMATION_FPS = 8
RUN_ANIMATION_FPS = 12
MOVE_SPEED = 300
RUN_SPEED_MULTIPLIER = 1.3

SPRITE_DIRECTORY = Path(__file__).resolve().parent.parent / "sprites" / "player"

_RUN_KEYS = {pico2d.SDLK_LSHIFT, pico2d.SDLK_RSHIFT}
_DIRECTION_KEYS = {
    pico2d.SDLK_DOWN: (0, -1, 0),
    pico2d.SDLK_RIGHT: (1, 0, 1),
    pico2d.SDLK_LEFT: (-1, 0, 2),
    pico2d.SDLK_UP: (0, 1, 3),
}
_SPRITE_ROW_BY_DIRECTION = (0, 2, 1, 3)


class Player:
    def __init__(self):
        self.idle_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_idle.png")
        )
        self.walk_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_walk.png")
        )
        self.run_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_run.png")
        )

        self.x = pico2d.get_canvas_width() / 2
        self.y = pico2d.get_canvas_height() / 2
        self.direction = 0
        self.pressed_keys = []
        self.run_pressed = False
        self.animation_time = 0
        self.last_update = time.perf_counter()
        self.moving = False

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key in _RUN_KEYS:
            self.run_pressed = True
        elif event.type == pico2d.SDL_KEYUP and event.key in _RUN_KEYS:
            self.run_pressed = False
        elif event.type == pico2d.SDL_KEYDOWN and event.key in _DIRECTION_KEYS:
            if event.key not in self.pressed_keys:
                self.pressed_keys.append(event.key)
        elif event.type == pico2d.SDL_KEYUP and event.key in _DIRECTION_KEYS:
            if event.key in self.pressed_keys:
                self.pressed_keys.remove(event.key)

    def update(self):
        now = time.perf_counter()
        delta_time = min(now - self.last_update, 0.1)
        self.last_update = now

        dx = 0
        dy = 0
        for key in self.pressed_keys:
            key_dx, key_dy, direction = _DIRECTION_KEYS[key]
            dx += key_dx
            dy += key_dy
            if key_dx:
                self.direction = direction
            elif key_dy:
                self.direction = direction

        self.moving = dx != 0 or dy != 0
        if self.moving:
            speed = MOVE_SPEED * (
                RUN_SPEED_MULTIPLIER if self.run_pressed else 1
            )
            distance = speed * delta_time / math.hypot(dx, dy)
            self.x += dx * distance
            self.y += dy * distance

        canvas_width = pico2d.get_canvas_width()
        canvas_height = pico2d.get_canvas_height()
        self.x = min(max(self.x, FRAME_WIDTH / 2), canvas_width - FRAME_WIDTH / 2)
        self.y = min(max(self.y, FRAME_HEIGHT / 2), canvas_height - FRAME_HEIGHT / 2)
        self.animation_time += delta_time

    def draw(self):
        if self.moving and self.run_pressed:
            sprite = self.run_sprite
            frame = int(self.animation_time * RUN_ANIMATION_FPS) % RUN_FRAME_COUNT
        elif self.moving:
            sprite = self.walk_sprite
            frame = int(self.animation_time * ANIMATION_FPS) % FRAME_COUNT
        else:
            sprite = self.idle_sprite
            frame = int(self.animation_time * ANIMATION_FPS) % FRAME_COUNT
        left = frame * FRAME_WIDTH
        bottom = _SPRITE_ROW_BY_DIRECTION[self.direction] * FRAME_HEIGHT
        sprite.clip_draw(
            left,
            bottom,
            FRAME_WIDTH,
            FRAME_HEIGHT,
            self.x,
            self.y,
            FRAME_WIDTH,
            FRAME_HEIGHT,
        )
