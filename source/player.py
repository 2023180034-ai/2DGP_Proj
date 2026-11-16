import math
from pathlib import Path
import pico2d

import direction as dirs


FRAME_WIDTH = 128
FRAME_HEIGHT = 128
FRAME_COUNT = 12
RUN_FRAME_COUNT = 8
ROLL_FRAME_COUNT = 10
ATTACK_FRAME_COUNT = 12
SKILL_FRAME_WIDTH = 128
SKILL_FRAME_HEIGHT = 128
SKILL_FRAME_COUNT = 18
SKILL_ANIMATION_FPS = 15
SKILL_HIT_FRAMES = (3, 6, 9, 12, 15)
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
PLAYER_MAX_HP = 100
PLAYER_ATTACK_DAMAGE = 10
PLAYER_SKILL_DAMAGE_PER_HIT = int(PLAYER_ATTACK_DAMAGE * 0.6)
PLAYER_ATTACK_ACTIVE_FRAME_START = 4
PLAYER_ATTACK_ACTIVE_FRAME_END = 6
PLAYER_ATTACK_EXTRA_RANGE = 64
PLAYER_SKILL_EXTRA_RANGE = 64
BASE_SCREEN_HEIGHT = 600
WALL_COLLISION_CLEARANCE = 32
PLAYER_COLLISION_RADIUS = 24
PLAYER_HITBOX_FOOT_OFFSET = 44

SPRITE_DIRECTORY = Path(__file__).resolve().parent.parent / "sprites" / "player"

_RUN_KEYS = {pico2d.SDLK_LSHIFT, pico2d.SDLK_RSHIFT}
_ROLL_KEY = pico2d.SDLK_SPACE
_ATTACK_KEY = pico2d.SDLK_z
_SKILL_KEY = pico2d.SDLK_x
_DIRECTION_KEYS = {
    pico2d.SDLK_DOWN: (0, -1, dirs.DOWN),
    pico2d.SDLK_RIGHT: (1, 0, dirs.RIGHT),
    pico2d.SDLK_LEFT: (-1, 0, dirs.LEFT),
    pico2d.SDLK_UP: (0, 1, dirs.UP),
}
_SPRITE_ROW_BY_DIRECTION = (0, 2, 1, 3)


