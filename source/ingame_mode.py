from pathlib import Path

import pico2d

from boss import (
    BOSS1_CHARGE_DAMAGE,
    BOSS1_JUMP_DAMAGE,
    BOSS1_SHIELD_SWEEP_DAMAGE,
    BOSS1_SLAM_DAMAGE,
    Boss,
)
from camera import Camera
import direction as dirs
import game_framework
from game_over import GameOverUI
from gold_display import GoldDisplay
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
        # 골드는 맵을 바꿔도 유지된다 (게임을 끄면 사라짐, 저장은 아직 없음)
        self.gold_ui = GoldDisplay(gold=0)
        self.game_over = GameOverUI()
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
        # 이번 도전에서 보스에게 입힌 피해. 플레이어나 보스가 죽으면 골드로 정산
        self.run_damage = 0
        self.run_settled = False
        self.game_over.stop()

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            game_framework.quit()
        elif self.game_over.active:
            self._handle_game_over_event(event)
        elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_m:
            game_framework.push_mode(MapSelectMode(self))
        elif not self.player.is_dead:
            self.player.handle_event(event)

    def _handle_game_over_event(self, event):
        """사망 화면 버튼. 사망 중에는 플레이어 조작과 맵 선택(M)을 막는다."""
        result = self.game_over.handle_event(event)
        if result == "restart":
            self.reset_map("boss1")
        elif result == "quit":
            game_framework.quit()
        # "upgrade"(강화)는 아직 연결하지 않음

    def pause(self):
        self.player.clear_input()

    def update(self, delta_time):
        if self.game_over.active:
            # 사망 화면 동안 게임은 멈추고, 사망 화면과 골드 표시만 움직인다.
            self.game_over.update()
            self.gold_ui.update()
            return

        player = self.player
        boss = self.boss
        previous_player_x = player.x
        previous_player_y = player.y
        if not player.is_dead:
            player.update(delta_time)

        if boss is not None:
            if not boss.is_dead:
                boss.update(player, delta_time)
            # 공중에 뜬 보스와는 부딪히지 않고,
            # 돌진 중인 보스는 구르기(무적)로 뚫고 지나갈 수 있다.
            if not boss.is_airborne and not (
                boss.charging and player.is_invulnerable
            ):
                boss.resolve_player_collision(
                    player,
                    previous_player_x,
                    previous_player_y,
                )
            self._apply_player_attacks(player, boss)
            if not boss.is_dead:
                self._apply_boss_attacks(boss, player)
            self.boss_hp_bar.update(delta_time)
            if player.is_dead or boss.is_dead:
                self._settle_run()
            if player.is_dead:
                self.game_over.start()

        self.player_hp_bar.update(delta_time)
        self.gold_ui.update()
        self.camera.follow(player.x, player.y, delta_time)

    def _damage_boss(self, boss, amount):
        self.run_damage += boss.take_damage(amount)

    def _settle_run(self):
        """도전이 끝나면(플레이어 사망 또는 보스 처치) 입힌 피해를 골드로 적립."""
        if self.run_settled:
            return
        self.run_settled = True
        self.gold_ui.add(self.run_damage * self.player.gold_rate)

    def _apply_player_attacks(self, player, boss):
        skill_hit_events = player.consume_skill_hit_events()
        if boss.is_dead or player.is_dead or boss.is_airborne:
            return
        if player.attack_hits(boss):
            self._damage_boss(boss, PLAYER_ATTACK_DAMAGE)
            player.register_attack_hit()
        if skill_hit_events and player.skill_hits(boss):
            self._damage_boss(
                boss,
                PLAYER_SKILL_DAMAGE_PER_HIT * skill_hit_events,
            )

    def _apply_boss_attacks(self, boss, player):
        if boss.shield_sweep_hits(player) and player.take_damage(
            BOSS1_SHIELD_SWEEP_DAMAGE
        ):
            boss.register_shield_sweep_hit()
        if boss.slam_hits(player) and player.take_damage(BOSS1_SLAM_DAMAGE):
            boss.register_slam_hit()
        if boss.charge_hits(player) and player.take_damage(BOSS1_CHARGE_DAMAGE):
            boss.register_charge_hit()
        if boss.jump_hits(player) and player.take_damage(BOSS1_JUMP_DAMAGE):
            boss.register_jump_hit()

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
        self.game_over.draw()
        # 골드는 사망 화면(어두운 막) 위에 그려서 계속 또렷하게 보이게 한다.
        self.gold_ui.draw()
