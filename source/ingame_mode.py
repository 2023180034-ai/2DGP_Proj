from pathlib import Path

import pico2d

from boss import (
    BOSS1_CHARGE_DAMAGE,
    BOSS1_SHIELD_SWEEP_DAMAGE,
    BOSS1_SLAM_DAMAGE,
    Boss,
)
from camera import Camera
import direction as dirs
import game_framework
from hp_bar import BossHpBar, PlayerHpBar
from map_select_mode import MapSelectMode
from player import (
    PLAYER_ATTACK_DAMAGE,
    PLAYER_SKILL_DAMAGE_PER_HIT,
    Player,
)


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
        spawn_direction = dirs.DOWN
        north_boundary = None
        boss = None
        if map_id == "boss1":
            spawn_y = world_height * 0.15
            spawn_direction = dirs.UP
            north_boundary = world_height * (1 - BOSS1_WALL_BOTTOM_RATIO)
            boss = Boss(
                world_width / 2,
                world_height * BOSS1_BOSS_POSITION_RATIO,
                direction=dirs.DOWN,
                world_scale=CAMERA_ZOOM,
                world_width=world_width,
                world_height=world_height,
                north_boundary=north_boundary,
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
        self.current_map_id = map_id
        self.background = background
        self.boss = boss
        self.player_hp_bar = PlayerHpBar(self.player)
        self.boss_hp_bar = (
            BossHpBar(boss, name="보스 1")
            if boss is not None
            else None
        )

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            game_framework.quit()
        elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_m:
            game_framework.push_mode(MapSelectMode(self))
        elif not self.player.is_dead:
            self.player.handle_event(event)

    def pause(self):
        self.player.clear_input()

    def update(self, delta_time):
        player = self.player
        boss = self.boss
        previous_player_x = player.x
        previous_player_y = player.y
        if not player.is_dead:
            player.update(delta_time)

        if boss is not None:
            if not boss.is_dead:
                boss.update(player, delta_time)
            # 돌진 중인 보스는 구르기(무적)로 뚫고 지나갈 수 있다.
            if not (boss.charging and player.is_invulnerable):
                boss.resolve_player_collision(
                    player,
                    previous_player_x,
                    previous_player_y,
                )
            self._apply_player_attacks(player, boss)
            if not boss.is_dead:
                self._apply_boss_attacks(boss, player)
            self.boss_hp_bar.update(delta_time)

        self.player_hp_bar.update(delta_time)
        self.camera.follow(player.x, player.y, delta_time)

    def _apply_player_attacks(self, player, boss):
        skill_hit_events = player.consume_skill_hit_events()
        if boss.is_dead or player.is_dead:
            return
        if player.attack_hits(boss):
            boss.take_damage(PLAYER_ATTACK_DAMAGE)
            player.register_attack_hit()
        if skill_hit_events and player.skill_hits(boss):
            boss.take_damage(PLAYER_SKILL_DAMAGE_PER_HIT * skill_hit_events)

    def _apply_boss_attacks(self, boss, player):
        if boss.shield_sweep_hits(player) and player.take_damage(
            BOSS1_SHIELD_SWEEP_DAMAGE
        ):
            boss.register_shield_sweep_hit()
        if boss.slam_hits(player) and player.take_damage(BOSS1_SLAM_DAMAGE):
            boss.register_slam_hit()
        if boss.charge_hits(player) and player.take_damage(BOSS1_CHARGE_DAMAGE):
            boss.register_charge_hit()

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
        if self.boss is not None:
            self.boss.draw_slam_effects(self.camera.x, self.camera.y)
        self.player_hp_bar.draw()
        if self.boss_hp_bar is not None:
            self.boss_hp_bar.draw()