class Player:
    def __init__(
        self,
        world_width=None,
        world_height=None,
        spawn_x=None,
        spawn_y=None,
        direction=dirs.DOWN,
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
        self.skill_sprite = pico2d.load_image(
            str(SPRITE_DIRECTORY / "player_skill1.png")
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
        self.max_hp = PLAYER_MAX_HP
        self.hp = PLAYER_MAX_HP
        self.pressed_keys = []
        self.roll_key_held = False
        self.attack_key_held = False
        self.skill_key_held = False
        self.run_pressed = False
        self.equipped_skill = "combo_slash"
        self.animation_time = 0
        self.moving = False
        self.rolling = False
        self.roll_elapsed = 0
        self.roll_dx = 0
        self.roll_dy = 0
        self.attacking = False
        self.attack_elapsed = 0
        self.attack_hit_applied = False
        self.skill_attacking = False
        self.skill_elapsed = 0
        self.skill_hit_count = 0

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
        elif event.type == pico2d.SDL_KEYDOWN and event.key == _SKILL_KEY:
            if not self.skill_key_held:
                self.skill_key_held = True
                self._start_skill()
        elif event.type == pico2d.SDL_KEYUP and event.key == _SKILL_KEY:
            self.skill_key_held = False
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
        self.skill_key_held = False
        self.run_pressed = False

    @property
    def is_invulnerable(self):
        return self.rolling

    @property
    def is_dead(self):
        return self.hp <= 0

    def take_damage(self, amount):
        """피해를 입으면 True. 무적(구르기)이거나 이미 죽었으면 False."""
        if self.is_invulnerable or self.is_dead:
            return False
        self.hp = max(0, self.hp - amount)
        return True

    @property
    def collision_radius(self):
        screen_scale = (
            pico2d.get_canvas_height() / BASE_SCREEN_HEIGHT * self.world_scale
        )
        return PLAYER_COLLISION_RADIUS * screen_scale

    @property
    def hitbox_center(self):
        screen_scale = (
            pico2d.get_canvas_height() / BASE_SCREEN_HEIGHT * self.world_scale
        )
        return self.x, self.y - PLAYER_HITBOX_FOOT_OFFSET * screen_scale

    @property
    def attack_hit_active(self):
        if not self.attacking or self.attack_hit_applied:
            return False
        frame = int(self.attack_elapsed * ATTACK_ANIMATION_FPS)
        return (
            PLAYER_ATTACK_ACTIVE_FRAME_START
            <= frame
            <= PLAYER_ATTACK_ACTIVE_FRAME_END
        )

    def attack_hits(self, target):
        if not self.attack_hit_active:
            return False

        return self._hits_in_front(target, PLAYER_ATTACK_EXTRA_RANGE)

    def _hits_in_front(self, target, extra_range):
        direction_x, direction_y = dirs.VECTORS[self.direction]
        dx = target.x - self.x
        dy = target.y - self.y
        distance = math.hypot(dx, dy)
        max_distance = (
            self.collision_radius
            + target.collision_radius
            + extra_range
            * pico2d.get_canvas_height()
            / BASE_SCREEN_HEIGHT
            * self.world_scale
        )
        return (
            0 < distance <= max_distance
            and dx * direction_x + dy * direction_y >= distance * 0.5
        )

    def consume_skill_hit_events(self):
        if not self.skill_attacking:
            return 0

        frame = int(self.skill_elapsed * SKILL_ANIMATION_FPS)
        hit_events = 0
        while (
            self.skill_hit_count < len(SKILL_HIT_FRAMES)
            and frame >= SKILL_HIT_FRAMES[self.skill_hit_count]
        ):
            self.skill_hit_count += 1
            hit_events += 1
        return hit_events

    def skill_hits(self, target):
        return self.skill_attacking and self._hits_in_front(
            target,
            PLAYER_SKILL_EXTRA_RANGE,
        )

    def register_attack_hit(self):
        self.attack_hit_applied = True

    def _start_roll(self):
        if self.rolling or self.attacking or self.skill_attacking:
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
            dx, dy = dirs.VECTORS[self.direction]

        distance = math.hypot(dx, dy)
        self.roll_dx = dx / distance
        self.roll_dy = dy / distance
        self.rolling = True
        self.roll_elapsed = 0

    def _start_attack(self):
        if self.rolling or self.attacking or self.skill_attacking:
            return

        for key in self.pressed_keys:
            key_dx, key_dy, direction = _DIRECTION_KEYS[key]
            if key_dx or key_dy:
                self.direction = direction

        self.attacking = True
        self.attack_elapsed = 0
        self.attack_hit_applied = False

    def _start_skill(self):
        if (
            self.equipped_skill is None
            or self.rolling
            or self.attacking
            or self.skill_attacking
        ):
            return

        for key in self.pressed_keys:
            key_dx, key_dy, direction = _DIRECTION_KEYS[key]
            if key_dx or key_dy:
                self.direction = direction

        self.skill_attacking = True
        self.skill_elapsed = 0
        self.skill_hit_count = 0

    def update(self, delta_time):
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
        if self.skill_attacking:
            self.skill_elapsed += delta_time
            if self.skill_elapsed >= SKILL_FRAME_COUNT / SKILL_ANIMATION_FPS:
                self.skill_elapsed = SKILL_FRAME_COUNT / SKILL_ANIMATION_FPS
                self.skill_attacking = False

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
            frame_width = FRAME_WIDTH
            frame_height = FRAME_HEIGHT
        elif self.skill_attacking:
            sprite = self.skill_sprite
            frame = min(
                int(self.skill_elapsed * SKILL_ANIMATION_FPS),
                SKILL_FRAME_COUNT - 1,
            )
            frame_width = SKILL_FRAME_WIDTH
            frame_height = SKILL_FRAME_HEIGHT
        elif self.attacking:
            sprite = self.walk_attack_sprite if self.moving else self.attack_sprite
            frame = min(
                int(self.attack_elapsed * ATTACK_ANIMATION_FPS),
                ATTACK_FRAME_COUNT - 1,
            )
            frame_width = FRAME_WIDTH
            frame_height = FRAME_HEIGHT
        elif self.moving and self.run_pressed:
            sprite = self.run_sprite
            frame = int(self.animation_time * RUN_ANIMATION_FPS) % RUN_FRAME_COUNT
            frame_width = FRAME_WIDTH
            frame_height = FRAME_HEIGHT
        elif self.moving:
            sprite = self.walk_sprite
            frame = int(self.animation_time * ANIMATION_FPS) % FRAME_COUNT
            frame_width = FRAME_WIDTH
            frame_height = FRAME_HEIGHT
        else:
            sprite = self.idle_sprite
            frame = int(self.animation_time * ANIMATION_FPS) % FRAME_COUNT
            frame_width = FRAME_WIDTH
            frame_height = FRAME_HEIGHT
        left = frame * frame_width
        bottom = _SPRITE_ROW_BY_DIRECTION[self.direction] * frame_height
        sprite.clip_draw(
            left,
            bottom,
            frame_width,
            frame_height,
            self.x - camera_x,
            self.y - camera_y,
            frame_width * screen_scale,
            frame_height * screen_scale,
        )
