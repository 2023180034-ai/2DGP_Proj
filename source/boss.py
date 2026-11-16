import math
from pathlib import Path
import random

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
BOSS_COLLISION_RADIUS = 12
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
CHARGE_FRAME_WIDTH = 128
CHARGE_FRAME_HEIGHT = 128
CHARGE_FOOT_Y = 118
CHARGE_READY_FRAME_COUNT = 4
CHARGE_READY_ANIMATION_FPS = 8
CHARGE_FRAME_COUNT = 6
CHARGE_ANIMATION_FPS = 12
CHARGE_WARNING_FRAME_WIDTH = 200
CHARGE_WARNING_FRAME_HEIGHT = 48
CHARGE_WARNING_FRAME_COUNT = 8
CHARGE_WARNING_ANIMATION_FPS = 8
CHARGE_WARNING_DURATION = (
    CHARGE_WARNING_FRAME_COUNT / CHARGE_WARNING_ANIMATION_FPS
)
# 예고 화살표: 꼬리 x=2, 끝 x=198 (길이 196px). 꼬리를 보스 발에 두고
# 보스 몸 앞쪽이 화살표 끝에 닿을 때까지 돌진한다.
CHARGE_WARNING_ARROW_LENGTH = 196
CHARGE_DISTANCE = CHARGE_WARNING_ARROW_LENGTH - BOSS_COLLISION_RADIUS
CHARGE_SPEED = 300
CHARGE_HIT_MARGIN = 4
CHARGE_COOLDOWN = 12.0
BOSS1_CHARGE_DAMAGE = 150
JUMP_FRAME_WIDTH = 128
JUMP_FRAME_HEIGHT = 128
JUMP_FOOT_Y = 118
JUMP_FRAME_COUNT = 13
JUMP_ANIMATION_FPS = 12
JUMP_LIFTOFF_FRAME = 9  # 이 프레임에서 보스가 화면 위로 사라진다
JUMP_TAKEOFF_DURATION = JUMP_LIFTOFF_FRAME / JUMP_ANIMATION_FPS
JUMP_AIR_DURATION = 1.2  # 공중에 있는 시간 (착지 그림자 예고 시간)
JUMP_TRACK_DURATION = 0.6  # 도약 준비 + 공중 시간 앞부분까지 플레이어를 따라가고 이후 고정
LAND_FRAME_COUNT = 12
LAND_ANIMATION_FPS = 12
LAND_IMPACT_FRAME = 3
LAND_IMPACT_FRAME_END = 4
LAND_SHADOW_FRAME_COUNT = 8
# 그림자 마지막 프레임 타원: 가로 반지름 27.5px, 세로 반지름 8px (발 위치 중심)
LAND_SHADOW_RADIUS_X = 27.5
LAND_SHADOW_RADIUS_Y = 8
LAND_SHADOW_DRAW_SCALE = 1.75
JUMP_MIN_RANGE = 150  # 약 8.7m 이상 떨어져 있어야 점프 사용
JUMP_COOLDOWN = 15.0
BOSS1_JUMP_DAMAGE = 120
BOSS1_MAX_HP = 10_000
BOSS_STANDOFF_DISTANCE = 16
TIME_EPSILON = 1e-9
CHASE_DELAY = 3.0
BOSS_MOVE_SPEED = 80
BASE_SCREEN_HEIGHT = 600
SPRITE_SCALE = 3

SPRITE_DIRECTORY = Path(__file__).resolve().parent.parent / "sprites" / "boss1"



