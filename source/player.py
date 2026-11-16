import math
from pathlib import Path
import time

import pico2d


FRAME_WIDTH = 128
FRAME_HEIGHT = 128
FRAME_COUNT = 12
RUN_FRAME_COUNT = 8
ROLL_FRAME_COUNT = 10
ATTACK_FRAME_COUNT = 12
ANIMATION_FPS = 8
RUN_ANIMATION_FPS = 12
ROLL_ANIMATION_FPS = 20
ATTACK_ANIMATION_FPS = 12
MOVE_SPEED = 300
RUN_SPEED_MULTIPLIER = 1.3
ATTACK_MOVE_SPEED_MULTIPLIER = 0.7
ROLL_DURATION = ROLL_FRAME_COUNT / ROLL_ANIMATION_FPS
ROLL_SPEED_MULTIPLIER = 2
ATTACK_DURATION = ATTACK_FRAME_COUNT / ATTACK_ANIMATION_FPS
BASE_SCREEN_HEIGHT = 600
DIRECTION_UP = 3
WALL_COLLISION_CLEARANCE = 32
PLAYER_COLLISION_RADIUS = 24

SPRITE_DIRECTORY = Path(__file__).resolve().parent.parent / "sprites" / "player"

_RUN_KEYS = {pico2d.SDLK_LSHIFT, pico2d.SDLK_RSHIFT}
_ROLL_KEY = pico2d.SDLK_SPACE
_ATTACK_KEY = pico2d.SDLK_z
_DIRECTION_KEYS = {
    pico2d.SDLK_DOWN: (0, -1, 0),
    pico2d.SDLK_RIGHT: (1, 0, 1),
    pico2d.SDLK_LEFT: (-1, 0, 2),
    pico2d.SDLK_UP: (0, 1, DIRECTION_UP),
}
_SPRITE_ROW_BY_DIRECTION = (0, 2, 1, 3)
_DIRECTION_VECTOR_BY_DIRECTION = (
    (0, -1),
    (1, 0),
    (-1, 0),
    (0, 1),
)


