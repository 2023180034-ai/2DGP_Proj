from pathlib import Path
import time

import pico2d


IDLE_FRAME_WIDTH = 64
IDLE_FRAME_HEIGHT = 64
IDLE_FRAME_COUNT = 6
IDLE_ANIMATION_FPS = 6
WALK_FRAME_COUNT = 8
WALK_ANIMATION_FPS = 8
CHASE_DELAY = 3.0
BOSS_MOVE_SPEED = 80
BASE_SCREEN_HEIGHT = 600
SPRITE_SCALE = 3
BOSS_COLLISION_RADIUS = 18

SPRITE_DIRECTORY = Path(__file__).resolve().parent.parent / "sprites" / "boss1"

DIRECTION_DOWN = 0
DIRECTION_LEFT = 1
DIRECTION_RIGHT = 2
DIRECTION_UP = 3


class Boss:
    def __init__(self, x, y, direction=DIRECTION_DOWN, world_scale=1.0):
        self.idle_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_idle.png")
        )
        self.walk_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_walk.png")
        )
        self.x = x
        self.y = y
        self.direction = direction
        self.world_scale = world_scale
        self.animation_time = 0
        self.walk_animation_time = 0
        self.elapsed_time = 0
        self.moving = False
        self.last_update = time.perf_counter()

    def update(self, player):
        now = time.perf_counter()
        delta_time = min(now - self.last_update, 0.1)
        self.last_update = now
        self.elapsed_time += delta_time
        self.animation_time += delta_time
        self.moving = False

        if self.elapsed_time >= CHASE_DELAY:
            dx = player.x - self.x
            dy = player.y - self.y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance:
                self.direction = (
                    DIRECTION_RIGHT if dx > 0 else DIRECTION_LEFT
                ) if abs(dx) > abs(dy) else (
                    DIRECTION_UP if dy > 0 else DIRECTION_DOWN
                )
                remaining_distance = (
                    distance - self.collision_radius - player.collision_radius
                )
                travel_distance = min(
                    BOSS_MOVE_SPEED * self.movement_scale * delta_time,
                    max(0, remaining_distance),
                )
                if travel_distance > 0:
                    self.x += dx / distance * travel_distance
                    self.y += dy / distance * travel_distance
                    self.moving = True

        if self.moving:
            self.walk_animation_time += delta_time
        else:
            self.walk_animation_time = 0

    @property
    def movement_scale(self):
        return (
            pico2d.get_canvas_height()
            / BASE_SCREEN_HEIGHT
            * self.world_scale
        )

    @property
    def collision_radius(self):
        return BOSS_COLLISION_RADIUS * SPRITE_SCALE * self.movement_scale

    def resolve_player_collision(self, player, previous_x, previous_y):
        move_x = player.x - previous_x
        move_y = player.y - previous_y
        move_length_squared = move_x * move_x + move_y * move_y
        if move_length_squared:
            closest_t = (
                (self.x - previous_x) * move_x
                + (self.y - previous_y) * move_y
            ) / move_length_squared
            closest_t = min(max(closest_t, 0), 1)
        else:
            closest_t = 0

        closest_x = previous_x + move_x * closest_t
        closest_y = previous_y + move_y * closest_t
        offset_x = closest_x - self.x
        offset_y = closest_y - self.y
        minimum_distance = self.collision_radius + player.collision_radius
        distance = (offset_x * offset_x + offset_y * offset_y) ** 0.5
        if distance >= minimum_distance:
            return

        if distance == 0:
            offset_x = previous_x - self.x
            offset_y = previous_y - self.y
            distance = (offset_x * offset_x + offset_y * offset_y) ** 0.5
            if distance == 0:
                offset_x = -move_x
                offset_y = -move_y
                distance = (offset_x * offset_x + offset_y * offset_y) ** 0.5
            if distance == 0:
                offset_x = 0
                offset_y = -1
                distance = 1

        player.x = self.x + offset_x / distance * minimum_distance
        player.y = self.y + offset_y / distance * minimum_distance

    def draw(self, camera_x=0, camera_y=0):
        if self.moving:
            sprite = self.walk_sprite
            frame = (
                int(self.walk_animation_time * WALK_ANIMATION_FPS)
                % WALK_FRAME_COUNT
            )
        else:
            sprite = self.idle_sprite
            frame = (
                int(self.animation_time * IDLE_ANIMATION_FPS)
                % IDLE_FRAME_COUNT
            )
        screen_scale = self.movement_scale * SPRITE_SCALE
        sprite.clip_draw(
            frame * IDLE_FRAME_WIDTH,
            self.direction * IDLE_FRAME_HEIGHT,
            IDLE_FRAME_WIDTH,
            IDLE_FRAME_HEIGHT,
            self.x - camera_x,
            self.y - camera_y,
            IDLE_FRAME_WIDTH * screen_scale,
            IDLE_FRAME_HEIGHT * screen_scale,
        )