class Boss:
    def __init__(
        self,
        x,
        y,
        direction=dirs.DOWN,
        world_scale=1.0,
        max_hp=BOSS1_MAX_HP,
        world_width=None,
        world_height=None,
        north_boundary=None,
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
        self.charge_ready_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_charge_ready.png")
        )
        self.charge_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_charge.png")
        )
        self.charge_warning_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_charge_warning.png")
        )
        self.jump_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_jump.png")
        )
        self.land_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_land.png")
        )
        self.land_shadow_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "boss1_land_shadow.png")
        )
        self.world_width = world_width
        self.world_height = world_height
        self.north_boundary = north_boundary
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
        self.charge_warning = False
        self.charge_warning_elapsed = 0
        self.charging = False
        self.charge_elapsed = 0
        self.charge_length = 0
        self.charge_traveled = 0
        self.charge_hit_applied = False
        self.charge_cooldown = 0
        # 점프: None -> "takeoff" -> "air" -> "land" -> None
        self.jump_state = None
        self.jump_elapsed = 0
        self.jump_origin = (x, y)
        self.jump_target = (x, y)
        self.jump_hit_applied = False
        self.jump_cooldown = 0

    def update(self, player, delta_time):
        self.elapsed_time += delta_time
        self.animation_time += delta_time
        self.shield_sweep_cooldown = max(
            0,
            self.shield_sweep_cooldown - delta_time,
        )
        self.slam_cooldown = max(0, self.slam_cooldown - delta_time)
        self.charge_cooldown = max(0, self.charge_cooldown - delta_time)
        if self.shield_sweep_cooldown < TIME_EPSILON:
            self.shield_sweep_cooldown = 0
        if self.slam_cooldown < TIME_EPSILON:
            self.slam_cooldown = 0
        if self.charge_cooldown < TIME_EPSILON:
            self.charge_cooldown = 0
        self.jump_cooldown = max(0, self.jump_cooldown - delta_time)
        if self.jump_cooldown < TIME_EPSILON:
            self.jump_cooldown = 0
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

        if self.jump_state is not None:
            self._update_jump(player, delta_time)
            return

        if self.charging:
            self._update_charge(delta_time)
            return

        if self.charge_warning:
            self.charge_warning_elapsed += delta_time
            if (
                self.charge_warning_elapsed + TIME_EPSILON
                >= CHARGE_WARNING_DURATION
            ):
                self.charge_warning = False
                self.charging = True
                self.charge_elapsed = 0
                self.charge_traveled = 0
                self.charge_hit_applied = False
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
                in_sweep_range = distance <= shield_sweep_range
                # 휘두르기 사거리 밖일 때만 내려찍기/돌진을 쓴다.
                ranged_attacks = []
                if not in_sweep_range:
                    if (
                        distance <= SLAM_MAX_RANGE * self.movement_scale
                        and self.slam_cooldown == 0
                    ):
                        ranged_attacks.append(self._start_slam_warning)
                    if self.charge_cooldown == 0:
                        ranged_attacks.append(self._start_charge_warning)
                    if (
                        distance >= JUMP_MIN_RANGE * self.sprite_scale
                        and self.jump_cooldown == 0
                    ):
                        ranged_attacks.append(self._start_jump)

                if in_sweep_range and self.shield_sweep_cooldown == 0:
                    self._start_sweep_warning()
                elif ranged_attacks:
                    random.choice(ranged_attacks)()
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
                        self.x, self.y = self._clamp_to_world(self.x, self.y)
                        self.moving = True

        if self.moving:
            self.walk_animation_time += delta_time
        else:
            self.walk_animation_time = 0

    def _lock_attack_direction(self):
        self.attack_direction = self.aim_direction
        self.attack_sprite_direction = self.direction

    def _start_sweep_warning(self):
        self._lock_attack_direction()
        self.sweep_warning = True
        self.sweep_warning_elapsed = 0
        self.shield_sweep_cooldown = SHIELD_SWEEP_COOLDOWN

    def _start_slam_warning(self):
        self._lock_attack_direction()
        self.slam_warning = True
        self.slam_warning_elapsed = 0
        self.slam_cooldown = SLAM_COOLDOWN

    def _start_charge_warning(self):
        self._lock_attack_direction()
        self.charge_warning = True
        self.charge_warning_elapsed = 0
        self.charge_cooldown = CHARGE_COOLDOWN
        # 벽에 막히면 그만큼 짧게 돌진하고, 예고 화살표도 그 길이로 그린다.
        self.charge_length = self._charge_length_to_wall(
            CHARGE_DISTANCE * self.sprite_scale
        )

    def _update_charge(self, delta_time):
        self.charge_elapsed += delta_time
        step = min(
            CHARGE_SPEED * self.sprite_scale * delta_time,
            self.charge_length - self.charge_traveled,
        )
        direction_x, direction_y = self.attack_direction
        self.x, self.y = self._clamp_to_world(
            self.x + direction_x * step,
            self.y + direction_y * step,
        )
        self.charge_traveled += step
        if self.charge_traveled + TIME_EPSILON >= self.charge_length:
            self.charging = False

    def _start_jump(self):
        self._lock_attack_direction()
        self.jump_state = "takeoff"
        self.jump_elapsed = 0
        self.jump_cooldown = JUMP_COOLDOWN

    def _foot_offset(self):
        """보스 중심에서 발까지의 거리 (화면 px)."""
        return (IDLE_FOOT_Y - IDLE_FRAME_HEIGHT / 2) * self.sprite_scale

    def _track_jump_target(self, player):
        foot_x, foot_y = player.hitbox_center
        self.jump_target = self._clamp_to_world(
            foot_x,
            foot_y + self._foot_offset(),
        )

    def _update_jump(self, player, delta_time):
        self.jump_elapsed += delta_time
        if self.jump_state == "takeoff":
            self._track_jump_target(player)
            frame = int(self.jump_elapsed * JUMP_ANIMATION_FPS)
            if frame >= JUMP_LIFTOFF_FRAME:
                self.jump_state = "air"
                self.jump_elapsed = 0
                self.jump_origin = (self.x, self.y)
        elif self.jump_state == "air":
            if self.jump_elapsed <= JUMP_TRACK_DURATION:
                self._track_jump_target(player)
            if self.jump_elapsed + TIME_EPSILON >= JUMP_AIR_DURATION:
                target_x, target_y = self.jump_target
                self._face_target(target_x - self.x, target_y - self.y)
                self._lock_attack_direction()
                self.x, self.y = self.jump_target
                self.jump_state = "land"
                self.jump_elapsed = 0
                self.jump_hit_applied = False
        elif self.jump_state == "land":
            if self.jump_elapsed + TIME_EPSILON >= (
                LAND_FRAME_COUNT / LAND_ANIMATION_FPS
            ):
                self.jump_state = None

    @property
    def is_airborne(self):
        """공중에 있어서 맞지도 않고 부딪히지도 않는 상태."""
        if self.jump_state == "air":
            return True
        if self.jump_state == "land":
            frame = int(self.jump_elapsed * LAND_ANIMATION_FPS)
            return frame < LAND_IMPACT_FRAME
        return False

    def _world_limits(self):
        """보스 중심(self.x, self.y)이 있을 수 있는 범위. 맵 정보가 없으면 None."""
        if self.world_width is None or self.world_height is None:
            return None
        radius = self.collision_radius
        foot_offset = (IDLE_FOOT_Y - IDLE_FRAME_HEIGHT / 2) * self.sprite_scale
        max_y = self.world_height - radius
        if self.north_boundary is not None:
            max_y = min(max_y, self.north_boundary)
        return radius, foot_offset, self.world_width - radius, max_y

    def _clamp_to_world(self, x, y):
        limits = self._world_limits()
        if limits is None:
            return x, y
        min_x, min_y, max_x, max_y = limits
        return min(max(x, min_x), max_x), min(max(y, min_y), max_y)

    def _charge_length_to_wall(self, length):
        limits = self._world_limits()
        if limits is None:
            return length
        min_x, min_y, max_x, max_y = limits
        direction_x, direction_y = self.attack_direction
        for position, velocity, low, high in (
            (self.x, direction_x, min_x, max_x),
            (self.y, direction_y, min_y, max_y),
        ):
            if velocity > TIME_EPSILON:
                length = min(length, (high - position) / velocity)
            elif velocity < -TIME_EPSILON:
                length = min(length, (low - position) / velocity)
        return max(0, length)

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
        """피해를 주고, 실제로 깎인 체력을 돌려준다 (이미 죽었으면 0)."""
        if self.is_dead:
            return 0
        dealt = min(self.hp, amount)
        self.hp -= dealt
        return dealt

    @property
    def movement_scale(self):
        return (
            pico2d.get_canvas_height()
            / BASE_SCREEN_HEIGHT
            * self.world_scale
        )

    @property
    def sprite_scale(self):
        """스프라이트 1px이 화면에서 몇 px인지."""
        return self.movement_scale * SPRITE_SCALE

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

    def charge_hits(self, target):
        """돌진 중 몸에 부딪히면 맞는다 (돌진 한 번에 한 번만)."""
        if not self.charging or self.charge_hit_applied:
            return False
        hit_distance = (
            self.collision_radius
            + target.collision_radius
            + CHARGE_HIT_MARGIN * self.sprite_scale
        )
        return math.hypot(target.x - self.x, target.y - self.y) <= hit_distance

    def register_charge_hit(self):
        self.charge_hit_applied = True

    def jump_hits(self, target):
        """착지 충격 프레임에 그림자 타원 안에 대상의 발이 있으면 맞는다."""
        if self.jump_state != "land" or self.jump_hit_applied:
            return False
        frame = int(self.jump_elapsed * LAND_ANIMATION_FPS)
        if not LAND_IMPACT_FRAME <= frame <= LAND_IMPACT_FRAME_END:
            return False
        foot_x, foot_y = self._foot_position()
        target_x, target_y = target.hitbox_center
        scale = self.sprite_scale * LAND_SHADOW_DRAW_SCALE
        radius_x = LAND_SHADOW_RADIUS_X * scale + target.collision_radius
        radius_y = LAND_SHADOW_RADIUS_Y * scale + target.collision_radius
        return (
            ((target_x - foot_x) / radius_x) ** 2
            + ((target_y - foot_y) / radius_y) ** 2
            <= 1
        )

    def register_jump_hit(self):
        self.jump_hit_applied = True

    def _draw_land_shadow(self, camera_x, camera_y):
        """착지 예고 그림자. 도약 준비부터 착지 직전까지 점점 커진다."""
        if self.jump_state == "takeoff":
            warning_elapsed = self.jump_elapsed
        else:
            warning_elapsed = JUMP_TAKEOFF_DURATION + self.jump_elapsed
        progress = warning_elapsed / (JUMP_TAKEOFF_DURATION + JUMP_AIR_DURATION)
        frame = min(
            int(progress * LAND_SHADOW_FRAME_COUNT),
            LAND_SHADOW_FRAME_COUNT - 1,
        )
        target_x, target_y = self.jump_target
        shadow_scale = self.sprite_scale * LAND_SHADOW_DRAW_SCALE
        # 시트의 발 위치(위에서 118px)는 칸 가운데보다 54px 아래
        # -> 칸 가운데는 착지 발 위치보다 54px 위에 그린다.
        shadow_center_y = (
            target_y
            - self._foot_offset()
            + (JUMP_FOOT_Y - JUMP_FRAME_HEIGHT / 2) * shadow_scale
        )
        self.land_shadow_sprite.clip_draw(
            frame * JUMP_FRAME_WIDTH,
            0,
            JUMP_FRAME_WIDTH,
            JUMP_FRAME_HEIGHT,
            target_x - camera_x,
            shadow_center_y - camera_y,
            JUMP_FRAME_WIDTH * shadow_scale,
            JUMP_FRAME_HEIGHT * shadow_scale,
        )

    def _draw_jump_air(self, camera_x, camera_y):
        screen_scale = self.sprite_scale
        self._draw_land_shadow(camera_x, camera_y)
        # 뛰어오른 자리에 남는 먼지 (점프 시트 9~12프레임)
        dust_frame = JUMP_LIFTOFF_FRAME + int(
            self.jump_elapsed * JUMP_ANIMATION_FPS
        )
        if dust_frame < JUMP_FRAME_COUNT:
            origin_x, origin_y = self.jump_origin
            self.jump_sprite.clip_draw(
                dust_frame * JUMP_FRAME_WIDTH,
                self.attack_sprite_direction * JUMP_FRAME_HEIGHT,
                JUMP_FRAME_WIDTH,
                JUMP_FRAME_HEIGHT,
                origin_x - camera_x,
                origin_y + self._draw_offset_for_foot(
                    JUMP_FOOT_Y, JUMP_FRAME_HEIGHT
                ) - camera_y,
                JUMP_FRAME_WIDTH * screen_scale,
                JUMP_FRAME_HEIGHT * screen_scale,
            )

    def _draw_offset_for_foot(self, foot_y_in_frame, frame_height):
        """발 위치가 다른 시트를 64칸 대기 모션과 발을 맞춰 그릴 때의 y 보정값."""
        return (
            foot_y_in_frame
            - frame_height / 2
            - IDLE_FOOT_Y
            + IDLE_FRAME_HEIGHT / 2
        ) * self.sprite_scale

    def _foot_position(self):
        return self.x, self.y - self._foot_offset()

    def _draw_charge_warning(self, camera_x, camera_y):
        screen_scale = self.sprite_scale
        arrow_length = (
            self.charge_length + BOSS_COLLISION_RADIUS * screen_scale
        )
        stretch = arrow_length / (CHARGE_WARNING_ARROW_LENGTH * screen_scale)
        direction_x, direction_y = self.attack_direction
        foot_x, foot_y = self._foot_position()
        frame = int(
            self.charge_warning_elapsed * CHARGE_WARNING_ANIMATION_FPS
        ) % CHARGE_WARNING_FRAME_COUNT
        self.charge_warning_sprite.clip_composite_draw(
            0,
            (CHARGE_WARNING_FRAME_COUNT - 1 - frame)
            * CHARGE_WARNING_FRAME_HEIGHT,
            CHARGE_WARNING_FRAME_WIDTH,
            CHARGE_WARNING_FRAME_HEIGHT,
            math.atan2(direction_y, direction_x),
            "",
            foot_x + direction_x * arrow_length / 2 - camera_x,
            foot_y + direction_y * arrow_length / 2 - camera_y,
            CHARGE_WARNING_FRAME_WIDTH * screen_scale * stretch,
            CHARGE_WARNING_FRAME_HEIGHT * screen_scale,
        )

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
        if self.jump_state == "air":
            self._draw_jump_air(camera_x, camera_y)
            return
        if self.jump_state == "takeoff":
            self._draw_land_shadow(camera_x, camera_y)

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

        if self.charge_warning:
            self._draw_charge_warning(camera_x, camera_y)

        foot_y_in_frame = None
        if self.jump_state == "takeoff":
            sprite = self.jump_sprite
            frame_width = JUMP_FRAME_WIDTH
            frame_height = JUMP_FRAME_HEIGHT
            foot_y_in_frame = JUMP_FOOT_Y
            frame = min(
                int(self.jump_elapsed * JUMP_ANIMATION_FPS),
                JUMP_FRAME_COUNT - 1,
            )
        elif self.jump_state == "land":
            sprite = self.land_sprite
            frame_width = JUMP_FRAME_WIDTH
            frame_height = JUMP_FRAME_HEIGHT
            foot_y_in_frame = JUMP_FOOT_Y
            frame = min(
                int(self.jump_elapsed * LAND_ANIMATION_FPS),
                LAND_FRAME_COUNT - 1,
            )
        elif self.charging:
            sprite = self.charge_sprite
            frame_width = CHARGE_FRAME_WIDTH
            frame_height = CHARGE_FRAME_HEIGHT
            foot_y_in_frame = CHARGE_FOOT_Y
            frame = (
                int(self.charge_elapsed * CHARGE_ANIMATION_FPS)
                % CHARGE_FRAME_COUNT
            )
        elif self.charge_warning:
            sprite = self.charge_ready_sprite
            frame_width = CHARGE_FRAME_WIDTH
            frame_height = CHARGE_FRAME_HEIGHT
            foot_y_in_frame = CHARGE_FOOT_Y
            frame = min(
                int(self.charge_warning_elapsed * CHARGE_READY_ANIMATION_FPS),
                CHARGE_READY_FRAME_COUNT - 1,
            )
        elif self.slamming:
            sprite = self.shield_slam_sprite
            frame_width = SLAM_FRAME_WIDTH
            frame_height = SLAM_FRAME_HEIGHT
            foot_y_in_frame = SLAM_FOOT_Y
            frame = min(
                int(self.slam_elapsed * SLAM_ANIMATION_FPS),
                SLAM_FRAME_COUNT - 1,
            )
        elif self.shield_sweeping:
            sprite = self.shield_sweep_sprite
            frame_width = SHIELD_SWEEP_FRAME_WIDTH
            frame_height = SHIELD_SWEEP_FRAME_HEIGHT
            foot_y_in_frame = SHIELD_SWEEP_FOOT_Y
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
        if foot_y_in_frame is not None:
            # 128칸 시트는 발 위치가 달라서 64칸 대기 모션과 발을 맞춰 그린다.
            draw_y += self._draw_offset_for_foot(foot_y_in_frame, frame_height)
        sprite_direction = (
            self.attack_sprite_direction
            if foot_y_in_frame is not None
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
