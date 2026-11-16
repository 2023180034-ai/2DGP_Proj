from pathlib import Path
import time

import pico2d


IDLE_FRAME_WIDTH = 64
IDLE_FRAME_HEIGHT = 64
IDLE_FRAME_COUNT = 6
IDLE_ANIMATION_FPS = 6
IDLE_FOOT_Y = 59
WALK_FRAME_COUNT = 8
WALK_ANIMATION_FPS = 8
SWEEP_WARNING_FRAME_WIDTH = 80
SWEEP_WARNING_FRAME_HEIGHT = 80
SWEEP_WARNING_FRAME_COUNT = 8
SWEEP_WARNING_ANIMATION_FPS = 8
SWEEP_WARNING_DURATION = (
    SWEEP_WARNING_FRAME_COUNT / SWEEP_WARNING_ANIMATION_FPS
)
SHIELD_SWEEP_FRAME_WIDTH = 128
SHIELD_SWEEP_FRAME_HEIGHT = 128
SHIELD_SWEEP_FOOT_Y = 118
SHIELD_SWEEP_FRAME_COUNT = 10
SHIELD_SWEEP_ANIMATION_FPS = 12
SHIELD_SWEEP_COOLDOWN = 7.0
BOSS_STANDOFF_DISTANCE = 16
TIME_EPSILON = 1e-9
CHASE_DELAY = 3.0
BOSS_MOVE_SPEED = 80
BASE_SCREEN_HEIGHT = 600
SPRITE_SCALE = 3
BOSS_COLLISION_RADIUS = 12

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
        self.shield_sweep_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_shield_sweep.png")
        )
        self.sweep_warning_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_sweep_warning.png")
        )
        self.x = x
        self.y = y
        self.direction = direction
        self.world_scale = world_scale
        self.animation_time = 0
        self.walk_animation_time = 0
        self.elapsed_time = 0
        self.moving = False
        self.sweep_warning = False
        self.sweep_warning_elapsed = 0
        self.shield_sweeping = False
        self.shield_sweep_elapsed = 0
        self.shield_sweep_cooldown = 0
        self.last_update = time.perf_counter()

    def update(self, player):
        now = time.perf_counter()
        delta_time = min(now - self.last_update, 0.1)
        self.last_update = now
        self.elapsed_time += delta_time
        self.animation_time += delta_time
        self.shield_sweep_cooldown = max(
            0,
            self.shield_sweep_cooldown - delta_time,
        )
        if self.shield_sweep_cooldown < TIME_EPSILON:
            self.shield_sweep_cooldown = 0
        self.moving = False

        if self.shield_sweeping:
            self.shield_sweep_elapsed += delta_time
            if self.shield_sweep_elapsed + TIME_EPSILON >= (
                SHIELD_SWEEP_FRAME_COUNT / SHIELD_SWEEP_ANIMATION_FPS
            ):
                self.shield_sweeping = False
            return

        if self.sweep_warning:
            self.sweep_warning_elapsed += delta_time
            if (
                self.sweep_warning_elapsed + TIME_EPSILON
                >= SWEEP_WARNING_DURATION
            ):
                self.sweep_warning = False
                self.shield_sweeping = True
                self.shield_sweep_elapsed = 0
            return

        if self.elapsed_time >= CHASE_DELAY:
            dx = player.x - self.x
            dy = player.y - self.y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance:
                self._face_target(dx, dy)
                shield_sweep_range = (
                    self.collision_radius
                    + player.collision_radius
                    + BOSS_STANDOFF_DISTANCE * self.movement_scale
                )
                if (
                    distance <= shield_sweep_range
                    and self.shield_sweep_cooldown == 0
                ):
                    self.sweep_warning = True
                    self.sweep_warning_elapsed = 0
                    self.shield_sweep_cooldown = SHIELD_SWEEP_COOLDOWN
                else:
                    remaining_distance = (
                        distance
                        - self.collision_radius
                        - player.collision_radius
                        - BOSS_STANDOFF_DISTANCE * self.movement_scale
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

    def _face_target(self, dx, dy):
        if abs(dx) > abs(dy):
            self.direction = DIRECTION_RIGHT if dx > 0 else DIRECTION_LEFT
        else:
            self.direction = DIRECTION_UP if dy > 0 else DIRECTION_DOWN

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
        screen_scale = self.movement_scale * SPRITE_SCALE
        if self.sweep_warning:
            warning_frame = min(
                int(self.sweep_warning_elapsed * SWEEP_WARNING_ANIMATION_FPS),
                SWEEP_WARNING_FRAME_COUNT - 1,
            )
            warning_y = self.y + (
                IDLE_FRAME_HEIGHT / 2
                - IDLE_FOOT_Y
                + 8
            ) * screen_scale
            self.sweep_warning_sprite.clip_draw(
                warning_frame * SWEEP_WARNING_FRAME_WIDTH,
                self.direction * SWEEP_WARNING_FRAME_HEIGHT,
                SWEEP_WARNING_FRAME_WIDTH,
                SWEEP_WARNING_FRAME_HEIGHT,
                self.x - camera_x,
                warning_y - camera_y,
                SWEEP_WARNING_FRAME_WIDTH * screen_scale,
                SWEEP_WARNING_FRAME_HEIGHT * screen_scale,
            )

        if self.shield_sweeping:
            sprite = self.shield_sweep_sprite
            frame_width = SHIELD_SWEEP_FRAME_WIDTH
            frame_height = SHIELD_SWEEP_FRAME_HEIGHT
            frame = min(
                int(self.shield_sweep_elapsed * SHIELD_SWEEP_ANIMATION_FPS),
                SHIELD_SWEEP_FRAME_COUNT - 1,
            )
        elif self.moving:
            sprite = self.walk_sprite
            frame_width = IDLE_FRAME_WIDTH
            frame_height = IDLE_FRAME_HEIGHT
            frame = (
                int(self.walk_animation_time * WALK_ANIMATION_FPS)
                % WALK_FRAME_COUNT
            )
        else:
            sprite = self.idle_sprite
            frame_width = IDLE_FRAME_WIDTH
            frame_height = IDLE_FRAME_HEIGHT
            frame = (
                int(self.animation_time * IDLE_ANIMATION_FPS)
                % IDLE_FRAME_COUNT
            )
        draw_y = self.y
        if self.shield_sweeping:
            draw_y += (
                SHIELD_SWEEP_FOOT_Y
                - SHIELD_SWEEP_FRAME_HEIGHT / 2
                - IDLE_FOOT_Y
                + IDLE_FRAME_HEIGHT / 2
            ) * screen_scale
        sprite.clip_draw(
            frame * frame_width,
            self.direction * frame_height,
            frame_width,
            frame_height,
            self.x - camera_x,
            draw_y - camera_y,
            frame_width * screen_scale,
            frame_height * screen_scale,
        )
