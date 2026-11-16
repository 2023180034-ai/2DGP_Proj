import math
from pathlib import Path
import pico2d

import direction as dirs


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
# 예고 이펙트는 반지름 34px 반원 고리, 칸 가운데 = 보스 발보다 8px 위
SWEEP_WARNING_CENTER_ABOVE_FOOT = 8
SWEEP_WARNING_OUTER_RADIUS = 34
SHIELD_SWEEP_FRAME_WIDTH = 128
SHIELD_SWEEP_FRAME_HEIGHT = 128
SHIELD_SWEEP_FOOT_Y = 118
SHIELD_SWEEP_FRAME_COUNT = 10
SHIELD_SWEEP_ANIMATION_FPS = 12
SHIELD_SWEEP_COOLDOWN = 7.0
SHIELD_SWEEP_ACTIVE_FRAME_START = 4
SHIELD_SWEEP_ACTIVE_FRAME_END = 6
BOSS1_SHIELD_SWEEP_DAMAGE = 50
SLAM_WARNING_FRAME_WIDTH = 128
SLAM_WARNING_FRAME_HEIGHT = 128
SLAM_WARNING_FRAME_COUNT = 8
SLAM_WARNING_ANIMATION_FPS = 8
SLAM_WARNING_DURATION = SLAM_WARNING_FRAME_COUNT / SLAM_WARNING_ANIMATION_FPS
SLAM_WARNING_FORWARD_OFFSET = 20
SLAM_WARNING_DEPTH = 110
SLAM_WARNING_START_HALF_WIDTH = 18
SLAM_WARNING_END_HALF_WIDTH = 50
SLAM_FRAME_WIDTH = 128
SLAM_FRAME_HEIGHT = 128
SLAM_FOOT_Y = 118
SLAM_FRAME_COUNT = 12
SLAM_ANIMATION_FPS = 12
SLAM_IMPACT_FRAME = 5
SLAM_IMPACT_FRAME_END = 6
SLAM_ERUPTION_FRAME_COUNT = 10
SLAM_ERUPTION_ANIMATION_FPS = 12
SLAM_ERUPTION_DURATION = (
    SLAM_ERUPTION_FRAME_COUNT / SLAM_ERUPTION_ANIMATION_FPS
)
SLAM_ERUPTION_DRAW_SCALE = 1.25
SLAM_COOLDOWN = 9.0
SLAM_MAX_RANGE = 256
BOSS1_SLAM_DAMAGE = 90
BOSS1_MAX_HP = 10_000
BOSS_STANDOFF_DISTANCE = 16
TIME_EPSILON = 1e-9
CHASE_DELAY = 3.0
BOSS_MOVE_SPEED = 80
BASE_SCREEN_HEIGHT = 600
SPRITE_SCALE = 3
BOSS_COLLISION_RADIUS = 12

SPRITE_DIRECTORY = Path(__file__).resolve().parent.parent / "sprites" / "boss1"