class Player:
    def __init__(
        self,
        world_width=None,
        world_height=None,
        spawn_x=None,
        spawn_y=None,
        direction=0,
        world_scale=1.0,
        north_boundary=None,
    ):
        self.idle_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_idle.png")
        )
        self.walk_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_walk.png")
        )
        self.run_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_run.png")
        )
        self.roll_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_roll.png")
        )
        self.attack_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_attack.png")
        )
        self.walk_attack_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_walk_attack.png")
        )

        self.world_width = (
            pico2d.get_canvas_width() if world_width is None else world_width
        )
        self.world_height = (
            pico2d.get_canvas_height() if world_height is None else world_height
        )
        self.world_scale = world_scale
        self.north_boundary = north_boundary
        self.x = self.world_width / 2 if spawn_x is None else spawn_x
        self.y = self.world_height / 2 if spawn_y is None else spawn_y
        self.direction = direction
        self.pressed_keys = []
        self.roll_key_held = False
        self.attack_key_held = False
        self.run_pressed = False
        self.animation_time = 0
        self.last_update = time.perf_counter()
        self.moving = False
        self.rolling = False
        self.roll_elapsed = 0
        self.roll_dx = 0
        self.roll_dy = 0
        self.attacking = False
        self.attack_elapsed = 0

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key == _ROLL_KEY:
            if not self.roll_key_held:
                self.roll_key_held = True
                self._start_roll()
        elif event.type == pico2d.SDL_KEYUP and event.key == _ROLL_KEY:
            self.roll_key_held = False
        elif event.type == pico2d.SDL_KEYDOWN and event.key == _ATTACK_KEY:
            if not self.attack_key_held:
                self.attack_key_held = True
                self._start_attack()
        elif event.type == pico2d.SDL_KEYUP and event.key == _ATTACK_KEY:
            self.attack_key_held = False
        elif event.type == pico2d.SDL_KEYDOWN and event.key in _RUN_KEYS:
            self.run_pressed = True
        elif event.type == pico2d.SDL_KEYUP and event.key in _RUN_KEYS:
            self.run_pressed = False
        elif event.type == pico2d.SDL_KEYDOWN and event.key in _DIRECTION_KEYS:
            if event.key not in self.pressed_keys:
                self.pressed_keys.append(event.key)
        elif event.type == pico2d.SDL_KEYUP and event.key in _DIRECTION_KEYS:
            if event.key in self.pressed_keys:
                self.pressed_keys.remove(event.key)

    def clear_input(self):
        self.pressed_keys.clear()
        self.roll_key_held = False
        self.attack_key_held = False
        self.run_pressed = False

    @property
    def is_invulnerable(self):
        return self.rolling

    @property
    def collision_radius(self):
        screen_scale = (
            pico2d.get_canvas_height() / BASE_SCREEN_HEIGHT * self.world_scale
        )
        return PLAYER_COLLISION_RADIUS * screen_scale

    def _start_roll(self):
        if self.rolling or self.attacking:
            return

        dx = 0
        dy = 0
        for key in self.pressed_keys:
            key_dx, key_dy, direction = _DIRECTION_KEYS[key]
            dx += key_dx
            dy += key_dy
            if key_dx or key_dy:
                self.direction = direction

        if dx == 0 and dy == 0:
            dx, dy = _DIRECTION_VECTOR_BY_DIRECTION[self.direction]

        distance = math.hypot(dx, dy)
        self.roll_dx = dx / distance
        self.roll_dy = dy / distance
        self.rolling = True
        self.roll_elapsed = 0

    def _start_attack(self):
        if self.rolling or self.attacking:
            return

        for key in self.pressed_keys:
            key_dx, key_dy, direction = _DIRECTION_KEYS[key]
            if key_dx or key_dy:
                self.direction = direction

        self.attacking = True
        self.attack_elapsed = 0

    def update(self):
        now = time.perf_counter()
        delta_time = min(now - self.last_update, 0.1)
        self.last_update = now
        screen_scale = (
            pico2d.get_canvas_height() / BASE_SCREEN_HEIGHT * self.world_scale
        )

        if self.rolling:
            roll_delta = min(delta_time, ROLL_DURATION - self.roll_elapsed)
            roll_speed = MOVE_SPEED * ROLL_SPEED_MULTIPLIER * screen_scale
            self.x += self.roll_dx * roll_speed * roll_delta
            self.y += self.roll_dy * roll_speed * roll_delta
            self.roll_elapsed += roll_delta
            if self.roll_elapsed >= ROLL_DURATION - 1e-9:
                self.roll_elapsed = ROLL_DURATION
                self.rolling = False
        else:
            dx = 0
            dy = 0
            for key in self.pressed_keys:
                key_dx, key_dy, direction = _DIRECTION_KEYS[key]
                dx += key_dx
                dy += key_dy
                if key_dx or key_dy:
                    self.direction = direction

            self.moving = dx != 0 or dy != 0
            if self.moving:
                if self.attacking:
                    speed_multiplier = ATTACK_MOVE_SPEED_MULTIPLIER
                else:
                    speed_multiplier = (
                        RUN_SPEED_MULTIPLIER if self.run_pressed else 1
                    )
                speed = MOVE_SPEED * speed_multiplier * screen_scale
                distance = speed * delta_time / math.hypot(dx, dy)
                self.x += dx * distance
                self.y += dy * distance

        if self.attacking:
            self.attack_elapsed += delta_time
            if self.attack_elapsed >= ATTACK_DURATION - 1e-9:
                self.attack_elapsed = ATTACK_DURATION
                self.attacking = False

        player_width = FRAME_WIDTH * screen_scale
        player_height = FRAME_HEIGHT * screen_scale
        max_y = self.world_height - player_height / 2
        if self.north_boundary is not None:
            wall_clearance = WALL_COLLISION_CLEARANCE * screen_scale
            max_y = min(max_y, self.north_boundary - wall_clearance)
        self.x = min(
            max(self.x, player_width / 2),
            self.world_width - player_width / 2,
        )
        self.y = min(
            max(self.y, player_height / 2),
            max_y,
        )
        self.animation_time += delta_time

    def draw(self, camera_x=0, camera_y=0):
        screen_scale = (
            pico2d.get_canvas_height() / BASE_SCREEN_HEIGHT * self.world_scale
        )
        if self.rolling:
            sprite = self.roll_sprite
            frame = min(
                int(self.roll_elapsed * ROLL_ANIMATION_FPS),
                ROLL_FRAME_COUNT - 1,
            )
        elif self.attacking:
            sprite = self.walk_attack_sprite if self.moving else self.attack_sprite
            frame = min(
                int(self.attack_elapsed * ATTACK_ANIMATION_FPS),
                ATTACK_FRAME_COUNT - 1,
            )
        elif self.moving and self.run_pressed:
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
            self.x - camera_x,
            self.y - camera_y,
            FRAME_WIDTH * screen_scale,
            FRAME_HEIGHT * screen_scale,
        )