class Boss:
    def __init__(
        self,
        x,
        y,
        direction=dirs.DOWN,
        world_scale=1.0,
        max_hp=BOSS1_MAX_HP,
    ):
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
        self.shield_slam_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_shield_slam.png")
        )
        self.slam_warning_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_slam_warning.png")
        )
        self.slam_eruption_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_slam_eruption.png")
        )
        self.x = x
        self.y = y
        self.direction = direction
        self.max_hp = max_hp
        self.hp = max_hp
        self.aim_direction = dirs.VECTORS[direction]
        self.attack_direction = self.aim_direction
        self.attack_sprite_direction = direction
        self.world_scale = world_scale
        self.animation_time = 0
        self.walk_animation_time = 0
        self.elapsed_time = 0
        self.moving = False
        self.sweep_warning = False
        self.sweep_warning_elapsed = 0
        self.shield_sweeping = False
        self.shield_sweep_elapsed = 0
        self.shield_sweep_hit_applied = False
        self.shield_sweep_cooldown = 0
        self.slam_warning = False
        self.slam_warning_elapsed = 0
        self.slamming = False
        self.slam_elapsed = 0
        self.slam_hit_applied = False
        self.slam_impact_started = False
        self.slam_eruption = False
        self.slam_eruption_elapsed = 0
        self.slam_cooldown = 0

    def update(self, player, delta_time):
        self.elapsed_time += delta_time
        self.animation_time += delta_time
        self.shield_sweep_cooldown = max(
            0,
            self.shield_sweep_cooldown - delta_time,
        )
        self.slam_cooldown = max(0, self.slam_cooldown - delta_time)
        if self.shield_sweep_cooldown < TIME_EPSILON:
            self.shield_sweep_cooldown = 0
        if self.slam_cooldown < TIME_EPSILON:
            self.slam_cooldown = 0
        self.moving = False

        if self.slam_eruption:
            self.slam_eruption_elapsed += delta_time
            if self.slam_eruption_elapsed >= SLAM_ERUPTION_DURATION:
                self.slam_eruption = False

        if self.shield_sweeping:
            self.shield_sweep_elapsed += delta_time
            if self.shield_sweep_elapsed + TIME_EPSILON >= (
                SHIELD_SWEEP_FRAME_COUNT / SHIELD_SWEEP_ANIMATION_FPS
            ):
                self.shield_sweeping = False
            return

        if self.slamming:
            self.slam_elapsed += delta_time
            slam_frame = int(self.slam_elapsed * SLAM_ANIMATION_FPS)
            if not self.slam_impact_started and slam_frame >= SLAM_IMPACT_FRAME:
                self.slam_impact_started = True
                self.slam_eruption = True
                self.slam_eruption_elapsed = 0
            if self.slam_elapsed + TIME_EPSILON >= (
                SLAM_FRAME_COUNT / SLAM_ANIMATION_FPS
            ):
                self.slamming = False
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
                self.shield_sweep_hit_applied = False
            return

        if self.slam_warning:
            self.slam_warning_elapsed += delta_time
            if self.slam_warning_elapsed + TIME_EPSILON >= SLAM_WARNING_DURATION:
                self.slam_warning = False
                self.slamming = True
                self.slam_elapsed = 0
                self.slam_hit_applied = False
                self.slam_impact_started = False
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
                    self.attack_direction = self.aim_direction
                    self.attack_sprite_direction = self.direction
                    self.sweep_warning = True
                    self.sweep_warning_elapsed = 0
                    self.shield_sweep_cooldown = SHIELD_SWEEP_COOLDOWN
                elif (
                    distance > shield_sweep_range
                    and distance <= SLAM_MAX_RANGE * self.movement_scale
                    and self.slam_cooldown == 0
                ):
                    self.attack_direction = self.aim_direction
                    self.attack_sprite_direction = self.direction
                    self.slam_warning = True
                    self.slam_warning_elapsed = 0
                    self.slam_cooldown = SLAM_COOLDOWN
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
        distance = math.hypot(dx, dy)
        if not distance:
            return

        self.aim_direction = (dx / distance, dy / distance)
        if abs(dx) > abs(dy):
            self.direction = dirs.RIGHT if dx > 0 else dirs.LEFT
        else:
            self.direction = dirs.UP if dy > 0 else dirs.DOWN

    def _attack_rotation(self):
        aim_x, aim_y = self.attack_direction
        sprite_x, sprite_y = dirs.VECTORS[
            self.attack_sprite_direction
        ]
        rotation = math.atan2(aim_y, aim_x) - math.atan2(sprite_y, sprite_x)
        return (rotation + math.pi) % (2 * math.pi) - math.pi

    @property
    def is_dead(self):
        return self.hp <= 0

    def take_damage(self, amount):
        if self.is_dead:
            return False
        self.hp = max(0, self.hp - amount)
        return True

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

    @property
    def shield_sweep_hit_active(self):
        if not self.shield_sweeping or self.shield_sweep_hit_applied:
            return False
        frame = int(self.shield_sweep_elapsed * SHIELD_SWEEP_ANIMATION_FPS)
        return (
            SHIELD_SWEEP_ACTIVE_FRAME_START
            <= frame
            <= SHIELD_SWEEP_ACTIVE_FRAME_END
        )

    def _sweep_center(self):
        """휘두르기 예고 반원의 중심 (보스 발보다 조금 위)."""
        screen_scale = self.movement_scale * SPRITE_SCALE
        return self.x, self.y + (
            IDLE_FRAME_HEIGHT / 2
            - IDLE_FOOT_Y
            + SWEEP_WARNING_CENTER_ABOVE_FOOT
        ) * screen_scale

    def shield_sweep_hits(self, target):
        """예고로 보여준 반원 범위 안에 대상의 발이 닿으면 맞는다."""
        if not self.shield_sweep_hit_active:
            return False

        center_x, center_y = self._sweep_center()
        target_x, target_y = target.hitbox_center
        dx = target_x - center_x
        dy = target_y - center_y
        direction_x, direction_y = self.attack_direction
        target_radius = target.collision_radius
        reach = (
            SWEEP_WARNING_OUTER_RADIUS
            * self.movement_scale
            * SPRITE_SCALE
        )
        return (
            math.hypot(dx, dy) <= reach + target_radius
            and dx * direction_x + dy * direction_y >= -target_radius
        )

    def register_shield_sweep_hit(self):
        self.shield_sweep_hit_applied = True

    @property
    def slam_hit_active(self):
        if not self.slamming or self.slam_hit_applied:
            return False
        frame = int(self.slam_elapsed * SLAM_ANIMATION_FPS)
        return SLAM_IMPACT_FRAME <= frame <= SLAM_IMPACT_FRAME_END

    def slam_hits(self, target):
        if not self.slam_hit_active:
            return False
        return self._target_in_slam_warning(target)

    def register_slam_hit(self):
        self.slam_hit_applied = True

    def _target_in_slam_warning(self, target):
        direction_x, direction_y = self.attack_direction
        target_x, target_y = target.hitbox_center
        dx = target_x - self.x
        dy = target_y - self.y
        screen_scale = self.movement_scale * SPRITE_SCALE
        forward = (
            (dx * direction_x + dy * direction_y) / screen_scale
            - SLAM_WARNING_FORWARD_OFFSET
        )
        lateral = abs(dx * direction_y - dy * direction_x) / screen_scale
        target_radius = target.collision_radius / screen_scale
        if not (
            -target_radius
            <= forward
            <= SLAM_WARNING_DEPTH + target_radius
        ):
            return False

        progress = min(max(forward / SLAM_WARNING_DEPTH, 0), 1)
        half_width = (
            SLAM_WARNING_START_HALF_WIDTH
            + (
                SLAM_WARNING_END_HALF_WIDTH
                - SLAM_WARNING_START_HALF_WIDTH
            )
            * progress
        )
        return lateral <= half_width + target_radius

    def _slam_effect_position(self, draw_scale=1.0):
        direction_x, direction_y = self.attack_direction
        offset = (
            60 * draw_scale + SLAM_WARNING_FORWARD_OFFSET
        ) * self.movement_scale * SPRITE_SCALE
        return (
            self.x + direction_x * offset,
            self.y + direction_y * offset,
        )

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
            _, warning_y = self._sweep_center()
            self.sweep_warning_sprite.clip_composite_draw(
                warning_frame * SWEEP_WARNING_FRAME_WIDTH,
                self.attack_sprite_direction * SWEEP_WARNING_FRAME_HEIGHT,
                SWEEP_WARNING_FRAME_WIDTH,
                SWEEP_WARNING_FRAME_HEIGHT,
                self._attack_rotation(),
                "",
                self.x - camera_x,
                warning_y - camera_y,
                SWEEP_WARNING_FRAME_WIDTH * screen_scale,
                SWEEP_WARNING_FRAME_HEIGHT * screen_scale,
            )

        if self.slamming:
            sprite = self.shield_slam_sprite
            frame_width = SLAM_FRAME_WIDTH
            frame_height = SLAM_FRAME_HEIGHT
            frame = min(
                int(self.slam_elapsed * SLAM_ANIMATION_FPS),
                SLAM_FRAME_COUNT - 1,
            )
        elif self.shield_sweeping:
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
        if self.shield_sweeping or self.slamming:
            draw_y += (
                (
                    SLAM_FOOT_Y
                    if self.slamming
                    else SHIELD_SWEEP_FOOT_Y
                )
                - (
                    SLAM_FRAME_HEIGHT
                    if self.slamming
                    else SHIELD_SWEEP_FRAME_HEIGHT
                ) / 2
                - IDLE_FOOT_Y
                + IDLE_FRAME_HEIGHT / 2
            ) * screen_scale
        sprite_direction = (
            self.attack_sprite_direction
            if self.slamming or self.shield_sweeping
            else self.direction
        )
        sprite.clip_draw(
            frame * frame_width,
            sprite_direction * frame_height,
            frame_width,
            frame_height,
            self.x - camera_x,
            draw_y - camera_y,
            frame_width * screen_scale,
            frame_height * screen_scale,
        )

    def draw_slam_effects(self, camera_x=0, camera_y=0):
        if not (self.slam_warning or self.slam_eruption):
            return

        screen_scale = self.movement_scale * SPRITE_SCALE
        if self.slam_warning:
            effect_x, effect_y = self._slam_effect_position()
            frame = int(
                self.slam_warning_elapsed * SLAM_WARNING_ANIMATION_FPS
            ) % SLAM_WARNING_FRAME_COUNT
            self.slam_warning_sprite.clip_composite_draw(
                frame * SLAM_WARNING_FRAME_WIDTH,
                self.attack_sprite_direction * SLAM_WARNING_FRAME_HEIGHT,
                SLAM_WARNING_FRAME_WIDTH,
                SLAM_WARNING_FRAME_HEIGHT,
                self._attack_rotation(),
                "",
                effect_x - camera_x,
                effect_y - camera_y,
                SLAM_WARNING_FRAME_WIDTH * screen_scale,
                SLAM_WARNING_FRAME_HEIGHT * screen_scale,
            )
        if self.slam_eruption:
            effect_x, effect_y = self._slam_effect_position(
                SLAM_ERUPTION_DRAW_SCALE
            )
            frame = min(
                int(
                    self.slam_eruption_elapsed
                    * SLAM_ERUPTION_ANIMATION_FPS
                ),
                SLAM_ERUPTION_FRAME_COUNT - 1,
            )
            self.slam_eruption_sprite.clip_composite_draw(
                frame * SLAM_FRAME_WIDTH,
                self.attack_sprite_direction * SLAM_FRAME_HEIGHT,
                SLAM_FRAME_WIDTH,
                SLAM_FRAME_HEIGHT,
                self._attack_rotation(),
                "",
                effect_x - camera_x,
                effect_y - camera_y,
                SLAM_FRAME_WIDTH * screen_scale * SLAM_ERUPTION_DRAW_SCALE,
                SLAM_FRAME_HEIGHT * screen_scale * SLAM_ERUPTION_DRAW_SCALE,
            )
